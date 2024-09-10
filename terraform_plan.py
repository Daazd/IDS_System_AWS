#!/usr/bin/env python3

import subprocess
import sys
import os

TERRAFORM_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "terraform")

def terraform_plan():
    try:
        # Change to the Terraform directory
        os.chdir(TERRAFORM_DIR)
        subprocess.run(["terraform", "plan"], check=True)
        print("Terraform plan completed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error during Terraform plan: {e}")
        sys.exit(1)
    finally:
        # Change back to the original directory
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    terraform_plan()