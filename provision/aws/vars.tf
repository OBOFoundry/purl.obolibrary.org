variable "tags" {
  type = map
  default = { Name = "test-purl-obolibrary" }
}

variable "region" {
  default = "us-east-1"
}

variable "ami" {
  default = "ami-01e51d86b60c02297"
}

variable "disk_size" {
  default = 100
  description = "size of disk in Gigabytes"
}

variable "instance_type" {
  default = "t2.micro" 
}

variable "public_key_path" {
  default = "~/.ssh/id_rsa.pub"
}

variable "private_key_path" {
  default = "~/.ssh/id_rsa"
}

variable "ssh_port" {
  type        = number
  default     = 22
  description = "ssh server port"
}

variable "http_port" {
  type        = number
  default     = 80
  description = "purl server port"
}
