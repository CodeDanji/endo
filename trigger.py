import urllib.request
import json
import traceback

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

try:
    skeleton_script = BASE_DIR / 'src' / 'build_endocrab_model' / 'build_p1_skeleton.py'
    with open(skeleton_script, 'r', encoding='utf-8') as f:
        code = f.read()
    
    url = 'http://localhost:8080/execute_code'
    data = json.dumps({'code': code}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    
    with urllib.request.urlopen(req) as response:
        print("Response:", response.read().decode('utf-8'))
        
    # After executing, get inspect
    url_inspect = 'http://localhost:8080/inspect'
    req_inspect = urllib.request.Request(url_inspect, method='GET')
    with urllib.request.urlopen(req_inspect) as response:
        res = json.loads(response.read().decode('utf-8'))
        print("Inspect State:", res.get('state'))
        # save image
        import base64
        img_data = res.get('image_b64', '')
        if img_data:
            out_img = BASE_DIR / 'output_skeleton.png'
            with open(out_img, 'wb') as f:
                f.write(base64.b64decode(img_data))
            print(f"Saved image to {out_img}")
except Exception as e:
    print("Error:", str(e))
    traceback.print_exc()
