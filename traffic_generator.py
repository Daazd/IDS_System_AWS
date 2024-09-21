from trex_stl_lib.api import STLClient, STLProfile, STLStream, STLPktBuilder, STLTXCont, STLError
from scapy.all import Ether, IP, UDP, TCP
import time
from terraform_output_reader import get_terraform_output_reader

class TRexTrafficGenerator:
    def __init__(self, server):
        self.client = STLClient(server=server)

    def connect(self):
        for i in range(5):  # Retry connection up to 5 times
            try:
                self.client.connect()
                print("Connected to TRex server")
                return
            except STLError as e:
                print(f"Connection attempt {i+1} failed: {e}")
                time.sleep(5)
        raise Exception("Failed to connect to TRex server after 5 attempts")

    def disconnect(self):
        self.client.disconnect()
        print("Disconnected from TRex server")

    def generate_normal_traffic(self, duration=60):
        print("Generating normal traffic...")
        profile = STLProfile([
            STLStream(
                packet=STLPktBuilder(
                    pkt=Ether()/IP(src="16.0.0.1", dst="48.0.0.1")/UDP(dport=12, sport=1025)
                ),
                mode=STLTXCont(pps=1000)
            )
        ])
        self._generate_traffic(profile, duration)

    def generate_attack_traffic(self, duration=60):
        print("Generating attack traffic...")
        profile = STLProfile([
            STLStream(
                packet=STLPktBuilder(
                    pkt=Ether()/IP(src="16.0.0.1", dst="48.0.0.1")/TCP(dport=80, flags="S")
                ),
                mode=STLTXCont(pps=10000)
            )
        ])
        self._generate_traffic(profile, duration)

    def _generate_traffic(self, profile, duration):
        try:
            self.client.reset()
            self.client.add_streams(profile)
            self.client.start(duration=duration)
            self.client.wait_on_traffic()
        except STLError as e:
            print(f"Error generating traffic: {e}")

if __name__ == "__main__":
    trex_server_ip = get_terraform_output_reader('trex_instance_public_ip') # Getting the TRex server IP from Terraform output
    generator = TRexTrafficGenerator(server=trex_server_ip)
    
    try:
        generator.connect()
        generator.generate_normal_traffic(duration=30)
        generator.generate_attack_traffic(duration=30)
    finally:
        generator.disconnect()