# Multimodal Construction Intelligence Platform
**Skill Wallet Capstone Project 1**

A Streamlit application for AI-assisted construction site safety screening, crack triage, concept-stage project estimation, and weather-aware field guidance.

## Features
- Optional Google Gemini API key, entered securely in the sidebar (`type=password`).
- Graceful demonstration mode when no key is configured or AI is unavailable.
- Site Safety & PPE Audit: image upload, structured JSON output, PPE checklist, hazards and remedies, downloadable report.
- Crack Diagnostics: defect classification, approximate width (when estimable), possible causes, next steps, urgency and red flags.
- Planning & Valuation: configurable concept-stage construction estimate, CAPEX progress, asset value, steel/cement quantities, downloadable JSON.
- Conceptual rendering prompt with optional Pollinations AI image URL.
- Weather-aware site advisory and multi-turn construction assistant.
- No external database. Session data stays in Streamlit session state.

## Run locally
Python 3.10+ recommended.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

Open the local URL Streamlit prints in the terminal.

## Enable Gemini
1. Obtain an API key from Google AI Studio.
2. Run the app and paste the key into the sidebar.
3. Uploaded image bytes and prompts are sent to the Gemini API for image analysis. Chat questions are sent to Gemini for assistant replies.
4. Do not hard-code API keys or commit them to source control. For shared deployments, prefer Streamlit secrets or an organization-approved secret manager.

The app uses the `google-genai` SDK and `gemini-2.5-flash`. If your account/project does not have access to this model, change `GEMINI_MODEL` in `app.py` to a supported Gemini model.

## Deploy to Streamlit Community Cloud
1. Create a GitHub repository and add `app.py`, `requirements.txt`, and `README.md`.
2. In Streamlit Community Cloud, create an app pointing to `app.py`.
3. No secret is required for demo mode. To provide a shared API key, use the platform's secrets feature and update the app to read the approved secret, or ask each user to enter their own key in the sidebar.
4. Keep the repository free of credentials and private construction-site images.

## Estimation assumptions
Planning rates and material intensity values are editable illustrative defaults, not market quotations or a bill of quantities. Current asset value is a rough model using the selected tier multiplier plus the user's land value input. Real costs depend on drawings, soil, specification, city, taxes, approvals, services, contractor rates, and market conditions.

## Safety, code, and engineering limitations
- AI image analysis can miss hazards, misread PPE, and be affected by image quality, occlusion, and camera angle.
- A photo cannot certify PPE compliance or prove a site is hazard-free.
- OSHA is a US regulatory framework. Indian projects must follow applicable Indian laws, state rules, project requirements, and competent-person guidance. **IS 456 is a plain concrete/reinforced concrete code, not a PPE checklist.**
- Crack width cannot be reliably measured from a photo without a known scale and suitable calibration. AI output is not a structural diagnosis.
- Epoxy injection, re-grouting, strengthening, and other repair methods must be selected by a qualified engineer after determining cause, activity, substrate, and structural significance.
- Pollinations concept art is illustrative only, not construction documentation.
- The app is a capstone prototype and is not a substitute for a qualified structural engineer, site safety professional, or quantity surveyor.

## Project structure
```text
.
├── app.py
├── requirements.txt
└── README.md
```
