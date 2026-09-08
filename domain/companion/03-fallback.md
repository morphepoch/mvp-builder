> **对应实现**：`companion_core/fallback.py`（九类失败的兜底决策与固定话术）——**就在本目录下，先去读它。**
> 找到了就**以代码为权威**，本文降为背景说明与设计理由；
> 万一没找到，**只找这一次，不要反复试**，直接按本文架构 +
> `README.md` 的「关键常量速查」执行。
>
> ⚠️ 本文正文提到的**其他**文件路径（`prompts/xinji_source/`、`letter-*.py`、
> `imemory-agent/`、`manifest.json`、`proactive/` 等）**均不在本仓库**，
> 它们只是说明原实现出处，**一律不要去找**。
>
> ⚠️ 这是 Python 规格，产品是单文件 HTML+JS：**用 JS 等价重写，不要运行 Python**。

# 03 兜底

交付类型：错误策略代码 + 固定话术 + 宿主执行适配。

现有依据：`imemory-agent/src/errors.py`、`src/ilink/service/processor.py`、`src/agent/model_router.py`。聊天业务边界快速失败；原实现没有显式多模型 fallback chain。SDK 或上游网关仍可能内部重试，不能把“业务层不重跑”说成全链路零重试。原项目旧 README 的 fallback_chain 描述不能当当前实现。

`companion_core/fallback.py` 实现九类错误决策。`retry_now=false` 是此便携策略的默认行为，不控制第三方 SDK。话术为本次示例；心迹原话术另存 `prompts/xinji_source/fallback-texts.json`。

迁移时按环节处理：

- 身份失败：停止业务，避免切到别的用户身份；仅回适当错误提示。
- 模型超时：首字节前可在宿主总 deadline 内进行有界重试；已有部分回复、已执行工具时，不直接重跑整个回合。
- 工具失败：返回结构化失败结果，不许回复“已经设好”。真实工具写入以业务幂等键保护。
- 内容不足/非法格式：日记可回原摘要；情书内容不足可不发布。技术错误和内容不足分开记录，禁止用虚构内容填满。
- 发送失败：区分“明确未发送”和“结果未知”。结果未知先核对回执，有渠道幂等支持再重发；没有时标 delivery_unknown，避免盲重发。
- 崩溃恢复：当前心迹采用道歉后标处理；其他宿主可以选择 durable outbox 重放，前提是工具与发送都能幂等。

策略对象只是建议，调用方负责真正的消息结算与报警。fallback 文案不作为人物事实写入记忆，但应作为 operational event 留审计。日志、trace、错误原文不要直接交给用户；可识别业务错误也必须来自受控文案映射。

待接入的最小状态：received → generating → generated → sending → delivered / delivery_unknown / failed；静默单独记 silenced。存 tenant/user/character、input_event_id、response_id、工具幂等键、错误分类、结果和时间。不要把“已处理”解释成“用户已经收到”。
