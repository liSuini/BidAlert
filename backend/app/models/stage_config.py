# -*- coding: utf-8 -*-
"""StageConfig ORM 模型"""
from sqlalchemy import Column, Integer, String, Float
from app.core.database import Base


class StageConfig(Base):
    __tablename__ = "stage_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stage_name = Column(String(100), nullable=False, comment="阶段名称")
    stage_order = Column(Integer, nullable=False, comment="阶段顺序")
    start_field = Column(String(100), nullable=False, comment="起始时间字段名")
    end_field = Column(String(100), nullable=False, comment="结束时间字段名")
    limit_days_below_500 = Column(Integer, nullable=False, comment="500万以下时限")
    limit_days_above_500 = Column(Integer, nullable=False, comment="500万以上时限")
    warning_threshold = Column(Float, default=0.8, comment="预警阈值")
