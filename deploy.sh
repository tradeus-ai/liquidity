#!/bin/bash
# Liquidity Market Structure Analyzer - Ubuntu 24.04 LTS Deployment Script

set -e # Exit immediately if a command exits with a non-zero status

# --- Configuration ---
APP_DIR="/opt/liquidity"
APP_REPO_DIR="$(pwd)"
SERVICE_NAME="liquidity-dashboard"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
PORT=80
USERNAME=${SUDO_USER:-$(whoami)}

echo "========================================================"
echo "Starting deployment of Liquidity Market Structure Analyzer"
echo "Target OS: Ubuntu 24.04 LTS"
echo "========================================================"

# 0. Clean up existing service
echo "[0/6] Checking for existing service..."
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "Stopping existing $SERVICE_NAME service..."
    sudo systemctl stop $SERVICE_NAME
fi

if systemctl is-enabled --quiet $SERVICE_NAME 2>/dev/null; then
    echo "Disabling existing $SERVICE_NAME service..."
    sudo systemctl disable $SERVICE_NAME
fi

if [ -f "$SERVICE_FILE" ]; then
    echo "Removing existing service file..."
    sudo rm -f "$SERVICE_FILE"
    sudo systemctl daemon-reload
fi

# 1. System Updates and Dependencies
echo "[1/6] Updating system and installing dependencies..."
export DEBIAN_FRONTEND=noninteractive
export NEEDRESTART_MODE=a
sudo -E apt-get update
sudo -E apt-get install -y python3 python3-venv python3-pip git curl htop

# 2. Setup Application Directory
echo "[2/6] Setting up application directory at $APP_DIR..."
sudo mkdir -p $APP_DIR
# Assuming we are running this from the repository root, copy files
sudo cp -r $APP_REPO_DIR/* $APP_DIR/
# Copy the hidden files like .env and .venv might be too much, but we need config.py (it's not hidden)
sudo chown -R $USERNAME:$USERNAME $APP_DIR

# 3. Setup Virtual Environment and Install Python Dependencies
echo "[3/6] Setting up Python virtual environment..."
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
git+https://github.com/rongardF/tvdatafeed.git
pyarrow
lightweight_charts
EOF

pip install -r requirements.txt

# 4. Configure Systemd Service
echo "[4/6] Configuring systemd service ($SERVICE_NAME)..."

sudo bash -c "cat > $SERVICE_FILE" << EOF
[Unit]
Description=Liquidity Market Structure Analyzer Dashboard
After=network.target

[Service]
User=$USERNAME
AmbientCapabilities=CAP_NET_BIND_SERVICE
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/.venv/bin"
# Executing app.py which binds to PORT 80
ExecStart=$APP_DIR/.venv/bin/python $APP_DIR/app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 5. Start and Enable Service
echo "[5/6] Starting and enabling the service..."
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
