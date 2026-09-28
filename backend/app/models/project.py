# -*- coding: utf-8 -*-
"""Project ORM 模型"""
from datetime import date, datetime
from sqlalchemy import Column, Integer, String, Float, Date, Boolean, Text, DateTime
from app.core.database import Base


class Project(Base):
    __tablename__ = "projects"

    # 基本信息
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(500), nullable=False, comment="项目名称")
    region = Column(String(100), comment="地市/部门")
    responsible_person = Column(String(100), comment="责任人")
    amount = Column(Float, comment="项目金额（万元）")
    bid_subject = Column(String(50), comment="投标主体")

    # 时间节点
    bid_open_date = Column(Date, comment="开标时间")
    publicity_end_date = Column(Date, comment="公示期结束时间")
    bid_notice_date = Column(Date, comment="中标通知书获得时间")
    contract_content_settled_date = Column(Date, comment="合同内容敲定时间")
    service_fee_date = Column(Date, comment="中标服务费打出时间")
    contract_draft_date = Column(Date, comment="信产OA立项时间")
    contract_start_date = Column(Date, comment="合同发起时间")
    contract_approved_date = Column(Date, comment="合同完成审批时间")
    contract_signed_date = Column(Date, comment="完成签约时间")
    contract_filed_date = Column(Date, comment="合同归档时间")
    biz_analysis_date = Column(Date, comment="业务解构完成时间")
    contract_parse_date = Column(Date, comment="合同解析完成时间")
    ict_provincial_date = Column(Date, comment="省内ICT协议级立项完成时间")
    ict_digital_date = Column(String(50), comment="数智集团ICT（日期或'不涉及'）")

    # 流程标记
    has_plan_review = Column(Boolean, default=False, comment="是否召开方案评审会")
    has_bpm_analysis = Column(Boolean, default=False, comment="是否BPM方案解构")
    has_pre_bid_review = Column(Boolean, default=False, comment="是否召开标前评审会")
    has_business_review = Column(Boolean, default=False, comment="是否召开业财评审会")
    contract_content_settled = Column(Boolean, default=False, comment="是否敲定合同内容")

    # 进展记录
    status_remark = Column(Text, comment="情况说明")
    remark_updated_at = Column(DateTime, comment="情况说明最后更新时间")

    # 元数据
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def get_field_value(self, field_name: str):
        """获取字段值（支持动态访问）"""
        return getattr(self, field_name, None)

    def get_date_field(self, field_name: str):
        """获取日期字段的 date 值，处理'不涉及'等特殊值"""
        val = getattr(self, field_name, None)
        if val is None:
            return None
        if isinstance(val, date):
            return val
        # 字符串类型（如 ict_digital_date = "不涉及"）
        if isinstance(val, str):
            if val == "不涉及":
                return None
            try:
                return date.fromisoformat(val)
            except (ValueError, TypeError):
                return None
        return None
