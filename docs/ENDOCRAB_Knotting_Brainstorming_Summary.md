# ENDOCRAB Knotting Module Brainstorming Summary

## 1. 프로젝트 배경 및 ENDOCRAB 분석 요약 (Project Context & ENDOCRAB Paper Analysis)
* **ENDOCRAB 시스템 구조:** 본체 크기 $50\times 15\times 5.45\text{ mm}$, $6\text{ mm}$ 듀얼 집게(Dual grippers), $13\text{ mm}$ 링 바늘(Ring needle), 4-0 나일론 봉합사, T-Bar 앵커.
* **내시경 결합 및 장착 원리:** 내시경 선단 캡에 스킨테이프를 활용하여 부착, 상향 경사각을 통한 시야 확보, 외장 와이어를 통한 기계적 구동 전달.
* **단계별 수술 절차 및 핵심 한계점:** 1번부터 6번 포인트까지 지그재그 형태로 조직을 관통함. 가장 치명적인 병목 현상은 봉합을 마친 후 매듭(Knot)을 짓기 위해 내시경을 체외로 완전히 빼내어 실을 꿰고 다시 삽입해야 하는 체외 탈착-재삽입 과정임. (체내 100% In-Situ 봉합 마감 모듈 필수)

---

## 2. 시중/학술 내시경 Knotting & Suturing 레퍼런스 정밀 분석

### 2.1. Apollo Overstitch / Overstitch NXT
* **구동 원리:** 곡선 바늘 아암(Curved Needle Arm)과 앵커 드라이버(Anchor Driver) 간 앵커 주고받기(Suture Transfer) 메커니즘.
* **실 공급 경로:** 1.5m 봉합사가 체외(시술자 손)에서부터 내시경 채널을 따라 연속 공급됨.
* **1번 앵커 고정:** T-Fastener(Blue Anchor)를 1번 조직 뒤로 배출하여 90도 회전(Toggle-lock)시켜 체내 고정 앵커 형성.
* **Continuous Cinching:** 6번 관통 후 6번을 빠져나온 실 줄기가 내시경 관을 타고 체외 손으로 연결되어 있으므로, 체외에서 실을 손으로 당기면 신발끈 원리로 1~6번 전체 봉합선이 쫙 조여짐.
* **Suture Cinch 모듈:** 조여진 텐션을 유지한 채 Cinch 카테터를 6번 표면으로 밀어 넣어 PEEK Plug & Collar를 기계적 압착(Crimping)하고 내장 칼날로 잔여 실을 절단(Cut).

### 2.2. LSI Solutions Ti-KNOT
* **구동 원리:** 손으로 매듭을 묶지 않는 100% 기계적 Cinch (Mechanical Crimping) 방식.
* **Hammer-Anvil 메커니즘:** 샤프트 끝단($5\text{ mm}$)에 장전된 버섯 모양의 순수 티타늄 슬리브(Titanium Fastener) 구멍으로 실 2가닥을 통과시킨 후, 핸들을 쥐면 내부 망치(Hammer)가 모루(Anvil) 방향으로 강하게 피스톤 운동하여 티타늄을 납작하게 찌그러뜨림 (소성 변형).
* **고정력 & 절단:** $1000\text{ mmHg}$ 이상의 인장 고정력을 발휘하며, 압착과 동시에 내장 칼날이 잉여 실 2가닥을 단칼에 잘라냄.

---

## 3. 치밀한 기계적 구조 검증 및 사용자 질의응답 (Critical Mechanical Q&A & Feasibility Analysis)

### 3.1. 6번 지점 실 당김 메커니즘의 오해 해소 및 모순 해명
* **Overstitch 방식 (체외 실 당김 성립):** 1번 끝은 T-Bar로 체내 조직에 결박되어 있고, 실은 6번 기구/카테터에서 1.5m가 통째로 체외 시술자 손까지 이어져 있으므로 체외 당김이 가능함.
* **Native ENDOCRAB 방식 (Short Pre-cut Suture):** 미리 잘라둔 10~20cm 짧은 실을 링 바늘에 꿰어 쓰므로, 6번 관통 후 남은 실은 몇 cm 길이의 짧은 실 꼬리(Short tail)일 뿐임. 따라서 **Native ENDOCRAB 구조에서는 체외에서 실을 손으로 당길 수 없음.**

