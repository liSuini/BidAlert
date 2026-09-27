# -*- coding: utf-8 -*-
"""数据库引擎与Session"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import DATABASE_URL, DATA_DIR

DATA_DIR.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite需要
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI 依赖：获取数据库Session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库：创建表 + 插入预设数据"""
    from app.models import project, stage_config, import_log  # noqa: F401
    Base.metadata.create_all(bind=engine)
    _seed_stage_configs()


def _seed_stage_configs():
    """插入预设阶段配置"""
    from app.models.stage_config import StageConfig
    from sqlalchemy import text

    db = SessionLocal()
    try:
        count = db.query(StageConfig).count()
        if count == 0:
            configs = [
                StageConfig(stage_name="合同敲定", stage_order=1,
                            start_field="bid_notice_date",
                            end_field="contract_content_settled_date",
                            limit_days_below_500=7, limit_days_above_500=13,
                            warning_threshold=0.8),
                StageConfig(stage_name="合同审批", stage_order=2,
                            start_field="contract_start_date",
                            end_field="contract_approved_date",
                            limit_days_below_500=3, limit_days_above_500=4,
                            warning_threshold=0.8),
                StageConfig(stage_name="业务解构", stage_order=3,
                            start_field="contract_filed_date",
                            end_field="biz_analysis_date",
                            limit_days_below_500=1, limit_days_above_500=1,
                            warning_threshold=0.8),
                StageConfig(stage_name="合同解析", stage_order=4,
                            start_field="biz_analysis_date",
                            end_field="contract_parse_date",
                            limit_days_below_500=2, limit_days_above_500=2,
                            warning_threshold=0.8),
                StageConfig(stage_name="ICT立项", stage_order=5,
                            start_field="contract_parse_date",
                            end_field="ict_provincial_date",
                            limit_days_below_500=1, limit_days_above_500=1,
                            warning_threshold=0.8),
            ]
            db.add_all(configs)
            db.commit()
    finally:
        db.close()
