# UNiCORE Automated Attendance Service

Automated attendance check-in and check-out service for the UNiCORE ERP system built in Python. Designed for reliable background operation on local systems or cloud Linux servers (e.g. AWS EC2 Amazon Linux 2023).

---

## 🌟 Key Features

1. **Randomized Daily Scheduling (Mongolia Timezone)**:
   - **Check-In**: Picks a random time between **08:30 and 08:50 AM** (`Asia/Ulaanbaatar` UTC+8).
   - **Check-Out**: Picks a random time between **16:10 and 16:30 PM** (`Asia/Ulaanbaatar` UTC+8).
   - **Skip Weekends**: Automatically skips Saturday and Sunday (configurable).

2. **Realistic GPS Offset Simulation**:
   - Computes realistic GPS coordinates within a 200m radius of the target location (`Tselmeg Digital International School` at `47.896883, 106.889669`) using geodesic trigonometric offset matching the official mobile application.

3. **Multiple Execution Modes**:
   - `daemon`: Continuous long-running daemon loop.
   - `check-in`: Immediate manual check-in API call.
   - `check-out`: Immediate manual check-out API call.
   - `status`: Fetch current UNiCORE attendance status.
   - `test-schedule`: Preview generated random schedule for the next 7 days without making API calls.
   - `cron-checkin` & `cron-checkout`: Designed for Linux cron triggers with built-in random sleep (0-20 min).

4. **Notifications**:
   - Optional Telegram Bot and Discord Webhook integration for instant mobile notifications upon check-in/out success or failure.

5. **AWS Amazon Linux Ready**:
   - Includes 1-click installer (`setup_amazon_linux.sh`), `systemd` service unit (`unicore-attendance.service`), and `Dockerfile` + `docker-compose.yml`.

---

## 🚀 Getting Started

### 1. Configuration

Copy `.env.example` to `.env` and fill in your UNiCORE credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```env
UNICORE_LOGIN=your_email_or_phone@example.com
UNICORE_PASSWORD=your_password_here
TIMEZONE=Asia/Ulaanbaatar
SKIP_WEEKENDS=true
```

### 2. Manual / CLI Usage

```bash
# Preview upcoming 7-day schedule
python3 main.py test-schedule

# Check UNiCORE API status
python3 main.py status

# Trigger immediate manual Check-In
python3 main.py check-in

# Trigger immediate manual Check-Out
python3 main.py check-out

# Run continuous Daemon mode locally
python3 main.py daemon
```

---

## ☁️ Deployment on AWS Amazon Linux 2023 (EC2)

### Method A: Systemd Daemon (Recommended)

1. Launch an AWS EC2 instance with **Amazon Linux 2023** (t3.micro or t4g.nano free tier).
2. Transfer or clone this repository to `/home/ec2-user/unicore_auto_attendance`.
3. Create and edit your `.env` file:
   ```bash
   cp .env.example .env
   nano .env
   ```
4. Run the 1-click setup script:
   ```bash
   chmod +x setup_amazon_linux.sh
   ./setup_amazon_linux.sh
   ```
5. Start and monitor the service:
   ```bash
   sudo systemctl start unicore-attendance.service
   sudo systemctl status unicore-attendance.service
   sudo journalctl -u unicore-attendance.service -f
   ```

### Method B: Linux Crontab

If you prefer lightweight cron execution instead of a daemon:

Run `crontab -e` on Amazon Linux and add:
```cron
# Trigger check-in at 08:30 AM (script sleeps randomly between 0-20 mins until 08:50)
30 8 * * 1-5 /usr/bin/python3 /home/ec2-user/unicore_auto_attendance/main.py cron-checkin >> /home/ec2-user/unicore.log 2>&1

# Trigger check-out at 16:10 PM (script sleeps randomly between 0-20 mins until 16:30)
10 16 * * 1-5 /usr/bin/python3 /home/ec2-user/unicore_auto_attendance/main.py cron-checkout >> /home/ec2-user/unicore.log 2>&1
```

### Method C: Docker / Docker Compose

```bash
docker-compose up -d --build
docker-compose logs -f
```

---

## 📄 License

MIT License.