### 3.2. 체내 직접 조임/드럼/집게 대안의 기계적 한계 검증
1. **1번 라쳇 허브 통과 불가:** 6번 지점 바늘/집게가 $50\text{ mm}$ 캡 구동 범위 내에서 멀리 떨어진 1번 허브로 실을 꺾어 꽂는 것은 공간/궤적 상 불가능하며 100% 잼(Jamming) 발생.
2. **와인딩 드럼 불가:** 링 바늘($13\text{ mm}$) 회전축과 드럼 회전축이 실을 사이에 두고 대립하므로 바늘이 부러지거나 실이 즉시 끊어짐.
3. **듀얼 집게 당김 불가:** $6\text{ mm}$ 듀얼 집게는 개폐(Open/Close)용일 뿐 후방 선형 슬라이딩 스트로크가 없어 수 cm 당김 텐셔닝 형성 불가.

### 3.3. 1.5m 내시경 힘 전달 물리 역학 (Crimping Force Transmission Physics)
* **압착 하중:** 티타늄 슬리브 압착 하중 $30 \sim 60\text{ N}$ ($3 \sim 6\text{ kgf}$), PEEK 플러그 압착 하중 $15 \sim 30\text{ N}$ ($1.5 \sim 3\text{ kgf}$).
* **힘 전달 3대 메커니즘:**
  1. **보우덴 케이블 (Bowden Cable):** 고탄성 강선 + 외벽 금속 코일 구조로 1.5m 구부러진 내시경 내부에서도 힘 손실 없이 85% 이상 전달.
  2. **선단부 쐐기(Wedge Angle $10^\circ \sim 15^\circ$) 기계 이득:** 체외 $1\text{ kgf}$ 입력 시 선단부 압착력을 3~5배 증폭 ($5 \sim 10\text{ kgf}$ 형성).
  3. **스크류 드라이브:** 나사 회전 구동으로 적은 힘으로도 $100\text{ N}$ 이상 수직 하중 형성.

---

## 4. 최종 확정 ENDOCRAB 체내 봉합 모듈 설계안 (In-Situ Fast Cinch & Cut Module)

* **Option A (외장 가이드 튜브 + 체외 실 당김):** 내시경 외벽을 따라 $1.0\sim 1.5\text{ mm}$ 마이크로 가이드 튜브를 부착하여 실과 Cinch 와이어를 체외로 연결. 내시경 주 작업 채널을 100% 다른 수술 도구용으로 비워둠.
* **Option B (주 작업 채널 + Cinch 카테터):** 내시경 내부 2.8mm/3.7mm 작업 채널로 실과 Cinch 카테터를 통과시켜 체외 핸들로 조임/압착/절단 완결.
* **Option C (Native ENDOCRAB 전용 In-Situ Short-Tail Cinch & Crimp Module):** 짧은 실 꼬리를 체내 선단 캡에 장착된 미세 Cinch 모듈이 1회 쐐기 압착(PEEK/Titanium Crimp) + 절단하여 수 초 내 체내 100% In-Situ 봉합 완료.

---

## 5. 3D Visualizer 시뮬레이터 및 AI 프롬프트 리소스
* **`endocrab_knotting_visualizer.html` 사용 가이드:** 인터랙티브 3D 모델을 통해 봉합 단계 및 슬라이드 신치 모듈 구동 시뮬레이션 활용법 안내.
* **초정밀 3D 메디컬 렌더링 프롬프트 2종 (Gemini / Imagen 3 / Midjourney / Flux 용):**
  1. *Macro-lens Medical Render:* "A highly detailed, photorealistic 3D medical render of an endoscopic suturing device (ENDOCRAB) inside a human stomach tissue environment, featuring a 6mm dual gripper holding a 13mm ring needle with 4-0 nylon suture, bright surgical lighting, depth of field."
  2. *Mechanical Exploded View:* "An exploded isometric 3D CAD render of a microscopic medical knotting module, featuring a titanium cinch collar, cutting mechanism, and push-pull wire interface, clean white background, studio lighting, hyper-detailed mechanical engineering design."
