import uuid

class AlertGenerator:
    def __init__(self):
        self.alert_id = 0

    def generate_alert(self, anomaly_details):
        self.alert_id += 1
        alert = {
            'alert_id': str(uuid.uuid4()),
            'timestamp': anomaly_details.get('timestamp', 'N/A'),
            'source_ip': anomaly_details.get('source_ip', 'N/A'),
            'destination_ip': anomaly_details.get('destination_ip', 'N/A'),
            'severity': 'High',
            'description': 'Potential intrusion detected'
        }
        return alert

if __name__ == "__main__":
    generator = AlertGenerator()
    sample_anomaly = {
        'timestamp': '2023-09-01 12:00:00',
        'source_ip': '192.168.1.100',
        'destination_ip': '10.0.0.1'
    }
    alert = generator.generate_alert(sample_anomaly)
    print(f"Generated alert: {alert}")