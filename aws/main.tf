resource "aws_instance" "purl_server" {
  ami                    = "ami-0169da6ccb6347f50"
  instance_type          = var.instance_type
  vpc_security_group_ids = [aws_security_group.test_purl_sg.id]
  subnet_id = aws_subnet.purl_app_stack_public_subnet.id
  key_name               = var.key_name
  tags                   = var.tags

  ebs_block_device {
    device_name           = "/dev/sda1"
    delete_on_termination = true
    tags                  = var.tags
    volume_size           = 100
  }
}
