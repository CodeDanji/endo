# ENDOCRAB Fusion 360 CAD 구현 및 실행 가이드

본 가이드는 Nature Scientific Reports (2024) 기반 **ENDOCRAB 위장관 천공 봉합 수술 모듈**의 Fusion 360 3D CAD 파라메트릭 자동 모델링 파이프라인 및 실행 방법입니다.

---

## 1. 구현 파일 구성

| 구분 | 파일 경로 | 설명 |
| :--- | :--- | :--- |
| **CAD 빌더 스크립트** | [`src/build_endocrab_model.py`](../src/build_endocrab_model.py) | Fusion 360 4개 서브어셈블리 및 13개 부품 파라메트릭 생성 코드 |
| **On-Demand 애드온** | [`src/AntigravityOnDemand/AntigravityOnDemand.py`](../src/AntigravityOnDemand/AntigravityOnDemand.py) | Port 8080 REST 서버 (`/inspect`, `/modify`, `/build` 지원) |
| **스크립트 매니페스트** | [`src/ENDOCRAB_Builder/ENDOCRAB_Builder.manifest`](../src/ENDOCRAB_Builder/ENDOCRAB_Builder.manifest) | Fusion 360 Scripts 등록 매니페스트 |
| **자동 배포 스크립트** | [`src/install_to_fusion360.ps1`](../src/install_to_fusion360.ps1) | Fusion 360 AppData 경로 자동 설치 스크립트 |

---

## 2. Fusion 360 실행 및 모델링 자동 생성 방법 (2가지 연동 지원)

### 방법 A: Fusion 360 대화상자에서 직접 실행 (Direct Script Run)
1. Autodesk Fusion 360을 실행합니다.
2. 단축키 **`Shift + S`** (또는 `Utilities` ➔ `Add-Ins` ➔ `Scripts and Add-Ins`)를 누릅니다.
3. **`My Scripts`** 목록에서 **`ENDOCRAB_Builder`**를 선택하고 **`Run`** 버튼을 클릭합니다.
4. `ENDOCRAB_Master_Assembly.f3d` 문서가 신규 생성되고, 4개 서브어셈블리와 13개 부품 3D CAD 모델이 파라메트릭으로 완전 자동 생성됩니다!

---

### 방법 B: Antigravity AI On-Demand REST 호출 (AI-Driven Generation)
1. Fusion 360 실행 후 `Shift + S` ➔ `Add-Ins` 탭 ➔ **`AntigravityOnDemand`** 선택 후 **`Run`**을 클릭합니다.
2. AI 대화창에서 아래 명령을 전송합니다:
   > *"Fusion 360에 ENDOCRAB 모델 자동 생성 진행해줘"*
3. AI가 `POST http://localhost:8080/build` 엔드포인트를 호출하여 UI 메인 스레드에서 안전하게 CAD 모델링을 자동 생성합니다.

---

## 3. 생성되는 부품 계층 구조 및 파라메트릭 치수 (`fx`)

### 1) 어셈블리 트리 구조
```text
ENDOCRAB_Master_Assembly.f3d
├── 📁 01_Distal_EndEffector_SubAssy (선단부 엔드이펙터 어셈블리)
│   ├── 📄 Main_Body_Frame (메인 바디 - 50 x 15 x 5.45 mm, Stainless Steel 316L)
│   ├── 📄 Endoscope_Mounting_Cap (내시경 결합 마운트 캡 - Ø11.5 mm, Rubber)
│   ├── 📄 Gripper_Jaw_Left (좌측 조직 잡기 조 - 6.0 mm)
│   ├── 📄 Gripper_Jaw_Right (우측 조직 잡기 조 - 6.0 mm)
│   ├── 📄 Gripper_Linkage_Pin (힌지 핀 - Ø1.0 mm)
│   ├── 📄 Ring_Needle_13mm (360° 회전 원형 바늘 - Ø13.0 mm, 선경 1.2 mm)
│   └── 📄 Ring_Needle_Guide_Track (바늘 가이드 트랙 - 슬롯 유격 0.1 mm)
│
├── 📁 02_Cable_Actuation_SubAssy (구동 전달부)
│   ├── 📄 Gripper_Control_Wire (그리퍼 개폐 와이어 - Ø0.6 mm Stainless Wire)
│   └── 📄 Needle_Rotation_Wire (바늘 회전 와이어 - Ø0.6 mm Stainless Wire)
│
├── 📁 03_Proximal_Controller_SubAssy (체외 조작 핸들)
│   ├── 📄 Needle_Rotation_Handle (바늘 360° 회전 핸들)
│   └── 📄 Gripper_OpenClose_Handle (그리퍼 개폐 조작 핸들)
│
└── 📁 04_Knotting_Fastener_SubAssy (매듭 신치/락킹 모듈)
    ├── 📄 Male_Stud (사선 수형 스터드)
    └── 📄 Female_Lock_Ring (압착 암형 락 링)
```

### 2) 등록된 `fx` User Parameters
Fusion 360의 `Modify` ➔ `Change Parameters` (`fx`) 메뉴에서 언제든지 수치를 수정할 수 있습니다.

* `Body_Length`: 50.0 mm
* `Body_Width`: 15.0 mm
* `Body_Thickness`: 5.45 mm
* `Scope_Attach_Dia`: 11.5 mm
* `Gripper_Length`: 6.0 mm
* `Needle_Outer_Dia`: 13.0 mm
* `Needle_Wire_Dia`: 1.2 mm
* `Suture_Dia`: 0.15 mm
* `Track_Clearance`: 0.10 mm
