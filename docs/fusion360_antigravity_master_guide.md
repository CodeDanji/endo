# Fusion 360 × Antigravity On-Demand AI 마스터 가이드

---

## 1. 프로젝트 개요

본 문서는 **Autodesk Fusion 360**과 **Google Antigravity AI Agent** 간의 **On-Demand (AI 주도형 호출 및 수정)** 연동을 통해, 의료용 내시경 모듈(Endoscope Module) 등의 3D CAD 모델을 사용자가 대화창에서 명령을 내릴 때 비로소 점검, 수정, 검증하는 차세대 AI-CAD 통합 가이드입니다.

---

## 2. On-Demand(Pull & Execute) 연동 아키텍처

사용자가 대화창에서 명령을 내리지 않을 때 Fusion 360은 어떠한 리소스도 소모하지 않으며, **사용자가 AI(Antigravity)에게 명령을 내리는 바로 그 순간** AI가 MCP(Model Context Protocol) 툴을 이용해 Fusion 360의 최신 뷰포트/수치 데이터를 직접 조회(Pull)하고 파라미터를 안전하게 수정(Execute)합니다.

```mermaid
sequenceDiagram
    autonumber
### Step 2: 애드온 소스코드 구성 (`AntigravitySync` 폴더)
`AddIns` 폴더 내에 `AntigravitySync` 폴더를 생성하고 아래 2개 파일을 작성합니다.

#### 1) `AntigravitySync.manifest`
```json
{
	"autodeskProduct":	"Fusion360",
	"type":	"addin",
	"id":	"antigravity-sync-bridge",
	"author":	"Antigravity Agent",
	"description":	"Exports linked Viewport PNG and Design State JSON to Antigravity Workspace",
	"version":	"1.0.0",
	"runOnStartup":	true,
	"supportedOS":	"windows"
}
```

#### 2) `AntigravitySync.py`
```python
import adsk.core, adsk.fusion, traceback, os, json

# 동기화 디렉토리 설정
WORKSPACE_DIR = r"C:\Users\권원중학부재학바이오의공학부\Desktop\ENDO\docs"

def export_design_state():
    try:
        if not os.path.exists(WORKSPACE_DIR):
            os.makedirs(WORKSPACE_DIR)
            
        app = adsk.core.Application.get()
        design = adsk.fusion.Design.cast(app.activeProduct)
        vp = app.activeViewport
        
        # 1. 뷰포트 시각 캡처 (PNG)
        png_path = os.path.join(WORKSPACE_DIR, "current_viewport.png")
        vp.saveAsImageFile(png_path, 0, 0)
        
        # 2. 치수 파라미터 및 구조 JSON 덤프
        params = {}
        for param in design.allParameters:
            params[param.name] = {
                "expression": param.expression,
                "value": param.value,
                "unit": param.unit
            }
            
        state_data = {
            "document_name": app.activeDocument.name,
            "parameters": params,
            "body_count": design.rootComponent.bRepBodies.count
        }
        
        json_path = os.path.join(WORKSPACE_DIR, "design_state.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(state_data, f, indent=2, ensure_ascii=False)
            
        app.userInterface.messageBox("Antigravity 동기화 완료!\n- Image: current_viewport.png\n- Data: design_state.json")
    except:
        if app and app.userInterface:
            app.userInterface.messageBox('Sync Failed:\n{}'.format(traceback.format_exc()))

def run(context):
    try:
        export_design_state()
    except:
        pass

def stop(context):
    pass
```

### Step 3: Fusion 360 적용 및 실행
1. Fusion 360 실행 후 **`Shift + S`** 누르기
2. **`Add-Ins`** 탭 선택 → **`My Add-Ins`** 옆 **`+`** 아이콘 클릭 후 `AntigravitySync` 폴더 선택
3. **`Run on Startup`** 체크 후 **`Run`** 클릭!

---

## 6. 검토 및 사용 절차

1. Fusion 360에서 내시경 초안 작성 및 수정.
2. `Shift + S`로 `AntigravitySync` 실행 또는 `Ctrl + S` 저장.
3. Antigravity 챗에 *"수정 사항 확인해줘"* 요청.
4. Antigravity가 `current_viewport.png`와 `design_state.json`을 읽어 검증 결과 및 자동 보정안 제시.
