from scapy.all import sniff, wrpcap

class TrafficCapture:
    def __init__(self, interface="eth0"):
        self.interface = interface

    def capture_packets(self, count=1000, output_file="captured_traffic.pcap"):
        print(f"Capturing {count} packets on interface {self.interface}")
        packets = sniff(iface=self.interface, count=count)
        wrpcap(output_file, packets)
        print(f"Captured packets saved to {output_file}")
        return packets

if __name__ == "__main__":
    capturer = TrafficCapture()
    capturer.capture_packets()