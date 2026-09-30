# ENDOCRAB 체내 봉합 마감 스토퍼(Stopper) 정밀 CAD 설계 사양서
(ENDOCRAB In-Situ Knotting Stopper Detailed CAD & Kinematic Specification - v1.0)

---

## 1. 개요 및 설계 목표 (Design Objectives)

본 문서는 ENDOCRAB 내시경 봉합 시스템의 **체내 봉합 마감 모듈(In-Situ Knotting Module v3.2)** 중 핵심 결속 장치인 **스토퍼 어셈블리(Knotting Stopper Assembly)**의 3D CAD 파라메트릭 치수, 5축 스위스턴 가공 공차(DFM), 마이크로 스프링 역학, 원터치 자가 잠금(Self-Locking) 메커니즘을 정의합니다.

```
                  [스토퍼 어셈블리 단면 및 동축 작동 구조]

       ◀── [조직 외벽 밀착]                 [체외 동축 카테터 인터페이스] ──▶
  ┌──────────────────────────────────────────────────────────────────────┐
  │ ① 외통 하우징 (Outer Housing, Ti-6Al-4V ELI)                          │
  │   - 플랜지: Ø 1.60 mm x 0.30 mm (조직 파고듦 방지 지지면)              │
  │   - 몸통 외경: Ø 1.40 mm, 전장: 2.40 mm                              │
  │   - 내부 보어(Bore): Ø 0.96 mm (플런저 슬라이딩 가이드)              │
  │   - 스프링 안착 턱(Step Shoulder): Ø 0.90 mm -> 관통홀 Ø 0.40 mm      │
  │ ┌──────────────────────────────────────────────────────────────────┐ │
  │ │ ② 마이크로 압축 스프링 (Micro Spring, 316LVM/Nitinol)             │ │
  │ │   - 선경: Ø 0.10 mm, 외경: Ø 0.90 mm, 내경: Ø 0.70 mm            │ │
  │ │   - 자유장: 1.20 mm, 압축장: 0.60 mm, k = 0.50 N/mm, 초기압: 0.15N│ │
  │ ├──────────────────────────────────────────────────────────────────┤ │
  │ │ ③ 내통 톱니 플런저 (Inner Serrated Plunger, Ti-6Al-4V / PEEK)     │ │
  │ │   - 외경: Ø 0.95 mm, 축방향 전장: 1.60 mm                         │ │
  │ │   - 관통홀/슬롯: Ø 0.30~0.35 mm                                   │ │
  │ │   - 비대칭 래칫 톱니: 45° 경사면(전진 무저항) / 90° 수직턱(역방향 잠금)│ │
  │ └──────────────────────────────────────────────────────────────────┘ │
  └──────────────────────────────────────────────────────────────────────┘
              │                                      ▲
              ▼ 4-0 봉합사 (Ø 0.18 mm)               │ 외장 푸시 튜브 (Push Sheath)
      [Free-Pass / Self-Locking]             [가압 Push & 개방 유지]
```

---

## 2. 정밀 부품 사양 및 GD&T 공차 매트릭스 (Precision Specifications)

### 2.1 스토퍼 외통 하우징 (Outer Housing)
* **재질:** Ti-6Al-4V ELI (ASTM F136 / Grade 23)
* **주요 치수:**
  * 몸통 외경: $\varnothing 1.40_{-0.015}^{0}\text{ mm}$
  * 선단 플랜지: $\varnothing 1.60 \pm 0.02\text{ mm}$ (두께 $0.30\text{ mm}$)
  * 전장: $2.40\text{ mm}$
  * 내부 보어: $\varnothing 0.96^{+0.010}_{0}\text{ mm}$ (H7 정밀 슬라이딩 가이드)
  * 봉합사 횡단 관통홀: $\varnothing 0.35\text{ mm}$ (플랜지 후방 $0.80\text{ mm}$ 지점)
  * 스프링 안착 턱: 직경 $\varnothing 0.90\text{ mm} \to$ 선단 관통홀 $\varnothing 0.40\text{ mm}$ 단차 구조
* **가공 공정:** 5축 스위스턴(Swiss Lathe) 자동선반 선삭 + 마이크로 와이어 EDM 횡단 슬롯.

