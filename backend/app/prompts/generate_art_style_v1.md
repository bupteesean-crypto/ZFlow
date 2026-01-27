生成短视频素材包的「视觉风格」。

只输出 JSON：
{"art_style":{"style_name":"...","style_prompt":"...","palette":["..."]}}

style_prompt 包含：媒介/材质/光线/构图/色调一致性（简洁即可）。

要求：
- 全部中文，具体可视化
- 与 summary 一致
- 不照搬用户输入或反馈

输入 JSON 字段：
- mode, user_prompt, summary, previous_art_style(可选), feedback(可选), documents(可选), input_config(可选)

有 feedback 时基于上一版优化。
只返回 JSON，不要 Markdown。
