---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: '6021b1de-51a9-4bd0-8ba9-fe78b4499c27'
  PropagateID: '6021b1de-51a9-4bd0-8ba9-fe78b4499c27'
  ReservedCode1: '8b213a2a-05bf-4bb5-8c85-09e7abf2c888'
  ReservedCode2: '8b213a2a-05bf-4bb5-8c85-09e7abf2c888'
---

# 交接文档

> 项目：BidAlert - 中标未签约项目进度追踪系统
> 日期：2026-09-27
> 仓库：git@github.com:liSuini/BidAlert.git

## 1. 项目概述

可视化大屏追踪中标未签约项目的进度状态，支持预警/超期自动计算、进展录入、Excel 导入导出。本地部署，个人使用。

## 2. 技术栈

- **后端**：Python 3.11+ / FastAPI / SQLAlchemy / SQLite / openpyxl
- **前端**：Vue3 / Vite / ECharts / Element Plus / Pinia / axios
- **数据库**：SQLite（本地文件 `backend/data/bidalert.db`，后续可迁移 PostgreSQL）

## 3. 快速启动

### 后端

```bash
cd backend
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

访问 http://127.0.0.1:8000/docs 查看 Swagger API 文档。

### 前端

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:3000 打开大屏。

## 4. 项目结构

```
BidAlert/
├── backend/                    # 后端
│   ├── app/
│   │   ├── main.py             # FastAPI 入口
│   │   ├── core/               # 配置 + 数据库
│   │   ├── models/             # ORM 模型 (Project, StageConfig, ImportLog)
│   │   ├── schemas/            # Pydantic DTO
│   │   ├── api/                # 路由 (projects, stats, excel, stage_config)
│   │   ├── services/           # 业务逻辑 (ProjectService, StatsService, ExcelService)
│   │   └── engine/             # 预警计算引擎 (核心深模块)
│   └── requirements.txt
├── frontend/                   # 前端
│   ├── src/
│   │   ├── views/              # 4 个视图 (总览/看板/列表/管理)
│   │   ├── components/         # 组件 (StatusBadge, MetricCard, ProjectDetail)
│   │   ├── api/                # API 调用封装
│   │   └── styles/            # 深色主题样式
│   └── package.json
├── docs/                       # 设计文档
│   ├── brainstorming/         # 头脑风暴设计文档
│   ├── specs/                 # 技术规格 + 架构设计 + 原型验证
│   ├── requirements/          # 需求拆分
│   ├── plans/                 # 开发计划
│   └── adr/                   # 架构决策记录
├── tasks/                     # PRD
├── CONTEXT.md                 # 领域术语表
└── README.md
```

## 5. 核心设计

### 预警计算引擎

系统核心模块，位于 `backend/app/engine/warning_engine.py`。

**接口**：`calculate(project, stage_configs) -> ProjectStatus`

**5 个阶段时效规则**（按 500 万分界）：

| 阶段 | ≤500万 | >500万 |
|------|--------|--------|
| 合同敲定 | 7工作日 | 13工作日 |
| 合同审批 | 3工作日 | 4工作日 |
| 业务解构 | 1工作日 | 1工作日 |
| 合同解析 | 2工作日 | 2工作日 |
| ICT立项 | 1工作日 | 1工作日 |
| **总计** | **≤14工作日** | **≤21工作日** |

**状态判定**：
- 正常 → 各阶段均未触发 80% 阈值
- 预警 → 某阶段达到 80% 时效
- 超期 → 阶段超期或总时长超期（区分 stage_overdue/total_overdue/both）
- 已完成 → 所有阶段时间节点已填写

### API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/projects | 项目列表（筛选+分页+计算字段） |
| GET | /api/projects/{id} | 项目详情（含时间线） |
| POST | /api/projects | 新增项目 |
| PUT | /api/projects/{id} | 更新项目 |
| DELETE | /api/projects/{id} | 删除项目 |
| PUT | /api/projects/{id}/remark | 更新情况说明 |
| GET | /api/stats/overview | 总览统计 |
| GET | /api/stats/stages | 阶段分布 |
| GET | /api/stats/regions | 地市分布 |
| GET | /api/stats/overdue | 超期TOP |
| POST | /api/excel/import | Excel 导入 |
| GET | /api/excel/template | 下载模板 |
| POST | /api/excel/export | Excel 导出 |
| GET | /api/stage-config | 阶段配置 |

## 6. 已完成功能

- [x] 后端 FastAPI 项目骨架 + 数据库初始化
- [x] Project / StageConfig / ImportLog 三张表
- [x] 预警计算引擎（工作日计算 + 阶段检查 + 总时长检查 + 状态合成）
- [x] 项目 CRUD API（含计算字段）
- [x] 统计 API（总览 + 阶段分布 + 地市分布 + 超期TOP）
- [x] Excel 导入（字段映射 + 校验 + 重复检测 + 日志）
- [x] Excel 导出（字段选择 + 筛选 + 模板下载）
- [x] 前端 Vue3 + 深色主题
- [x] 总览大屏（指标卡片 + 柱状图 + 环形图 + 地市图 + 超期列表）
- [x] 阶段看板（5列卡片 + 颜色编码 + 点击详情）
- [x] 列表视图（搜索 + 筛选 + 排序 + 分页 + 导出）
- [x] 管理视图（导入 + 导出 + 手动新增）
- [x] 项目详情弹窗（时间线 + 情况说明录入 + 阶段日期编辑）

## 7. 后续建议

1. **法定节假日配置**：当前工作日计算仅排除周末，建议新增 HolidayCalendar 表支持法定节假日
2. **数据库迁移**：从 SQLite 迁移到 PostgreSQL，只需更改 `DATABASE_URL` 环境变量
3. **数据缓存**：统计 API 可引入内存缓存（TTL 1分钟），数据更新时主动失效
4. **单元测试**：补充后端 API 层和 Excel 服务的自动化测试
5. **性能优化**：ECharts 按需引入减小前端包体积
6. **导入历史页面**：在管理视图展示 ImportLog 历史记录
7. **批量操作**：列表视图支持批量删除/导出