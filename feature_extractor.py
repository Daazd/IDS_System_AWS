from scapy.all import IP, TCP, UDP
import numpy as np

class FeatureExtractor:
    def extract_features(self, packets):
        features = []
        for packet in packets:
            if IP in packet:
                ip_len = packet[IP].len
                protocol = packet[IP].proto
                ttl = packet[IP].ttl
                
                if TCP in packet:
                    sport = packet[TCP].sport
                    dport = packet[TCP].dport
                    flags = packet[TCP].flags
                elif UDP in packet:
                    sport = packet[UDP].sport
                    dport = packet[UDP].dport
                    flags = 0
                else:
                    sport = dport = flags = 0
                
                features.append([ip_len, protocol, ttl, sport, dport, flags])
        
        return np.array(features)

if __name__ == "__main__":
    from scapy.all import rdpcap
    
    extractor = FeatureExtractor()
    packets = rdpcap("captured_traffic.pcap")
    features = extractor.extract_features(packets)
    print(f"Extracted features shape: {features.shape}")