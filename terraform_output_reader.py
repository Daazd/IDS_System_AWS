import json
import subprocess

def get_terraform_output(output_name):
    try:
        result = subprocess.run(['terraform', 'output', '-json'], capture_output=True, text=True, check=True)
        outputs = json.loads(result.stdout)
        return outputs.get(output_name, {}).get('value')
    except subprocess.CalledProcessError as e:
        print(f"Error running terraform output: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing terraform output: {e}")
        return None

if __name__ == "__main__":
    trex_ip = get_terraform_output('trex_instance_public_ip')
    print(f"TRex instance public IP: {trex_ip}")