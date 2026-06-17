"""Weekly report endpoints. PDF generation lands in Phase 6."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response

from api import repository as repo
from api.db import ApiDB
from api.deps import get_db
from api.schemas import Report, ReportSummary

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("", response_model=list[ReportSummary])
def list_reports(db: ApiDB = Depends(get_db)) -> list[dict]:
    return repo.list_reports(db)


@router.get("/{report_id}", response_model=Report)
def get_report(report_id: str, db: ApiDB = Depends(get_db)) -> dict:
    found = repo.get_report(db, report_id)
    if not found:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found.")
    return found


@router.get("/{report_id}/pdf")
def get_report_pdf(report_id: str, db: ApiDB = Depends(get_db)) -> Response:
    found = repo.get_report(db, report_id)
    if not found:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found.")

    from pipeline.report.pdf import render_report_pdf

    pdf_bytes = render_report_pdf(found["title"], found.get("body_md") or "")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{report_id}.pdf"'},
    )
