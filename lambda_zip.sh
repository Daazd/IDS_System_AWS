#!/bin/bash

mkdir lambda_temp
cd lambda_temp

cat << EOF > lambda_function.py
import boto3
import json
import pickle
from botocore.exceptions import ClientError

class AWSManager:
    def __init__(self, sns_topic_arn, lambda_function_name, s3_bucket_name, dynamodb_table_name):
        self.sns_client = boto3.client('sns')
        self.lambda_client = boto3.client('lambda')
        self.s3_client = boto3.client('s3')
        self.dynamodb = boto3.resource('dynamodb')
        
        self.sns_topic_name = 'ids-alerts'
        self.lambda_function_name = 'ids_alert_processor'
        self.s3_bucket_name = f'ids-ml-models-{self.get_bucket_suffix()}'
        self.dynamodb_table_name = 'ids-alerts'
        
    def get_bucket_suffix(self):
        account_id = boto3.client('sts').get_caller_identity().get('Account')
        return account_id[-6:]
    
    def send_notification(self, message):
        try:
            response = self.sns_client.publish(
                TopicArn=self.sns_topic_arn,
                Message=json.dumps(message),
                Subject='IDS Alert'
            )
            print(f"Notification sent: {response['MessageId']}")
            return response
        except ClientError as e:
            print(f"Error sending notification: {e}")
            return None

    def invoke_lambda(self, payload):
        try:
            response = self.lambda_client.invoke(
                FunctionName=self.lambda_function_name,
                InvocationType='Event',
                Payload=json.dumps(payload)
            )
            print(f"Lambda function invoked: {self.lambda_function_name}")
            return response
        except ClientError as e:
            print(f"Error invoking Lambda function: {e}")
            return None

    def save_model(self, model, model_name):
        try:
            model_bytes = pickle.dumps(model)
            self.s3_client.put_object(
                Bucket=self.s3_bucket_name,
                Key=f'models/{model_name}.pkl',
                Body=model_bytes
            )
            print(f"Model saved to S3: {model_name}")
        except ClientError as e:
            print(f"Error saving model to S3: {e}")

    def load_model(self, model_name):
        try:
            response = self.s3_client.get_object(
                Bucket=self.s3_bucket_name,
                Key=f'models/{model_name}.pkl'
            )
            model_bytes = response['Body'].read()
            model = pickle.loads(model_bytes)
            print(f"Model loaded from S3: {model_name}")
            return model
        except ClientError as e:
            print(f"Error loading model from S3: {e}")
            return None

    def save_anomaly(self, anomaly_data):
        table = self.dynamodb.Table(self.dynamodb_table_name)
        try:
            response = table.put_item(Item=anomaly_data)
            print(f"Anomaly saved to DynamoDB: {anomaly_data['id']}")
            return response
        except ClientError as e:
            print(f"Error saving anomaly to DynamoDB: {e}")
            return None

    def get_anomalies(self, limit=100):
        table = self.dynamodb.Table(self.dynamodb_table_name)
        try:
            response = table.scan(Limit=limit)
            return response.get('Items', [])
        except ClientError as e:
            print(f"Error retrieving anomalies from DynamoDB: {e}")
            return []

def lambda_handler(event, context):
    def lambda_handler(event, context):
    # This function would be deployed as a Lambda function
    aws_manager = AWSManager(
        sns_topic_arn='arn:aws:sns:us-west-2:123456789012:ids-alerts',
        lambda_function_name='ids_model_update',
        s3_bucket_name='ids-model-storage',
        dynamodb_table_name='ids-anomalies'
    )

    if event.get('action') == 'update_model':
        # Load the current model
        current_model = aws_manager.load_model('anomaly_detector')
        
        # Get recent anomalies
        recent_anomalies = aws_manager.get_anomalies()
        
        # Update the model 
        current_model.partial_fit([anomaly['features'] for anomaly in recent_anomalies])
        
        # Save the updated model
        aws_manager.save_model(current_model, 'anomaly_detector')
        
        return {
            'statusCode': 200,
            'body': json.dumps('Model updated successfully')
        }
    else:
        return {
            'statusCode': 400,
            'body': json.dumps('Invalid action')
        }

EOF

# Install dependencies
pip install boto3 -t .

# Zip the contents
zip -r ../lambda_function.zip .

# Clean up
cd ..
rm -rf lambda_temp

echo "Lambda function has been packaged into lambda_function.zip"