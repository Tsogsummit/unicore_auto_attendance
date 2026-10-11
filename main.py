#!/usr/bin/env python3
import sys
import time
import argparse
import random
from datetime import datetime, timedelta
import config
from api import UnicoreApi, notify
from scheduler import get_daily_schedule

def format_dt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S %Z")

def run_checkin():
    print(f"\n[ATTENDANCE] Initiating Check-In at {format_dt(datetime.now(config.MONGOLIA_TZ))}...")
    api = UnicoreApi()
    try:
        token = api.login()
        res, loc = api.check_in(token)
        msg = (
            f"✅ [UNiCORE AUTO CHECK-IN SUCCESS]\n"
            f"• Time: {format_dt(datetime.now(config.MONGOLIA_TZ))}\n"
            f"• Location: {loc['location_name']}\n"
            f"• Coordinates: {loc['latitude']}, {loc['longitude']} ({loc['_distance_meters']}m offset)\n"
            f"• Response: {res}"
        )
        print(msg)
        notify(msg)
    except Exception as e:
        err_msg = f"❌ [UNiCORE AUTO CHECK-IN FAILED]\n• Error: {e}\n• Time: {format_dt(datetime.now(config.MONGOLIA_TZ))}"
        print(err_msg)
        notify(err_msg)

def run_checkout():
    print(f"\n[ATTENDANCE] Initiating Check-Out at {format_dt(datetime.now(config.MONGOLIA_TZ))}...")
    api = UnicoreApi()
    try:
        token = api.login()
        res, loc = api.check_out(token)
        msg = (
            f"✅ [UNiCORE AUTO CHECK-OUT SUCCESS]\n"
            f"• Time: {format_dt(datetime.now(config.MONGOLIA_TZ))}\n"
            f"• Location: {loc['location_name']}\n"
            f"• Coordinates: {loc['latitude']}, {loc['longitude']} ({loc['_distance_meters']}m offset)\n"
            f"• Response: {res}"
        )
        print(msg)
        notify(msg)
    except Exception as e:
        err_msg = f"❌ [UNiCORE AUTO CHECK-OUT FAILED]\n• Error: {e}\n• Time: {format_dt(datetime.now(config.MONGOLIA_TZ))}"
        print(err_msg)
        notify(err_msg)

def run_status():
    print(f"[STATUS] Fetching attendance status...")
    api = UnicoreApi()
    try:
        token = api.login()
        status = api.get_status(token)
        print(f"[STATUS RESPONSE]:\n{status}")
    except Exception as e:
        print(f"[STATUS ERROR]: {e}")

def print_test_schedule(days: int = 7):
    print(f"\n=== UNiCORE Random Attendance Schedule Preview (Next {days} Days) ===")
    print(f"Timezone: {config.TIMEZONE_STR}")
    print(f"Check-In Range: {config.CHECKIN_START_TIME} - {config.CHECKIN_END_TIME}")
    print(f"Check-Out Range: {config.CHECKOUT_START_TIME} - {config.CHECKOUT_END_TIME}")
    print(f"Active Weekdays: Wednesday-Friday\n" + "-"*60)

    today = datetime.now(config.MONGOLIA_TZ).date()
    for i in range(days):
        target_date = today + timedelta(days=i)
        sched = get_daily_schedule(target_date)
        skip_label = " [SKIP INACTIVE DAY]" if sched["should_skip"] else ""
        print(f"📅 {sched['date']} ({sched['weekday']}){skip_label}")
        if not sched["should_skip"]:
            print(f"   🟢 Check-In:  {sched['check_in'].strftime('%H:%M:%S')}")
            print(f"   🔴 Check-Out: {sched['check_out'].strftime('%H:%M:%S')}")
        print("-" * 60)

def run_cron_checkin():
    """Triggered by cron at 08:30: picks random sleep duration (0-20 min) before checking in."""
    today = datetime.now(config.MONGOLIA_TZ).date()
    if today.weekday() not in config.ACTIVE_WEEKDAYS:
        print("[CRON CHECKIN] Skipping inactive day today.")
        return

    delay_seconds = random.randint(0, 1200) # 0 to 20 minutes
    print(f"[CRON CHECKIN] Sleeping for {delay_seconds} seconds ({delay_seconds // 60}m {delay_seconds % 60}s) before check-in...")
    time.sleep(delay_seconds)
    run_checkin()

