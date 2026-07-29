#!/bin/bash
# Liquidity Market Structure Analyzer - Ubuntu 20.04 Deployment Script

set -e # Exit immediately if a command exits with a non-zero status

# --- Configuration ---
APP_DIR="/opt/liquidity"
APP_REPO_DIR="$(pwd)"
SERVICE_NAME="liquidity-dashboard"
PORT=8081
USERNAME=$(whoami)

echo "========================================================"
echo "Starting deployment of Liquidity Market Structure Analyzer"
echo "Target OS: Ubuntu 20.04"
echo "========================================================"

# 1. System Updates and Dependencies
echo "[1/5] Updating system and installing dependencies..."
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip git curl htop

# 2. Setup Application Directory
echo "[2/5] Setting up application directory at $APP_DIR..."
sudo mkdir -p $APP_DIR
# Assuming we are running this from the repository root, copy files
sudo cp -r $APP_REPO_DIR/* $APP_DIR/
sudo chown -R $USERNAME:$USERNAME $APP_DIR

# 3. Setup Virtual Environment and Install Python Dependencies
echo "[3/5] Setting up Python virtual environment..."
cd $APP_DIR
python3 -m venv .venv

echo "Installing Python packages..."
source .venv/bin/activate
pip install --upgrade pip

# Create a requirements.txt if it doesn't exist
cat <<EOF > requirements.txt
pandas
numpy
mplfinance
tvDatafeed
pyarrow
lightweight_charts
EOF

pip install -r requirements.txt

# 4. Configure Systemd Service
echo "[4/5] Configuring systemd service ($SERVICE_NAME)..."
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

sudo bash -c "cat > $SERVICE_FILE" << EOF
[Unit]
Description=Liquidity Market Structure Analyzer Dashboard
After=network.target

[Service]
User=$USERNAME
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/.venv/bin"
# Executing app.py which binds to PORT 8081
ExecStart=$APP_DIR/.venv/bin/python $APP_DIR/app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 5. Start and Enable Service
echo "[5/5] Starting and enabling the service..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl restart $SERVICE_NAME

echo "========================================================"
echo "Deployment Complete!"
echo "The dashboard is now running as a background service."
echo "You can check the status with: sudo systemctl status $SERVICE_NAME"
echo "You can view logs with: sudo journalctl -u $SERVICE_NAME -f"
echo "The application should be accessible at http://<your-server-ip>:$PORT"
echo "========================================================"
