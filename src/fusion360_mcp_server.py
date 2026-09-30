#!/usr/bin/env python3
"""
Fusion 360 Model Context Protocol (MCP) Server Bridge (v2.0)
------------------------------------------------------------
Anthropic MCP (Model Context Protocol) Stdio JSON-RPC 표준 규격을 지원하는 Fusion 360 연동 서버입니다.
Fusion 360 내부에 상주하는 `AntigravityOnDemand` REST Add-in (Port 8080)과 통신하여
Claude Desktop, Cursor, Antigravity 등의 AI 모델이 3D CAD를 직접 제어하고,
동적 기구학 시뮬레이션, MuJoCo MJCF 에셋 내보내기, DFM 멀티모달 뷰 검수를 수행하도록 중계합니다.
"""

import sys
import json
import urllib.request
import urllib.parse
import base64
import time

FUSION360_REST_URL = "http://localhost:8080"


def call_fusion_get(endpoint):
    url = f"{FUSION360_REST_URL}{endpoint}"
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def call_fusion_post(endpoint, data_dict):
    url = f"{FUSION360_REST_URL}{endpoint}"
    json_bytes = json.dumps(data_dict).encode("utf-8")
    req = urllib.request.Request(url, data=json_bytes, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


TOOLS_DEFINITIONS = [
    {
        "name": "fusion360_get_view",
        "description": "Fusion 360의 3D 뷰포트 스크린샷(PNG)과 파라미터표, 바디 수 등 상태(state.json)를 캡처하여 반환합니다. Vision 모델 검수용으로 사용합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "fusion360_modify_parameters",
        "description": "Fusion 360 문서의 파라메트릭 변수(userParameters)를 실시간 수정하고 모델을 0.1초 내 재연산시킵니다. 실행 후 최신 스크린샷과 상태를 함께 반환합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "parameters": {
                    "type": "object",
                    "description": "변경할 파라미터 이름과 수식/치수 맵 (예: {'Body_Length': '65.0 mm', 'Gripper_Angle': '15.0 deg'})"
                }
            },
            "required": ["parameters"]
        }
    },
    {
        "name": "fusion360_execute_code",
        "description": "Fusion 360 파이썬 API(`adsk.core`, `adsk.fusion`) 임의 코드를 메인 UI 스레드에서 안전하게 동적 실행합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Fusion 360에서 실행할 파이썬 코드 스크립트"
                }
            },
            "required": ["code"]
        }
    },
    {
        "name": "fusion360_import_step",
        "description": "외부 CadQuery나 OpenCASCADE로 생성된 STEP CAD 파일(.step) 경로를 받아 Fusion 360 활성 문서로 가져옵니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "step_path": {
                    "type": "string",
                    "description": "임포트할 STEP 파일의 절대 경로"
                }
            },
            "required": ["step_path"]
        }
    },
    {
        "name": "fusion360_build_endocrab_model",
        "description": "Endocrab 수술 로봇 3D 풀 파라메트릭 CAD 모델 빌드 스크립트(`build_endocrab_model.py`)를 Fusion 360에서 빌드합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "fusion360_animate_and_inspect",
        "description": "Fusion 360 어셈블리의 특정 조인트를 단계별(0%, 50%, 100%)로 구동하며 다단계 스크린샷과 토폴로지를 연속 캡처합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "joint_name": {
                    "type": "string",
                    "description": "구동할 조인트 이름 (비어있을 경우 첫 번째 조인트)"
                },
                "steps": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "구동 단계 비율 배열 (예: [0.0, 0.5, 1.0])"
                },
                "range": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "구동 범위 [최소값, 최대값] (단위: cm 또는 rad)"
                }
            },
            "required": []
        }
    },
    {
        "name": "fusion360_export_mjcf",
        "description": "현재 Fusion 360 모델의 컴포넌트별 STL 메시, 질량, CoM, 관성 모멘트, 조인트 계층 구조를 추출하여 MuJoCo MJCF XML 파일 및 에셋을 생성합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "mechanism_name": {
                    "type": "string",
                    "description": "내보낼 메커니즘 이름"
                },
                "output_dir": {
                    "type": "string",
                    "description": "내보낼 대상 디렉토리 경로 (선택 사항)"
                }
            },
            "required": []
        }
    },
    {
        "name": "fusion360_capture_dfm_views",
        "description": "초소형 내시경 기구 특화 4대 DFM 뷰(아이소 투시, 텐던 채널 단면, 핀 어셈블리 단면, 분해 조립 뷰)를 연속 캡처하고 이미지들을 반환합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "output_dir": {
                    "type": "string",
                    "description": "캡처 이미지 저장 대상 디렉토리 (선택 사항)"
                }
            },
            "required": []
        }
    }
]


