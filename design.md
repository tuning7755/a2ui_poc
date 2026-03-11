# LangChain + LiteLLM 版 A2UI POC 详细设计（更新版）

## 1. 目标与变更

当前实现基于 LangChain + LiteLLM，保持 `restaurant_finder` 风格：
- 使用 `tools` 查询数据
- 使用独立 `AGENT_INSTRUCTION`
- 使用 `prompt_builder` 组织规则与示例

本次更新点：
1. `custom_catalog_definition.json`、`custom_example.json` 已移动到 `zhida/`。
2. schema 不再单独注入，**schema 视为 catalog**。
3. 提示词中 **catalog 放在最后一个区块**。
4. 增加后台日志与 LangSmith tracing。

---

## 2. 架构

```text
POST /api/ui/generate
  -> RevenueUiAgentService
     -> Tool: get_revenue_trend(query)
     -> build_ui_prompt(query, tool_data, example, catalog[last])
     -> LiteLLM (via LangChain ChatOpenAI)
     -> parse_json_object + validate_a2ui_payload
  <- {query, tool_data, a2ui, meta}
```

---

## 3. 模块设计

- `zhida/app.py`
  - FastAPI 入口
  - 请求级日志（request_id）
- `zhida/agent_service.py`
  - 先调用 tool，再调用模型
  - 解析/校验/重试
  - LangSmith trace（`@traceable`）
- `zhida/agent_instruction.py`
  - `AGENT_INSTRUCTION` 常量
- `zhida/tools.py`
  - `get_revenue_trend`，记录 tool 调用日志
- `zhida/prompt_builder.py`
  - 读取本地 example/catalog
  - 构建提示词，catalog 置于末尾
- `zhida/parser.py`
  - 解析模型输出 JSON
- `zhida/validator.py`
  - 最小结构校验并记录结果

---

## 4. Prompt 结构（最终版）

按 `restaurant_finder` 组织方式：
- 角色和机制（`AGENT_INSTRUCTION`）
- Workflow and Rules
- 用户 query
- tool 数据
- example
- **catalog（最后）**

模板顺序：

```text
[AGENT_INSTRUCTION]

--- WORKFLOW AND RULES ---
...

--- BEGIN USER QUERY ---
{query}
--- END USER QUERY ---

--- BEGIN QUERY RESULT JSON ---
{tool_data_json}
--- END QUERY RESULT JSON ---

--- BEGIN A2UI EXAMPLE ---
{example}
--- END A2UI EXAMPLE ---

--- BEGIN A2UI CATALOG ---
{catalog}
--- END A2UI CATALOG ---
```

说明：
- 不再包含 `A2UI JSON SCHEMA` 区块。

---

## 5. 可观测性设计

## 5.1 日志

日志覆盖链路：
- API 接收请求（request_id、query）
- Tool 调用（参数、返回规模）
- Prompt 构建（长度）
- 模型调用（输出长度）
- JSON 解析与校验结果
- 重试原因与结果

日志配置：
- `LOG_LEVEL` 默认 `INFO`
- 日志格式：时间 + 级别 + logger 名 + 内容

## 5.2 LangSmith

接入方式：
- 安装 `langsmith` 包
- 在 `agent_service` 关键函数使用 `@traceable`
- 通过环境变量启用：
  - `LANGSMITH_TRACING=true`
  - `LANGSMITH_API_KEY`
  - `LANGSMITH_PROJECT`
  - `LANGSMITH_ENDPOINT`

Trace 范围：
- `generate_revenue_ui`（chain）
- `invoke_ui_model`（llm）

---

## 6. 数据与校验

Tool 返回数据：
- `page_title`
- `card_title`
- `months`
- `actual`
- `budget`

最小校验：
- 顶层 object
- 包含 `beginRendering` / `surfaceUpdate` / `dataModelUpdate`
- `surfaceUpdate.components` 非空
- `dataModelUpdate.contents` 非空
- `surfaceId` 一致

---

## 7. 配置

环境变量：
- `LITELLM_MODEL`
- `LITELLM_BASE_URL`
- `LITELLM_API_KEY`
- `LITELLM_TEMPERATURE`
- `LITELLM_TIMEOUT`
- `LOG_LEVEL`
- `LANGSMITH_TRACING`
- `LANGSMITH_API_KEY`
- `LANGSMITH_PROJECT`
- `LANGSMITH_ENDPOINT`

依赖：
- `langchain`
- `langchain-openai`
- `litellm`
- `langsmith`
- `fastapi`
- `uvicorn`

---

## 8. 后续增强

- 强制检查 tool 调用轨迹
- 增加组件白名单校验
- Mock tool 替换真实查询服务
