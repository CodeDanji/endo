---
name: fusion360-cad-automation
description: "Autodesk Fusion 360 파라메트릭 3D CAD 모델 생성, CadQuery STEP 파이프라인, Master Template fx 변수 제어, MuJoCo 물리 시뮬레이터 닫힌 루프(Closed-Loop) 동역학 검증 및 멀티모달 VLM 초소형 DFM/조립성 자동 감사 (v2.0) 스킬"
---

# Fusion 360 AI CAD Automation Skill (v2.0)

본 스킬은 **Autodesk Fusion 360**과 **Google Antigravity AI Agent** 간의 파라메트릭 3D CAD 자동화, CadQuery STEP 파일 내보내기/임포트, Master Template `fx` 변수 제어, REST 브릿지 커스텀 이벤트 연동, **동적 기구학 다단계 뷰포트 시각 검수**, **MuJoCo 3.x 닫힌 루프 물리 동역학 검증**, 그리고 **멀티모달 VLM 기반 마이크로 DFM/조립성 자동 감사** 프로토콜(ADR-2026-ENDO-002)을 규정합니다.

---

## 1. 하이브리드 CAD 자동화 선택 매트릭스 (Strategy Selection Matrix)

Fusion 360 자동화 시 모델의 복잡도와 설계 목적에 따라 최적의 접근 방식을 선택합니다.

| 전략 (Strategy) | 주요 적용 대상 | 기술적 구현 메커니즘 | 장점 / 해결하는 한계점 |
| :--- | :--- | :--- | :--- |
| **1. Master Template `fx` 제어** | 복잡한 수술 장비 전원/구동부 전체 조립품 (`.f3d`) | REST `POST /modify` ➔ `userParameters.itemByName(key).expression` 갱신 | 100% 실물 렌더링 퀄리티 보장, 0.1초 내 형상 재계산 |
| **2. CadQuery STEP 파이프라인** | 유선형 곡면(Organic Loft), 정밀 인볼루트 기어 치형, 톱니 집게 | Host 파이썬 환경에서 `cadquery`로 `.step` 내보내기 ➔ REST `POST /import_step` | Fusion API의 B-Rep 엣지 인덱스 손실 및 스케치 구속 예외 완전 방지 |
| **3. Pure Fusion 360 API** | 단순 하우징 브라켓, 직육면체 플레이트, 관통 구멍 | `adsk.fusion` Python API 직접 호출 (`extrudeFeatures`, `combineFeatures`) | 외부 파이썬 라이브러리 의존성 없이 단일 스크립트로 동작 |
| **4. MuJoCo 물리 폐루프** | 와이어 텐던 구동, 팁단 조직 관통력, 앵커 도킹 래치 | REST `POST /export_mjcf` ➔ `src/mujoco_endo_sim.py` 동역학 시뮬레이션 | CAD 파라미터 변경 후 장력/굴절각/접촉력 정량 수치 피드백 |
| **5. VLM DFM 감사관** | 초소형 마이크로 의료기기 가공성/조립성 검증 | REST `POST /capture_dfm_views` ➔ `src/vlm_dfm_auditor.py` (Gemini Vision) | 4대 단면/투시 뷰 기반 벽두께, 툴 클리어런스, 와이어 곡률 자동 감사 |

---

## 2. 6단계 엔지니어링 프로토콜 (6-Stage Engineering Protocol)

