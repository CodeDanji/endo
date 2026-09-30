"""
Fusion 360 Master Template Parameter Driver & REST Client.

Validates parametric fx inputs against parameters_schema.json schema
and sends POST requests to the Fusion 360 REST Add-In (AntigravityOnDemand).
"""

import json
import os
import urllib.request
import urllib.parse
import argparse

REST_PORT = 8080
BASE_URL = f"http://localhost:{REST_PORT}"

def validate_parameters(param_dict: dict, schema_path: str) -> bool:
    """
    Validates parameter inputs against JSON schema limits.
    """
    if not os.path.exists(schema_path):
        print(f"[WARN] Schema file not found: {schema_path}, skipping schema validation.")
        return True
    
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
        
    properties = schema.get("properties", {})
    for key, val_str in param_dict.items():
        if key in properties:
            spec = properties[key]
            # Parse number from string like '65.0 mm'
            try:
                num_val = float(str(val_str).replace("mm", "").replace("deg", "").strip())
                if "minimum" in spec and num_val < spec["minimum"]:
                    print(f"[REJECT] Parameter {key}={num_val} is below minimum ({spec['minimum']})")
                    return False
                if "maximum" in spec and num_val > spec["maximum"]:
                    print(f"[REJECT] Parameter {key}={num_val} exceeds maximum ({spec['maximum']})")
                    return False
            except ValueError:
                pass
    return True

def send_modify_request(parameters: dict):
    """
    Sends POST /modify payload to Fusion 360 REST server.
    """
    url = f"{BASE_URL}/modify"
    payload = json.dumps({"parameters": parameters}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"[REST SUCCESS] Modify status: {data.get('status')}")
            return data
    except Exception as e:
        print(f"[REST ERROR] Failed to send /modify request to Fusion 360: {e}")
        return None

def send_import_step_request(step_path: str):
    """
    Sends POST /import_step payload to Fusion 360 REST server.
    """
    url = f"{BASE_URL}/import_step"
    payload = json.dumps({"step_path": step_path}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"[REST SUCCESS] Import STEP status: {data.get('status')}")
            return data
    except Exception as e:
        print(f"[REST ERROR] Failed to send /import_step request to Fusion 360: {e}")
        return None

def send_inspect_request():
    """
    Sends GET /inspect request to capture viewport and state.
    """
    url = f"{BASE_URL}/inspect"
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"[REST SUCCESS] Inspect state retrieved. Document: {data.get('state', {}).get('document_name')}")
            return data
    except Exception as e:
        print(f"[REST ERROR] Failed to send /inspect request to Fusion 360: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fusion 360 Master Template Driver")
    parser.add_argument("--action", choices=["inspect", "modify", "import_step"], default="inspect")
    parser.add_argument("--param", action="append", nargs=2, metavar=("KEY", "VAL"), help="Parameter key and value (e.g. Body_Length 65.0mm)")
    parser.add_argument("--step_path", help="Path to STEP file for import_step action")
    args = parser.parse_args()

    schema_file = os.path.join(os.path.dirname(__file__), "..", "resources", "parameters_schema.json")

    if args.action == "inspect":
        send_inspect_request()
    elif args.action == "modify":
        if args.param:
            param_dict = {k: v for k, v in args.param}
            if validate_parameters(param_dict, schema_file):
                send_modify_request(param_dict)
        else:
            print("No parameters supplied. Use --param Key Val")
    elif args.action == "import_step":
        if args.step_path:
            send_import_step_request(args.step_path)
        else:
            print("No STEP file supplied. Use --step_path path/to/file.step")
