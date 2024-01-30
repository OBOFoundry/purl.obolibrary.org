resource "aws_instance" "purl_server" {
  ami                    = var.ami
  instance_type          = var.instance_type
  vpc_security_group_ids = [aws_security_group.purl_sg.id]
  subnet_id              = aws_subnet.purl_app_stack_public_subnet.id
  key_name               = aws_key_pair.ssh_key.key_name
  tags                   = var.tags

  ebs_block_device {
    device_name           = "/dev/sda1"
    delete_on_termination = true
    tags                  = var.tags
    volume_size           = var.disk_size 
  }

  lifecycle {
    ignore_changes = [
      ebs_block_device,
      tags,
    ]
  }
}

resource "aws_eip" "purl_eip" {
  vpc   = true
  tags  = var.tags
}

resource "aws_eip_association" "eip_assoc" {
  instance_id   = aws_instance.purl_server.id
  allocation_id = aws_eip.purl_eip.id
}