### Stage 1: REST Listener & MCP Stdio Server 실시간 동기화
* Fusion 360 내부 상주 Add-In (`AntigravityOnDemand`, Port 8080) 및 MCP 표준 서버(`fusion360_mcp_server.py`)를 구동합니다.
* `GET /inspect`: `viewport.png` 캡처 및 `state.json` (파라미터표, 바디 수, 토폴로지)을 반환합니다.
* `POST /execute_code`: 임의의 파이썬 CAD 코드를 메인 스레드에서 안전하게 `exec(code)`로 즉시 실행합니다.
* `POST /animate_and_inspect`: 조인트 명칭과 스트로크 단계(`[0.0, 0.5, 1.0]`)를 받아 조인트를 실제로 구동하며 다단계 프레임을 연속 캡처합니다.
* `GET /animation_results`: 각 구동 단계별 프레임 이미지(base64)와 바운딩 박스/조인트 토폴로지를 수집합니다.
* `POST /export_mjcf`: 컴포넌트별 STL 메시 및 질량/CoM/관성 행렬/조인트 트리를 내보내고 `model.xml`을 생성합니다.
* `POST /capture_dfm_views`: 4대 관점(아이소 투시, 텐던 채널 단면, 핀 어셈블리 단면, 분해 뷰) 이미지를 일괄 캡처합니다.

### Stage 2: CadQuery / OpenCASCADE 정밀 STEP 파이프라인
* 곡면 로프트, 톱니 집게 Notch, toroidal 링 바늘 등 Fusion API 수동 코딩이 불안정한 지오메트리는 `scripts/cadquery_step_generator.py`를 실행합니다.
* 에이전트는 호스트 환경에서 `cadquery` 스크립트를 실행하여 `%TEMP%\AntigravityCAD\` 폴더에 `.step` 파일로 내보낸 후, Fusion 360 REST 엔드포인트 `/import_step`을 통해 임포트합니다.

### Stage 3: Master Template `fx` 변수 실시간 바인딩
* `resources/parameters_schema.json` 스키마로 검증된 수술용 디바이스 변수를 REST `/modify`로 전송합니다.
* 파라미터 변경 시 Fusion 360 Compute Graph가 파라메트릭 피처 트리를 자동 재계산합니다.

### Stage 4: 동적 기구학 다단계 뷰포트 시각 검수 (Dynamic Kinematic Multi-Frame Vision Audit)
* **절대 원칙**: 움직임(회전, 슬라이더, 링크, 톱니 맞물림 등)이 존재하는 기구학 어셈블리는 **단 1장의 정적 스크린샷으로 검수를 종결해서는 안 됩니다**.
* **3단계 필수 구동 검수**:
  1. **Step 0: 초기 대기 상태 (Initial Rest State, 0% Stroke)**: 초기 조립 공차 및 클리어런스 확인.
  2. **Step 1: 중간 작동/맞물림 상태 (Mid-Stroke Engagement, 50% Stroke)**: 기어 톱니 맞물림 연속성, 슬라이더 레일 가이드 지지 상태 확인.
  3. **Step 2: 최대 구동/관통 상태 (Full Stroke / Peak Actuation, 100% Stroke)**: 하우징 간섭(Collision), 선단 돌출 한계, 바늘 조직 관통 궤적 확인.

### Stage 5: MuJoCo 닫힌 루프 물리 동역학 검증 (MuJoCo Physics Closed-Loop)
* Fusion 360에서 `POST /export_mjcf`를 호출하여 물리 모델 에셋(STL 메시 + `model.xml`)을 추출합니다.
* `src/mujoco_endo_sim.py`를 실행하여 텐던 장력($0 \sim 15\text{ N}$) 및 팁단 조직 저항 반력($2.0\text{ N}$)을 인가합니다.
* `simulation_results.json`의 평가 메트릭스를 확인합니다:
  - `achieved_sweep_angle_deg >= 0.9 * target_sweep_angle_deg`
  - `max_tendon_tension_N <= tension_limit_N` ($10.0\text{ N}$)
  - `anchor_docking_success == true`
  - `buckling_risk_detected == false`
* 메트릭스 미달 시 파라메트릭 보정($\Delta r_{pulley}, \Delta t_{arm}$) 후 재시뮬레이션을 수행합니다.

### Stage 6: 공간 지능 & 멀티모달 VLM DFM / 조립성 자동 감사 (Multimodal VLM DFM Audit)
* Fusion 360에서 `POST /capture_dfm_views`를 호출하여 4개 뷰 이미지를 획득합니다:
  1. `Isometric_Wireframe.png`: 골격 및 내부 와이어 경로 투시
  2. `Section_Tendon_Channel.png`: 와이어 채널 모서리 Fillet/Chamfer 반경 ($R \ge 1.5 \times \varnothing_{wire}$)
  3. `Section_Pin_Assembly.png`: 힌지 핀 결합 및 Micro-forceps 진입 클리어런스 ($\ge 1.2\text{ mm}$)
  4. `Exploded_Assembly_View.png`: 분해 조립 순서 및 간섭 검사
* `src/vlm_dfm_auditor.py`를 실행하여 `dfm_audit_report.json`을 생성하고 `overall_dfm_verdict` (`PASS`/`WARNING`/`FAIL`)을 최종 확인합니다.

---

## 3. 핵심 Fusion 360 API 제약 사항 및 단위 규칙 (Critical Rules)

### Rule 1: 내부 데이터베이스 단위 시스템 (cm vs. mm)
* **길이 단위**: Fusion 360 API 내부 DB는 모든 길이 값을 **센티미터 (cm)** 단위로 저장 및 계산합니다.
* **변환 규칙**: `Point3D.create(x, y, z)` 또는 `ValueInput.createByReal(val)` 호출 시 값은 반드시 **cm** (`mm_val / 10.0`) 단위여야 합니다.
* **문자열 파싱**: `ValueInput.createByString("50.0 mm")`은 단위 문자열(`mm`, `cm`, `deg`)을 자동으로 올바르게 파싱합니다.

### Rule 2: 읽기 전용 (Read-Only) 속성 보호
* `doc.name`: 읽기 전용 속성입니다. `doc.name = "name.f3d"` 할당 시 `AttributeError: can't set attribute 'name'` 예외가 발생합니다.
* `root_comp.name`: 읽기 전용 속성입니다. `root_comp.name = "name"` 할당 시 `RuntimeError: 3 : root component name cannot be changed` 오류가 발생합니다.