### 2.2 내통 톱니 플런저 (Inner Serrated Plunger)
* **재질:** Ti-6Al-4V ELI 또는 Medical PEEK (Optima LT1)
* **주요 치수:**
  * 외경: $\varnothing 0.95_{-0.015}^{-0.005}\text{ mm}$ (g6 활주 끼워맞춤, 직경 틈새 $10\sim 20\,\mu\text{m}$)
  * 전장: $1.60\text{ mm}$
  * 봉합사 관통 슬롯: $\varnothing 0.30\text{ mm}$ (푸시 가압 시 하우징 $\varnothing 0.35\text{ mm}$ 홀과 $100\%$ 일치)
  * 비대칭 톱니 래칫 (Sawtooth Ratchet):
    * 진입각 $\alpha = 45^\circ$: 전진 인장 시 수직항력 분력 최소화 $\to F_{\text{cinch}} < 0.5\text{ N}$
    * 잠금각 $\beta = 90^\circ$: 역방향 인장 시 기하학적 쐐기 잠금 $\to F_{\text{holding}} \ge 22.5\text{ N}$
    * 톱니 팁 라운딩: $R = 0.02\text{ mm}$ (실의 전단 손상 방지)
  * 후방 푸시 인터페이스: 외장 푸시 튜브 가압용 $15^\circ$ 리드인 테이퍼.

### 2.3 마이크로 압축 코일 스프링 (Micro Compression Spring)
* **재질:** 316LVM / Superelastic Nitinol (ASTM F2063)
* **기하학적 파라미터:**
  * 선경 ($d$): $\varnothing 0.10\text{ mm}$
  * 코일 외경 ($D_o$): $\varnothing 0.90\text{ mm}$
  * 코일 내경 ($D_i$): $\varnothing 0.70\text{ mm}$
  * 평균 코일경 ($D$): $\varnothing 0.80\text{ mm}$
  * 스프링 지수 ($C = D/d$): $8.0$ (최적 가공성)
  * 자유장 ($L_0$): $1.20\text{ mm}$
  * 작동 압축장 ($L_{\text{push}}$): $0.60\text{ mm}$ ($\Delta x = 0.60\text{ mm}$)
  * 스프링 상수 ($k$): $0.50\text{ N/mm}$
  * 초기 프리로드 ($F_{\text{pre}}$ at Lock): $0.15\text{ N}$ ($\Delta x_{\text{pre}} = 0.30\text{ mm}$)
  * 최대 개방 하중 ($F_{\text{open}}$): $0.30\text{ N}$

---

## 3. 동축 이중 푸시-풀 & 스프링 락킹 기구학 (Kinematic Principles)

```
[4단계 작동 시퀀스 선도]
Step 0: Push & Open      (Sheath +0.6mm, Plunger +0.6mm, Wire 0.0mm)  --> Hole 100% Aligned
Step 1: Needle Threading (Needle Rotates 90 deg into Stopper & U-Loop) --> Suture Captured
Step 2: Hold & Cinch     (Sheath +0.6mm, Plunger +0.6mm, Wire -12mm)   --> Suture Pulled Smoothly
Step 3: Release & Lock   (Sheath -3.0mm, Plunger 0.0mm, Wire -12mm)    --> Spring Clamps Suture >20N
```

1. **Forward Cinching 역학 ($F < 0.5\text{ N}$):**
   $$\mu_{\text{effective}} = \mu \cdot \cos 45^\circ \approx 0.04 \implies F_{\text{pull}} \approx 0.35\text{ N}$$
2. **Reverse Tension Locking 역학 ($F > 20\text{ N}$):**
   $$F_{\text{Holding}} = F_{\text{Shear}}(\text{Suture}) + \mu \cdot e^{\mu \theta} \cdot F_{\text{Normal}} \ge 22.5\text{ N} > 15\text{ N}$$

---

## 4. Fusion 360 파라메트릭 CAD 모델링 가이드

1. **3D 나선 스플라인 기반 스프링 스윕:**
   - $X(t) = X_{\text{base}} + t \cdot L$
   - $Y(t) = Y_{\text{base}} + R_{\text{mean}} \cdot \cos(2\pi N t)$
   - $Z(t) = Z_{\text{base}} + R_{\text{mean}} \cdot \sin(2\pi N t)$
   - 경로 수직 Construction Plane 생성 후 $\varnothing 0.10\text{ mm}$ 원형 프로파일 Sweep.
2. **As-Built Slider Joint 및 한계(Limits) 부여:**
   - Joint Type: Slider along X-Axis
   - Minimum Value: $0.0\text{ mm}$
   - Maximum Value: $0.6\text{ mm}$
   - Rest Position: $0.0\text{ mm}$ (외력 제거 시 스프링 자가 복원 락킹)
