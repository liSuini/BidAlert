---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: '00294f25-efa6-4841-9627-4a9127cb1710'
  PropagateID: '00294f25-efa6-4841-9627-4a9127cb1710'
  ReservedCode1: '9d108276-b0ca-40fb-b739-c5e58c52577a'
  ReservedCode2: '9d108276-b0ca-40fb-b739-c5e58c52577a'
---

# 开发计划

> 日期：2026-09-27
> 项目：BidAlert 中标未签约项目进度追踪系统

## 里程碑

| 里程碑 | 内容 | 预估天数 | 依赖 |
|--------|------|----------|------|
| M1 | 后端骨架 + 数据模型 + 预警引擎 | 2天 | 无 |
| M2 | 后端 API 全部完成 | 2天 | M1 |
| M3 | Excel 导入导出 | 1.5天 | M1 |
| M4 | 前端骨架 + 总览大屏 | 2天 | M2 |
| M5 | 前端看板 + 列表 + 详情弹窗 | 2.5天 | M2, M4 |
| M6 | 前端管理视图 + 联调测试 | 1天 | M3, M5 |
| **总计** | | **~11天** | |

## 开发批次与任务清单

### 批次 1：后端核心（M1 + M2 + M3）

#### T01: 后端项目初始化
- 创建 FastAPI 项目骨架
- 安装依赖（fastapi, uvicorn, sqlalchemy, openpyxl, pydantic）
- 配置 SQLite 数据库连接
- 创建 core/config.py 和 core/database.py

#### T02: 数据模型定义
- 定义 Project ORM 模型（23+ 字段）
- 定义 StageConfig ORM 模型
- 定义 ImportLog ORM 模型
- 数据库初始化脚本 + 预设阶段配置
- 信产项目 ict_digital_date 自动填充"不涉及"

#### T03: 预警计算引擎
- 实现 WorkingDayCalculator（工作日计算）
- 实现 StageChecker（阶段时效检查）
- 实现 TotalTimeChecker（总时长检查）
- 实现 StatusComposer（状态合成）
- 实现 WarningEngine.calculate() 统一接口
- ICT 立项结束字段动态选择
- 单元测试：9 个场景全覆盖（基于原型验证）

#### T04: 项目 CRUD API
- GET /api/projects（筛选 + 分页 + 计算字段）
- GET /api/projects/{id}（详情 + 时间线）
- POST /api/projects（新增）
- PUT /api/projects/{id}（更新）
- DELETE /api/projects/{id}
- PUT /api/projects/{id}/remark（更新情况说明）
- API 测试

#### T05: 统计 API
- GET /api/stats/overview
- GET /api/stats/stages
- GET /api/stats/regions
- GET /api/stats/overdue

#### T06: Excel 导入
- 文件上传接口
- openpyxl 读取 + 字段映射
- 数据校验 + 重复检测
- 批量写入 + 失败跳过
- 导入模板下载
- 导入日志记录

#### T07: Excel 导出
- 导出接口（字段选择 + 筛选条件）
- openpyxl 写入 + 表头
- 日期格式化 + 状态中文标签
- 全部导出 / 筛选结果导出

### 批次 2：前端核心（M4 + M5）

#### T08: 前端项目初始化
- Vite + Vue3 项目初始化
- 安装 Element Plus, ECharts, Pinia, axios, vue-router
- 路由配置（4 个视图）
- API Client 封装
- Pinia Store 定义
- 深色主题基础样式
- 顶部导航栏 + 视图切换标签

#### T09: 总览大屏视图
- 5 个指标卡片组件
- 阶段分布柱状图（ECharts）
- 状态占比环形图（ECharts）
- 地市分布图（ECharts）
- 超期 TOP 5 列表
- 数据加载 + 自动刷新

#### T10: 阶段看板视图
- 5 列看板布局
- 项目卡片组件（颜色编码）
- 卡片点击 → 详情弹窗

#### T11: 列表视图
- 搜索框 + 筛选下拉
- Element Plus 表格（分页、排序）
- 状态标签组件
- 导出按钮
- 编辑按钮 → 详情弹窗

#### T12: 项目详情弹窗
- 基本信息展示
- 阶段时间线组件（横向进度条）
- 当前状态展示
- 情况说明编辑 + 保存
- 阶段时间节点编辑表单
- 保存后刷新

### 批次 3：收尾（M6）

#### T13: 管理视图
- Excel 导入区（上传 + 模板下载）
- 导入历史列表
- 导出字段勾选 + 导出按钮
- 手动新增项目表单

#### T14: 联调测试
- 前后端联调
- 端到端测试（导入→展示→编辑→导出）
- 性能验证（200+ 项目加载）

#### T15: 交接文档
- 编写 handoff 文档
- 运行说明
- 后续建议

## 任务依赖关系

```
T01 ──→ T02 ──→ T03 ──→ T04 ──→ T05
                ↗              ↘
T01 ──→ T02 ──→ T06            T08 ──→ T09
                ↘              ↘
T01 ──→ T02 ──→ T07            T08 ──→ T10
                                ↘
                        T08 ──→ T11
                                ↘
                        T08 ──→ T12
                                ↘
T06 + T07 ──→ T13 ──→ T14 ──→ T15
```

## 验收标准

每个任务完成的验收标准：
1. 代码通过类型检查和 lint
2. 核心逻辑有对应单元测试
3. API 接口可通过 Swagger 文档测试
4. 前端视图可在浏览器中正常展示和交互