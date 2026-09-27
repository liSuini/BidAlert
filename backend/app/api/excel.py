# -*- coding: utf-8 -*-
"""Excel 导入导出路由"""
from fastapi import APIRouter, Depends, UploadFile, File, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.excel_service import ExcelService
from app.schemas.excel import ImportResult, ExportQuery

router = APIRouter(prefix="/api/excel", tags=["Excel"])


@router.post("/import", response_model=ImportResult)
async def import_excel(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    service = ExcelService(db)
    result = service.import_projects(content, file.filename or "upload.xlsx")
    return result


@router.get("/template")
def download_template(db: Session = Depends(get_db)):
    service = ExcelService(db)
    content = service.get_template()
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=import_template.xlsx"},
    )


@router.post("/export")
def export_excel(query: ExportQuery, db: Session = Depends(get_db)):
    service = ExcelService(db)
    content = service.export_projects(query)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=export.xlsx"},
    )
