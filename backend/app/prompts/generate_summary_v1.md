生成短视频素材包的「故事梗概」。

只输出 JSON：
{"summary": "..."}

要求：
- 中文 1-2 句，包含 主体/目标/阻力/转折/结果
- 不写镜头与场景细节
- 不照搬用户输入或反馈

输入 JSON 字段：
- mode, user_prompt, summary(可选), feedback(可选), documents(可选), input_config(可选)

有 feedback 时基于上一版优化。
只返回 JSON，不要 Markdown。
