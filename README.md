# countDowner
countDowner - 轻量高效的 汇报展示 倒计时工具

A lightweight, customizable countdown timer designed for presentations (PPT/Keynote), with a clean UI and flexible configuration options.

## ✨ 核心功能

参数自定义：支持设置总时长、提醒时间、警告时间，满足不同演讲场景需求

多阶段样式：正常 / 提醒 / 警告三阶段独立配置背景色、文字色及透明度，视觉区分清晰

超时灵活处理：支持负计时显示或自定义超时文字，适配不同演示节奏

便捷操作：窗口置顶、鼠标拖拽移动、右键菜单（重置 / 暂停 / 继续 / 关闭）

无终端运行：打包后双击即可启动，无需依赖 Python 环境，不干扰演示流程

## 🚀 快速开始

* 方式 1：直接运行（需 Python 环境）

安装依赖：pip install pillow tkinter

下载源码：git clone https://github.com/你的用户名/countDowner.git

启动程序：python countDowner.py 或直接双击脚本（Windows 建议用pythonw.exe关联以隐藏终端）

* 方式 2：下载可执行文件（无需 Python 环境）
* 
前往 Releases 下载对应系统的打包版本（Windows/macOS/Linux），双击即可运行。

## ⚙️ 配置说明

启动后自动弹出参数设置窗口，支持以下配置：

时间设置：总倒计时（1-60 分钟）、提醒时间（1-59 分钟）、警告时间（1-59 秒）

样式设置：三阶段独立的背景色、文字色及透明度（0%-100%）

字体设置：倒计时数字大小（10-60 号）、超时文字大小（10-60 号）

超时设置：负计时模式或自定义文字模式（支持颜色配置）

## 🎨 使用场景

课堂演示 / 学术报告：精准控制演讲时长，避免超时

会议发言：提醒发言人时间进度，提升会议效率

培训教学：分阶段提示教学环节，把控课堂节奏

## 🛠️ 技术栈

语言：Python 3.8+

框架：tkinter（UI）、Pillow（图片处理）

打包：PyInstaller（支持跨平台打包）
