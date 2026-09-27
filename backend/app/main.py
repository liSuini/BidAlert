# -*- coding: utf-8 -*-
"""FastAPI 应用入口"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import init_db
from app.api import projects, stats, excel, stage_config


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化数据库
    init_db()
    yield


app = FastAPI(
    title="BidAlert - 中标未签约项目进度追踪系统",
    description="可视化大屏追踪中标未签约项目的进度状态",
    version="1.0.0",
    lifespan=lifespan,
)

# 允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(projects.router)
app.include_router(stats.router)
app.include_router(excel.router)
app.include_router(stage_config.router)


@app.get("/")
def root():
    return {"name": "BidAlert", "version": "1.0.0", "docs": "/docs"}
