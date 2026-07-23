# Dermalyze — Product Requirements Document (PRD)

*AI-powered skin lesion analysis, from your phone — Draft v1.1*

---

## 1. Problem & Goal

**Definition**: When users notice a skin lesion (mole, spot, etc.), they have no reliable basis to decide whether to see a doctor — so most people default to “wait and see.”

| Item | Description |
| --- | --- |
| **Problem** | Lesion noticed → no way to assess risk → either neglected or leads to an unnecessary clinic visit |
| **Root cause** | (1) lack of expert knowledge, (2) barriers to visiting a clinic (time/cost), (3) existing apps stop at a risk score with no clear next action |
| **Goal (Success)** | One photo → 7-class classification + natural-language report → guidance on the concrete next action (self-care vs. clinic visit), branched by risk level |
| **North Star Metric** | **Recall** on high-risk classes (mel/bcc/akiec) — minimizing missed malignant cases. Currently 95.1% (after oversampling) |
| **Secondary Metric** | Report-to-clinic-visit conversion rate, PDF report download rate |

> **Differentiation in one line**: SkinVision stops at a risk score; SkinIO is built around a professional clinical workflow (full-body tracking, medical-grade documentation). Dermalyze sits in between — an accessible consumer experience that still connects the result to a concrete next action.
> 

---

## 2. Target User (Persona)

| Category | Description |
| --- | --- |
| **Primary Persona** | Consumers in their 20s–40s who notice a skin abnormality but hesitate to visit a clinic |
| **Need** | Wants to quickly know “is this serious?” without medical jargon |
| **Trigger behavior** | “I noticed something odd on my skin — should I see a doctor?” |
| **Secondary Persona** | Higher-risk age group (60s–70s) — malignant/precancerous classes (akiec, bcc) skew toward older patients in the data |
| **Not the target (for now)** | Patients already under regular dermatology follow-up needing **clinical-grade longitudinal tracking** — that is SkinIO’s professional-medical-workflow territory, out of scope for now |

---

## 3. Core Features — MVP vs. Later

### 🟢 MVP (building now)

| # | Feature | Description |
| --- | --- | --- |
| 1 | Sign-up / Login | Basic info input (age, sex) |
| 2 | Body-part selection | Select lesion location on a body map |
| 3 | Photo capture/upload | Image quality check → request retake if unusable |
| 4 | AI classification (7 classes) | Vertex AI AutoML, oversampled model (all-labels Recall 95.1%, mel Recall 89%) |
| 5 | Natural-language report | Gemini-based, translates classification into plain-language explanation |
| 6 | Risk-based branching | High risk → nearby dermatologist map (Google Maps API) / Low risk → self-care guidance |
| 7 | PDF report generation | Downloadable summary to bring to a clinic visit |

### 🔵 Nice-to-have (later)

| # | Feature | Description | Rationale for lower priority |
| --- | --- | --- | --- |
| 1 | **AR capture guide** | On first capture, overlay a coin-sized reference point + distance guide circle via AR. On retake, overlay the previous photo semi-transparently to align the same angle | Solves the reliability problem for time-series comparison via UX — a prerequisite for the history feature, so it comes right before it |
| 2 | **Lesion history tracking** | Tap a body part → view registered lesion history (e.g., “Left arm → nv 3 months ago, no change ✅”) — positions the app like a routine check-up tool | Drives retention/repeat use; invest after MVP validation |
| 3 | Custom model migration | Move from AutoML to a self-trained model on a Vertex AI Endpoint | Gives direct control over architecture, enables continuous improvement |
| 4 | Broader, more balanced data | Collect additional data across diverse skin tones/ethnicities | Improves real-world generalization |

---

## 4. User Flows

### 4.1 User Flow (from the user’s perspective)

```
Launch app → Sign up / Log in
   → Select lesion location on the body map
   → Capture / upload photo → (if quality check fails, request retake)
   → AI analysis → Review Gemini natural-language report
   → Branch by severity:
        ├─ High risk (mel/bcc/akiec) → nearby dermatologist map + clinic connection + PDF report saved
        └─ Low risk (nv/bkl/df/vasc) → self-care guidance
```

### 4.2 Service Flow (backend perspective)

```
User info → stored in PostgreSQL
Body part + image → stored in GCP Cloud Storage
→ Call Vertex AI Endpoint → return 7-class classification result
→ Branch: Google Maps API (high risk) or Gemini API (report generation)
→ Return result to frontend
```

### 4.3 (Later) Retake / History Flow

```
Tap lesion location → view past capture history
→ On retake, overlay the previous photo semi-transparently to align the angle
→ Compare new result with past result → flag change status (no change / possible worsening)
```

---

## 5. Out of Scope (not doing this now)

| Item | Reason |
| --- | --- |
| Full-body photography & tracking | SkinIO’s territory — built around a professional, clinical/medical workflow. We focus on individual-lesion screening instead |
| Medical-grade diagnosis/prescription | Legal/regulatory risk — we only go as far as “screening + next-step guidance,” not a clinical diagnosis |
| Real-time telemedicine connection | MVP scope stops at “guiding” the user to a clinic, not providing the consultation itself |
| Multi-language / global launch | Initial validation should focus on a single market first |
| AR capture guide, lesion history tracking | See “Later” section above — invest sequentially after MVP validation |

---

## 6. Appendix — Technical / Model Reference (from PPTX)

| Item | Description |
| --- | --- |
| Dataset | HAM10000 (10,015 images / 7,470 unique lesions) |
| Model | Vertex AI AutoML Image Classification |
| Class-imbalance mitigation | Oversampling (10,013 → 23,351 images) → all-labels Recall 90.3%→95.1%, mel Recall 78%→89% |
| Tech Stack | FE: HTML/CSS · BE: Python+FastAPI · DB: PostgreSQL (Render) · AI: GCP Vertex AI Endpoint · Hosting: Render · VCS: GitHub |