---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: 'a6983e24-3056-4a16-87e5-1397760544fa'
  PropagateID: 'a6983e24-3056-4a16-87e5-1397760544fa'
  ReservedCode1: '0e83476a-f22c-4df8-8fc9-1d5ba53cad7c'
  ReservedCode2: '0e83476a-f22c-4df8-8fc9-1d5ba53cad7c'
---

# BidAlert - 中标未签约项目进度追踪系统 设计文档

> 日期：2026-09-27
> 状态：已确认

## 1. 项目概述

### 1.1 背景

当前中标未签约项目通过 Excel 清单手动管理，缺乏直观的进度可视化与预警机制。本系统旨在提供一个可视化大屏，让领导直观查看项目进展，同时支持预警/超期自动计算、进展录入和 Excel 导入导出。

### 1.2 目标用户

- **主要使用者**：商机签约组（个人使用，本地部署）
- **展示对象**：领导（通过大屏直观查看项目进展）

### 1.3 核心价值

- 可视化大屏多视图展示项目进度
- 按阶段时效自动计算预警/超期状态
- 支持项目进展录入与 Excel 导入导出

## 2. 系统架构

### 2.1 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端 | Vue3 + Vite + ECharts + Element Plus | 大屏可视化 + 交互管理 |
| 后端 | Python 3.11+ / FastAPI | REST API 服务 |
| 数据库 | SQLite (SQLAlchemy ORM) | 本地文件，后续可迁移 PostgreSQL |
| Excel | openpyxl | 导入导出处理 |
| 部署 | 本地启动 | 浏览器访问 |

### 2.2 架构图

