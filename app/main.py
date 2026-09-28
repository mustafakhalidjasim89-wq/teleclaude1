"""
Telecom Audit AI Platform — Streamlit entry point.

Run with: streamlit run app/main.py
"""
import sys
from pathlib import Path

import streamlit as st

# Make src/ importable when run from repo root
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.ingestion.docling_extractor import extract_pdf_content
from src.vision.gemini_vision import analyze_site_photo
from src.rag.findings_engine import match_findings
from src.reporting.excel_report import build_excel_report

st.set_page_config(page_title="Telecom Audit AI Platform", layout="wide")

st.title("📡 Telecom Audit AI Platform")
st.caption("AI-powered digital inspection for telecom site audits")

tab_upload, tab_findings, tab_dashboard = st.tabs(
    ["Upload Site Data", "Findings", "Dashboard"]
)

with tab_upload:
    st.subheader("Upload site photos and PDF reports")
    site_id = st.text_input("Site ID")
    photos = st.file_uploader(
        "Site photos", type=["jpg", "jpeg", "png"], accept_multiple_files=True
    )
    pdf_report = st.file_uploader("Site PDF report", type=["pdf"])

    if st.button("Run Audit Analysis", type="primary"):
        if not site_id:
            st.warning("Enter a Site ID first.")
        else:
            with st.spinner("Analyzing site data..."):
                # Pipeline stubs — wire up real calls once ingestion/vision/rag are implemented
                pdf_text = extract_pdf_content(pdf_report) if pdf_report else ""
                observations = [analyze_site_photo(p) for p in (photos or [])]
                findings = match_findings(observations, pdf_text)
            st.success(f"Analysis complete for site {site_id}: {len(findings)} findings.")
            st.session_state["last_findings"] = findings
            st.session_state["last_observations"] = observations

            # Surface a warning right away if any photo's response didn't
            # parse as valid JSON — otherwise that silently looks identical
            # to "no issues found", which is misleading.
            parse_failures = [o for o in observations if not o.get("_parse_ok", False)]
            if parse_failures:
                names = ", ".join(o.get("filename", "unknown") for o in parse_failures)
                st.warning(
                    f"⚠️ {len(parse_failures)} photo(s) didn't return valid JSON from "
                    f"Claude, so they show 0 findings by default rather than a real "
                    f"result: {names}. Check the debug expander below or in the "
                    f"Findings tab for the raw model response."
                )

    observations = st.session_state.get("last_observations", [])
    if observations:
        with st.expander("🔍 Debug: per-photo analysis details"):
            for obs in observations:
                ok = obs.get("_parse_ok", False)
                icon = "✅" if ok else "❌"
                st.markdown(
                    f"**{icon} {obs.get('filename', 'unknown')}** — "
                    f"asset category: `{obs.get('asset_category', 'Unclassified')}`, "
                    f"findings: {len(obs.get('findings', []))}"
                )
                if not ok:
                    st.code(obs.get("_raw_response", "(no response captured)"))

with tab_findings:
    st.subheader("Findings")
    findings = st.session_state.get("last_findings", [])
    if findings:
        st.dataframe(findings)
        if st.button("Export to Excel"):
            path = build_excel_report(findings)
            st.success(f"Report generated: {path}")
    else:
        observations = st.session_state.get("last_observations", [])
        if observations:
            st.info(
                "No findings were extracted from the last run. Check the "
                "'Debug: per-photo analysis details' expander in the Upload "
                "tab to see what Claude actually returned for each photo."
            )
        else:
            st.info("Run an audit analysis in the Upload tab to see findings here.")

with tab_dashboard:
    st.subheader("Management Dashboard")
    st.info("KPI tiles (sites audited, open/closed findings, regional metrics) go here.")
