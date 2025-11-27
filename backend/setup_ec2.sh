#!/bin/bash

# Exit on error
set -e

# Amazon Linux defaults
APP_DIR="/home/ec2-user/laf/backend"
VENV_DIR="$APP_DIR/venv"
USER="ec2-user"
SERVICE_NAME="laf"

echo "--- Starting Setup for Amazon Linux ---"

# 1. Install System Dependencies
echo "--- Installing System Dependencies ---"
sudo dnf update -y
# Install Python 3.11/3.12 (AL2023 usually has python3), git, gcc, postgresql-devel
sudo dnf install -y python3 python3-devel git gcc postgresql-devel acl

# 2. Navigate to App Directory
if [ ! -d "$APP_DIR" ]; then
    echo "Error: Directory $APP_DIR does not exist."
    echo "Please upload your code to /home/ec2-user/laf first."
    exit 1
fi
cd "$APP_DIR"

# 3. Create Virtual Environment
echo "--- Setting up Virtual Environment ---"
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi

# 4. Install Python Dependencies
echo "--- Installing Python Dependencies ---"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install .
pip install gunicorn uvloop httptools

# 5. Create Systemd Service
echo "--- Creating Systemd Service ---"
sudo bash -c "cat > /etc/systemd/system/$SERVICE_NAME.service" <<EOL
[Unit]
Description=Gunicorn instance to serve LAF Backend
After=network.target

[Service]
User=$USER
Group=$USER
WorkingDirectory=$APP_DIR
Environment="PATH=$VENV_DIR/bin"
EnvironmentFile=$APP_DIR/.env
ExecStart=$VENV_DIR/bin/gunicorn -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000 --workers 2
Restart=always

[Install]
WantedBy=multi-user.target
EOL

# 6. Start and Enable Service
echo "--- Starting Service ---"
sudo systemctl daemon-reload
sudo systemctl start $SERVICE_NAME
sudo systemctl enable $SERVICE_NAME

# 7. Configure Firewall (if needed, usually handled by Security Groups on AWS)
# Amazon Linux doesn't enable ufw by default, it relies on Security Groups.
echo "--- Setup Complete! ---"
echo "Your app should be running on port 8000."
echo "Check status with: sudo systemctl status $SERVICE_NAME"
