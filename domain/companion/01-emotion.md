> **对应实现**：`companion_core/emotion.py`（情绪状态归约与回应策略）——**就在本目录下，先去读它。**
> 找到了就**以代码为权威**，本文降为背景说明与设计理由；
> 万一没找到，**只找这一次，不要反复试**，直接按本文架构 +
> `README.md` 的「关键常量速查」执行。
>
> ⚠️ 本文正文提到的**其他**文件路径（`prompts/xinji_source/`、`letter-*.py`、
> `imemory-agent/`、`manifest.json`、`proactive/` 等）**均不在本仓库**，
> 它们只是说明原实现出处，**一律不要去找**。
>
> ⚠️ 这是 Python 规格，产品是单文件 HTML+JS：**用 JS 等价重写，不要运行 Python**。

# 01 情绪引擎

交付类型：代码 + 提取 Prompt + 回应 Skill。

**现状**：本地心迹的 `AI_PERSONA_XINJI.md` 规定倾听、低密度建议、开心回应、2–5 句和最多一个问题，并建议情绪波动时调用记挂工具。本次检查的聊天主链路没有发现独立的持久化情绪状态机。不能把这一发现扩大成外部 Memory 服务完全没有情绪能力。

**新增实现**：`companion_core/emotion.py` 把语义提取结果归一化、时间衰减、置信度融合，产生状态与回复策略。`prompts/emotion_signal.md` 用于调用模型提取 JSON；`skills/emotion-response/SKILL.md` 约束自然表达。代码本身不调用模型。

信号包含 primary、valence、arousal、intensity、confidence、need、risk、cues。状态另外保存 episode_id、updated_at 和正负连续轮数。episode_id 是原型级标识，不应直接作为一次触达的幂等键。

8 小时半衰期、0.72 融合系数、60/180 分钟回访候选均为**本次设计的可调起点，未经过线上实验**。数值表达产品策略，不是心理量表。高风险状态由宿主明确结案才能清除；此原型不能替代宿主完整安全处理。

接入：宿主按 `(tenant_id, user_id, character_id)` 保存状态；用 event_id 去重和版本号 CAS 更新，拒绝乱序。每次先解析模型 JSON，再运行 reducer，将 decision 作为可信控制参数注入回应模板。用户未允许主动关心时，仅用它调整被动回复。`proactive_eligible` 只表示可考虑，必须再经频控与用户授权检查。

降级：情绪提取失败时保留已有状态并按自然语气回复，不把失败解析为“用户已恢复”。涉及高风险的独立判断不能被普通情绪提取超时跳过。
