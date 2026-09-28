# -*- coding: utf-8 -*-
"""项目 CRUD 路由"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.project_service import ProjectService
from app.schemas.project import (
    ProjectDTO, ProjectDetailDTO, ProjectCreate, ProjectUpdate,
    PageResult, RemarkUpdate,
)

router = APIRouter(prefix="/api/projects", tags=["项目"])


@router.get("", response_model=PageResult)
def list_projects(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    stage: str = Query(None),
    status: str = Query(None),
    region: str = Query(None),
    keyword: str = Query(None),
    db: Session = Depends(get_db),
):
    service = ProjectService(db)
    return service.list(page=page, size=size, stage=stage, status=status, region=region, keyword=keyword)


@router.get("/{project_id}", response_model=ProjectDetailDTO)
def get_project(project_id: int, db: Session = Depends(get_db)):
    service = ProjectService(db)
    result = service.get(project_id)
    if result is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    return result


@router.post("", response_model=ProjectDTO)
def create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    service = ProjectService(db)
    project = service.create(data)
    return service._to_dto(project)


@router.put("/{project_id}", response_model=ProjectDetailDTO)
def update_project(project_id: int, data: ProjectUpdate, db: Session = Depends(get_db)):
    service = ProjectService(db)
    project = service.update(project_id, data)
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    return service._to_detail_dto(project)


@router.delete("/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    service = ProjectService(db)
    if not service.delete(project_id):
        raise HTTPException(status_code=404, detail="项目不存在")
    return {"message": "已删除"}


@router.put("/{project_id}/remark")
def update_remark(project_id: int, data: RemarkUpdate, db: Session = Depends(get_db)):
    service = ProjectService(db)
    project = service.update_remark(project_id, data.status_remark)
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    return {"id": project.id, "status_remark": project.status_remark}
