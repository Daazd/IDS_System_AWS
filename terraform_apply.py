import os
import subprocess
import logging
from datetime import datetime

def terraform_apply(os, subprocess, account, tfvars_file_name):
    original_dir = os.getcwd()
    
    try:
        os.chdir("./terraform")
        
        my_env = os.environ.copy()
        my_env["AWS_PROFILE"] = account
        
        while True:
            command = ["terraform", "apply", f"-var-file={tfvars_file_name}"]
            process = subprocess.run(command, env=my_env, text=True, stderr=subprocess.PIPE)
        
            if process.returncode == 0:
                logging.info("Terraform apply succeeded.")
                break
            
            logging.info("Terraform apply failed.")
            logging.info(process.stderr)
            
            retry = input("Do you want to retry? (y/n): ").strip().lower()
            if retry != 'yes':
                logging.info("Exiting. Terraform apply not complete.")
                break
    finally:
        os.chdir(original_dir)