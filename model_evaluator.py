import boto3
import json
import pickle
import subprocess
import numpy as np
from sklearn.metrics import confusion_matrix, classification_report
from botocore.exceptions import ClientError
from anomaly_detection import AnomalyDetector  # Import your actual anomaly detection class
from traffic_generator import TRexTrafficGenerator
from feature_extractor import FeatureExtractor
from terraform_output_reader import get_terraform_output
    
def get_bucket_name():
    sts = boto3.client('sts')
    account_id = sts.get_caller_identity()['Account']
    return f"ids-ml-models-{account_id[-6:]}"

def get_latest_model_key(s3_client, bucket_name):
    try:
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix='models/anomaly_detector_'
        )
        if 'Contents' in response:
            latest = max(response['Contents'], key=lambda x: x['LastModified'])
            return latest['Key']
        else:
            raise Exception("No model found in the bucket")
    except ClientError as e:
        print(f"Error accessing S3 bucket: {e}")
        raise

def generate_test_data(trex_server_ip, num_samples=1000):
    trex_generator = TRexTrafficGenerator(server=trex_server_ip)
    feature_extractor = FeatureExtractor()
    
    try:
        trex_generator.connect()
        
        # Generate normal traffic
        normal_packets = trex_generator.generate_normal_traffic(duration=30)
        normal_features = feature_extractor.extract_features(normal_packets)
        normal_labels = np.zeros(len(normal_features))
        
        # Generate attack traffic
        attack_packets = trex_generator.generate_attack_traffic(duration=30)
        attack_features = feature_extractor.extract_features(attack_packets)
        attack_labels = np.ones(len(attack_features))
        
        # Combine and shuffle the data
        features = np.vstack((normal_features, attack_features))
        labels = np.hstack((normal_labels, attack_labels))
        
        # Shuffle the data
        shuffle_idx = np.random.permutation(len(features))
        features = features[shuffle_idx]
        labels = labels[shuffle_idx]
        
        # Limit to num_samples
        features = features[:num_samples]
        labels = labels[:num_samples]
        
        return {'features': features, 'labels': labels}
    
    finally:
        trex_generator.disconnect()

def evaluate_model(trex_server_ip):
    try:
        
        trex_server_ip = get_terraform_output('trex_instance_public_ip')
        if not trex_server_ip:
            raise ValueError("Failed to retrieve TRex instance IP from Terraform output")
        
        # Set up S3 client
        s3 = boto3.client('s3')
        
        # Dynamically get the bucket name
        bucket_name = get_bucket_name()
        
        # Get the latest model key
        model_key = get_latest_model_key(s3, bucket_name)
        
        print(f"Loading model from bucket: {bucket_name}, key: {model_key}")

        # Load the model
        response = s3.get_object(Bucket=bucket_name, Key=model_key)
        model_str = response['Body'].read()
        model = pickle.loads(model_str)

        # Generate test data
        test_data = generate_test_data(trex_server_ip)

        # Make predictions
        predictions = model.predict(test_data['features'])

        # Calculate metrics
        cm = confusion_matrix(test_data['labels'], predictions)
        report = classification_report(test_data['labels'], predictions)

        print("Confusion Matrix:")
        print(cm)
        print("\nClassification Report:")
        print(report)

        # Calculate accuracy and false positive rate
        accuracy = (cm[0][0] + cm[1][1]) / np.sum(cm)
        false_positive_rate = cm[0][1] / (cm[0][1] + cm[1][1]) if (cm[0][1] + cm[1][1]) > 0 else 0

        # Send results to CloudWatch
        cloudwatch = boto3.client('cloudwatch')
        cloudwatch.put_metric_data(
            Namespace='IDS_Metrics',
            MetricData=[
                {
                    'MetricName': 'ModelAccuracy',
                    'Value': accuracy * 100,  # Convert to percentage
                    'Unit': 'Percent'
                },
                {
                    'MetricName': 'FalsePositiveRate',
                    'Value': false_positive_rate * 100,  # Convert to percentage
                    'Unit': 'Percent'
                }
            ]
        )
        
        print(f"Evaluation complete. Accuracy: {accuracy:.2%}, False Positive Rate: {false_positive_rate:.2%}")
        
    except Exception as e:
        print(f"An error occurred during model evaluation: {e}")

if __name__ == "__main__":
    evaluate_model()