---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: 'b4d8ee46-686d-422f-87ce-51ad4c9da3c1'
  PropagateID: 'b4d8ee46-686d-422f-87ce-51ad4c9da3c1'
  ReservedCode1: '0a94b56c-b92e-45e4-ae07-ba49a5482389'
  ReservedCode2: '0a94b56c-b92e-45e4-ae07-ba49a5482389'
---

# BidAlert - 中标未签约项目进度追踪系统

可视化大屏追踪中标未签约项目的进度状态，支持预警提醒与情况录入。

## 技术栈

- 后端：Python + FastAPI
- 前端：Vue3 + ECharts
- 数据库：PostgreSQL
- 部署：Docker Compose

## 快速开始

```bash
# 后端
cd backend
python -m pip install -r requirements.txt
uvicorn app.main:app --reload

# 前端
cd frontend
npm install
npm run dev
```