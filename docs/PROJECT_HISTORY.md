# 📜 ENDOCRAB 프로젝트 연구 및 대화 히스토리 (Project History & Decision Records)

본 문서는 **120여 회에 걸친 AI 에이전트와의 연구 대화, 아티팩트 생성 및 엔지니어링 의사결정의 전 과정**을 체계적으로 정리한 마스터 연표입니다.
원시 대화 로그(기계 판독용 DB/JSONL)를 보지 않고도 프로젝트의 발단부터 최종 성과까지의 맥락과 기술적 Rationale을 완벽히 파악할 수 있도록 구성되었습니다.

---

## 🧭 대화 및 엔지니어링 생애주기 (5대 핵심 단계)

### 📍 Phase 1: 임상적 미충족 수요 및 한계 분석 (Clinical Problem Definition)
- **주요 대화 주제**:
  - 기존 수술용 로봇 및 내시경 봉합 기구 분석: Nature (2024) ENDOCRAB, Assut Europe Endo360, Apollo OverStitch, IITB 복강경 봉합 기구
  - 봉합 바늘의 구동 방식과 체내 조직 관통 후의 실제 봉합 프로세스 비교
- **핵심 문제 의식**:
  - 기존 기구들은 C-링 바늘을 통해 조직을 관통하는 것(Tissue Penetration)은 성공했으나, **체내의 협소한 내강(Stomach/GI Tract, 지름 20~30mm) 안에서 실을 엮어 매듭을 짓는 수기 매듭(In-situ Hand-tied Knotting)이 극도로 어렵고 시술 시간을 지연**시킴.
  - 내시경 작업 채널($\varnothing 2.8\sim 3.2\text{ mm}$)을 통해 투입할 수 있는 **원터치 자동 체내 봉합사 고정 장치(Stopper/Cinch)**가 필수적임.
- **주요 산출물**:
  - [`endo_suture_cinch_whitepaper.md`](../endo_suture_cinch_whitepaper.md) (봉합 고정 기구 종합 백서)
  - [`docs/Endo360.pdf`](Endo360.pdf) (상용 Endo360 카탈로그 분석)
  - [`images/nature_fig3_endocrab_photo.jpg`](../images/nature_fig3_endocrab_photo.jpg), [`images/nature_fig4_suturing_steps.png`](../images/nature_fig4_suturing_steps.png)

---

### 📍 Phase 2: 3D CAD AI 생태계 심층 조사 및 패러다임 전환 (CAD AI Landscape)
- **주요 대화 주제**:
  - 생성형 AI(LLM)를 활용한 3D CAD 모델링 도구 전수 조사: OpenSCAD, CadQuery, Zoo KCL, FreeCAD MCP, Leo AI 등
  - LLM에게 프롬프트를 주어 직접 코드를 짜게 했을 때의 문제점 진단
- **핵심 결론 및 의사결정 (ADR-01)**:
  - **"Zero Mock-up / Anti-Proxy Rule" 채택**: 단순 텍스트 프롬프트는 실제 제조 불가능한 '속 빈 박스형 프록시(Block-like Proxy)'만 생성함.
  - 의료기기의 정밀 공차($\pm 0.05\text{ mm}$)와 치수 연동을 보장하기 위해서는 표준 엔지니어링 툴인 **Autodesk Fusion 360의 파라메트릭 CAD 환경과 AI 간의 폐루프(Closed-Loop) API 제어 파이프라인**이 필수적임을 규명.
- **주요 산출물**:
  - [`docs/3D_CAD_AI_Research_Report.html`](3D_CAD_AI_Research_Report.html) (3D CAD AI 전수 조사 보고서)
  - [`docs/ENDOCRAB_Fusion360_Error_Analysis_Report.html`](ENDOCRAB_Fusion360_Error_Analysis_Report.html) (AI 프록시 발생 근본 원인 분석)
  - [`docs/Zoo_Dev_Detailed_Guide.html`](Zoo_Dev_Detailed_Guide.html) (Zoo KCL 프로그래밍 가이드)
  - [`RULES.md`](../RULES.md) 및 [`.cursorrules`](../.cursorrules) (엔지니어링 거버넌스 수립)

---

### 📍 Phase 3: Antigravity × Fusion 360 양방향 제어 인프라 구축 (Infrastructure)
- **주요 대화 주제**:
  - 로컬 윈도우 환경에서 구동 중인 Fusion 360과 에이전트 간의 실시간 통신 브리지 설계
  - 뷰포트 캡처, 지오메트리 피처 검사, 파라미터 실시간 주입 프로토콜
- **핵심 기술 성과**:
  - `src/AntigravityOnDemand/`: Fusion 360 내부에서 구동되는 고속 경량 REST API 서버 (Port 8080)
  - `src/fusion360_mcp_server.py`: FastMCP 프로토콜을 준수하여 AI 도구(Inspect, Modify, Execute)로 제어
  - **4-Pillar 자율 검증 체계 확립**:
    1. 뷰포트 다각도 이미지 자동 검사 (`POST /inspect`)
    2. MuJoCo 접촉 역학 시뮬레이션 (`src/mujoco_endo_sim.py`)
    3. 멀티모달 시각 DFM 결함 감사 (`src/vlm_dfm_auditor.py`)
    4. 파라메트릭 `fx` 자율 최적화 루프
- **주요 산출물**:
  - [`src/AntigravityOnDemand/AntigravityOnDemand.py`](../src/AntigravityOnDemand/AntigravityOnDemand.py)
  - [`src/fusion360_mcp_server.py`](../src/fusion360_mcp_server.py)
  - [`.agents/rules/fusion360-rendering-rule.md`](../.agents/rules/fusion360-rendering-rule.md)
  - [`.gemini/skills/fusion360-cad-automation/`](../.gemini/skills/fusion360-cad-automation/)

