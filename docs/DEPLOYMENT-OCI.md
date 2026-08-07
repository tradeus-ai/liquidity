# OCI Terraform Deployment Guide

This document explains how to set up, configure, and execute the automated Terraform scripts and deployment pipeline to launch the Liquidity Market Structure Analyzer on an Oracle Cloud Infrastructure (OCI) instance.

---

## Prerequisites

### 1. Install Terraform
If you do not have Terraform installed on your system (Ubuntu), run the following commands in your terminal:

```bash
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform
```

### 2. Configure OCI Credentials
Terraform needs your Oracle Cloud API credentials to interact with your OCI account.
Create a new file called `terraform.tfvars` inside the `infrastructure/` directory:

```bash
nano infrastructure/terraform.tfvars
```

Paste your specific OCI details into that file (replace the placeholder values with your actual OCIDs):

```hcl
tenancy_ocid     = "ocid1.tenancy.oc1..."
user_ocid        = "ocid1.user.oc1..."
fingerprint      = "xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx"
private_key_path = "/path/to/your/oci_api_key.pem"
compartment_ocid = "ocid1.compartment.oc1..."
region           = "us-ashburn-1" # Or whichever region your tenancy is in
```
*(Note: `terraform.tfvars` is automatically ignored by Git to ensure your secrets stay safe).*

---

## Launching the Infrastructure

Once your credentials are in place, navigate into the infrastructure folder to provision the server:

```bash
cd infrastructure

# 1. Initialize the directory (downloads the OCI provider plugin)
terraform init

# 2. Preview what Terraform is going to create
terraform plan

# 3. Actually create the infrastructure (you will need to type "yes" to confirm)
terraform apply
```

The infrastructure script will automatically:
- Create a Virtual Cloud Network (VCN) and a public subnet.
- Configure Security Lists to open **Port 22 (SSH)** and **Port 80 (HTTP)**.
- Provision a `VM.Standard.E2.1.Micro` instance (Always Free tier eligible) running Ubuntu 24.04 Minimal.
- Inject your pre-configured SSH public key into the server.

---

## Deploying the Code

After `terraform apply` finishes successfully, it will print out the new server's Public IP address. 

To zip your local project code, SCP it securely to the cloud instance, and automatically start the system service, run the deployment wrapper script from the main project folder:

```bash
cd ..
./deploy_to_oci.sh
```

**What this script does:**
1. Looks up the instance Public IP automatically from Terraform.
2. Zips the `Liquidity` directory (excluding heavy/secret folders like `.git`, `.venv`, and `node_modules`).
3. Uses `scp` and your specific private key to push the zip to the new instance.
4. Uses `ssh` to connect to the instance, extract the files, and automatically executes `sudo ./deploy.sh` on the remote machine.

Once the script finishes, you can access your dashboard by visiting `http://<YOUR_INSTANCE_PUBLIC_IP>` in your browser!
