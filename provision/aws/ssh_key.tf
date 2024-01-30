resource "aws_key_pair" "ssh_key" {
  public_key = file(var.public_key_path)
  tags       = var.tags
}
