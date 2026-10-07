terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 5.0.0"
    }
  }
}

provider "oci" {
  tenancy_ocid     = var.tenancy_ocid
  user_ocid        = var.user_ocid
  fingerprint      = var.fingerprint
  private_key_path = var.private_key_path
  region           = var.region
}

# --- Data Sources ---

# Get Availability Domains
data "oci_identity_availability_domains" "ads" {
  compartment_id = var.compartment_ocid
}

# Get latest Ubuntu 24.04 Minimal Image
data "oci_core_images" "ubuntu_24_04_minimal" {
  compartment_id           = var.compartment_ocid
  operating_system         = "Canonical Ubuntu"
  operating_system_version = "24.04 Minimal"
  shape                    = "VM.Standard.E2.1.Micro"
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
}

# --- Network Resources ---

resource "oci_core_vcn" "liquidity_vcn" {
  cidr_block     = "10.0.0.0/16"
  compartment_id = var.compartment_ocid
  display_name   = "liquidity-vcn"
}

resource "oci_core_internet_gateway" "liquidity_igw" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.liquidity_vcn.id
  display_name   = "liquidity-igw"
  enabled        = true
}

resource "oci_core_route_table" "liquidity_route_table" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.liquidity_vcn.id
  display_name   = "liquidity-route-table"

  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_internet_gateway.liquidity_igw.id
  }
}

resource "oci_core_security_list" "liquidity_security_list" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.liquidity_vcn.id
  display_name   = "liquidity-security-list"

  egress_security_rules {
    destination = "0.0.0.0/0"
    protocol    = "all"
  }

  # Allow SSH (Port 22)
  ingress_security_rules {
    protocol = "6" # TCP
    source   = "0.0.0.0/0"
    tcp_options {
      max = 22
      min = 22
    }
  }

  # Allow HTTP (Port 80)
  ingress_security_rules {
    protocol = "6" # TCP
    source   = "0.0.0.0/0"
    tcp_options {
      max = 80
      min = 80
    }
  }
}

resource "oci_core_subnet" "liquidity_public_subnet" {
  cidr_block                 = "10.0.1.0/24"
  compartment_id             = var.compartment_ocid
  vcn_id                     = oci_core_vcn.liquidity_vcn.id
  display_name               = "liquidity-public-subnet"
  route_table_id             = oci_core_route_table.liquidity_route_table.id
  security_list_ids          = [oci_core_security_list.liquidity_security_list.id]
  prohibit_public_ip_on_vnic = false
}

# --- Compute Resources ---

resource "oci_core_instance" "liquidity_instance" {
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  compartment_id      = var.compartment_ocid
  shape               = "VM.Standard.E2.1.Micro"
  display_name        = "liquidity-dashboard-vm"

  shape_config {
    ocpus         = 1
    memory_in_gbs = 1
  }

  create_vnic_details {
    subnet_id        = oci_core_subnet.liquidity_public_subnet.id
    assign_public_ip = true
  }

  source_details {
    source_type             = "image"
    source_id               = data.oci_core_images.ubuntu_24_04_minimal.images[0].id
    boot_volume_size_in_gbs = 150
  }

  metadata = {
    ssh_authorized_keys = file(var.ssh_public_key_path)
  }
}
