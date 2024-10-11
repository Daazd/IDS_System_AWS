#!/usr/bin/env python3

import os
import subprocess
import sys
import time
import signal
import configparser
from IDS_visualization import IDSVisualizer
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
# from traffic_generator import TRexTrafficGenerator
# from traffic_capture import TrafficCapture
# from feature_extractor import FeatureExtractor
# from anomaly_detection import AnomalyDetector
# from alert_generation import AlertGenerator
from aws import AWSManager
from terraform_output_reader import get_terraform_output

IDS_PID_FILE = '/tmp/ids_pid.txt'

def start_ids():
    try:
        # Start the IDS process
        process = subprocess.Popen([sys.executable, "main.py"], 
                                   stdout=subprocess.DEVNULL, 
                                   stderr=subprocess.DEVNULL)
        
        # Save the PID to a file
        with open(IDS_PID_FILE, 'w') as f:
            f.write(str(process.pid))
        
        print(f"IDS started with PID {process.pid}. It's running in the background.")
    except Exception as e:
        print(f"An error occurred while starting the IDS: {e}")

def stop_ids():
    if os.path.exists(IDS_PID_FILE):
        with open(IDS_PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        try:
            os.kill(pid, signal.SIGTERM)
            print(f"Sent termination signal to IDS process with PID {pid}")
            
            # Wait for the process to terminate
            for _ in range(10):  # Wait up to 10 seconds
                time.sleep(1)
                try:
                    os.kill(pid, 0)  # Check if process still exists
                except OSError:
                    print("IDS process has terminated.")
                    os.remove(IDS_PID_FILE)
                    return
            
            print("IDS process did not terminate. Forcing shutdown...")
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            print("IDS process not found. It may have already been stopped.")
        except Exception as e:
            print(f"An error occurred while stopping the IDS: {e}")
        finally:
            if os.path.exists(IDS_PID_FILE):
                os.remove(IDS_PID_FILE)
    else:
        print("No running IDS process found.")

def check_ids_status():
    if os.path.exists(IDS_PID_FILE):
        with open(IDS_PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        try:
            os.kill(pid, 0)  # This will raise an OSError if the process is not running
            print(f"IDS is running with PID {pid}")
        except OSError:
            print("IDS process not found, but PID file exists. Cleaning up...")
            os.remove(IDS_PID_FILE)
    else:
        print("IDS is not running")
        
def run_script(script_name, *args):
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script_name)
    if not os.path.exists(script_path):
        print(f"Error: The script '{script_name}' does not exist.")
        return

    try:
        subprocess.run([sys.executable, script_path] + list(args), check=True)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running '{script_name}':")
        print(e)

def check_s3_backend_config():
    return os.path.exists('backend_config.ini')

def terraform_menu():
    while True:
        print("\nTerraform Menu:")
        print("1. Configure S3 Backend")
        print("2. Initialize")
        print("3. Plan")
        print("4. Apply")
        print("5. Destroy")
        print("6. State List")
        print("7. Import")
        print("8. Back to main menu")
        
        choice = input("Enter your choice (1-8): ")
        
        if choice == '1':
            if check_s3_backend_config():
                print("S3 backend already configured. Do you want to reconfigure? (y/n)")
                if input().lower() != 'y':
                    continue
            run_script("configure_s3.py")
        elif choice == '2':
            if not check_s3_backend_config():
                print("S3 backend not configured. Please run configuration first.")
                continue
            run_script("terraform_init.py")
            #run_script("terraform_init.py", "--upgrade")
        elif choice == '3':
            run_script("terraform_plan.py")
        elif choice == '4':
            run_script("terraform_apply.py")
        elif choice == '5':
            run_script("terraform_destroy.py")
        elif choice == '6':
            run_script("terraform_show.py")
        elif choice == '7':
            run_script("terraform_import.py")
        elif choice == '8':
            break
        else:
            print("Invalid choice. Please try again.")

def run_ids():
    print("\nIDS Menu:")
    print("1. Start IDS")
    print("2. Stop IDS (if running)")
    print("3. Run IDS with visualization")
    print("4. Back to main menu")
    
    choice = input("Enter your choice (1-3): ")
    
    if choice == '1':
        try:
            subprocess.Popen([sys.executable, "main.py"])
            print("IDS started. It's running in the background.")
        except Exception as e:
            print(f"An error occurred while starting the IDS: {e}")
    elif choice == '2':
        
        print("Stopping IDS...")
    elif choice == '3':
        subprocess.Popen([sys.executable, "IDS_visualization.py"])
        print("Running IDS Visualizer...")
    elif choice == '4':
        return
    else:
        print("Invalid choice. Please try again.")
    try:
        subprocess.run([sys.executable, "main.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running the IDS: {e}")
    except KeyboardInterrupt:
        print("\nIDS execution was interrupted by user.")

def main_menu():
    while True:
        print("\nMain Menu:")
        print("1. Terraform operations")
        print("2. Run IDS")
        print("3. Exit")
        
        choice = input("Enter your choice (1-3): ")
        
        if choice == '1':
            terraform_menu()
        elif choice == '2':
            run_ids()
        elif choice == '3':
            print("Exiting...")
            sys.exit(0)
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main_menu()