```
┌─────────────────────────────────────────┐
│              浏览器 (领导/你)              │
│   Vue3 + ECharts + Element Plus         │
│   ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐       │
│   │总览  │ │看板  │ │列表  │ │管理  │       │
│   │视图  │ │视图  │ │视图  │ │视图  │       │
│   └─────┘ └─────┘ └─────┘ └─────┘       │
└──────────────┬──────────────────────────┘
               │ HTTP/REST API
┌──────────────┴──────────────────────────┐
│         FastAPI 后端 (localhost:8000)     │
│   ┌──────────┐ ┌──────────┐ ┌────────┐  │
│   │项目CRUD   │ │Excel导入 │ │预警计算 │  │
│   │API       │ │/导出模块  │ │引擎    │  │
│   └──────────┘ └──────────┘ └────────┘  │
│   ┌──────────────────────────────────┐   │
│   │        SQLite (本地文件)          │   │
│   │   后续可迁移到 PostgreSQL         │   │
│   └──────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

### 2.3 目录结构

```
BidAlert/
├── backend/           # FastAPI 后端
│   ├── app/
│   │   ├── main.py     # 入口
│   │   ├── models/     # 数据模型
│   │   ├── api/        # API 路由
│   │   ├── services/   # 业务逻辑(预警引擎等)
│   │   └── core/       # 配置、数据库
│   └── requirements.txt
├── frontend/          # Vue3 前端
│   ├── src/
│   │   ├── views/      # 页面视图
│   │   ├── components/ # 通用组件
│   │   ├── api/        # API 调用
│   │   └── stores/     # Pinia状态管理
│   └── package.json
├── docs/              # 设计文档
└── docker-compose.yml # (后续可选)
```

## 3. 数据模型

### 3.1 Project 实体

**基本信息：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键自增 |
| name | str | 项目名称 |
| region | str | 地市/部门 |
| responsible_person | str | 责任人 |
| amount | float | 项目金额（万元） |
| bid_subject | str | 投标主体（信产/数智/...） |

**时间节点：**

| 字段 | 类型 | 说明 |
|------|------|------|
| bid_open_date | date | 开标时间 |
| publicity_end_date | date | 公示期结束时间 |
| bid_notice_date | date | 中标通知书获得时间 |
| contract_content_settled_date | date | 合同内容敲定时间 |
| service_fee_date | date | 中标服务费打出时间 |
| contract_draft_date | date | 信产OA立项时间 |
| contract_start_date | date | 合同发起时间 |
| contract_approved_date | date | 合同完成审批时间 |
| contract_signed_date | date | 完成签约时间 |
| contract_filed_date | date | 合同归档时间 |
| biz_analysis_date | date | 业务解构完成时间 |
| contract_parse_date | date | 合同解析完成时间 |
| ict_provincial_date | date | 省内ICT协议级立项完成时间 |
| ict_digital_date | date | 数智集团ICT协议级立项完成时间 |

**流程标记：**

| 字段 | 类型 | 说明 |
|------|------|------|
| has_plan_review | bool | 是否召开方案评审会 |
| has_bpm_analysis | bool | 是否BPM方案解构 |
| has_pre_bid_review | bool | 是否召开标前评审会 |
| has_business_review | bool | 是否召开业财评审会 |
| contract_content_settled | bool | 是否敲定合同内容（由日期是否填写自动派生） |

**进展记录：**

| 字段 | 类型 | 说明 |
|------|------|------|
| current_stage | str | 当前阶段（自动计算） |
| status_remark | str | 情况说明（手动录入） |

**计算字段（后端自动）：**

| 字段 | 类型 | 说明 |
|------|------|------|
| status | enum | normal/warning/overdue/completed |
| overdue_type | str | stage_overdue/total_overdue/both |
| overdue_stage | str | 超期的具体阶段名称 |
| days_in_stage | int | 当前阶段已用工作日 |
| days_remaining | int | 当前阶段剩余工作日 |
| total_days_used | int | 项目总已用工作日 |
| total_days_limit | int | 项目总时限（14或21） |

### 3.2 StageConfig 实体（阶段时效配置）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键自增 |
| stage_name | str | 阶段名称 |
| stage_order | int | 阶段顺序 |
| start_field | str | 起始时间对应字段名 |
| end_field | str | 结束时间对应字段名 |
| limit_days_below_500 | int | 500万以下时限（工作日） |
| limit_days_above_500 | int | 500万以上时限（工作日） |
| warning_threshold | float | 预警阈值（默认0.8） |

**预设阶段配置：**

| 序号 | 阶段名称 | 起始字段 | 结束字段 | ≤500万 | >500万 |
|------|----------|----------|----------|--------|--------|
| 1 | 合同敲定 | bid_notice_date | contract_content_settled_date | 7 | 13 |
| 2 | 合同审批 | contract_start_date | contract_approved_date | 3 | 4 |
| 3 | 业务解构 | contract_filed_date | biz_analysis_date | 1 | 1 |
| 4 | 合同解析 | biz_analysis_date | contract_parse_date | 2 | 2 |
| 5 | ICT立项 | contract_parse_date | ict_provincial_date/ict_digital_date | 1 | 1 |

> 注：ICT立项的结束字段取决于投标主体——信产项目取 ict_provincial_date，数智项目取 ict_digital_date。投标主体为信产时 ict_digital_date 自动填充"不涉及"。

### 3.3 ImportLog 实体（导入记录）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键自增 |
| import_time | datetime | 导入时间 |
| file_name | str | 文件名 |
| total_count | int | 总条数 |
| success_count | int | 成功数 |
| fail_count | int | 失败数 |
| fail_details | json | 失败详情（行号+原因） |

## 4. 阶段定义与时效规则

### 4.1 阶段流程

```
中标通知书获得 → 合同内容敲定 → 合同发起 → 合同完成审批 → 
完成签约 → 合同归档 → 业务解构完成 → 合同解析完成 → 协议级立项完成
```

### 4.2 时效规则

| 阶段 | 起始节点 | 结束节点 | ≤500万 | >500万 |
|------|----------|----------|--------|--------|
| 合同敲定 | 中标通知书获得 | 合同内容敲定 | 7工作日 | 13工作日 |
| 合同审批 | 合同发起 | 合同完成审批 | 3工作日 | 4工作日 |
| 业务解构 | 合同归档 | 业务解构完成 | 1工作日 | 1工作日 |
| 合同解析 | 业务解构完成 | 合同解析完成 | 2工作日 | 2工作日 |
| ICT立项 | 合同解析完成 | 协议级立项完成 | 1工作日 | 1工作日 |
| **总计** | **中标通知书获得** | **协议级立项完成** | **≤14工作日** | **≤21工作日** |

### 4.3 状态计算逻辑

```
状态判定优先级：
1. completed — 所有阶段时间节点都已填写
2. overdue   — 某阶段超期 或 总时长超期
   - overdue_type:
     - stage_overdue: 具体阶段超期（显示哪个阶段及超期天数）
     - total_overdue: 总时长超期（各阶段未超但总时长超限）
     - both: 既有阶段超期又有总时长超期
