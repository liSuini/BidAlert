# -*- coding: utf-8 -*-
"""项目服务"""
from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.stage_config import StageConfig
from app.engine.warning_engine import calculate, ProjectStatus, Status
from app.schemas.project import (
    ProjectDTO, ProjectDetailDTO, ProjectCreate, ProjectUpdate,
    PageResult, StageTimelineItemDTO, RemarkUpdate,
)


class ProjectService:
    def __init__(self, db: Session):
        self.db = db
        self._stage_configs = None

    @property
    def stage_configs(self):
        if self._stage_configs is None:
            self._stage_configs = self.db.query(StageConfig).order_by(StageConfig.stage_order).all()
        return self._stage_configs

    def _calc(self, project: Project) -> ProjectStatus:
        return calculate(project, self.stage_configs)

    def _to_dto(self, project: Project) -> ProjectDTO:
        status = self._calc(project)
        return ProjectDTO(
            id=project.id,
            name=project.name,
            region=project.region,
            responsible_person=project.responsible_person,
            amount=project.amount,
            bid_subject=project.bid_subject,
            current_stage=status.current_stage,
            status=status.status.value,
            overdue_type=status.overdue_type.value,
            overdue_stage=status.overdue_stage,
            days_in_stage=status.days_in_stage,
            days_remaining=status.days_remaining,
            total_days_used=status.total_days_used,
            total_days_limit=status.total_days_limit,
        )

    def _to_detail_dto(self, project: Project) -> ProjectDetailDTO:
        status = self._calc(project)
        dto = ProjectDetailDTO(
            id=project.id,
            name=project.name,
            region=project.region,
            responsible_person=project.responsible_person,
            amount=project.amount,
            bid_subject=project.bid_subject,
            current_stage=status.current_stage,
            status=status.status.value,
            overdue_type=status.overdue_type.value,
            overdue_stage=status.overdue_stage,
            days_in_stage=status.days_in_stage,
            days_remaining=status.days_remaining,
            total_days_used=status.total_days_used,
            total_days_limit=status.total_days_limit,
            bid_open_date=project.bid_open_date,
            publicity_end_date=project.publicity_end_date,
            bid_notice_date=project.bid_notice_date,
            contract_content_settled_date=project.contract_content_settled_date,
            service_fee_date=project.service_fee_date,
            contract_draft_date=project.contract_draft_date,
            contract_start_date=project.contract_start_date,
            contract_approved_date=project.contract_approved_date,
            contract_signed_date=project.contract_signed_date,
            contract_filed_date=project.contract_filed_date,
            biz_analysis_date=project.biz_analysis_date,
            contract_parse_date=project.contract_parse_date,
            ict_provincial_date=project.ict_provincial_date,
            ict_digital_date=project.ict_digital_date,
            has_plan_review=project.has_plan_review or False,
            has_bpm_analysis=project.has_bpm_analysis or False,
            has_pre_bid_review=project.has_pre_bid_review or False,
            has_business_review=project.has_business_review or False,
            contract_content_settled=project.contract_content_settled or False,
            status_remark=project.status_remark,
            stage_timeline=[
                StageTimelineItemDTO(
                    stage=item.stage,
                    start=item.start,
                    end=item.end,
                    days_used=item.days_used,
                    limit=item.limit,
                    status=item.status,
                )
                for item in status.stage_timeline
            ],
        )
        return dto

    def list(self, page: int = 1, size: int = 20,
             stage: str = None, status: str = None,
             region: str = None, keyword: str = None) -> PageResult:
        query = self.db.query(Project)

        if keyword:
            query = query.filter(Project.name.contains(keyword))
        if region:
            query = query.filter(Project.region == region)

        total = query.count()
        projects = query.offset((page - 1) * size).limit(size).all()
        items = [self._to_dto(p) for p in projects]

        # 内存筛选 stage 和 status（基于计算字段）
        if stage:
            items = [i for i in items if i.current_stage == stage]
        if status:
            items = [i for i in items if i.status == status]

        # 重新计算 total 如果有内存筛选
        if stage or status:
            all_projects = query.all()
            all_items = [self._to_dto(p) for p in all_projects]
            if stage:
                all_items = [i for i in all_items if i.current_stage == stage]
            if status:
                all_items = [i for i in all_items if i.status == status]
            total = len(all_items)
            start = (page - 1) * size
            items = all_items[start:start + size]

        return PageResult(total=total, page=page, size=size, items=items)

    def get(self, project_id: int) -> Optional[ProjectDetailDTO]:
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if project is None:
            return None
        return self._to_detail_dto(project)

    def create(self, data: ProjectCreate) -> Project:
        project = Project(**data.model_dump())
        # 信产项目 ict_digital_date 自动填"不涉及"
        if project.bid_subject == "信产" and not project.ict_digital_date:
            project.ict_digital_date = "不涉及"
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def update(self, project_id: int, data: ProjectUpdate) -> Optional[Project]:
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if project is None:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(project, key, value)
        # 信产项目自动填"不涉及"
        if project.bid_subject == "信产" and not project.ict_digital_date:
            project.ict_digital_date = "不涉及"
        self.db.commit()
        self.db.refresh(project)
        return project

    def delete(self, project_id: int) -> bool:
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if project is None:
            return False
        self.db.delete(project)
        self.db.commit()
        return True

    def update_remark(self, project_id: int, remark: str) -> Optional[Project]:
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if project is None:
            return None
        project.status_remark = remark
        self.db.commit()
        self.db.refresh(project)
        return project

    def get_all_with_status(self) -> List[ProjectDTO]:
        """获取所有项目（含计算字段），用于统计"""
        projects = self.db.query(Project).all()
        return [self._to_dto(p) for p in projects]
