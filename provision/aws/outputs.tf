output "private_key_path" {
  value = var.private_key_path
}

output "http_port" {
  value = var.http_port
}

output "public_ip" {
  value = data.aws_eip.purl_eip.public_ip
}
