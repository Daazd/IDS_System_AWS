from traffic_generator import TRexTrafficGenerator
from traffic_capture import TrafficCapture
from feature_extractor import FeatureExtractor
from anomaly_detection import AnomalyDetector
from alert_generation import AlertGenerator
from aws import AWSManager
from terraform_output_reader import get_terraform_output

def main():
    # Dynamically get TRex server IP
    trex_server_ip = get_terraform_output('trex_instance_public_ip')
    if not trex_server_ip:
        raise ValueError("Failed to retrieve TRex instance IP from Terraform output")

    # Initialize components
    trex_generator = TRexTrafficGenerator(server=trex_server_ip)
    traffic_cap = TrafficCapture()
    feature_ext = FeatureExtractor()
    anomaly_det = AnomalyDetector()
    alert_gen = AlertGenerator()
    aws_manager = AWSManager(
        sns_topic_arn='arn:aws:sns:us-west-2:123456789012:ids-alerts',
        lambda_function_name='ids_model_update',
        s3_bucket_name='ids-ml-models-{suffix}',  # The suffix will be determined by AWSManager
        dynamodb_table_name='ids-alerts'
    )

    try:
        # Connect to TRex
        trex_generator.connect()

        # Generate and capture mixed traffic
        print("Generating mixed traffic...")
        trex_generator.generate_normal_traffic(duration=300)  # 5 minutes of normal traffic
        trex_generator.generate_attack_traffic(duration=60)   # 1 minute of attack traffic
        packets = traffic_cap.capture_packets()

        # Extract features and detect anomalies
        features = feature_ext.extract_features(packets)
        anomalies = anomaly_det.detect_anomalies(features)

        # Generate and send alerts for anomalies
        for i, is_anomaly in enumerate(anomalies):
            if is_anomaly:
                alert = alert_gen.generate_alert({
                    'timestamp': str(packets[i].time),
                    'source_ip': packets[i].ip.src,
                    'destination_ip': packets[i].ip.dst
                })
                aws_manager.save_anomaly(alert)
                aws_manager.send_notification(alert)

        # Trigger model update
        aws_manager.invoke_lambda({'action': 'update_model'})

        # Save the updated model
        aws_manager.save_model(anomaly_det, 'anomaly_detector')

    finally:
        # Disconnect from TRex
        trex_generator.disconnect()

if __name__ == "__main__":
    main()