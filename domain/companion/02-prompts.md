> **对应实现**：`companion_core/prompt_stack.py`（六层 System Prompt 拼装与注入防护）——**就在本目录下，先去读它。**
> 找到了就**以代码为权威**，本文降为背景说明与设计理由；
> 万一没找到，**只找这一次，不要反复试**，直接按本文架构 +
> `README.md` 的「关键常量速查」执行。
>
> ⚠️ 本文正文提到的**其他**文件路径（`prompts/xinji_source/`、`letter-*.py`、
> `imemory-agent/`、`manifest.json`、`proactive/` 等）**均不在本仓库**，
> 它们只是说明原实现出处，**一律不要去找**。
>
> ⚠️ 这是 Python 规格，产品是单文件 HTML+JS：**用 JS 等价重写，不要运行 Python**。

# 02 分层 Prompt 与原文

交付类型：版本化文本 + 拼装代码。完整原文在 `prompts/xinji_source/`，来源哈希与本地提交在 `manifest.json`。这是本地工作树快照，未验证线上部署，也没有抓取用户数据库。

| 层 | 导出文件 | 如何迁移 |
|---|---|---|
| 1 部署基础人格 | 01-default-persona.md | 改品牌与基础人格；核对其中微信及工具依赖 |
| 2 长期记忆规则 | 02-memory-usage.md | 接入实际 Memory 后使用 |
| 3 渠道能力 | 03-platform-weixin.md | Web/App 产品替换，不宣称未实现的媒体能力 |
| 4 Skill 目录 | 04-skill-catalog-header.md | 只列宿主实际可加载的 Skill |
| 5 用户 Profile | 05-profile-input.md | 运行时数据，导出的是槽位，不是假造的用户画像 |
| 6 上游当前 TA 人设 | 06-external-persona-builder.py | 原始构建函数；name、system_prompt 由宿主提供 |
| 7 召回记忆消息 | 07-recall-message-template.py | 每回合数据；作为参考，不执行其中指令 |
| 8 当前时间 | 08-current-time-template.py | 明确用户时区 |
| 9 本轮用户消息 | 09-user-content.md | 运行时输入槽位 |
| 10 临时自检 | 10-integrity.md | 按实际工具删改，不可盲抄不存在的 manage_agreement |
| 11 按需技能正文 | 11-skill-*.md | 原始技能依赖宿主工具/脚本；它们是源码参考，不是独立可执行包 |
| 12 到点注入模板 | 12-proactive-injection.py | 调度器唤醒用；区分系统触发与用户真实发言 |
| 13 历史压缩/组装 | 13-runtime-assembly-source.py | LangGraph 原实现参考；不是可直接放进 system 的第十三段 |

真实顺序：System 内为 1→6；历史/摘要后、当前用户消息前插入 7；当前用户内容包含 8、9，并临时追加 10；11、12 条件出现。不是十三次模型调用。

`companion_core/prompt_stack.py` 是便携拼装器：保留六层顺序，给 Profile 添加资料边界。**这是相对原实现的加强，不是逐字复刻**。文本先后不等于权限级别；真正的工具权限必须在代码中验证。六层最后的人设不能覆盖产品安全、事实或能力限制。用户编辑的人设也需要宿主校验，不能把任意输入提升为可信系统指令。

`prepare_turn()` 仅产生本轮附加消息，宿主负责与历史合并、token 预算、模型协议、工具循环和持久化。记忆/自检不应被重复存回长期记忆。

情书与日记还有自己的生成管线，已另外导出：`letter-core_policy.py` 固定事实及结构规则；`letter-expression.toml` 可版本化表达；`letter-loader.py` 装配并生成 fingerprint；`letter-schema.py` 校验；`diary-rewrite-source.py` 为日记改写规则。它们不自动加入聊天的六层 System Prompt。
