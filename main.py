import time
import schedule
from traffic_generator import TRexTrafficGenerator
from traffic_capture import TrafficCapture
from feature_extractor import FeatureExtractor
from anomaly_detection import AnomalyDetector
from alert_generation import AlertGenerator
from aws import AWSManager
from terraform_output_reader import get_terraform_output

# Configuration
RUN_INTERVAL_HOURS = 24  # Run once a day
NORMAL_TRAFFIC_DURATION = 60  # 1 minute of normal traffic
ATTACK_TRAFFIC_DURATION = 30  # 30 seconds of attack traffic

def run_ids_cycle():
    print("Starting IDS cycle...")
    
    # Dynamically get TRex server IP
    trex_server_ip = get_terraform_output('trex_instance_public_ip')
    if not trex_server_ip:
        print("Failed to retrieve TRex instance IP from Terraform output")
        return

    # Initialize components
    trex_generator = TRexTrafficGenerator(server=trex_server_ip)
    traffic_cap = TrafficCapture()
    feature_ext = FeatureExtractor()
    anomaly_det = AnomalyDetector()
    alert_gen = AlertGenerator()
    aws_manager = AWSManager(
        sns_topic_arn='arn:aws:sns:us-west-2:123456789012:ids-alerts',
        lambda_function_name='ids_model_update',
        s3_bucket_name='ids-ml-models-{suffix}',
        dynamodb_table_name='ids-alerts'
    )

    try:
        trex_generator.connect()
        
        print("Generating mixed traffic...")
        trex_generator.generate_normal_traffic(duration=NORMAL_TRAFFIC_DURATION)
        trex_generator.generate_attack_traffic(duration=ATTACK_TRAFFIC_DURATION)
        packets = traffic_cap.capture_packets()

        features = feature_ext.extract_features(packets)
        anomalies = anomaly_det.detect_anomalies(features)

        for i, is_anomaly in enumerate(anomalies):
            if is_anomaly:
                alert = alert_gen.generate_alert({
                    'timestamp': str(packets[i].time),
                    'source_ip': packets[i].ip.src,
                    'destination_ip': packets[i].ip.dst
                })
                aws_manager.save_anomaly(alert)
                aws_manager.send_notification(alert)

        aws_manager.invoke_lambda({'action': 'update_model'})
        aws_manager.save_model(anomaly_det, 'anomaly_detector')

    except Exception as e:
        print(f"An error occurred during IDS operation: {e}")
    finally:
        trex_generator.disconnect()

    print("IDS cycle completed")

def main():
    print(f"IDS scheduled to run every {RUN_INTERVAL_HOURS} hours")
    schedule.every(RUN_INTERVAL_HOURS).hours.do(run_ids_cycle)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()