def handle_tool_call(tool_name, arguments):
    try:
        if tool_name == "fusion360_get_view":
            res = call_fusion_get("/inspect")
            state = res.get("state", {})
            img_b64 = res.get("image_b64", "")
            
            content = [
                {
                    "type": "text",
                    "text": f"Fusion 360 inspection state:\n{json.dumps(state, indent=2, ensure_ascii=False)}"
                }
            ]
            if img_b64:
                content.append({
                    "type": "image",
                    "data": img_b64,
                    "mimeType": "image/png"
                })
            return {"content": content}

        elif tool_name == "fusion360_modify_parameters":
            params = arguments.get("parameters", {})
            call_fusion_post("/modify", {"parameters": params})
            time.sleep(0.6)
            inspect_res = call_fusion_get("/inspect")
            
            content = [
                {
                    "type": "text",
                    "text": f"Parameters modified successfully. Current state:\n{json.dumps(inspect_res.get('state', {}), indent=2, ensure_ascii=False)}"
                }
            ]
            if inspect_res.get("image_b64"):
                content.append({
                    "type": "image",
                    "data": inspect_res["image_b64"],
                    "mimeType": "image/png"
                })
            return {"content": content}

        elif tool_name == "fusion360_execute_code":
            code = arguments.get("code", "")
            call_fusion_post("/execute_code", {"code": code})
            time.sleep(0.8)
            inspect_res = call_fusion_get("/inspect")
            state = inspect_res.get("state", {})
            
            if state.get("last_error"):
                content_text = f"❌ FUSION 360 API EXECUTION FAILED ❌\n\nTraceback:\n{state['last_error']}\n\n[ACTION REQUIRED] The scene has been rolled back. Please analyze the traceback above, fix your python code, and call fusion360_execute_code again."
            else:
                content_text = f"✅ Execution Successful. State updated.\n{json.dumps(state, indent=2, ensure_ascii=False)}"
            
            content = [
                {
                    "type": "text",
                    "text": content_text
                }
            ]
            if inspect_res.get("image_b64"):
                content.append({
                    "type": "image",
                    "data": inspect_res["image_b64"],
                    "mimeType": "image/png"
                })
            return {"content": content}

        elif tool_name == "fusion360_import_step":
            step_path = arguments.get("step_path", "")
            call_fusion_post("/import_step", {"step_path": step_path})
            time.sleep(1.0)
            inspect_res = call_fusion_get("/inspect")
            
            content = [
                {
                    "type": "text",
                    "text": f"STEP file import triggered ({step_path}). Updated state:\n{json.dumps(inspect_res.get('state', {}), indent=2, ensure_ascii=False)}"
                }
            ]
            if inspect_res.get("image_b64"):
                content.append({
                    "type": "image",
                    "data": inspect_res["image_b64"],
                    "mimeType": "image/png"
                })
            return {"content": content}

        elif tool_name == "fusion360_build_endocrab_model":
            call_fusion_post("/build", {})
            time.sleep(1.5)
            inspect_res = call_fusion_get("/inspect")
            
            content = [
                {
                    "type": "text",
                    "text": f"Endocrab model build triggered. Current state:\n{json.dumps(inspect_res.get('state', {}), indent=2, ensure_ascii=False)}"
                }
            ]
            if inspect_res.get("image_b64"):
                content.append({
                    "type": "image",
                    "data": inspect_res["image_b64"],
                    "mimeType": "image/png"
                })
            return {"content": content}

        elif tool_name == "fusion360_animate_and_inspect":
            call_fusion_post("/animate_and_inspect", arguments)
            time.sleep(1.5)
            res = call_fusion_get("/animation_results")
            
            content = [
                {
                    "type": "text",
                    "text": f"Kinematic animation completed. Summary:\n{json.dumps({k: v for k, v in res.items() if k != 'frames'}, indent=2, ensure_ascii=False)}"
                }
            ]
            for idx, frame in enumerate(res.get("frames", [])):
                if frame.get("image_b64"):
                    content.append({
                        "type": "image",
                        "data": frame["image_b64"],
                        "mimeType": "image/png"
                    })
            return {"content": content}

        elif tool_name == "fusion360_export_mjcf":
            call_fusion_post("/export_mjcf", arguments)
            time.sleep(1.2)
            res = call_fusion_get("/mjcf_results")
            summary = res.get("summary", {})
            xml_sample = res.get("xml_content", "")[:1000]
            
            content = [
                {
                    "type": "text",
                    "text": f"✅ MuJoCo MJCF Export Complete!\nSummary:\n{json.dumps(summary, indent=2, ensure_ascii=False)}\n\nXML Preview (First 1000 chars):\n{xml_sample}..."
                }
            ]
            return {"content": content}

        elif tool_name == "fusion360_capture_dfm_views":
            call_fusion_post("/capture_dfm_views", arguments)
            time.sleep(1.5)
            res = call_fusion_get("/dfm_views")
            
            views = res.get("views", [])
            content = [
                {
                    "type": "text",
                    "text": f"✅ DFM 4-View Capture Complete! ({len(views)} views captured at {res.get('audit_timestamp')})\n\nView details:\n" + "\n".join([f"- [{v.get('view_name')}]: {v.get('description')} ({v.get('filename')})" for v in views])
                }
            ]
            for v in views:
                if v.get("image_b64"):
                    content.append({
                        "type": "image",
                        "data": v["image_b64"],
                        "mimeType": "image/png"
                    })
            return {"content": content}

        else:
            return {
                "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}],
                "isError": True
            }

    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Fusion 360 Communication Error: {str(e)}\nEnsure Fusion 360 and AntigravityOnDemand Add-in (Port 8080) are running."}],
            "isError": True
        }


def main():
    """Stdio JSON-RPC Main Loop (Anthropic MCP Protocol)"""
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            req = json.loads(line.strip())
            req_id = req.get("id")
            method = req.get("method")
            params = req.get("params", {})

            if method == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "fusion360-mcp",
                            "version": "2.0.0"
                        }
                    }
                }
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()

            elif method == "notifications/initialized":
                pass

            elif method == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "tools": TOOLS_DEFINITIONS
                    }
                }
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()

            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                result = handle_tool_call(tool_name, arguments)
                
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": result
                }
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()

            elif req_id is not None:
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()

        except Exception as e:
            sys.stderr.write(f"Error handling MCP request: {e}\n")
            sys.stderr.flush()


if __name__ == "__main__":
    main()
