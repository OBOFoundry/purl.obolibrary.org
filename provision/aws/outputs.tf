output "private_key_path" {
  value = var.private_key_path
}

output "public_ip" {
  value = aws_eip.purl_eip.public_ip
}
