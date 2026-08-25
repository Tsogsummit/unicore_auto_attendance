#!/bin/bash
set -e

echo "=== UNiCORE Auto-Attendance Amazon Linux 2023 Setup Script ==="

# Install python3 if not present
sudo dnf update -y
sudo dnf install -y python3 python3-pip git

# Set system timezone to Asia/Ulaanbaatar if supported
sudo timedatectl set-timezone Asia/Ulaanbaatar 2>/dev/null || true

# Setup target directory
TARGET_DIR="/home/ec2-user/unicore_auto_attendance"
if [ "$PWD" != "$TARGET_DIR" ]; then
    echo "Setting up directory at $TARGET_DIR..."
    mkdir -p $TARGET_DIR
    cp -r ./* $TARGET_DIR/ 2>/dev/null || true
fi

cd $TARGET_DIR

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env from template..."
    cp .env.example .env
    echo "⚠️ IMPORTANT: Please edit .env with your UNiCORE login credentials!"
fi

# Install systemd service
echo "Installing systemd service..."
sudo cp unicore-attendance.service /etc/systemd/system/unicore-attendance.service
sudo systemctl daemon-reload
sudo systemctl enable unicore-attendance.service

echo ""
echo "✅ Setup Completed!"
echo "• To start service:   sudo systemctl start unicore-attendance.service"
echo "• To check status:   sudo systemctl status unicore-attendance.service"
echo "• To view live logs: sudo journalctl -u unicore-attendance.service -f"
