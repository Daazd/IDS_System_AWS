#!/usr/bin/env python3

import sys
import configparser
import boto3
import json

def setup_s3_backend_config():
    print("Configuring S3 backend for Terraform state...")
    
    bucket_name = input("Enter the name for the S3 bucket to store Terraform state: ")
    region = input("Enter the AWS region to create/use the bucket in: ")
    key = input("Enter the key for the state file (default: terraform.tfstate): ") or "terraform.tfstate"
    
    # Create S3 client
    s3_client = boto3.client('s3', region_name=region)
    
    # Check if bucket exists, create if it doesn't
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"Bucket {bucket_name} already exists.")
    except:
        print(f"Bucket {bucket_name} does not exist. Creating...")
        try:
            if region == 'us-west-2':
                s3_client.create_bucket(Bucket=bucket_name)
            else:
                s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': region}
                )
            print(f"Bucket {bucket_name} created successfully.")
        except Exception as e:
            print(f"Error creating bucket: {e}")
            sys.exit(1)
    
    # Enable versioning on the bucket
    try:
        s3_client.put_bucket_versioning(
            Bucket=bucket_name,
            VersioningConfiguration={'Status': 'Enabled'}
        )
        print("Bucket versioning enabled.")
    except Exception as e:
        print(f"Error enabling bucket versioning: {e}")
        sys.exit(1)
    
    # Create an empty state file if it doesn't exist
    try:
        s3_client.head_object(Bucket=bucket_name, Key=key)
        print(f"State file {key} already exists in the bucket.")
    except:
        print(f"Creating initial empty state file {key}...")
        empty_state = {
            "version": 4,
            "terraform_version": "1.6.3",
            "serial": 1,
            "lineage": "",
            "outputs": {},
            "resources": []
        }
        s3_client.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=json.dumps(empty_state)
        )
        print(f"Initial state file {key} created in the bucket.")
    
    # Create configuration file
    config = configparser.ConfigParser()
    config['S3'] = {
        'bucket_name': bucket_name,
        'region': region,
        'key': key
    }
    
    try:
        with open('backend_config.ini', 'w') as configfile:
            config.write(configfile)
        print("Backend configuration file created successfully.")
    except IOError as e:
        print(f"Error creating backend configuration file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_s3_backend_config()