### Rule 3: 진정한 파라메트릭 구속 (`sketchDimensions`)
* `addTwoPointRectangle`이나 `addByCenterRadius`로 그린 스케치에 구속조건을 주지 않으면 파라미터가 연결되지 않습니다.
* **필수**: `sketch.sketchDimensions.addDistanceDimension()` 또는 `addDiameterDimension()`을 호출하고 `dim.parameter.expression = "User_Param_Name"`으로 명시적 치수 구속을 부여해야 합니다.

### Rule 4: 3D Toroidal 및 곡면 회전 피처
* 동심원 2D 원을 Z축으로 평면 압출하면 평평한 와셔/튜브 형태가 됩니다.
* **진정한 3D Toroidal Ring Needle**: 중심축에서 거리 $R$만큼 떨어진 평면에 원형 단면($\text{Ø}1.2\text{ mm}$)을 그린 뒤, `revolveFeatures.createInput(profile, axis, NewBody)`를 호출하여 중심 Z축을 기준으로 330°~360° 회전 스위프합니다.

### Rule 5: 파라메트릭 모드에서 메모리 B-Rep 직접 주입 금지 (BRepBodies_add 에러 방지)
* **주의**: `TemporaryBRepManager` 객체를 `comp.bRepBodies.add(brep)`로 직접 추가하려 하면 `RuntimeError: 3 : A valid targetBaseFeature is required`가 발생합니다.
* **필수**: 타임라인 활성 모드에서는 반드시 `Sketch + ExtrudeFeatures (NewBody / Cut / Join)` 또는 `RevolveFeatures` 정석 API를 사용하여 피처를 생성해야 합니다.

### Rule 6: `setAsRevoluteJointMotion` 반환값 오용 금지
* **주의**: `jointInput.setAsRevoluteJointMotion(...)` 메서드는 Motion 객체가 아니라 성공 여부(`bool`)를 반환합니다. 반환값에 `.customOrigin` 등을 할당하면 `AttributeError: 'bool' object has no attribute 'customOrigin'`이 발생합니다.
* **필수**: 피벗 중심점은 `JointGeometry` 생성 시점에 전달해야 합니다.

