"""
Excel audit report generation.

Builds a professional Excel workbook (findings sheet, executive
summary sheet, priority dashboard) from a list of finding dicts.
"""
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


def build_excel_report(
    findings: List[Dict[str, Any]], output_dir: str = "outputs"
) -> str:
    """
    Write findings to a formatted .xlsx report.

    Args:
        findings: List of finding dicts (finding, asset_category, priority, ...).
        output_dir: Directory to write the report into.

    Returns:
        Path to the generated Excel file.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = str(Path(output_dir) / f"audit_report_{timestamp}.xlsx")

    df = pd.DataFrame(findings)

    with pd.ExcelWriter(out_path, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Findings", index=False)
        # TODO: add Executive Summary sheet, Priority Dashboard sheet,
        # conditional formatting, and KPI tiles.

    return out_path
