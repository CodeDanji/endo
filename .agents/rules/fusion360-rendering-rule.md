---
description: Mandatory autonomous CAD modeling, MuJoCo physics simulation, VLM DFM auditing, and requirement clarification rule for ENDOCRAB.
---

# Fusion 360 Autonomous Closed-Loop Engineering Rule (v2.0)

When working on the ENDOCRAB surgical robotics project (`ENDO`), the AI agent must operate under an **autonomous, self-verifying, closed-loop engineering standard**.

---

## 1. Requirement Ambiguity & Clarification Principle
* **Do NOT make blind assumptions on critical surgical specifications.**
* If the user's request is underspecified (e.g., target sweep angle, outer diameter limit, suture wire tension capacity, tissue penetration depth, latch type):
  1. Immediately ask clarifying questions to resolve the ambiguity, OR
  2. Clearly state standard medical robotics baseline parameters (e.g., $\varnothing 15\text{ mm}$ outer diameter, $\varnothing 0.2\text{ mm}$ SUS304 wire, $10\text{ N}$ tension safety limit) before execution.

---

## 2. Mandatory 4-Pillar Verification Workflow
For every CAD design, parametric change, or mechanism generation, the agent **MUST automatically execute the complete verification pipeline without requiring separate explicit user commands**:

```
[CAD Edit / fx Modify]
         │
         ▼
[Pillar 1: 3D Viewport Inspection] (POST /inspect or POST /animate_and_inspect)
         │  ↳ Visually verify geometry, clearances, and collision-free assembly.
         ▼
[Pillar 2: MuJoCo Physics Simulation] (POST /export_mjcf ➔ python src/mujoco_endo_sim.py)
         │  ↳ Quantitatively verify tendon tension (<= 10N), sweep angle (>= target), and latch engagement.
         ▼
[Pillar 3: Multimodal VLM DFM Audit] (POST /capture_dfm_views ➔ python src/vlm_dfm_auditor.py)
         │  ↳ Check wire bend radius (R >= 1.5*d), tool clearance (>= 1.2mm), thin-wall (t >= 0.25mm), and drainage ports.
         ▼
[Pillar 4: Autonomous Parameter Optimization]
            ↳ If physical/DFM limits fail, automatically adjust CAD fx parameters and iterate until convergence.
```

---

## 3. Strict Prohibitions
1. **Never finalize or declare CAD modeling complete with blind code generation.**
2. **Never conclude dynamic kinematic mechanisms with only a single static frame.**
3. **Never ignore physics simulation failures** (`convergence_status: FAILED` or `is_tension_safe: false`).
4. **Never ignore HIGH severity DFM findings** (e.g., sharp wire edges causing fatigue rupture).
