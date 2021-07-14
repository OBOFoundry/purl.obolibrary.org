resource "aws_vpc" "purl_app_stack_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true 
  enable_dns_hostnames = true 
  tags                 = var.tags
}

data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_subnet" "purl_app_stack_public_subnet" {
  vpc_id                  = aws_vpc.purl_app_stack_vpc.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true
  availability_zone       = data.aws_availability_zones.available.names[0]
  tags                    = var.tags
}

resource "aws_internet_gateway" "purl_app_stack_igw" {
  vpc_id = aws_vpc.purl_app_stack_vpc.id
  tags   = var.tags
}

resource "aws_route_table" "purl_app_stack_public_routing_table" {
  vpc_id = aws_vpc.purl_app_stack_vpc.id
  tags   = var.tags
    
  route {
    cidr_block = "0.0.0.0/0"         
    gateway_id = aws_internet_gateway.purl_app_stack_igw.id 
  }
}

resource "aws_route_table_association" "purl_app_stack_public_route_table_association" {
  subnet_id      = aws_subnet.purl_app_stack_public_subnet.id
  route_table_id = aws_route_table.purl_app_stack_public_routing_table.id
}
