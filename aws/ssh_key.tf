resource "aws_key_pair" "ssh_key" {
  key_name   = var.key_name
  public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC1TL5/v2/fy0kyX68/W8YT2bML7XvK6IF84vgSYDCqk2E/UbsLXYbUEk5/nxFOBW+4gEmQP9D80jkAAOEN4zXalctKokib8SMHhCSzv+epCtqsbxKzU71Gfl9elJWNWZcwnCzwkZrO6RDZeu7Jcp3Asx4NiyAKd7PjWuLU8qmJo5rjwbAS4dumvlDLdjVWka4jRT02jVP5+p2J/+JwvZJCGMlEb6d4WKuy8UsO4wZXXzgwrYRPfBu3XaZFA19MoLAO1UyzZwKSsin7yg/+JN8IE7sIwvvL9pExD4DU0krfNyjAO8c88UhzrUbN/vEGxDXEIvvmIQ8k1MtHh8o6WwP3 AEssiari@aessiari-mba"
  tags       = var.tags
}
