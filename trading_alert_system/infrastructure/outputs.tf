output "instance_public_ip" {
  description = "The public IP address of the Compute instance"
  value       = oci_core_instance.liquidity_instance.public_ip
}
