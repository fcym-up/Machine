# 实施计划：全息投影 Dashboard

## 步骤 1: 备份旧文件
- 将现有 index.html 重命名为 index.html.bak

## 步骤 2: 编写新的 index.html
- 文件: app/static/index.html
- 内容: 完整全息投影风格单页应用
  - HTML 结构 (语义化标签, 全息面板布局)
  - CSS 动效系统 (呼吸发光、扫描线、粒子流、脉冲波纹)
  - JavaScript 数据层 (API 调用、定时刷新、错误隔离)
  - JavaScript 交互层 (聊天、语音输入输出)
  - JavaScript 动画系统 (打字机、数字滚动、环形进度)

## 步骤 3: 启动服务验证
- 启动 uvicorn 服务
- 检查 dashboard 是否正常渲染
- 检查情绪/活动/聊天等 API 是否正常
- 验证语音按钮功能

## 步骤 4: 修复潜在问题
- 检查控制台错误
- 确认响应式布局
- 确认所有动态效果正常
