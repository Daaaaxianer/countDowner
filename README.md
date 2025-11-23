# countDowner

![countDowner 扁平化拟形图标](./images/countDowner128.ico) countDowner - 一款轻量 **汇报展示** 倒计时工具

A lightweight, customizable countdown timer designed for presentations (PPT/Keynote), with a clean UI and flexible configuration options.

一款轻量可自定义的倒计时工具，专为演示场景（PPT/Keynote）设计，具备简洁的用户界面和灵活的配置选项。

* 参数设置页面

<img width="937" height="1036" alt="image" src="https://github.com/user-attachments/assets/b253e1db-3fd6-4f76-b53b-c4b5b4ca5cff" />


* 正常/提醒/警告阶段示例

<img width="375" height="125" alt="image" src="https://github.com/user-attachments/assets/faaa0edf-2174-45f6-a477-83214550b64f" />
<img width="375" height="125" alt="image" src="https://github.com/user-attachments/assets/7f506713-bef3-47fe-b935-be044e7c13d5" />
<img width="375" height="125" alt="image" src="https://github.com/user-attachments/assets/be89153b-ea29-42f0-b5f5-90c4f3b4865d" />
<img width="375" height="125" alt="image" src="https://github.com/user-attachments/assets/9a9a3494-67af-4c67-8ded-9fa90cb6f5fc" />



## ✨ 核心功能

参数自定义：支持设置总时长、提醒时间、警告时间，满足不同演讲场景需求

多阶段样式：正常 / 提醒 / 警告三阶段独立配置背景色、文字色及透明度，视觉区分清晰

超时灵活处理：支持负计时显示或自定义超时文字，适配不同演示节奏

便捷操作：窗口置顶、鼠标拖拽移动、右键菜单（重置 / 暂停 / 继续 / 关闭）

无终端运行：打包后双击即可启动，无需依赖 Python 环境，不干扰演示流程

## 🚀 快速开始

* 方式 1：直接运行（需 Python 环境）

安装依赖：`pip install pillow tkinter`

下载源码：`git clone https://github.com/Daaaaxianer/countDowner.git`

启动程序：`python countDowner.py` 或直接双击脚本（Windows 建议用pythonw.exe关联以隐藏终端）

* 方式 2：下载可执行文件（无需 Python 环境）

前往 Releases 下载对应系统的打包版本（Windows/macOS/Linux），双击即可运行。

## ⚙️ 配置说明

启动后自动弹出参数设置窗口，支持以下配置：

时间设置：总倒计时（1-60 分钟）、提醒时间（1-59 分钟）、警告时间（1-59 秒）

样式设置：三阶段独立的背景色、文字色及透明度（0%-100%）

字体设置：倒计时数字大小（10-60 号）、超时文字大小（10-60 号）

超时设置：负计时模式或自定义文字模式（支持颜色配置）

## 🎨 使用场景

课堂演示/学术报告：精准控制演讲时长，避免超时

会议发言：提醒发言人时间进度，提升会议效率

培训教学：分阶段提示教学环节，把控课堂节奏

## 🛠️ 技术栈

语言：Python 3.8+

框架：tkinter（UI）、Pillow（图片处理）

打包：PyInstaller（支持跨平台打包）

## ✅ 注意事项

理论上支持 Windows/macOS/Linux 跨平台运行，打包时需在对应系统执行命令

若设置窗口最小化按钮失效，检查系统窗口管理器设置（默认支持标准窗口操作）

避免中文路径存放脚本或可执行文件，防止运行异常

## 📄 许可证

本项目基于 MIT 许可证开源，详见 LICENSE 文件。
