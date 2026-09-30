# 🦀 ENDOCRAB: Flexible Endoscopic Suture & In-Situ Cinch Mechanism

> **Nature Scientific Reports (2024)** 기반의 내시경 위장관 천공 봉합 수술 모듈(ENDOCRAB) 및 체내 매듭 대체 초소형 봉합사 고정 캡(Endo Suture Cinch)의 3D CAD 파라메트릭 설계, 역학 시뮬레이션, AI 자율 검증 파이프라인 프로젝트입니다.

---

## 📌 1. 프로젝트 핵심 개요

유연 내시경(Flexible Endoscope) 환경의 좁은 작업 채널($\varnothing 2.8\sim 3.2\text{ mm}$)을 통해 체내 깊숙이 접근하여 위장관 천공을 봉합하는 기구입니다.
본 프로젝트는 기존 수기 매듭(Hand-tied knot)의 한계를 극복하고, **C-형 링 바늘의 360도 연속 회전 구동 메커니즘**과 **체내 원터치 자동 락킹 스토퍼(Cinch)**를 완전 파라메트릭 3D CAD(Autodesk Fusion 360)로 구현하고 다각도 시뮬레이션으로 검증합니다.

```
                    [ 4-Pillar AI Autonomous Engineering ]
                                      │
        ┌───────────────┬─────────────┴─────────────┬───────────────┐
        ▼               ▼                           ▼               ▼
 [ Pillar 1: Viewport ] [ Pillar 2: Contact Physics ] [ Pillar 3: DFM VLM ] [ Pillar 4: fx Optimization ]
  3D 다각도 검사        MuJoCo 와이어/접촉 동역학     멀티모달 시각적 결함 감사    파라메트릭 수렴 루프
```

---

## 📂 2. 디렉토리 구조 및 핵심 모듈

```
ENDO/
├── docs/                                  # 상세 사양서, 백서, 연구 리포트, 상용 기구 분석
│   ├── PROJECT_HISTORY.md                 # 120여 회 대화 발전 연표 및 의사결정 기록(ADR)
│   ├── ENDOCRAB_Knotting_Preparation_Master_Handoff.html # 총괄 마스터 인계 문서
│   ├── ENDOCRAB_Design_Specification.html # 19개 fx 파라메터 및 어셈블리 상세 사양
│   ├── ENDOCRAB_Stopper_Detailed_CAD_Design_Spec.md # 마이크로 스토퍼/신치 정밀 설계서
│   ├── 3D_CAD_AI_Research_Report.html     # CAD AI 자동화 생태계 심층 리포트
│   └── knotting module 설계/              # 매듭 모듈 개념 도면 및 분석 자료
├── images/                                # 기구학 도면(fig1~fig12), 논문 실물 사진, 드래프트
│   └── drafts/                            # 아이디어 및 메커니즘 드래프트 스케치
├── src/                                   # 파이프라인 핵심 소스코드 및 Add-in
│   ├── AntigravityOnDemand/               # Fusion 360 내부 On-Demand REST API Add-in (Port 8080)
│   ├── fusion360_mcp_server.py            # FastMCP 기반 AI 에이전트 ↔ Fusion 360 통신 브리지
│   ├── mujoco_endo_sim.py                 # MuJoCo 기반 와이어 장력 및 접촉 물리 시뮬레이터
│   ├── vlm_dfm_auditor.py                 # Vision-Language Model DFM 제조성 감사기
│   └── install_to_fusion360.ps1           # Windows Fusion 360 Add-in 자동 설치 스크립트
├── output/                                # 시뮬레이션 결과, 뷰포트 캡처, STEP/STL 내보내기 모델
│   ├── endo_bracket.step                  # CAD 표준 STEP 내보내기 파일
│   └── endo_bracket.stl                   # 3D 프린팅용 STL 메시 파일
├── cinch_mechanism_simulator.html         # [바로 실행] 브라우저 기반 2D 인터랙티브 신치 시뮬레이터
├── ENDOCRAB_Fusion360_Design_Specification.md # 마크다운 CAD 부품/조인트 명세서
├── endo_suture_cinch_whitepaper.md        # 봉합 고정 기구 물리/탄성 역학 종합 백서
├── RULES.md & .cursorrules                # 에이전트 엔지니어링 거버넌스 4대 규칙
└── .gitignore                             # 가상환경, 임시파일, 캐시 철저 배제 설정
```

---

## 🚀 3. 다른 컴퓨터에서 바로 열람 및 실행하는 방법

### A. 브라우저에서 인터랙티브 시뮬레이터 즉시 확인
- [`cinch_mechanism_simulator.html`](cinch_mechanism_simulator.html) 파일을 크롬 또는 엣지 브라우저에서 더블 클릭하여 실행합니다.
- 슬라이더 조작을 통해 체내 스토퍼의 **전진 ➔ 바늘 관통 ➔ 쐐기(Wedge) 락킹 ➔ 봉합사 절단** 시퀀스를 2D 인터랙티브 캔버스로 즉시 테스트할 수 있습니다.

### B. 주요 문서 및 연구 결과 열람
- **대화 및 의사결정 히스토리**: [`docs/PROJECT_HISTORY.md`](docs/PROJECT_HISTORY.md)
- **마스터 프로젝트 핸드오프**: [`docs/ENDOCRAB_Knotting_Preparation_Master_Handoff.html`](docs/ENDOCRAB_Knotting_Preparation_Master_Handoff.html)
- **봉합 메커니즘 종합 백서**: [`endo_suture_cinch_whitepaper.md`](endo_suture_cinch_whitepaper.md)

### C. Autodesk Fusion 360 연동 및 CAD 모델 생성
1. **Add-in 자동 설치**:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\src\install_to_fusion360.ps1
   ```
2. **CAD 모델 생성**:
   - Fusion 360 실행 후 단축키 `Shift + S` ➔ `My Scripts` ➔ `ENDOCRAB_Builder` 실행
   - 4개 서브어셈블리(Base Bracket, Needle Driver, Stopper Module, Transmission)와 13개 부품이 파라메트릭으로 자동 생성됩니다.

---

## 🛡️ 4. 에이전트 거버넌스 4대 규칙 (RULES.md)
1. **성급한 실행 금지 (Look Before You Leap)**: 전체 기구학 관계 확인 전 섣부른 피처 수정 금지
2. **금지 구역 보존 (Strict Keep-Out Enforcement)**: 내시경 광학계/작업 채널 침범 절대 불가
3. **불필요한 프록시 바디 생성 금지 (Zero Mock-up Rule)**: 단순 박스 모델이 아닌 실제 제조 가능한 파라메트릭 솔리드 생성
4. **다각도 시각/물리적 자기비판 루프 (Continuous Multi-View Audit)**: 뷰포트 캡처 및 간섭 검사 무조건 통과 후 커밋
