#!/bin/bash
# Script to build, zip, and deploy the Liquidity Dashboard to OCI

set -e

# Configuration
SSH_PRIVATE_KEY="/home/arun-sush/Downloads/OCI - ajtvsv07@hotmail.com/ssh-key-2026-07-29.key"
REMOTE_USER="ubuntu"
TMP_DIR="/tmp/liquidity_deploy"
ZIP_NAME="liquidity.zip"

echo "========================================================"
echo "Deploying Liquidity Market Structure Analyzer to OCI"
echo "========================================================"

# 1. Get Instance IP from Terraform
echo "[1/4] Fetching OCI Instance IP from Terraform..."
cd infrastructure
INSTANCE_IP=$(terraform output -raw instance_public_ip 2>/dev/null || true)
cd ..

if [ -z "$INSTANCE_IP" ] || [[ "$INSTANCE_IP" == *"No outputs found"* ]]; then
    echo "ERROR: Could not find instance_public_ip. Did you run 'terraform apply' in the infrastructure directory?"
    exit 1
fi

echo "Found Instance IP: $INSTANCE_IP"

# 2. Zip the directory
echo "[2/4] Zipping the application directory..."
rm -f $ZIP_NAME
zip -r $ZIP_NAME . -x "*.git*" "*node_modules*" "*.venv*" "*infrastructure/.terraform*" "*infrastructure/terraform.tfstate*" "*__pycache__*"

# 3. SCP the zip file to the instance
echo "[3/4] Copying files to the OCI instance..."
scp -o StrictHostKeyChecking=no -i "$SSH_PRIVATE_KEY" $ZIP_NAME $REMOTE_USER@$INSTANCE_IP:/tmp/$ZIP_NAME

# 4. SSH into the instance and deploy
echo "[4/4] Extracting and running deploy.sh on the instance..."
ssh -o StrictHostKeyChecking=no -i "$SSH_PRIVATE_KEY" $REMOTE_USER@$INSTANCE_IP << EOF
    set -e
    
    echo "Creating deployment directory..."
    mkdir -p $TMP_DIR
    
    echo "Unzipping files..."
    # Ensure unzip is installed
    sudo apt-get update && sudo apt-get install -y unzip
    
    unzip -o /tmp/$ZIP_NAME -d $TMP_DIR > /dev/null
    
    echo "Running deploy.sh..."
    cd $TMP_DIR
    chmod +x deploy.sh
    sudo ./deploy.sh
    
    echo "Cleaning up temp files..."
    rm -rf /tmp/$ZIP_NAME
EOF

echo "========================================================"
echo "Deployment automation finished successfully!"
echo "You can access your dashboard at: http://$INSTANCE_IP"
echo "========================================================"
