variable "tags" {
  type = map
  default = { Name = "test-purl-obolibrary" }
}

variable "instance_type" {
  default = "t2.large" 
}

variable "key_name" {
  default = "test-purl-ssh-key"
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
  description = "noctua server port"
}