### Rule 7: 파라메트릭 모드에서 독립 ConstructionPoint 생성 금지
* **주의**: `comp.constructionPoints.add()` 호출 시 `RuntimeError: 3 : Environment is not supported` 에러가 발생합니다.
* **필수**: 별도 참조점을 만들지 말고, 이미 생성된 실제 3D B-Rep Body의 `Circle3DCurveType` 또는 `Line3DCurveType` 모서리(`BRepEdge`)를 검색하여 직접 참조해야 합니다.

### Rule 8: As-Built Joint의 JointGeometry 래핑 필수
* **주의**: `asBuiltJoints.createInput(occ1, occ2, geo)`에 순수 `BRepEdge`나 `Point3D`를 직접 넘기면 `TypeError: argument 4 of type 'Ptr<JointGeometry>'` C++ 타입 에러가 발생합니다.
* **필수**: 항상 `adsk.fusion.JointGeometry.createByCurve(edge, keyPointType)`로 래핑하여 전달해야 합니다.

### Rule 9: Multi-Frame Dynamic Motion Audit Rule (동적 모션 다단계 검수 규칙)
* 어셈블리 내에 기구학적 구동부가 포함된 경우 최소 3단계(0%, 50%, 100%) 이상의 조인트 변위를 순차 적용하여 간섭 및 궤적을 확인합니다.

### Rule 10: MuJoCo Inertia Matrix 단위 변환 규칙
* Fusion 360의 관성 모멘트 단위는 $\text{kg}\cdot\text{cm}^2$입니다. MuJoCo MJCF의 표준 단위인 $\text{kg}\cdot\text{m}^2$로 변환하려면 반드시 $10,000$으로 나누어야 합니다 ($I_{m} = I_{cm} / 10000.0$).

### Rule 11: 초소형 DFM 4대 최소 기준
1. 와이어 채널 최소 곡률: $R \ge 1.5 \times \varnothing_{wire}$ (예: $\varnothing 0.2\text{ mm}$ ➔ $R \ge 0.3\text{ mm}$)
2. 최소 벽 두께: $t_{min} \ge 0.25\text{ mm}$ (마이크로 밀링 및 DMLS 적층 한계)
3. 마이크로 조립 클리어런스: 핀셋 팁 접근 여유 $\ge 1.2\text{ mm}$
4. 멸균 배출 포트: 블라인드 캐비티 내 관통 배출홀 $\varnothing \ge 0.5\text{ mm}$

---

## 4. 파이프라인 연동 CLI & REST API 참조

### REST 엔드포인트 목록 (Port 8080)
* `GET /inspect`: 뷰포트 캡처 및 파라미터/B-Rep 토폴로지 추출
* `POST /modify`: `{"parameters": {"Pulley_Radius": "1.8 mm"}}`
* `POST /execute_code`: `{"code": "..."}`
* `POST /animate_and_inspect`: `{"joint_name": "...", "steps": [0.0, 0.5, 1.0]}`
* `GET /animation_results`: 다단계 캡처 이미지 및 토폴로지 반환
* `POST /export_mjcf`: `{"mechanism_name": "ENDOCRAB", "output_dir": "..."}`
* `GET /mjcf_results`: 내보낸 MJCF XML 및 메타데이터 반환
* `POST /capture_dfm_views`: 4대 관점 DFM 뷰포트 연속 캡처
* `GET /dfm_views`: 4개 캡처 이미지(base64) 및 설명 반환

### 물리 시뮬레이션 및 DFM 실행 명령어
```bash
# 1. MuJoCo 텐던 구동 및 팁단 반력 시뮬레이션
python src/mujoco_endo_sim.py --xml output/ENDOCRAB_Mechanism.xml --output output/simulation_results.json --target_angle 120.0 --max_tension 10.0 --tip_force 2.0

# 2. 멀티모달 VLM DFM 자동 감사
python src/vlm_dfm_auditor.py --views_dir output/dfm_views --state output/state.json --output output/dfm_audit_report.json
```
