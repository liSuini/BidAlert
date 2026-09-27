# -*- coding: utf-8 -*-
"""ImportLog ORM 模型"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.core.database import Base


class ImportLog(Base):
    __tablename__ = "import_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    import_time = Column(DateTime, nullable=False, default=datetime.now, comment="导入时间")
    file_name = Column(String(500), nullable=False, comment="文件名")
    total_count = Column(Integer, default=0, comment="总条数")
    success_count = Column(Integer, default=0, comment="成功数")
    fail_count = Column(Integer, default=0, comment="失败数")
    fail_details = Column(Text, comment="失败详情JSON")
