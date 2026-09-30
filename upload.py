import os
import sys
import base64
import json
import urllib.request

TOKEN_PATH = r"C:\Users\권원중학부재학바이오의공학부\Desktop\token.txt"
EXPORT_DIR = r"C:\Users\권원중학부재학바이오의공학부\Desktop\Fusion360_AI_Pipeline_Export"
REPO_OWNER = "CodeDanji"
REPO_NAME = "Fusion-linked-3D-design"

try:
    with open(TOKEN_PATH, "r") as f:
        TOKEN = f.read().strip()
except Exception as e:
    print(f"Error reading token: {e}")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "Antigravity-Agent"
}

def api_request(method, url, data=None):
    req = urllib.request.Request(url, method=method, headers=HEADERS)
    if data:
        req.data = json.dumps(data).encode("utf-8")
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as response:
            if response.status in [200, 201, 204]:
                if response.status == 204:
                    return None
                return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code} on {url}: {e.read().decode()}")
        raise e

# 1. Create Repo if not exists
try:
    api_request("GET", f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}")
    print("Repo exists.")
except urllib.error.HTTPError as e:
    if e.code == 404:
        print("Creating repo...")
        api_request("POST", "https://api.github.com/user/repos", {
            "name": REPO_NAME,
            "description": "Fusion 360 AI CAD Automation Pipeline"
        })
    else:
        raise e

# 2. Upload files (using Tree API)
print("Uploading files via Tree API...")
# Get base tree
try:
    ref_data = api_request("GET", f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/refs/heads/main")
    base_commit_sha = ref_data['object']['sha']
    commit_data = api_request("GET", f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/commits/{base_commit_sha}")
    base_tree_sha = commit_data['tree']['sha']
except urllib.error.HTTPError as e:
    if e.code == 404 or e.code == 409: # Empty repo (409 Conflict for empty git ref)
        base_tree_sha = None
        base_commit_sha = None
    else:
        raise e

tree_items = []
for root, dirs, files in os.walk(EXPORT_DIR):
    if '.git' in dirs: dirs.remove('.git')
    for file in files:
        file_path = os.path.join(root, file)
        rel_path = os.path.relpath(file_path, EXPORT_DIR).replace("\\", "/")
        with open(file_path, "rb") as f:
            content = f.read()
        
        # Create blob
        blob_data = api_request("POST", f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/blobs", {
            "content": base64.b64encode(content).decode('utf-8'),
            "encoding": "base64"
        })
        
        tree_items.append({
            "path": rel_path,
            "mode": "100644",
            "type": "blob",
            "sha": blob_data['sha']
        })
        print(f"Uploaded blob for: {rel_path}")

# Create Tree
tree_payload = {"tree": tree_items}
if base_tree_sha: tree_payload["base_tree"] = base_tree_sha

new_tree_data = api_request("POST", f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/trees", tree_payload)
new_tree_sha = new_tree_data['sha']

# Create Commit
commit_payload = {
    "message": "🚀 Initial deploy: Fusion 360 AI CAD Automation Pipeline (via AI)",
    "tree": new_tree_sha
}
if base_commit_sha: commit_payload["parents"] = [base_commit_sha]

new_commit_data = api_request("POST", f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/commits", commit_payload)
new_commit_sha = new_commit_data['sha']

# Update Ref
if base_commit_sha:
    api_request("PATCH", f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/refs/heads/main", {
        "sha": new_commit_sha,
        "force": True
    })
else:
    api_request("POST", f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/refs", {
        "ref": "refs/heads/main",
        "sha": new_commit_sha
    })

print("✅ Successfully pushed to GitHub!")

# Secure cleanup
os.remove(TOKEN_PATH)
print("Token deleted.")
