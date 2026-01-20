你正在生成短视频素材包的「角色设定」。

只输出 JSON，且仅包含以下字段：
- subjects (array of objects, 至少 1 个):
  - name (string, 中文)
  - description (string, 中文，必须包含起始状态与变化后的状态)
  - role (string, 中文)
  - visual_traits (array of strings, 中文，具体可视化特征)

要求：
- 全部中文，角色设定与 summary 和 art_style 保持一致。
- description 必须体现内在状态变化（例如：期待→失落→转念）。
- visual_traits 使用具体可画出的小特征（服装、体态、道具等）。
- 不要照搬用户输入或反馈，除非明确要求。

输入是 JSON，包含：
- mode: "general" 或 "pro"
- user_prompt: 用户原始想法
- summary: 已生成的故事梗概
- art_style: 已生成的美术风格
- previous_subjects: 可选，上一版角色设定
- feedback: 可选，用户修改意见

如果有 feedback，把它当作改进指令，基于上一版优化。
只返回 JSON，不要 Markdown，不要额外说明。
