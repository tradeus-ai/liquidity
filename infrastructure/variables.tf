variable "tenancy_ocid" {
  description = "OCI Tenancy OCID"
  type        = string
}

variable "user_ocid" {
  description = "OCI User OCID"
  type        = string
}

variable "fingerprint" {
  description = "OCI API Key Fingerprint"
  type        = string
}

variable "private_key_path" {
  description = "OCI API Private Key Path"
  type        = string
}

variable "compartment_ocid" {
  description = "OCI Compartment OCID"
  type        = string
}

variable "region" {
  description = "OCI Region (e.g., us-ashburn-1)"
  type        = string
}

variable "ssh_public_key_path" {
  description = "Path to the SSH public key for the instance"
  type        = string
  default     = "/home/arun-sush/Downloads/OCI - ajtvsv07@hotmail.com/ssh-key-2026-07-29.key.pub"
}
