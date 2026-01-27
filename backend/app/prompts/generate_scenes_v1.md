生成短视频素材包的「场景设定」。

只输出 JSON：
{"scenes":[{"name":"...","description":"...","mood":"...","purpose":"..."}]}

要求：
- 全部中文，和 summary/视觉风格/角色一致
- description 含时间/光线/关键物件/空间关系（空景）
- mood 可视化表达
- purpose 明确叙事功能
- 不照搬用户输入或反馈

输入 JSON 字段：
- mode, user_prompt, summary, art_style, subjects, previous_scenes(可选), feedback(可选), documents(可选), input_config(可选)

有 feedback 时基于上一版优化。
只返回 JSON，不要 Markdown。
