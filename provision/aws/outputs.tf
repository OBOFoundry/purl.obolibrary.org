output "public_ip" {
  value = aws_eip.purl_eip.public_ip
}

output "public_key_path" {
  value = var.public_key_path
}
