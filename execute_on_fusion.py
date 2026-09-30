import requests
import json
import os
from PIL import Image, ImageDraw, ImageFont

SCRIPT_PATH = r"c:\Users\권원중학부재학바이오의공학부\Desktop\ENDO\build_endocrab_stopper.py"
OUTPUT_DIR = r"c:\Users\권원중학부재학바이오의공학부\Desktop\ENDO\output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def execute_on_fusion():
    with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
        code = f.read()

    payload = {"code": code}
    url = "http://127.0.0.1:8080/execute_code"
    
    try:
        res = requests.post(url, json=payload, timeout=15)
        print("Execute POST response:", res.text)
    except Exception as e:
        print("Failed to send code to Fusion 360:", e)
        return

    import time
    time.sleep(2.5)  # Wait for build & 4-stage capture

    # Inspect endpoint
    try:
        inspect_res = requests.get("http://127.0.0.1:8080/inspect", timeout=10)
        data = inspect_res.json()
        state = data.get("state", {})
        print("--- Execution Result ---")
        print("Document:", state.get("document_name"))
        print("Occurrences count:", state.get("occurrence_count"))
        print("Bodies count:", state.get("body_count"))
        print("Topology:", json.dumps(state.get("brep_topology", []), indent=2))
        print("Joints:", json.dumps(state.get("joints_info", []), indent=2))
        print("Last Error:", state.get("last_error"))
    except Exception as e:
        print("Failed to inspect:", e)

    # Stitch dynamic 4-stage motion frames into a single sequence strip
    frame_files = [
        ("Step 0: Push & Hold Open (Free-Pass 100%)", os.path.join(OUTPUT_DIR, "stopper_step_0_open.png")),
        ("Step 1: Needle Penetration (Pass Stopper & U-Loop)", os.path.join(OUTPUT_DIR, "stopper_step_1_needle_pass.png")),
        ("Step 2: Hold Sheath & Pull Cinch (Suture Tightened)", os.path.join(OUTPUT_DIR, "stopper_step_2_cinch.png")),
        ("Step 3: Sheath Release & Spring Lock (>20N Clamped)", os.path.join(OUTPUT_DIR, "stopper_step_3_locked.png"))
    ]

    valid_images = []
    for title, fpath in frame_files:
        if os.path.exists(fpath):
            img = Image.open(fpath)
            valid_images.append((title, img))

    if valid_images:
        w, h = valid_images[0][1].size
        strip_w = w * len(valid_images)
        strip_h = h + 90  # Header space for captions
        strip = Image.new("RGB", (strip_w, strip_h), (15, 23, 42))
        draw = ImageDraw.Draw(strip)

        for i, (title, img) in enumerate(valid_images):
            offset_x = i * w
            strip.paste(img, (offset_x, 90))
            # Header Box
            draw.rectangle([offset_x, 0, offset_x + w, 90], fill=(30, 41, 59))
            draw.rectangle([offset_x, 0, offset_x + w, strip_h], outline=(71, 85, 105), width=3)
            # Text label
            draw.text((offset_x + 40, 32), f"Frame {i+1} | {title}", fill=(56, 189, 248))

        seq_path = os.path.join(OUTPUT_DIR, "stopper_motion_sequence.png")
        strip.save(seq_path)
        print("Dynamic stopper motion sequence strip saved to:", seq_path)

if __name__ == "__main__":
    execute_on_fusion()
