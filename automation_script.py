#!/usr/bin/env python3

import os
import subprocess
import sys
import configparser
from IDS_visualization import IDSVisualizer
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from traffic_generator import TRexTrafficGenerator
from traffic_capture import TrafficCapture
from feature_extractor import FeatureExtractor
from anomaly_detection import AnomalyDetector
from alert_generation import AlertGenerator
from aws import AWSManager
from terraform_output_reader import get_terraform_output

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
        print("6. Show")
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
    # Dynamically get TRex server IP
    trex_server_ip = get_terraform_output('trex_instance_public_ip')
    if not trex_server_ip:
        print("Failed to retrieve TRex instance IP from Terraform output.")
        return

    trex_generator = TRexTrafficGenerator(server=trex_server_ip)
    traffic_capture = TrafficCapture()
    feature_extractor = FeatureExtractor()
    anomaly_detector = AnomalyDetector()
    alert_generator = AlertGenerator()
    aws_manager = AWSManager(
        sns_topic_arn='arn:aws:sns:us-west-2:123456789012:ids-alerts',
        lambda_function_name='ids_model_update',
        s3_bucket_name='ids-ml-models-{suffix}',
        dynamodb_table_name='ids-alerts'
    )
    
    visualizer = IDSVisualizer()
    visualizer.setup_matplotlib()
    ani = FuncAnimation(visualizer.fig, visualizer.update_plot, frames=100, interval=500, blit=True)
    plt.show(block=False)

    print("Starting IDS...")
    try:
        trex_generator.connect()
        
        # Generate and capture mixed traffic
        print("Generating mixed traffic...")
        trex_generator.generate_normal_traffic(duration=300)  # 5 minutes of normal traffic
        trex_generator.generate_attack_traffic(duration=60)   # 1 minute of attack traffic
        packets = traffic_capture.capture_packets()

        # Process captured packets
        features = feature_extractor.extract_features(packets)
        anomalies = anomaly_detector.detect_anomalies(features)

        # Handle detected anomalies
        for i, is_anomaly in enumerate(anomalies):
            if is_anomaly:
                alert = alert_generator.generate_alert({
                    'timestamp': str(packets[i].time),
                    'source_ip': packets[i].ip.src,
                    'destination_ip': packets[i].ip.dst
                })
                aws_manager.save_anomaly(alert)
                aws_manager.send_notification(alert)

        # Update and save model
        aws_manager.invoke_lambda({'action': 'update_model'})
        aws_manager.save_model(anomaly_detector, 'anomaly_detector')

    except KeyboardInterrupt:
        print("\nStopping IDS...")
    finally:
        trex_generator.disconnect()

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