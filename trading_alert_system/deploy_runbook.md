# Deployment Runbook

## Overview
This runbook covers how to deploy the Trading Alert System to the OCI instance using the existing Terraform infrastructure.

## 1. Provision Infrastructure
1. Navigate to the `infrastructure/` directory.
2. Ensure you have your OCI credentials set up in `terraform.tfvars`.
3. Run `terraform init`.
4. Run `terraform plan` to verify resources.
5. Run `terraform apply` to provision the VM. The VM will be created with your SSH key.

## 2. Deploy Code
1. SSH into the newly created VM:
   ```bash
   ssh ubuntu@<VM_PUBLIC_IP>
   ```
2. Clone the repository or use `scp` / `rsync` to copy the `trading_alert_system` directory to the server.
   ```bash
   rsync -avz -e "ssh" ./trading_alert_system/ ubuntu@<VM_PUBLIC_IP>:~/trading_alert_system/
   ```

## 3. Set Up the Environment
On the VM:
1. Update system and install Python/pip/venv if not already installed:
   ```bash
   sudo apt update
   sudo apt install python3-venv python3-pip
   ```
2. Create and activate a virtual environment:
   ```bash
   cd ~/trading_alert_system
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 4. Run the Service
You can run it in a `tmux` session or create a `systemd` service for continuous background execution.

**Using systemd:**
1. Create a service file:
   ```bash
   sudo nano /etc/systemd/system/trading-alert.service
   ```
2. Add the following content:
   ```ini
   [Unit]
   Description=Trading Alert System
   After=network.target

   [Service]
   User=ubuntu
   WorkingDirectory=/home/ubuntu/trading_alert_system
   ExecStart=/home/ubuntu/trading_alert_system/venv/bin/python main.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
3. Enable and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable trading-alert.service
   sudo systemctl start trading-alert.service
   ```
4. View logs:
   ```bash
   journalctl -u trading-alert.service -f
   ```
