from __future__ import annotations

import json
import math
import re
from datetime import datetime
from typing import Any

import streamlit as st

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None


APP_TITLE = "Multimodal Construction Intelligence Platform"
APP_SUBTITLE = "Skill Wallet Capstone Project 1"
GEMINI_MODEL = "gemini-2.5-flash"

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------- Styling -------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
    :root { --ink:#172b3a; --muted:#647787; --line:#e2eaf0; --panel:#ffffff; --teal:#087f8c; --teal2:#dff5f2; --amber:#f4b942; }
    html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
    .stApp { background:linear-gradient(180deg,#f4f8fb 0%,#f7fafc 100%); color:var(--ink); }
    h1,h2,h3 { font-family:'Space Grotesk',sans-serif !important; letter-spacing:-.025em; color:var(--ink); }
    .hero { padding:1.35rem 1.55rem; border-radius:20px; color:#fff; background:linear-gradient(120deg,#123044,#087f8c); margin-bottom:1rem; box-shadow:0 12px 30px rgba(16,54,73,.13); }
    .hero h1 { color:#fff !important; font-size:2rem; margin:0 0 .25rem 0; }
    .hero p { color:#d7edf0; margin:0; }
    .eyebrow { text-transform:uppercase; letter-spacing:.14em; font-size:.72rem; font-weight:700; opacity:.82; margin-bottom:.45rem; }
    .panel { background:var(--panel); border:1px solid var(--line); border-radius:16px; padding:1rem 1.1rem; box-shadow:0 4px 16px rgba(18,48,68,.035); }
    .metric-card { background:#fff; border:1px solid var(--line); border-radius:15px; padding:1rem; min-height:112px; }
    .metric-label { font-size:.78rem; color:var(--muted); font-weight:600; margin-bottom:.35rem; }
    .metric-value { font-family:'Space Grotesk',sans-serif; font-size:1.65rem; font-weight:700; color:var(--ink); line-height:1.2; }
    .metric-sub { font-size:.76rem; color:var(--muted); margin-top:.35rem; }
    .pill { display:inline-block; padding:.28rem .65rem; border-radius:999px; font-size:.78rem; font-weight:700; border:1px solid transparent; }
    .pill-good { color:#116b43; background:#e2f7eb; border-color:#b8ebcd; }
    .pill-warn { color:#8a5800; background:#fff3d7; border-color:#f6dfa2; }
    .pill-bad { color:#a52c2c; background:#ffebeb; border-color:#ffc7c7; }
    .pill-info { color:#075b7b; background:#e3f4fb; border-color:#b9e6f5; }
    .small-muted { color:var(--muted); font-size:.85rem; }
    div[data-testid="stTabs"] button { border-radius:10px 10px 0 0; font-weight:700; }
    div.stButton > button, div.stDownloadButton > button { border-radius:10px; font-weight:700; border:1px solid #cddbe4; }
    div.stButton > button[kind="primary"] { background:#087f8c; border-color:#087f8c; }
    [data-testid="stSidebar"] { background:#edf4f7; border-right:1px solid #dbe6ec; }
    .sidebar-note { border:1px solid #d7e5eb; background:#fff; border-radius:12px; padding:.75rem; font-size:.82rem; color:#526a78; }
    .divider { height:1px; background:var(--line); margin:1rem 0; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ----------------------------- Helpers -------------------------------------
def json_download(data: dict[str, Any], filename: str) -> None:
    payload = json.dumps(data, indent=2, ensure_ascii=False)
    st.download_button(
        "⬇️ Download JSON report",
        data=payload,
        file_name=filename,
        mime="application/json",
        use_container_width=False,
    )


def metric_card(label: str, value: str, sub: str = "") -> None:
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div><div class="metric-sub">{sub}</div></div>',
        unsafe_allow_html=True,
    )


def status_pill(status: str) -> str:
    s = str(status).lower()
    cls = "pill-good" if any(x in s for x in ["compliant", "safe", "low", "normal", "on track"]) else (
        "pill-bad" if any(x in s for x in ["critical", "high risk", "unsafe", "urgent", "stop"]) else "pill-warn"
    )
    return f'<span class="pill {cls}">{status}</span>'


def get_gemini_client(api_key: str):
    if not api_key or genai is None:
        return None
    try:
        return genai.Client(api_key=api_key.strip())
    except Exception:
        return None


def parse_json_response(text: str) -> dict[str, Any]:
    """Parse JSON, tolerating common Markdown code fences."""
    cleaned = (text or "").strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        value = json.loads(cleaned)
        if isinstance(value, dict):
            return value
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", cleaned, flags=re.S)
    if match:
        try:
            value = json.loads(match.group(0))
            if isinstance(value, dict):
                return value
        except json.JSONDecodeError:
            pass
    raise ValueError("The AI response was not valid JSON. Please retry or use demonstration mode.")


def gemini_image_json(api_key: str, image_bytes: bytes, mime_type: str, prompt: str) -> dict[str, Any] | None:
    client = get_gemini_client(api_key)
    if client is None or types is None:
        return None
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[
            prompt,
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2,
        ),
    )
    return parse_json_response(response.text or "")


def gemini_text(api_key: str, prompt: str, history: list[dict[str, str]] | None = None) -> str | None:
    client = get_gemini_client(api_key)
    if client is None:
        return None
    contents: list[Any] = []
    for item in history or []:
        contents.append(types.Content(role=("model" if item["role"] == "assistant" else "user"), parts=[types.Part.from_text(text=item["content"])]))
    contents.append(prompt)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(temperature=0.4),
    )
    return response.text


def demo_safety_result() -> dict[str, Any]:
    return {
        "safety_score": 72,
        "overall_status": "Needs corrective action",
        "summary": "Demonstration result only. Replace with a real site image and configure Gemini for image-based assessment.",
        "ppe_detection": [
            {"item": "Safety helmet", "status": "Partially observed", "confidence": 0.68, "notes": "One worker appears to have head protection; verify every worker."},
            {"item": "High-visibility vest", "status": "Missing / unclear", "confidence": 0.63, "notes": "High-visibility clothing is not consistently distinguishable."},
            {"item": "Steel-toe boots", "status": "Not verifiable from image", "confidence": 0.91, "notes": "Footwear protection cannot reliably be confirmed from this view."},
            {"item": "Safety harness", "status": "Not applicable / unclear", "confidence": 0.58, "notes": "Assess only for workers exposed to fall hazards."},
        ],
        "hazards": [
            {"hazard": "Unprotected edge / fall exposure", "severity": "High", "location": "Elevated work area (verify on site)", "remedy": "Install compliant guardrails or covers; use an approved fall-arrest system and documented tie-off points."},
            {"hazard": "PPE compliance not fully verifiable", "severity": "Medium", "location": "Work zone", "remedy": "Conduct a supervisor-led PPE check before work and capture clear, wide-angle evidence."},
        ],
        "standards_note": "Use applicable local law and the project's approved safety plan. OSHA requirements are US-specific; IS 456 is a concrete design code, not a PPE checklist.",
        "limitations": ["Demo mode: this is illustrative, not a finding about the uploaded photo.", "Image-only review cannot certify compliance or replace a competent-person inspection."],
    }


def demo_crack_result() -> dict[str, Any]:
    return {
        "defect_type": "Hairline",
        "estimated_crack_width_mm": 0.3,
        "confidence": 0.52,
        "urgency": "Routine inspection",
        "possible_root_causes": ["Drying shrinkage", "Thermal movement", "Surface finish or plaster shrinkage"],
        "recommended_repairs": [
            "Map and monitor the crack; measure width with a crack comparator and record any change.",
            "For dormant, non-structural hairline cracks, use a compatible flexible sealant or approved surface repair system after diagnosis.",
            "Do not use epoxy injection until a qualified engineer confirms the crack is suitable and the cause is addressed.",
        ],
        "red_flags": ["If the crack is growing, diagonal through structural members, accompanied by deflection, leakage, or exposed/corroding reinforcement, restrict access and obtain urgent structural review."],
        "limitations": ["Demo mode: illustrative output only, not an assessment of the uploaded surface.", "Crack width cannot be measured reliably from an uncalibrated photo without a known scale."],
    }


def format_inr(value: float) -> str:
    if value >= 10_000_000:
        return f"₹{value / 10_000_000:.2f} Cr"
    if value >= 100_000:
        return f"₹{value / 100_000:.2f} L"
    return f"₹{value:,.0f}"


def render_hero() -> None:
    st.markdown(
        f'<div class="hero"><div class="eyebrow">{APP_SUBTITLE}</div>'
        f'<h1>🏗️ {APP_TITLE}</h1>'
        '<p>AI-assisted site safety, defect triage, project planning, and daily field guidance.</p></div>',
        unsafe_allow_html=True,
    )


# ----------------------------- Sidebar -------------------------------------
with st.sidebar:
    st.markdown("## 🏗️ Construction IQ")
    st.caption("Field intelligence workspace")
    api_key = st.text_input(
        "Google Gemini API key",
        type="password",
        help="Used only for requests from this app session. Do not commit keys to source control.",
        placeholder="Paste Gemini API key (optional)",
    )
    if api_key.strip():
        st.success("API key entered for this session")
    else:
        st.info("Demonstration mode is active")
    st.markdown("---")
    st.markdown("### Architecture overview")
    st.markdown(
        """
        <div class="sidebar-note">
        <b>UI:</b> Streamlit<br>
        <b>Vision + chat:</b> Google Gemini API (optional)<br>
        <b>Planning:</b> Local deterministic estimator<br>
        <b>Concept art:</b> Pollinations prompt / image URL<br>
        <b>Storage:</b> Session state only; no external database
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown("### Feature navigation")
    st.markdown("1. Site Safety & PPE Audit")
    st.markdown("2. Crack Diagnostics")
    st.markdown("3. Planning & Valuation")
    st.markdown("4. Daily Site Assistant")
    st.caption("Build: 1.0.0 · Python / Streamlit")


render_hero()
st.warning(
    "Engineering safety notice: AI outputs are preliminary decision support, not certification, a structural diagnosis, "
    "or a substitute for a qualified engineer / competent safety professional. Verify all site conditions in person."
)

tab_safety, tab_cracks, tab_planning, tab_assistant = st.tabs([
    "🦺 Site Safety & PPE Audit",
    "🧱 Crack Diagnostics",
    "📐 Planning & Valuation",
    "🌦️ Daily Site Assistant",
])

# ----------------------------- Tab 1 ---------------------------------------
with tab_safety:
    st.subheader("Site Safety & PPE Audit")
    st.write("Upload a site photo to review visible PPE indicators and potential hazards.")
    uploaded_safety = st.file_uploader(
        "Construction site photo (JPG / PNG)",
        type=["jpg", "jpeg", "png"],
        key="safety_image",
    )
    if uploaded_safety:
        st.image(uploaded_safety, caption="Uploaded site image", use_container_width=True)
    safety_prompt = """
You are a cautious construction-site safety assistant. Inspect the provided image and return JSON only.
Do not claim certainty when PPE is occluded or not visible. Do not infer steel-toe protection from appearance alone.
Use OSHA concepts where relevant and distinguish them from Indian requirements. IS 456 is a concrete code and is not a PPE standard;
do not claim it directly defines PPE requirements. Do not declare legal compliance from one photo.
Return this schema:
{
 "safety_score": integer 0-100,
 "overall_status": string,
 "summary": string,
 "ppe_detection": [
   {"item": "Safety helmet", "status": string, "confidence": number 0-1, "notes": string},
   {"item": "High-visibility vest", "status": string, "confidence": number 0-1, "notes": string},
   {"item": "Steel-toe boots", "status": string, "confidence": number 0-1, "notes": string},
   {"item": "Safety harness", "status": string, "confidence": number 0-1, "notes": string}
 ],
 "hazards": [{"hazard": string, "severity": "Low|Medium|High|Critical", "location": string, "remedy": string}],
 "standards_note": string,
 "limitations": [string]
}
List only visible or reasonably indicated hazards, include practical corrective actions, and use severity proportionately.
"""
    col_a, col_b = st.columns([1, 3])
    with col_a:
        run_safety = st.button("🔍 Analyze site photo", type="primary", use_container_width=True, disabled=uploaded_safety is None)
    with col_b:
        st.caption("Vision analysis works when a valid Gemini API key is supplied. Without one, the app displays a clearly labelled demo report.")
    if run_safety:
        with st.spinner("Reviewing visible PPE and hazards…"):
            result = None
            if api_key.strip() and uploaded_safety:
                try:
                    mime = "image/png" if uploaded_safety.type == "image/png" else "image/jpeg"
                    result = gemini_image_json(api_key, uploaded_safety.getvalue(), mime, safety_prompt)
                except Exception as exc:
                    st.error(f"Gemini analysis failed: {exc}")
            if result is None:
                result = demo_safety_result()
                result["mode"] = "demonstration"
            else:
                result["mode"] = "gemini"
            result["generated_at"] = datetime.now().isoformat(timespec="seconds")
            st.session_state["safety_result"] = result

    safety_result = st.session_state.get("safety_result")
    if safety_result:
        st.markdown("### Audit summary")
        if safety_result.get("mode") == "demonstration":
            st.info("DEMONSTRATION REPORT — not based on your uploaded image.")
        c1, c2, c3 = st.columns(3)
        with c1:
            metric_card("Safety score", f"{int(max(0, min(100, safety_result.get('safety_score', 0))))}/100", "AI-estimated; verify on site")
        with c2:
            metric_card("Hazards listed", str(len(safety_result.get("hazards", []))), "Potential observations")
        with c3:
            st.markdown('<div class="metric-card"><div class="metric-label">Overall status</div><div style="margin-top:.5rem;">' + status_pill(safety_result.get("overall_status", "Unknown")) + '</div><div class="metric-sub">Preliminary screening only</div></div>', unsafe_allow_html=True)
        st.progress(int(max(0, min(100, safety_result.get("safety_score", 0)))) / 100)
        st.write(safety_result.get("summary", ""))
        st.markdown("#### PPE detection checklist")
        ppe = safety_result.get("ppe_detection", [])
        if ppe:
            st.dataframe(ppe, use_container_width=True, hide_index=True)
        else:
            st.caption("No checklist items were returned.")
        st.markdown("#### Identified hazards & corrective remedies")
        hazards = safety_result.get("hazards", [])
        if hazards:
            for hazard in hazards:
                severity = hazard.get("severity", "Medium")
                with st.expander(f"{severity} · {hazard.get('hazard', 'Hazard')}", expanded=severity in ("Critical", "High")):
                    st.write(f"**Location:** {hazard.get('location', 'Not specified')}")
                    st.write(f"**Corrective action:** {hazard.get('remedy', 'Review with site safety lead.')}")
        else:
            st.success("No hazards were returned. This does not prove the site is hazard-free.")
        st.caption(safety_result.get("standards_note", ""))
        for limitation in safety_result.get("limitations", []):
            st.caption("• " + str(limitation))
        json_download(safety_result, "site_safety_audit.json")


# ----------------------------- Tab 2 ---------------------------------------
with tab_cracks:
    st.subheader("Crack Diagnostics & Structural Integrity")
    st.write("Use this as a triage aid. A photo alone cannot establish structural safety or reliably measure crack width.")
    uploaded_crack = st.file_uploader(
        "Concrete / wall surface photo (JPG / PNG)",
        type=["jpg", "jpeg", "png"],
        key="crack_image",
    )
    if uploaded_crack:
        st.image(uploaded_crack, caption="Uploaded surface image", use_container_width=True)
    crack_prompt = """
You are a cautious construction defect triage assistant. Analyze the image and return JSON only.
Do not claim that visual inspection establishes structural safety. A crack width estimate from an image without scale is uncertain.
Choose defect_type from: Hairline, Settlement, Structural Shear, Thermal Expansion, Spalling.
Schema:
{
 "defect_type": string,
 "estimated_crack_width_mm": number or null,
 "confidence": number 0-1,
 "visual_observations": [string],
 "possible_root_causes": [string],
 "recommended_repairs": [string],
 "urgency": "Monitor"|"Routine inspection"|"Prompt engineer review"|"Urgent - restrict access",
 "red_flags": [string],
 "limitations": [string]
}
Consider epoxy injection only where suitable after diagnosis; do not recommend structural repair as a definitive prescription.
Mention structural re-grouting only if technically appropriate to the observed defect and verified by an engineer.
"""
    crack_col1, crack_col2 = st.columns([1, 3])
    with crack_col1:
        run_crack = st.button("🧪 Analyze surface", type="primary", use_container_width=True, disabled=uploaded_crack is None)
    with crack_col2:
        st.caption("The output is a preliminary defect classification, not an engineering report.")
    if run_crack:
        with st.spinner("Classifying visible surface defects…"):
            result = None
            if api_key.strip() and uploaded_crack:
                try:
                    mime = "image/png" if uploaded_crack.type == "image/png" else "image/jpeg"
                    result = gemini_image_json(api_key, uploaded_crack.getvalue(), mime, crack_prompt)
                except Exception as exc:
                    st.error(f"Gemini analysis failed: {exc}")
            if result is None:
                result = demo_crack_result()
                result["mode"] = "demonstration"
            else:
                result["mode"] = "gemini"
            result["generated_at"] = datetime.now().isoformat(timespec="seconds")
            st.session_state["crack_result"] = result

    crack_result = st.session_state.get("crack_result")
    if crack_result:
        if crack_result.get("mode") == "demonstration":
            st.info("DEMONSTRATION REPORT — not based on your uploaded image.")
        cc1, cc2, cc3 = st.columns(3)
        with cc1:
            metric_card("Defect classification", str(crack_result.get("defect_type", "Unknown")), "Visual triage")
        with cc2:
            width = crack_result.get("estimated_crack_width_mm")
            metric_card("Estimated width", f"{width} mm" if width is not None else "Not estimable", "Requires calibrated measurement")
        with cc3:
            st.markdown('<div class="metric-card"><div class="metric-label">Urgency</div><div style="margin-top:.5rem;">' + status_pill(crack_result.get("urgency", "Unknown")) + '</div><div class="metric-sub">Escalate if red flags exist</div></div>', unsafe_allow_html=True)
        st.markdown("#### Visual observations")
        for item in crack_result.get("visual_observations", []):
            st.write("• " + str(item))
        st.markdown("#### Possible root causes")
        for item in crack_result.get("possible_root_causes", []):
            st.write("• " + str(item))
        st.markdown("#### Recommended next steps")
        for item in crack_result.get("recommended_repairs", []):
            st.write("• " + str(item))
        if crack_result.get("red_flags"):
            st.error("Red flags requiring professional review")
            for item in crack_result["red_flags"]:
                st.write("• " + str(item))
        for limitation in crack_result.get("limitations", []):
            st.caption("• " + str(limitation))
        json_download(crack_result, "crack_diagnostics_report.json")


# ----------------------------- Tab 3 ---------------------------------------
with tab_planning:
    st.subheader("Planning & Real Estate Valuation")
    st.write("A transparent concept-stage estimator. Update the assumptions with a local quantity surveyor and current market rates.")
    structure_options = {
        "Residential apartment": {"base_rate": 1900, "steel_kg_sqft": 3.8, "cement_bags_sqft": 0.40},
        "Independent house": {"base_rate": 1750, "steel_kg_sqft": 3.4, "cement_bags_sqft": 0.36},
        "Commercial building": {"base_rate": 2600, "steel_kg_sqft": 4.8, "cement_bags_sqft": 0.48},
        "Warehouse / industrial": {"base_rate": 1550, "steel_kg_sqft": 5.2, "cement_bags_sqft": 0.30},
        "Institutional building": {"base_rate": 2300, "steel_kg_sqft": 4.3, "cement_bags_sqft": 0.44},
    }
    tier_multiplier = {"Tier 1": 1.25, "Tier 2": 1.00, "Tier 3": 0.82}
    market_multiplier = {"Tier 1": 1.65, "Tier 2": 1.25, "Tier 3": 0.95}
    with st.form("planning_form"):
        p1, p2 = st.columns(2)
        with p1:
            structure_type = st.selectbox("Structure type", list(structure_options.keys()))
            built_up_sqft = st.number_input("Built-up area (sq ft)", min_value=100, max_value=2_000_000, value=2500, step=100)
            location_tier = st.selectbox("Location tier", ["Tier 1", "Tier 2", "Tier 3"], index=1)
        with p2:
            completion_pct = st.slider("Construction completion (%)", 0, 100, 35, 5)
            land_value_lakh = st.number_input("Estimated land value (₹ Lakhs)", min_value=0.0, value=25.0, step=5.0)
            contingency_pct = st.slider("Contingency allowance (%)", 0, 25, 10, 1)
        run_plan = st.form_submit_button("Calculate project estimate", type="primary", use_container_width=True)

    if run_plan:
        spec = structure_options[structure_type]
        base_cost = built_up_sqft * spec["base_rate"] * tier_multiplier[location_tier]
        contingency = base_cost * contingency_pct / 100
        total_budget = base_cost + contingency
        incurred = total_budget * completion_pct / 100
        remaining = total_budget - incurred
        asset_value = (built_up_sqft * spec["base_rate"] * market_multiplier[location_tier]) + land_value_lakh * 100_000
        steel_kg = built_up_sqft * spec["steel_kg_sqft"]
        cement_bags = built_up_sqft * spec["cement_bags_sqft"]
        estimate = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "structure_type": structure_type,
            "built_up_sqft": built_up_sqft,
            "location_tier": location_tier,
            "completion_percentage": completion_pct,
            "assumptions": {
                "base_construction_rate_inr_per_sqft": spec["base_rate"],
                "location_cost_multiplier": tier_multiplier[location_tier],
                "market_multiplier": market_multiplier[location_tier],
                "contingency_percentage": contingency_pct,
                "land_value_inr": land_value_lakh * 100_000,
                "steel_intensity_kg_per_sqft": spec["steel_kg_sqft"],
                "cement_bags_per_sqft": spec["cement_bags_sqft"],
            },
            "estimated_construction_budget_inr": round(total_budget),
            "estimated_capex_incurred_inr": round(incurred),
            "estimated_remaining_budget_inr": round(remaining),
            "estimated_current_asset_value_inr": round(asset_value),
            "estimated_steel_requirement_kg": round(steel_kg),
            "estimated_cement_requirement_50kg_bags": round(cement_bags),
            "disclaimer": "Illustrative estimates only; excludes project-specific design, soil, permits, taxes, financing, and market verification.",
        }
        st.session_state["planning_result"] = estimate

    plan_result = st.session_state.get("planning_result")
    if plan_result:
        st.markdown("### Project snapshot")
        c1, c2, c3 = st.columns(3)
        with c1:
            metric_card("Estimated project budget", format_inr(plan_result["estimated_construction_budget_inr"]), "Construction + contingency")
        with c2:
            metric_card("CAPEX incurred", format_inr(plan_result["estimated_capex_incurred_inr"]), f'{plan_result["completion_percentage"]}% completion assumption')
        with c3:
            metric_card("Current asset valuation", format_inr(plan_result["estimated_current_asset_value_inr"]), "Indicative; includes land input")
        c4, c5, c6 = st.columns(3)
        with c4:
            metric_card("Remaining budget", format_inr(plan_result["estimated_remaining_budget_inr"]), "Budget less estimated incurred CAPEX")
        with c5:
            metric_card("Steel requirement", f'{plan_result["estimated_steel_requirement_kg"]:,.0f} kg', "Concept-stage quantity")
        with c6:
            metric_card("Cement requirement", f'{plan_result["estimated_cement_requirement_50kg_bags"]:,.0f} bags', "Assumes 50 kg per bag")
        st.markdown("#### Milestone progress")
        st.progress(plan_result["completion_percentage"] / 100)
        st.caption(f'Estimated completion: {plan_result["completion_percentage"]}% · Estimated balance: {format_inr(plan_result["estimated_remaining_budget_inr"])}')
        st.markdown("#### Assumptions & breakdown")
        st.json(plan_result["assumptions"])
        json_download(plan_result, "project_planning_estimate.json")

    st.markdown("---")
    st.markdown("### Conceptual 3D architectural rendering")
    st.caption("Creates a visual concept prompt. Pollinations availability, output, terms, and image URL behavior may change; do not use concept art as construction documentation.")
    with st.form("render_prompt_form"):
        r1, r2 = st.columns(2)
        with r1:
            render_style = st.selectbox("Architectural style", ["Contemporary Indian", "Modern minimalist", "Traditional courtyard", "Sustainable tropical", "Industrial modern"])
            render_view = st.selectbox("View", ["Aerial 3D axonometric", "Street-level exterior", "Front elevation", "Courtyard perspective"])
        with r2:
            render_material = st.selectbox("Material palette", ["Exposed concrete and glass", "Brick, stone and timber", "White plaster and warm wood", "Steel, glass and dark metal"])
            render_context = st.text_input("City / context", "Indore, Madhya Pradesh")
        render_button = st.form_submit_button("Generate concept prompt")
    if render_button:
        area = built_up_sqft if "built_up_sqft" in locals() else 2500
        prompt = (
            f"High-quality architectural visualization, {render_view}, {render_style} building, "
            f"{render_material}, context: {render_context}, built-up area approximately {area} square feet, "
            "realistic Indian climate and streetscape, accurate proportions, professional architectural concept render, "
            "daylight, detailed landscaping, no text, no logos, not a construction drawing."
        )
        st.session_state["render_prompt"] = prompt
    if st.session_state.get("render_prompt"):
        prompt = st.session_state["render_prompt"]
        st.text_area("Generated prompt", prompt, height=110)
        encoded = __import__("urllib.parse", fromlist=["quote"]).quote(prompt)
        pollinations_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=768&nologo=true"
        st.markdown(f"[Open concept render via Pollinations AI]({pollinations_url})")
        st.caption("Opening the image URL may send the prompt to a third-party service. Avoid including private site details.")
        if st.button("Show concept render preview"):
            st.image(pollinations_url, caption="AI-generated concept visualization — not for construction use", use_container_width=True)


# ----------------------------- Tab 4 ---------------------------------------
with tab_assistant:
    st.subheader("Daily Site Assistant & Weather-Aware Advisory")
    weather = st.selectbox("Current / forecast weather condition", ["Normal", "High Wind", "Heavy Rain", "Extreme Heat"])
    alerts = {
        "Normal": {
            "level": "Routine precautions",
            "items": [
                "Follow the approved method statement, toolbox talk, and site-specific risk assessment.",
                "Inspect access routes, PPE, lifting accessories, and temporary works before starting.",
                "Maintain hydration, housekeeping, and daily inspection records.",
            ],
        },
        "High Wind": {
            "level": "Elevated risk — assess before work",
            "items": [
                "Pause crane and hoisting operations when wind exceeds the equipment/manufacturer or lift-plan limit; secure suspended loads.",
                "Secure loose materials, formwork, scaffolds, signage, and rooftop items; establish exclusion zones.",
                "Reassess work at height and stop if conditions exceed the approved safe-work threshold.",
            ],
        },
        "Heavy Rain": {
            "level": "High risk — protect people and works",
            "items": [
                "Stop work in flooded, unstable, lightning-exposed, or unsafe excavation areas; inspect slopes and shoring before re-entry.",
                "Isolate electrical equipment where water ingress is possible; use protected supplies and have a qualified electrician inspect affected circuits.",
                "Protect fresh concrete from washout; reassess placement and curing plan with the engineer. Do not pour into standing water.",
                "Check drainage, access, scaffold footing, and slip hazards before resuming.",
            ],
        },
        "Extreme Heat": {
            "level": "Heat-stress controls required",
            "items": [
                "Schedule strenuous work for cooler periods; provide shade, cool drinking water, rest breaks, and buddy monitoring.",
                "Train supervisors to recognize confusion, fainting, hot dry skin, and other heat-illness signs; activate emergency response if suspected.",
                "Follow the approved concrete placement and curing method: control evaporation, use suitable curing protection, and monitor temperature.",
                "Do not add water to concrete arbitrarily; consult the mix design and responsible engineer.",
            ],
        },
    }
    advisory = alerts[weather]
    st.markdown(f"**Weather advisory:** {status_pill(advisory['level'])}", unsafe_allow_html=True)
    for item in advisory["items"]:
        st.write("• " + item)
    st.caption("Always follow local weather alerts, site emergency procedures, equipment limits, and the approved project safety plan.")
    st.markdown("---")
    st.markdown("### Ask the construction engineering assistant")
    st.caption("Ask about sequencing, material planning, quality checks, site documentation, or general construction concepts. For high-risk decisions, consult the responsible professional.")
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    for message in st.session_state["chat_history"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    user_question = st.chat_input("Ask a construction question…")
    if user_question:
        st.session_state["chat_history"].append({"role": "user", "content": user_question})
        context = (
            "You are a careful construction engineering assistant for an Indian construction context. "
            "Give practical, concise, safety-first general guidance. Ask clarifying questions when important details are missing. "
            "Do not certify structural safety, invent code clauses, or prescribe unsafe shortcuts. Distinguish general guidance from project-specific engineering advice. "
            f"Current weather selection: {weather}. Current weather controls: {'; '.join(advisory['items'])}. "
            "Recommend checking current local codes and having a qualified engineer review design-critical decisions."
        )
        with st.chat_message("assistant"):
            with st.spinner("Preparing guidance…"):
                answer = None
                if api_key.strip():
                    try:
                        history = st.session_state["chat_history"][-10:-1]
                        answer = gemini_text(api_key, context + "\n\nUser question: " + user_question, history)
                    except Exception as exc:
                        st.warning(f"Gemini request failed; showing fallback guidance. ({exc})")
                if not answer:
                    answer = (
                        "I’m in demonstration mode, so I can provide general guidance but not a project-specific engineering decision. "
                        "Start by checking the approved drawings, method statement, applicable code, and site risk assessment; document the actual site conditions. "
                        "For structural stability, lifting plans, temporary works, electrical isolation, or other high-risk decisions, stop the affected activity if unsafe and contact the responsible qualified professional.\n\n"
                        f"**Your question:** {user_question}\n\n"
                        "Add a Gemini API key in the sidebar to enable multi-turn AI responses."
                    )
                st.markdown(answer)
        st.session_state["chat_history"].append({"role": "assistant", "content": answer})
    if st.session_state["chat_history"]:
        if st.button("Clear chat history"):
            st.session_state["chat_history"] = []
            st.rerun()

st.markdown("---")
st.markdown(
    '<p class="small-muted">Multimodal Construction Intelligence Platform · Skill Wallet Capstone Project 1 · '
    'AI-assisted workflow prototype. Always validate safety, quantities, costs, and structural recommendations with qualified professionals.</p>',
    unsafe_allow_html=True,
)
