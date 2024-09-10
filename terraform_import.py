#!/usr/bin/env python3

import subprocess
import sys

def terraform_import(resource_address, resource_id):
    try:
        subprocess.run(["terraform", "import", resource_address, resource_id], check=True)
        print(f"Successfully imported {resource_id} as {resource_address}")
    except subprocess.CalledProcessError as e:
        print(f"Error during Terraform import: {e}")
        sys.exit(1)

if __name__ == "__main__":
    resource_address = input("Enter the Terraform resource address to import: ")
    resource_id = input("Enter the ID of the existing resource: ")
    terraform_import(resource_address, resource_id)