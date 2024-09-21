#!/usr/bin/env python3

import subprocess
import sys
import os

TERRAFORM_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "terraform")

def check_terraform_files():
    return any(file.endswith('.tf') for file in os.listdir(TERRAFORM_DIR))

def list_state_resources():
    if not check_terraform_files():
        print(f"No Terraform configuration files (.tf) found in {TERRAFORM_DIR}")
        print("Please ensure your Terraform files are in the correct directory.")
        sys.exit(1)

    try:
        # Change to the Terraform directory
        original_dir = os.getcwd()
        os.chdir(TERRAFORM_DIR)

        # List the state
        print("Listing Terraform state...")
        output = subprocess.check_output(['terraform', 'state', 'list'], universal_newlines=True)
        
        # Split the output into a list of resources
        resources = output.strip().split('\n')
        
        # Print the resources
        if resources and resources[0]:
            print("Resources in Terraform state:")
            for resource in resources:
                print(resource)
        else:
            print("No resources found in the Terraform state.")
            
    except subprocess.CalledProcessError as e:
        if "No state file was found!" in str(e):
            print("No Terraform state file found. Have you run 'terraform apply' yet?")
        else:
            print(f"Error during Terraform state list: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)
    finally:
        # Change back to the original directory
        os.chdir(original_dir)

if __name__ == "__main__":
    list_state_resources()