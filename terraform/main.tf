provider "aws" {
  region = var.region
}

terraform {
  backend "s3" {}
}

data "aws_caller_identity" "current" {}
data "aws_ami" "amazon_linux_2" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

data "http" "my_public_ip" {
  url = "https://api.ipify.org"
}

# VPC
resource "aws_vpc" "ids_vpc" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "IDS VPC"
  }
}

# Subnet
resource "aws_subnet" "ids_subnet" {
  vpc_id                  = aws_vpc.ids_vpc.id
  cidr_block              = var.subnet_cidr
  map_public_ip_on_launch = true
  availability_zone       = var.availability_zone

  tags = {
    Name = "IDS Subnet"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "ids_igw" {
  vpc_id = aws_vpc.ids_vpc.id

  tags = {
    Name = "IDS IGW"
  }
}

# Route Table
resource "aws_route_table" "ids_rt" {
  vpc_id = aws_vpc.ids_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.ids_igw.id
  }

  tags = {
    Name = "IDS Route Table"
  }
}

# Route Table Association
resource "aws_route_table_association" "ids_rta" {
  subnet_id      = aws_subnet.ids_subnet.id
  route_table_id = aws_route_table.ids_rt.id
}

# Security Group
resource "aws_security_group" "ids_sg" {
  name        = "ids_sg"
  description = "Security group for IDS instance"
  vpc_id      = aws_vpc.ids_vpc.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# EC2 Instance
resource "aws_instance" "ids_instance" {
  ami                    = data.aws_ami.amazon_linux_2.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.ids_subnet.id
  vpc_security_group_ids = [aws_security_group.ids_sg.id]

  tags = {
    Name = "IDS Instance"
  }
}

# TRex Instance
resource "aws_instance" "trex_instance" {
  ami           = data.aws_ami.amazon_linux_2.id
  instance_type = "c5.4xlarge"
  subnet_id     = aws_subnet.ids_subnet.id
  vpc_security_group_ids = [aws_security_group.trex_sg.id]
  key_name      = aws_key_pair.trex_key_pair.key_name

  tags = {
    Name = "TRex Traffic Generator"
  }

  user_data = <<-EOF
              #!/bin/bash
              set -e
              
              # Update and install dependencies
              sudo yum update -y
              sudo yum install -y wget tar gcc gcc-c++ python3 python3-devel
              
              # Download and install TRex
              wget --no-check-certificate --no-cache https://trex-tgn.cisco.com/trex/release/latest
              tar -xzvf latest
              rm latest
              mv v* trex
              
              # Install TRex Python API
              pip3 install trex-stl-lib
              
              # Set up TRex configuration
              cat <<EOT > /etc/trex_cfg.yaml
              - port_limit    : 2
                version       : 2
                interfaces    : ["eth0", "eth1"]
                port_info     :
                    - ip         : 10.0.0.1
                      default_gw : 10.0.0.254
                    - ip         : 10.0.1.1
                      default_gw : 10.0.1.254
              EOT
              
              # Start TRex server
              cd trex
              ./t-rex-64 -i
              EOF

  root_block_device {
    volume_type = "gp2"
    volume_size = 20
  }
}

#TRex Security Group
resource "aws_security_group" "trex_sg" {
  name        = "trex_sg"
  description = "Security group for TRex instance"
  vpc_id      = aws_vpc.ids_vpc.id

  # SSH access
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["${chomp(data.http.my_public_ip.body)}/32"]
  }

  # TRex server ports
  ingress {
    from_port   = 4500
    to_port     = 4507
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.ids_vpc.cidr_block]
  }

  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "TRex Security Group"
  }
}

# S3
resource "aws_s3_bucket" "ids_bucket" {
  bucket = "ids-ml-models-${substr(data.aws_caller_identity.current.account_id, -6, 6)}"

  tags = {
    Name = "IDS ML Models Bucket"
  }
}

resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

resource "random_string" "suffix" {
  length  = 8
  special = false
  upper   = false
}

# SNS
resource "aws_sns_topic" "ids_alerts" {
  name = "ids-alerts"
}

# Lambda
resource "aws_lambda_function" "ids_model_update" {
  filename      = "lambda_function.zip"
  function_name = "ids_model_update"
  role          = aws_iam_role.lambda_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.8"
}

# IAM role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "ids_lambda_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# DynamoDB
resource "aws_dynamodb_table" "ids_alerts" {
  name         = "ids-alerts"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "alert_id"
  
  attribute {
    name = "alert_id"
    type = "S"
  }
}

# CloudWatch
resource "aws_cloudwatch_log_group" "ids_logs" {
  name = "/aws/lambda/ids_alert_processor"
}

# Generate a new key pair
resource "tls_private_key" "trex_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

# Create an AWS key pair using the generated public key
resource "aws_key_pair" "trex_key_pair" {
  key_name   = "trex-key-${random_string.suffix.result}"
  public_key = tls_private_key.trex_key.public_key_openssh
}

# Save the private key to a file (Be cautious with this in production!)
resource "local_file" "private_key" {
  content  = tls_private_key.trex_key.private_key_pem
  filename = "${path.module}/trex_private_key.pem"
  file_permission = "0600"
}