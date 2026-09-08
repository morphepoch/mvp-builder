# P3 · 设计语言：先出 DESIGN.md，我确认后再写代码

你拥有顶尖设计审美。**这一步不许写任何产品代码。**

---

## 【第 0 步：能力自测，10 秒，决定后面走哪条路】

请你现在生成一张图：深蓝色背景，中间一个白色圆形。直接给我图。

- **给得出图** → 走【路线 B：图驱动】
- **给不出图** → 直接告诉我"无图像生成能力，走路线 A"，然后走【路线 A：纯代码】

---

## 【第 1 步：调用技能】

**两条路线都必须读这三个**（共约 9.5KB）：

1. DESIGN.md 的写法与管理：
   https://raw.githubusercontent.com/nexu-io/open-design/main/skills/design-md/SKILL.md

2. 前端设计主力技能（Anthropic 上游，`mode: prototype`，零依赖）：
   https://raw.githubusercontent.com/nexu-io/open-design/main/skills/frontend-design/SKILL.md

3. 设计系统参考 —— 柔和微立体 Claymorphism：
   https://raw.githubusercontent.com/nexu-io/open-design/main/design-systems/claymorphism/DESIGN.md

**只有路线 B 才额外读下面两个**（各约 37KB，很大，确认走 B 再读）：

4. 出设计图 —— **Web 产品用这个**：
   https://raw.githubusercontent.com/nexu-io/open-design/main/skills/imagegen-frontend-web/SKILL.md

   **移动端 H5 产品改用**：
   https://raw.githubusercontent.com/nexu-io/open-design/main/skills/imagegen-frontend-mobile/SKILL.md

5. 照图实现（⚠️ 目录名是 `image-to-code-skill`，技能名是 `image-to-code`）：
   https://raw.githubusercontent.com/nexu-io/open-design/main/skills/image-to-code-skill/SKILL.md

> 若沙箱无外网：我会把内容直接贴给你，等我贴完再开始。

---

## 【第 2 步：确定视觉风格】

我要的是 **Blender 风格的 2.5D 柔和微立体**：

- 圆润饱满的几何形体，像捏出来的黏土，有厚度感但不写实
- 柔和的多向光照，阴影是**大范围低透明度的弥散阴影**，不是硬边投影
- 低饱和的柔和色彩，大面积留白，主色克制
- 微妙的渐变过渡，避免纯平色块
- 【补充：主色倾向、情绪关键词、参考产品】← 替换

⚠️ Claymorphism 只是**骨架参考**，**不要照抄它默认的蓝色 `#3B82F6`**。
结合我上面的描述，给出属于这个产品的配色。

---

## 【第 3 步：产出 DESIGN.md】

按 `design-md` 技能的规范写，只含设计规范、不含业务逻辑：

1. **设计理念** —— 三个关键词 + 说明这个视觉如何服务于产品定位
2. **色彩** —— 主色/辅助色/语义色/中性色阶，每个给 HEX 并说明用在哪；浅色深色两套
3. **字体** —— 中英文字体栈（必须有系统字体兜底）、字号阶梯、字重、行高
4. **间距与圆角** —— 基础栅格单位、间距阶梯、圆角阶梯（微立体圆角要大）
5. **阴影系统** —— **本风格的灵魂**。至少 4 级，给完整 CSS 值，说明各用在什么层级。
   柔和微立体通常需要**双层阴影**：一层大范围弥散 + 一层贴近元素的浅色高光
6. **组件规范** —— 按钮（hover/active/disabled）、输入框、卡片、列表项、弹窗、
   标签、加载态，每个给关键 CSS
7. **动效** —— 缓动函数、时长、哪些交互需要动效
8. **CSS 变量清单** —— 全部落成可直接用的 `:root { --xx: ... }`

---

## 【第 4 步：给我看效果，等我确认】

**路线 A**：做一个 `design-preview.html`，单文件无依赖，
把所有色彩、阴影、组件都实际渲染出来，我打开就能看到真实效果。

**路线 B**：先按 `imagegen-frontend-*` 的规范
**为每个主要界面各出一张独立大图**（不要把多个界面压进一张），
我看过图后，你再按 `image-to-code` 的方法把图转成代码，同时仍要交 `design-preview.html`。

然后**停下来等我确认**。我说「设计通过」你才能进入开发。
我提修改意见的话，改完再给我看一次。