---

### 📍 Phase 4: ENDOCRAB 뼈대 CAD 모델링 및 기구학 검증 (Kinematic Model)
- **주요 대화 주제**:
  - C형 곡선 바늘의 360도 연속 회전을 위한 래칫(Ratchet)-폴(Pawl) 구동부 및 캠 슬롯(Cam-slot) 링크 설계
  - 180도 왕복 와이어 장력 구동 시 사점(Dead-center) 통과 및 역전 방지 메커니즘
- **핵심 기술 성과**:
  - 19개 사용자 파라미터(`fx`) 완벽 수립 (내시경 외경, 핀 간격, 슬롯 곡률 등)
  - 4개 서브어셈블리(베이스 브래킷, 바늘 드라이버, 래칫 스토퍼, 동력 전달부)와 13개 부품 조립 완료
  - 다각도 뷰포트 캡처 및 관절 간섭 제로(Zero-Collision) 검증 통과
- **주요 산출물**:
  - [`docs/ENDOCRAB_Design_Specification.html`](ENDOCRAB_Design_Specification.html) & [`ENDOCRAB_Fusion360_Design_Specification.md`](../ENDOCRAB_Fusion360_Design_Specification.md)
  - [`images/fig1_assembly.png`](../images/fig1_assembly.png) ~ [`images/fig12_abnormal_kinematics.png`](../images/fig12_abnormal_kinematics.png)
  - [`build_and_verify_zero_collision.py`](../build_and_verify_zero_collision.py)
  - [`output/endo_bracket.step`](../output/endo_bracket.step), [`output/endo_bracket.stl`](../output/endo_bracket.stl)

---

### 📍 Phase 5: 체내 봉합 마감용 스토퍼(Stopper/Cinch) 정밀 설계 (In-Situ Knotting Alternative)
- **주요 대화 주제**:
  - 체내에서 실을 묶지 않고 락킹하는 동축 푸시-풀(Coaxial Push-Pull) 마이크로 메커니즘
  - 생체 적합성 재질(Titanium 외부 하우징 + PEEK 내부 쐐기 + Living Spring) 선정
  - 브라우저 기반 동적 시뮬레이터 개발 및 마스터 핸드오프 문서화
- **핵심 기술 성과**:
  - 바늘 관통 ➔ 쐐기 전진 ➔ 역방향 락킹(바늘 및 봉합사 양방향 고정) ➔ 봉합사 자동 절단 메커니즘 수립
  - 브라우저에서 슬라이더로 조작 가능한 2D 캔버스 인터랙티브 시뮬레이터 구축
- **주요 산출물**:
  - [`docs/ENDOCRAB_Stopper_Detailed_CAD_Design_Spec.md`](ENDOCRAB_Stopper_Detailed_CAD_Design_Spec.md)
  - [`docs/ENDOCRAB_InSitu_Knotting_Module_Design_Spec.md`](ENDOCRAB_InSitu_Knotting_Module_Design_Spec.md)
  - [`cinch_mechanism_simulator.html`](../cinch_mechanism_simulator.html)
  - [`docs/ENDOCRAB_Knotting_Preparation_Master_Handoff.html`](ENDOCRAB_Knotting_Preparation_Master_Handoff.html)

---

## 📊 핵심 산출물 및 문서 색인표 (Documentation Index)

| 분류 | 문서 / 파일명 | 핵심 내용 |
| :--- | :--- | :--- |
| **마스터 핸드오프** | [`docs/ENDOCRAB_Knotting_Preparation_Master_Handoff.html`](ENDOCRAB_Knotting_Preparation_Master_Handoff.html) | 프로젝트 총괄 배경, 선행기술 비교, 기구학 Rationale 및 차기 개발 인계 지침 |
| **상세 CAD 사양** | [`docs/ENDOCRAB_Design_Specification.html`](ENDOCRAB_Design_Specification.html) | 19개 fx 파라미터, 4대 서브어셈블리, 13개 부품 조인트 및 구속조건 명세 |
| **스토퍼 설계서** | [`docs/ENDOCRAB_Stopper_Detailed_CAD_Design_Spec.md`](ENDOCRAB_Stopper_Detailed_CAD_Design_Spec.md) | 체내 원터치 봉합 락킹 캡 상세 설계 및 마이크로 스프링 사양서 |
| **봉합 고정 백서** | [`endo_suture_cinch_whitepaper.md`](../endo_suture_cinch_whitepaper.md) | 티타늄 하우징 + PEEK 웨지 + 판스프링 역학 이론 및 실험 검증 마스터 백서 |
| **동적 시뮬레이터** | [`cinch_mechanism_simulator.html`](../cinch_mechanism_simulator.html) | 브라우저 즉시 구동 2D 인터랙티브 스토퍼 락킹 메커니즘 시뮬레이터 |
| **CAD AI 연구 리포트** | [`docs/3D_CAD_AI_Research_Report.html`](3D_CAD_AI_Research_Report.html) | OpenSCAD, CadQuery, Zoo KCL, Leo AI 등 프로그래밍 방식 CAD AI 비교 분석 |
| **에이전트 거버넌스** | [`RULES.md`](../RULES.md), [`.agents/rules/`](../.agents/rules/) | 4-Pillar 뷰포트/시뮬레이션 검증 룰 및 금지 구역 보존 원칙 |
| **3D CAD 파일** | [`output/endo_bracket.step`](../output/endo_bracket.step), [`.stl`](../output/endo_bracket.stl) | 상용 CAD 호환 표준 STEP 및 3D 프린팅용 STL 모델 |
