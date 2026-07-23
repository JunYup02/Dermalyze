# Dermalyze

**AI-powered skin lesion screening, from your phone.**

Dermalyze lets a user photograph a skin lesion (mole, spot, etc.) and get back a 7-class AI
classification, a plain-language report, and a concrete next step — self-care guidance for
low-risk results, or a map of nearby dermatology clinics for high-risk ones.

- 🌐 **Live app:** https://dermalyze-frontend.onrender.com
- 🔌 **API:** https://dermalyze-api.onrender.com
- 📋 **Product spec:** [PRD.md](PRD.md)
- 👥 **Team:** [TEAM.md](TEAM.md)

## Why

When someone notices a skin lesion, they usually have no reliable way to judge whether it's
worth seeing a doctor about — so most people default to "wait and see." Dermalyze turns one
photo into a risk read and a clear next action, sitting between apps that stop at a bare risk
score and full clinical tracking tools.

## How it works

```
Sign up / log in
  → Select the lesion's location on a body map
  → Capture or upload a photo (a quality check asks for a retake if it's unusable)
  → AI classification (Vertex AI, 7 lesion classes) + Gemini-generated plain-language report
  → Branch by risk:
       High risk  → nearby dermatologist map + PDF report to bring to the visit
       Low risk   → self-care guidance
```

## Tech stack

| Layer | Stack |
| --- | --- |
| Frontend | Static HTML / CSS / JS |
| Backend | Python, FastAPI |
| Database | PostgreSQL (Render) |
| AI / ML | GCP Vertex AI (AutoML image classification) + Gemini (report generation) |
| Hosting | Render (frontend static site + backend web service) |

See [`backend/README.md`](backend/README.md) and [`frontend/README.md`](frontend/README.md) for
setup instructions specific to each side.

## Repo layout

- `backend/` — FastAPI service (auth, lesion classification, clinic lookup, Gemini report)
- `frontend/` — static HTML/CSS/JS client
