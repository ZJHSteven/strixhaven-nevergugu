# Strixhaven Nevergugu — 多 DM 协作企划

让更多人一起把斯翠海文玩“活”。这是一个为 D&D5e 斯翠海文主题开展的多 DM 协作企划与内容仓库：我们不重述官方文本，而是共同创作扩展内容、分线剧情、校园生活片段、考试/课程、随机事件表、NPC 档案、Downtime 活动等，让原模组更有趣、更耐玩。

> 注意：本仓库不包含也不分发任何受版权保护的官方条目原文（包括但不限于《Strixhaven: A Curriculum of Chaos》的文本/数据块/插图等）。我们创作的是“增补与改造”内容，必要时仅给出引用指引（如“参见 S:CoC p.xx”）和我们自己的改写。

## 目标与原则

- 多 DM 协作：每位 DM 可认领一个学院、若干 NPC 或一条叙事线，带着一群玩家并行推进。
- 轻量规则，重在落地：统一最小集规范，降低协作与合并成本。
- 安全与包容：采用 Session Zero、Lines & Veils 等安全工具，尊重所有参与者。
- 明确正典（Canon）：约定“共同时间线”和“可选分线”，避免互相打架。
- 版权合规：仅提交原创/改写内容和可授权素材，严禁上传盗版摘录。

## 我们如何协作

角色分工（可一人多岗）：

- 总协调（Lead DM）：把控世界观边界、时间线冲突、最终合并。
- 学院负责人（College DM）：Lorehold / Prismari / Quandrix / Silverquill / Witherbloom 各学院线的总体走向与质量。
- 规则与平衡（Rules）：难度基线、奖励经济、考试/Downtime 框架。
- 工具与资产（Tools）：地图、素材、脚本，维护公共模版与目录。

时间线与正典：

- 维护一条“主时间线”（canon），重要事件与走向以 PR 共识为准。
- 允许分线（AU/可选），在元数据中标注 `canon: true|false` 与 `era`。
- 冲突优先级：主时间线 > 已合并分线 > 草稿/提案。

安全与约定：

- 使用 Lines & Veils、X-Card 等工具，并在内容元数据中标注 `contentWarnings`。
- 校园题材默认轻松，但允许惊悚/黑暗元素，需提前标注并给出替代方案。

## 仓库结构（建议）

```
modules/                # 完整模块（一次或多次 Session）
	├─ lorehold/
	├─ prismari/
	├─ quandrix/
	├─ silverquill/
	└─ witherbloom/
npcs/                   # NPC 档案（含目标、秘密、推进钩子）
encounters/             # 遭遇与挑战（含可调难度建议）
downtime/               # 校园生活、社团、兼职、研究、考试等模板化条目
tables/                 # 随机事件表、课程表、考试题库
items/                  # 道具与魔法物品（自制或改写）
lore/                   # 设定补充、地点、派系、校规等原创或改写内容
assets/                 # 合规素材（地图、图片、标志），需附来源与授权
	├─ images/
	└─ maps/
templates/              # 提交模板与示例
docs/                   # 规范扩展、风格指南、流程细化（可后续补充）
```

> 目录可以按需调整，但建议保持“类型 → 学院/主题 → 条目”的层级，以便检索。

## 提交内容规范（最低集）

每个条目文件请包含 YAML 元数据（frontmatter）与清晰的章节结构。推荐键：

```yaml
---
title: 示例：银鸦社的午夜辩论
author: 某某DM
version: 0.1.0
type: quest # scene|quest|exam|npc|item|encounter|table|downtime|lore
college: Silverquill
era: Year 1 # 或 Year 2 / 学年学期等
levelRange: 1-3
players: 4-5
estimatedSession: 2-3h
canon: true
tags: [校园生活, 辩论社, 社交挑战]
contentWarnings: [社交冲突, 群体压力]
dependencies: [] # 依赖的本仓库内容（路径或ID）
playtestStatus: draft # draft|playtested|approved
lastUpdated: 2025-10-16
---
```

正文建议包含：

- 剧情钩子与背景要点（不引述原书原文）
- 目标与成功条件；失败也有后果与推进
- 场景/试题/挑战拆分，含“读前概要”和“运行提示”
- 关键 NPC（目标、性格、秘密、关系），不要粘贴官方数据块
- 难度调整与替代方案（低/中/高/非战处理）
- 奖励与长期影响（学院声望、社团资源、剧情旗帜）
- 安全提示与内容边界（如敏感主题的替代叙事）

在 `templates/内容模板.md` 提供了完整模板，可直接复制开写。

## 命名与路径建议

- 文件名：`类型-学院-简短slug-作者-YYYYMM.md` 例如 `quest-silverquill-midnight-debate-steven-202510.md`
- 资源归档：图片/地图放在 `assets/images|maps`，同名子目录；引用请使用相对路径。
- 多版本：同一条目更新以 `version` 区分，必要时保留 `changelog` 段。

## 工作流（分支 / PR / 评审）

1. 建立分支：`feat/<类型>-<学院>-<slug>`，例如 `feat/quest-silverquill-midnight-debate`。
2. 基于模板撰写内容；本地自查“安全/难度/引用”三项清单。
3. 提交 PR，描述内容类型、涉及学院、时间线影响、是否 canon。
4. 评审标签：`college:*`、`type:*`、`safety`、`canon`、`needs-playtest`。
5. 至少一名学院负责人 + 总协调通过后合并；涉及冲突则走讨论/折中方案。

自查清单（节选）：

- [ ] 未粘贴官方受版权保护内容（文本/数据块/插画）。
- [ ] 写明内容警告与替代方案。
- [ ] 给出难度调整建议与非战解决路径。
- [ ] 说明对时间线/关系网的影响（可回滚）。
- [ ] 资源有明确授权或自制，并附来源说明。

## 版权与授权

- 我们与 Wizards of the Coast 无关，也未获得其背书。本仓库仅作粉丝创作与同人扩展使用。
- D&D 5.1 SRD 已以 CC-BY-4.0 授权发布，但《斯翠海文》一书并不在 CC 范围内。请勿上传其原文或受保护内容。
- 对于自制文本与素材：建议采用 CC BY-NC-SA 4.0（署名-非商用-相同方式共享）；若不同意，请在条目元数据与 PR 中明确声明授权条款。
- 对于代码脚本/工具（若后续新增）：建议使用 MIT 许可。

> 若你不确定某段内容是否可上传，请先开 Issue/Discussion 咨询，或仅给出“行为描述 + 运行提示”，避免直接抄录。

## 快速开始（贡献者）

- Fork 本仓库或新建分支
- 在相应目录下复制 `templates/内容模板.md` 并重命名
- 按模板填写元数据与正文
- 提交 PR 并等待评审

## 路线图（草案）

- [ ] Year 1 各学院最少 3 个“课程/考试/社团”活动模块
- [ ] 跨学院联动事件（节庆、校际比赛）
- [ ] 校园生活随机事件 d20 表（按季节/考试周细分）
- [ ] NPC 关系网与传闻系统（轻规则）
- [ ] Downtime 经济与研究/实习框架

## 致谢

感谢每一位 DM 与玩家的创作与测试。愿每一次掷骰都为斯翠海文带来新的火花。
