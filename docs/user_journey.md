# User Journey (End-to-End)

本章节从用户视角描述 ZFlow 的完整使用路径，
从首次访问到最终内容交付，按阶段组织。

并非所有阶段都已在当前版本实现，
部分步骤代表预期的未来行为。

---

### Stage 1: Login / Registration

**Page**

* Login / Registration Page

**User Actions**

1. 用户访问平台入口，进入登录页面
2. 输入手机号并获取验证码
3. 输入验证码完成登录
4. （可选）输入团队邀请码
5. 登录成功后自动进入创作首页

**Notes**

* 当前阶段假设登录流程轻量、无摩擦
* 团队逻辑可在后续版本中引入

---

### Stage 2: Input & Material Submission

**Page**

* Creation Homepage

**User Actions**

1. 登录后进入创作首页
2. 在输入区域顶部看到模式切换（Mode Toggle）：

   * 默认：General Mode
   * 可选：Professional Mode
3. 根据模式提供输入：

   * **General Mode**：一句话或一段自然语言描述（题材、人物、场景、情绪等）
   * **Professional Mode**：粘贴或上传剧本 / 大纲等结构化内容
4. （可选）设置快速参数：

   * 目标时长
   * 画幅 / 比例
5. 点击 **Generate** 提交创作意图

**Outcome**

* 系统创建一个新的 Task
* 流程进入素材生成阶段

---

### Stage 3: Generated Asset Management

**Page**

* Asset Management / Generated Materials Page

**User Actions**

1. 任务进入生成中状态
2. 用户查看当前任务进度（排队中 / 生成中）
3. 生成完成后浏览中间素材，例如：

   * 分镜 / 镜头
   * 画面素材
   * 配音
   * BGM
   * 字幕
4. 点击单个素材进行预览或查看详情
5. 进行迭代调整：

   * 左栏：方向性修改与素材包管理
   * 右栏：元素级微调与细节编辑

**Notes**

* 强调生成过程的透明性与可控性
* 中间素材被视为可检查、可修改的实体

---

### Stage 4: Editing & Composition

**Page**

* Editing & Composition Page

**User Actions**

1. 从素材管理进入剪辑与编排页
2. 预览包含画面、音频、字幕的成片草稿
3. 确认分镜后，逐镜头生成视频
4. 对镜头与结构进行调整：

   * 拖拽排序、增删片段
   * 替换画面 / 配音 / BGM / 字幕
   * 文案与字幕时间调整
   * 时长裁剪、画幅预览
5. 对单个镜头发起局部重生成
6. 使用一键生成完成所有镜头
7. 点击 **Generate Final Video / Update Final Version**

**Outcome**

* 任务进入可导出状态

---

### Stage 5: Export & Delivery

**Page**

* Export & Delivery（弹窗或独立页面）

**User Actions**

1. 点击 **Export**
2. 选择导出参数：

   * 分辨率
   * 文件格式
   * 画幅比例
   * 是否烧录字幕
   * 是否包含封面
3. 点击 **Start Export**
4. 导出完成后：

   * 下载文件
   * 保存到个人空间
   * 复制分享链接
   * 跳转发布入口

**Notes**

* 导出过程可能是异步的
* 交付方式可在后续版本扩展

---

## 9. Scope Clarification

* Stage 1–5 描述的是 **完整的目标用户路径**
* 当前 ZFlow 实现重点在于：

  * Task 创建
  * Task 生命周期可视化
  * Task 列表与详情查看
* 素材生成、剪辑与导出在当前阶段为部分或完全 mock

本章节作为产品演进的前瞻性参考存在。
