#!/usr/bin/env python3

import subprocess
import sys

def terraform_destroy():
    try:
        subprocess.run(["terraform", "destroy"], check=True)
        print("Terraform destroy completed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error during Terraform destroy: {e}")
        sys.exit(1)

if __name__ == "__main__":
    terraform_destroy()