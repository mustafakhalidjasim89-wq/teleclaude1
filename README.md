# Telecom Audit AI Platform (Prototype)

AI-powered digital inspection platform that automates telecom site audits: analyzes site photos and PDF reports, generates standardized engineering findings, tracks open/closed issues, and produces professional Excel reports and dashboards.

## Architecture

```
Site Photos + PDF Reports
        │
        ▼
   Docling Engine (PDF extraction)
        │
        ▼
   Claude Vision AI (observation layer)
        │
        ▼
   Telecom Findings RAG Engine (ChromaDB)
        │
        ▼
   Findings Classification
        │
        ▼
   Priority Scoring
        │
        ▼
   Historical Comparison (SQLite)
        │
        ▼
   Executive Summary
        │
        ▼
   Excel Reports & Dashboard
```

## Tech Stack

- **Frontend:** Streamlit
- **AI Vision / Reasoning:** Claude (Anthropic API, model: `claude-sonnet-5`)
- **Document Processing:** Docling
- **Knowledge Retrieval (RAG):** ChromaDB (FAISS optional)
- **Database:** SQLite (Phase 1) → PostgreSQL (future)
- **Reporting:** Pandas, OpenPyXL, XlsxWriter

## Repository Structure

```
telecom-audit-ai/
├── app/                  # Streamlit application entry point
│   └── main.py
├── src/
│   ├── ingestion/        # Docling-based PDF/photo ingestion
│   ├── vision/           # Claude Vision observation layer
│   ├── rag/              # ChromaDB findings retrieval
│   ├── db/                # SQLite models & historical tracking
│   └── reporting/        # Excel report + dashboard generation
├── data/
│   ├── sample_photos/
│   └── sample_reports/
├── docs/                 # Proposal and standardized findings reference
├── tests/
├── requirements.txt
├── .env.example
└── .gitignore
```

## Setup

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # then add your ANTHROPIC_API_KEY
streamlit run app/main.py
```

## Status

🚧 Prototype / Phase 1 — core pipeline scaffolding. See `docs/proposal.md` for the full project proposal.

## Roadmap

- [ ] Docling PDF extraction pipeline
- [ ] Claude Vision observation prompts per asset type (towers, DG, batteries, grounding, etc.)
- [ ] Standardized findings taxonomy + RAG matching
- [ ] Priority/risk scoring rules
- [ ] Historical comparison across site visits
- [ ] Excel report generation
- [ ] Management dashboard (KPIs, open/closed findings, regional metrics)
- [ ] SharePoint / Microsoft Lists integration (future phase)