def run_cron_checkout():
    """Triggered by cron at 16:10: picks random sleep duration (0-20 min) before checking out."""
    today = datetime.now(config.MONGOLIA_TZ).date()
    if today.weekday() not in config.ACTIVE_WEEKDAYS:
        print("[CRON CHECKOUT] Skipping inactive day today.")
        return

    delay_seconds = random.randint(0, 1200) # 0 to 20 minutes
    print(f"[CRON CHECKOUT] Sleeping for {delay_seconds} seconds ({delay_seconds // 60}m {delay_seconds % 60}s) before check-out...")
    time.sleep(delay_seconds)
    run_checkout()

def run_daemon():
    print(f"🚀 Starting Unicore Auto-Attendance Daemon...")
    print(f"📍 Timezone: {config.TIMEZONE_STR}")
    print(f"⏰ Target Check-In: {config.CHECKIN_START_TIME} - {config.CHECKIN_END_TIME}")
    print(f"⏰ Target Check-Out: {config.CHECKOUT_START_TIME} - {config.CHECKOUT_END_TIME}")
    print(f"📅 Active Days: Wednesday-Friday")
    print(f"📍 Location: {config.LOCATION_NAME} ({config.CENTER_LATITUDE}, {config.CENTER_LONGITUDE})\n")

    while True:
        now = datetime.now(config.MONGOLIA_TZ)
        today = now.date()
        sched = get_daily_schedule(today)

        if sched["should_skip"]:
            print(f"[{format_dt(now)}] Today is {sched['weekday']} ({sched['date']}). Skipping inactive day. Sleeping until tomorrow...")
            tomorrow_start = datetime(today.year, today.month, today.day, 0, 0, 0, tzinfo=config.MONGOLIA_TZ) + timedelta(days=1)
            sleep_time = max(10, (tomorrow_start - now).total_seconds())
            time.sleep(sleep_time)
            continue

        check_in_target = sched["check_in"]
        check_out_target = sched["check_out"]

        print(f"[{format_dt(now)}] Daily Schedule generated for {sched['date']}:")
        print(f"   🟢 Check-In Target:  {format_dt(check_in_target)}")
        print(f"   🔴 Check-Out Target: {format_dt(check_out_target)}")

        # Phase 1: Wait for Check-In
        if now < check_in_target:
            wait_seconds = (check_in_target - now).total_seconds()
            print(f"⏳ Waiting {int(wait_seconds // 60)} minutes {int(wait_seconds % 60)} seconds until Check-In at {format_dt(check_in_target)}...")
            time.sleep(wait_seconds)
            run_checkin()
            now = datetime.now(config.MONGOLIA_TZ)
        else:
            print(f"ℹ️ Past check-in time for today.")

        # Phase 2: Wait for Check-Out
        if now < check_out_target:
            wait_seconds = (check_out_target - now).total_seconds()
            print(f"⏳ Waiting {int(wait_seconds // 60)} minutes {int(wait_seconds % 60)} seconds until Check-Out at {format_dt(check_out_target)}...")
            time.sleep(wait_seconds)
            run_checkout()
            now = datetime.now(config.MONGOLIA_TZ)
        else:
            print(f"ℹ️ Past check-out time for today.")

        # Sleep until midnight to start next day's schedule
        tomorrow = today + timedelta(days=1)
        next_day_midnight = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 1, 0, tzinfo=config.MONGOLIA_TZ)
        sleep_seconds = max(30, (next_day_midnight - datetime.now(config.MONGOLIA_TZ)).total_seconds())
        print(f"😴 Finished today's cycle. Sleeping {int(sleep_seconds // 3600)}h {int((sleep_seconds % 3600) // 60)}m until tomorrow midnight...\n")
        time.sleep(sleep_seconds)

def main():
    parser = argparse.ArgumentParser(description="UNiCORE Automated Attendance Service")
    parser.add_argument(
        "action",
        choices=["daemon", "check-in", "check-out", "status", "test-schedule", "cron-checkin", "cron-checkout"],
        help="Action to perform"
    )
    args = parser.parse_args()

    if args.action == "daemon":
        run_daemon()
    elif args.action == "check-in":
        run_checkin()
    elif args.action == "check-out":
        run_checkout()
    elif args.action == "status":
        run_status()
    elif args.action == "test-schedule":
        print_test_schedule()
    elif args.action == "cron-checkin":
        run_cron_checkin()
    elif args.action == "cron-checkout":
        run_cron_checkout()

if __name__ == "__main__":
    main()
