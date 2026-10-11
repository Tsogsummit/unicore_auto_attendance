import random
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, Tuple
import config

def parse_time_str(time_str: str) -> Tuple[int, int]:
    """Parses 'HH:MM' string into (hour, minute)."""
    parts = time_str.strip().split(":")
    return int(parts[0]), int(parts[1])

def get_random_datetime(target_date: date, start_time_str: str, end_time_str: str) -> datetime:
    """
    Returns a datetime object on target_date with a randomized time strictly between
    start_time_str ('08:30') and end_time_str ('08:50') in Mongolia timezone.
    """
    start_h, start_m = parse_time_str(start_time_str)
    end_h, end_m = parse_time_str(end_time_str)

    start_seconds = start_h * 3600 + start_m * 60
    end_seconds = end_h * 3600 + end_m * 60

    if end_seconds <= start_seconds:
        raise ValueError(f"Invalid time range: {start_time_str} to {end_time_str}")

    chosen_seconds = random.randint(start_seconds, end_seconds)
    hours = chosen_seconds // 3600
    minutes = (chosen_seconds % 3600) // 60
    seconds = chosen_seconds % 60

    dt_naive = datetime(target_date.year, target_date.month, target_date.day, hours, minutes, seconds)
    return dt_naive.replace(tzinfo=config.MONGOLIA_TZ)

def get_daily_schedule(target_date: date = None) -> Dict[str, Any]:
    """
    Calculates the random check-in and check-out schedule for a given date.
    Default date is today in Mongolia Timezone.
    Runs on Wednesday (2), Thursday (3), and Friday (4).
    """
    if target_date is None:
        target_date = datetime.now(config.MONGOLIA_TZ).date()

    # Python weekday: Monday=0, Tuesday=1, Wednesday=2, Thursday=3, Friday=4, Saturday=5, Sunday=6
    is_active_day = target_date.weekday() in (2, 3, 4)
    should_skip = not is_active_day

    check_in_dt = get_random_datetime(
        target_date, 
        config.CHECKIN_START_TIME, 
        config.CHECKIN_END_TIME
    )
    
    check_out_dt = get_random_datetime(
        target_date, 
        config.CHECKOUT_START_TIME, 
        config.CHECKOUT_END_TIME
    )

    return {
        "date": target_date.strftime("%Y-%m-%d"),
        "weekday": target_date.strftime("%A"),
        "is_weekend": target_date.weekday() >= 5,
        "should_skip": should_skip,
        "check_in": check_in_dt,
        "check_out": check_out_dt,
    }
