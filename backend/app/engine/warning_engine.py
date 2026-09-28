# -*- coding: utf-8 -*-
"""预警计算引擎 - 核心深模块

接口：WarningEngine.calculate(project, stage_configs) -> ProjectStatus
内部：WorkingDayCalculator + StageChecker + TotalTimeChecker + StatusComposer
"""
from datetime import date
from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum

from app.core.config import WARNING_THRESHOLD, AMOUNT_THRESHOLD, TOTAL_LIMIT_BELOW_500, TOTAL_LIMIT_ABOVE_500
from app.engine.working_day import working_days, today


class Status(str, Enum):
    NORMAL = "normal"
    WARNING = "warning"
    OVERDUE = "overdue"
    COMPLETED = "completed"


class OverdueType(str, Enum):
    NONE = "none"
    STAGE_OVERDUE = "stage_overdue"
    TOTAL_OVERDUE = "total_overdue"
    BOTH = "both"


@dataclass
class StageTimelineItem:
    stage: str
    start: Optional[str] = None
    end: Optional[str] = None
    days_used: int = 0
    limit: int = 0
    status: str = "pending"  # normal/warning/overdue/completed/pending


@dataclass
class ProjectStatus:
    status: Status = Status.NORMAL
    overdue_type: OverdueType = OverdueType.NONE
    overdue_stage: Optional[str] = None
    days_in_stage: int = 0
    days_remaining: int = 0
    total_days_used: int = 0
    total_days_limit: int = 0
    current_stage: str = ""
    stage_timeline: List[StageTimelineItem] = field(default_factory=list)


def _get_stage_limit(config, amount: float) -> int:
    """根据金额获取阶段时限"""
    return config.limit_days_below_500 if amount < AMOUNT_THRESHOLD else config.limit_days_above_500


def _get_total_limit(amount: float) -> int:
    """根据金额获取总时限"""
    return TOTAL_LIMIT_BELOW_500 if amount < AMOUNT_THRESHOLD else TOTAL_LIMIT_ABOVE_500


def _get_end_date(project, config):
    """获取阶段结束日期，处理ICT立项的特殊逻辑"""
    end_field = config.end_field

    # ICT立项结束字段根据投标主体动态选择
    if end_field == "ict_provincial_date":
        if project.bid_subject == "数智":
            # 数智项目取 ict_digital_date
            val = project.ict_digital_date
            if val is None:
                return None
            if isinstance(val, date):
                return val
            if isinstance(val, str) and val != "不涉及":
                try:
                    return date.fromisoformat(val)
                except (ValueError, TypeError):
                    return None
            return None

    # 默认：直接取字段值
    val = getattr(project, end_field, None)
    if val is None:
        return None
    if isinstance(val, date):
        return val
    if isinstance(val, str):
        if val == "不涉及":
            return None
        try:
            return date.fromisoformat(val)
        except (ValueError, TypeError):
            return None
    return None


def _get_start_date(project, config):
    """获取阶段开始日期"""
    val = getattr(project, config.start_field, None)
    if val is None:
        return None
    if isinstance(val, date):
        return val
    return None


def calculate(project, stage_configs: list) -> ProjectStatus:
    """计算项目状态

    Args:
        project: Project ORM 对象
        stage_configs: StageConfig 列表

    Returns:
        ProjectStatus: 包含 status/overdue_type/days_in_stage 等完整状态
    """
    total_limit = _get_total_limit(project.amount or 0)

    has_overdue_stage = False
    has_warning_stage = False
    overdue_stage_name = None
    all_stages_completed = True
    current_stage_name = ""
    days_in_current = 0
    days_remaining_current = 0
    timeline: List[StageTimelineItem] = []

    for config in stage_configs:
        start_date = _get_start_date(project, config)
        end_date = _get_end_date(project, config)
        limit = _get_stage_limit(config, project.amount or 0)

        if start_date is None:
            # 阶段未开始
            all_stages_completed = False
            if not current_stage_name:
                current_stage_name = config.stage_name
            timeline.append(StageTimelineItem(
                stage=config.stage_name,
                start=None, end=None,
                days_used=0, limit=limit,
                status="pending",
            ))
            continue

        if end_date is None:
            # 当前阶段（已开始未完成）
            # 只取第一个此类阶段作为当前阶段，后续阶段视为待开始
            all_stages_completed = False
            if not current_stage_name:
                current_stage_name = config.stage_name
                days_in_current = working_days(start_date, today())
                days_remaining_current = limit - days_in_current

                stage_status = "normal"
                if days_in_current > limit:
                    has_overdue_stage = True
                    overdue_stage_name = config.stage_name
                    stage_status = "overdue"
                elif days_in_current >= limit * config.warning_threshold:
                    has_warning_stage = True
                    stage_status = "warning"
            else:
                # 前一个阶段仍在进行中，此阶段实际未开始
                stage_status = "pending"

            timeline.append(StageTimelineItem(
                stage=config.stage_name,
                start=start_date.isoformat() if not current_stage_name or current_stage_name != config.stage_name else start_date.isoformat(),
                end=None,
                days_used=days_in_current if current_stage_name == config.stage_name else 0,
                limit=limit,
                status=stage_status,
            ))
            continue

        # 已完成阶段
        days_used = working_days(start_date, end_date)
        stage_status = "completed"
        if days_used > limit:
            has_overdue_stage = True
            if not overdue_stage_name:
                overdue_stage_name = config.stage_name
            stage_status = "overdue"

        timeline.append(StageTimelineItem(
            stage=config.stage_name,
            start=start_date.isoformat(),
            end=end_date.isoformat(),
            days_used=days_used,
            limit=limit,
            status=stage_status,
        ))

    # 总时长检查
    total_days_used = 0
    if project.bid_notice_date:
        total_days_used = working_days(project.bid_notice_date, today())
    total_overdue = total_days_used > total_limit

    # 状态合成
    if all_stages_completed:
        return ProjectStatus(
            status=Status.COMPLETED,
            current_stage="已完成",
            total_days_used=total_days_used,
            total_days_limit=total_limit,
            stage_timeline=timeline,
        )

    if has_overdue_stage and total_overdue:
        overdue_type = OverdueType.BOTH
    elif has_overdue_stage:
        overdue_type = OverdueType.STAGE_OVERDUE
    elif total_overdue:
        overdue_type = OverdueType.TOTAL_OVERDUE
    else:
        overdue_type = OverdueType.NONE

    if has_overdue_stage or total_overdue:
        return ProjectStatus(
            status=Status.OVERDUE,
            overdue_type=overdue_type,
            overdue_stage=overdue_stage_name,
            days_in_stage=days_in_current,
            days_remaining=days_remaining_current,
            total_days_used=total_days_used,
            total_days_limit=total_limit,
            current_stage=current_stage_name or overdue_stage_name or "",
            stage_timeline=timeline,
        )

    if has_warning_stage:
        return ProjectStatus(
            status=Status.WARNING,
            days_in_stage=days_in_current,
            days_remaining=days_remaining_current,
            total_days_used=total_days_used,
            total_days_limit=total_limit,
            current_stage=current_stage_name,
            stage_timeline=timeline,
        )

    return ProjectStatus(
        status=Status.NORMAL,
        days_in_stage=days_in_current,
        days_remaining=days_remaining_current,
        total_days_used=total_days_used,
        total_days_limit=total_limit,
        current_stage=current_stage_name,
        stage_timeline=timeline,
    )
