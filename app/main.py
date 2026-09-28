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

with tab_findings:
    st.subheader("Findings")
    findings = st.session_state.get("last_findings", [])
    if findings:
        st.dataframe(findings)
        if st.button("Export to Excel"):
            path = build_excel_report(findings)
            st.success(f"Report generated: {path}")
    else:
        st.info("Run an audit analysis in the Upload tab to see findings here.")

with tab_dashboard:
    st.subheader("Management Dashboard")
    st.info("KPI tiles (sites audited, open/closed findings, regional metrics) go here.")
