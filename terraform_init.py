#!/usr/bin/env python3

import subprocess
import sys
import configparser
import os

TERRAFORM_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "terraform")

def check_terraform_files():
    return any(file.endswith('.tf') for file in os.listdir(TERRAFORM_DIR))

def terraform_init():
    if not check_terraform_files():
        print(f"No Terraform configuration files (.tf) found in {TERRAFORM_DIR}")
        print("Please ensure your Terraform files are in the correct directory.")
        sys.exit(1)

    config = configparser.ConfigParser()
    try:
        config.read('backend_config.ini')
        bucket_name = config['S3']['bucket_name']
        region = config['S3']['region']
        key = config['S3']['key']
    except:
        print("Error reading backend configuration. Please run configure_s3.py first.")
        sys.exit(1)

    init_command = [
        "terraform", "init",
        "-backend-config=bucket=" + bucket_name,
        "-backend-config=key=" + key,
        "-backend-config=region=" + region
    ]
    
    try:
        # Change to the Terraform directory
        os.chdir(TERRAFORM_DIR)
        subprocess.run(init_command, check=True)
        print("Terraform initialization successful")
    except subprocess.CalledProcessError as e:
        print(f"Error during Terraform init: {e}")
        sys.exit(1)
    finally:
        # Change back to the original directory
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    terraform_init()