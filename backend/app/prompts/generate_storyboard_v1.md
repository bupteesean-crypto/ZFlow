生成短视频素材包的「分镜脚本」。

只输出 JSON：
{"storyboard":[{"description":"...","scene_id":"scene_1","duration_sec":3,"camera":"..."}]}

要求：
- 全部中文，和 summary/视觉风格/角色/场景一致
- description: 动作 + 信息推进 + 情绪变化
- scene_id 依次使用 scene_1/scene_2...
- 不照搬用户输入或反馈

输入 JSON 字段：
- mode, user_prompt, summary, art_style, subjects, scenes, previous_storyboard(可选), feedback(可选), documents(可选), input_config(可选)

有 feedback 时基于上一版优化。
只返回 JSON，不要 Markdown。
