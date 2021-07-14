variable "tags" {
  type = map
  default = { Name = "test-purl-obolibrary" }
}

variable "region" {
  default = "us-east-1"
}

variable eip_id {
  default = "eipalloc-0dcdeb0173415c6c0"
}

variable "instance_type" {
  default = "t2.micro" 
}

variable "key_name" {
  default = "purl-ssh-key"
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
  description = "purl  server port"
}
