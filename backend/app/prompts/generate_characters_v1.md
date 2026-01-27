生成短视频素材包的「角色设定」。

只输出 JSON：
{"subjects":[{"name":"...","role":"...","description":"...","visual_traits":["..."]}]}

要求：
- 全部中文，和 summary/视觉风格一致
- description 有状态变化 + 目标/阻力
- visual_traits 4-6 个可画特征
- 不照搬用户输入或反馈

输入 JSON 字段：
- mode, user_prompt, summary, art_style, previous_subjects(可选), feedback(可选), documents(可选), input_config(可选)

若 input_config.subjects/subject_seeds 提供角色名，优先使用。
有 feedback 时基于上一版优化。
只返回 JSON，不要 Markdown。
