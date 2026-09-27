# -*- coding: utf-8 -*-
"""项目相关 Pydantic 模型"""
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class ProjectBase(BaseModel):
    name: str
    region: Optional[str] = None
    responsible_person: Optional[str] = None
    amount: Optional[float] = None
    bid_subject: Optional[str] = None

    bid_open_date: Optional[date] = None
    publicity_end_date: Optional[date] = None
    bid_notice_date: Optional[date] = None
    contract_content_settled_date: Optional[date] = None
    service_fee_date: Optional[date] = None
    contract_draft_date: Optional[date] = None
    contract_start_date: Optional[date] = None
    contract_approved_date: Optional[date] = None
    contract_signed_date: Optional[date] = None
    contract_filed_date: Optional[date] = None
    biz_analysis_date: Optional[date] = None
    contract_parse_date: Optional[date] = None
    ict_provincial_date: Optional[date] = None
    ict_digital_date: Optional[str] = None

    has_plan_review: bool = False
    has_bpm_analysis: bool = False
    has_pre_bid_review: bool = False
    has_business_review: bool = False
    contract_content_settled: bool = False

    status_remark: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    region: Optional[str] = None
    responsible_person: Optional[str] = None
    amount: Optional[float] = None
    bid_subject: Optional[str] = None
    bid_open_date: Optional[date] = None
    publicity_end_date: Optional[date] = None
    bid_notice_date: Optional[date] = None
    contract_content_settled_date: Optional[date] = None
    service_fee_date: Optional[date] = None
    contract_draft_date: Optional[date] = None
    contract_start_date: Optional[date] = None
    contract_approved_date: Optional[date] = None
    contract_signed_date: Optional[date] = None
    contract_filed_date: Optional[date] = None
    biz_analysis_date: Optional[date] = None
    contract_parse_date: Optional[date] = None
    ict_provincial_date: Optional[date] = None
    ict_digital_date: Optional[str] = None
    has_plan_review: Optional[bool] = None
    has_bpm_analysis: Optional[bool] = None
    has_pre_bid_review: Optional[bool] = None
    has_business_review: Optional[bool] = None
    contract_content_settled: Optional[bool] = None
    status_remark: Optional[str] = None


class StageTimelineItemDTO(BaseModel):
    stage: str
    start: Optional[str] = None
    end: Optional[str] = None
    days_used: int = 0
    limit: int = 0
    status: str = "pending"


class ProjectDTO(BaseModel):
    """列表响应中的项目（含计算字段）"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    region: Optional[str] = None
    responsible_person: Optional[str] = None
    amount: Optional[float] = None
    bid_subject: Optional[str] = None
    current_stage: str = ""
    status: str = "normal"
    overdue_type: str = "none"
    overdue_stage: Optional[str] = None
    days_in_stage: int = 0
    days_remaining: int = 0
    total_days_used: int = 0
    total_days_limit: int = 0


class ProjectDetailDTO(ProjectDTO):
    """详情响应（含全部字段 + 时间线）"""
    bid_open_date: Optional[date] = None
    publicity_end_date: Optional[date] = None
    bid_notice_date: Optional[date] = None
    contract_content_settled_date: Optional[date] = None
    service_fee_date: Optional[date] = None
    contract_draft_date: Optional[date] = None
    contract_start_date: Optional[date] = None
    contract_approved_date: Optional[date] = None
    contract_signed_date: Optional[date] = None
    contract_filed_date: Optional[date] = None
    biz_analysis_date: Optional[date] = None
    contract_parse_date: Optional[date] = None
    ict_provincial_date: Optional[date] = None
    ict_digital_date: Optional[str] = None
    has_plan_review: bool = False
    has_bpm_analysis: bool = False
    has_pre_bid_review: bool = False
    has_business_review: bool = False
    contract_content_settled: bool = False
    status_remark: Optional[str] = None
    stage_timeline: List[StageTimelineItemDTO] = []


class PageResult(BaseModel):
    """分页结果"""
    total: int
    page: int
    size: int
    items: List[ProjectDTO]


class RemarkUpdate(BaseModel):
    status_remark: str
