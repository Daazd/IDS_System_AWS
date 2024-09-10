output "trex_instance_public_ip" {
  value       = aws_instance.trex_instance.public_ip
  description = "The public IP address of the TRex instance"
}

output "trex_private_key_path" {
  value = local_file.private_key.filename
}