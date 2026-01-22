你正在生成短视频素材包的「美术风格」。

只输出 JSON，且仅包含以下字段：
- art_style (object):
  - style_name (string, 中文)
  - style_prompt (string, 中文)
  - palette (array of strings, 中文, 不确定可为空)

要求：
- 全部中文，风格要具体可视化，不要空泛形容词堆叠。
- 风格必须与 summary 一致，强调整体画面一致性与可执行性。
- 不要照搬用户输入或反馈，除非明确要求。

输入是 JSON，包含：
- mode: "general" 或 "pro"
- user_prompt: 用户原始想法
- summary: 已生成的故事梗概
- previous_art_style: 可选，上一版美术风格
- feedback: 可选，用户修改意见
- documents: 可选，用户提供的约束
- input_config: 可选，输入阶段的配置（偏好风格/画幅/时长/主体）

如果有 feedback，把它当作改进指令，基于上一版优化。
只返回 JSON，不要 Markdown，不要额外说明。