3. warning   — 某阶段已用工作日 ≥ 时效 × 80%
4. normal    — 其他情况
```

### 4.4 工作日计算

- 排除周六、周日
- 法定节假日后续通过配置表支持
- 时区统一使用 Asia/Shanghai
- 日期精度精确到天

## 5. 大屏视图设计

### 5.1 视图 1：总览大屏（默认首页）

**布局：**

- 顶部：标题栏 + 视图切换标签（总览|看板|列表|管理）
- 第一行：5个核心指标卡片（项目总数/正常/预警/超期/已完成）
- 第二行左：阶段分布柱状图（各阶段项目数量，按状态堆叠着色）
- 第二行右：状态占比环形图（正常/预警/超期/已完成）
- 第三行左：地市分布图（各区域项目数 + 状态标识）
- 第三行右：超期项目列表 TOP 5（项目名|阶段|超期天数|超期类型）

### 5.2 视图 2：阶段看板视图

**布局：**

- 5列看板，对应5个阶段（合同敲定/合同审批/业务解构/合同解析/ICT立项）
- 每列显示该阶段的项目卡片
- 卡片颜色：绿色（正常）/黄色（预警）/红色（超期）
- 卡片内容：项目名称、金额、已用天数/时限
- 点击卡片 → 弹出项目详情弹窗

### 5.3 视图 3：列表视图

**布局：**

- 顶部工具栏：搜索框 + 阶段筛选 + 状态筛选 + 地市筛选 + 导出按钮
- 表格列：项目名称、地市、金额、投标主体、当前阶段、已用天数、剩余天数、状态、操作
- 支持搜索、筛选、排序、分页
- 导出按钮可导出当前筛选结果
- 点击"编辑" → 项目详情弹窗

### 5.4 视图 4：管理视图

**布局：**

- 导入区：上传 Excel 按钮 + 导入模板下载
- 导入历史：最近导入记录（时间、文件名、成功/失败数）
- 导出区：字段勾选（全选/反选）+ 导出全部 / 导出筛选结果

### 5.5 项目详情弹窗

**内容：**

- 基本信息：名称、地市、金额、投标主体、责任人
- 阶段时间线：横向进度条，标注各阶段已用天数/时限
- 当前状态：状态标签 + 当前阶段 + 已用/总时限
- 情况说明：可编辑文本框 + 保存按钮
- 阶段时间节点：各时间节点列表，未填写的可填写，已填写的可修改

## 6. API 设计

### 6.1 项目管理 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/projects | 获取项目列表（支持筛选/分页） |
| GET | /api/projects/{id} | 获取项目详情 |
| POST | /api/projects | 手动新增项目 |
| PUT | /api/projects/{id} | 更新项目信息 |
| DELETE | /api/projects/{id} | 删除项目 |
| PUT | /api/projects/{id}/remark | 更新情况说明 |

### 6.2 统计 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/stats/overview | 总览统计数据 |
| GET | /api/stats/stages | 阶段分布统计 |
| GET | /api/stats/regions | 地市分布统计 |
| GET | /api/stats/overdue | 超期项目TOP列表 |

### 6.3 Excel API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/excel/import | 导入Excel |
| GET | /api/excel/template | 下载导入模板 |
| POST | /api/excel/export | 导出Excel（指定字段+筛选） |

### 6.4 阶段配置 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/stage-config | 获取阶段时效配置 |
| PUT | /api/stage-config | 更新阶段时效配置 |

## 7. Excel 导入流程

1. 用户上传 .xlsx 文件
2. 后端用 openpyxl 读取
3. 字段映射（Excel 列 → 系统字段）
4. 数据校验：必填字段、日期格式、金额数值
5. 投标主体为"信产"时，ict_digital_date 自动填"不涉及"
6. 重复检测（按项目名称匹配）
7. 写入数据库，返回导入结果（成功数/失败数/失败详情）
8. 记录导入日志

## 8. 错误处理

- Excel 导入失败：返回行号 + 错误原因，不中断整体导入
- 日期解析失败：记录为"未填写"，不影响其他字段
- 网络异常：前端显示错误提示，支持重试

## 9. 非功能需求

- 性能：列表页支持 200+ 项目流畅加载
- 兼容性：Chrome/Edge 浏览器
- 数据安全：本地部署，数据不离开设备
- 可扩展性：数据库可从 SQLite 迁移到 PostgreSQL，阶段配置可调整