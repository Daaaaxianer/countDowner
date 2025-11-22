import tkinter as tk
from tkinter import font, ttk, colorchooser, messagebox
import time
import webbrowser
import sys  # 导入系统模块，用于跨平台系统判断
from PIL import Image, ImageTk
import os

class PPTCountdown:
    def __init__(self, root):
        self.root = root  # 主窗口对象
        self.is_paused = False  # 倒计时暂停状态标识
        self.is_stopped = False  # 倒计时停止状态标识
        self.drag_data = {"x": 0, "y": 0}  # 拖拽窗口的坐标缓存
        self.settings = None  # 存储参数设置窗口的配置结果
        
        # 尝试加载参数设置窗口，捕获异常并弹窗提示
        try:
            self.settings = self.show_settings_window()
        except Exception as e:
            messagebox.showerror("启动失败", f"设置窗口加载出错：{str(e)}")
            self.root.destroy()  # 异常时销毁主窗口
            return
        
        # 若未获取到设置（关闭设置窗口），则退出程序
        if not self.settings:
            self.root.destroy()
            return
        
        # 提取设置参数并初始化
        self.init_parameters()
        
        # 初始化倒计时窗口UI并显示
        self.init_ui()
        
        # 绑定窗口拖拽事件
        self.root.bind("<ButtonPress-1>", self.start_drag)  # 鼠标按下时触发拖拽开始
        self.root.bind("<B1-Motion>", self.do_drag)  # 鼠标拖动时触发拖拽执行
        self.root.bind("<ButtonRelease-1>", self.end_drag)  # 鼠标松开时触发拖拽结束
        self.root.bind("<Button-3>", self.show_right_menu)  # 右键触发菜单显示
        
        # 创建右键菜单
        self.create_right_menu()
        # 启动倒计时更新循环
        self.update_timer()

    def init_parameters(self):
        """提取设置参数并初始化倒计时变量"""
        self.total_minutes = self.settings['total']  # 总倒计时分钟数
        self.remind_minutes = self.settings['remind']  # 提醒时间分钟数
        self.warning_seconds = self.settings['warning']  # 最后警告秒数
        self.original_total_seconds = self.total_minutes * 60  # 总倒计时秒数（原始值，用于重置）
        
        # 颜色与透明度配置初始化
        self.normal_bg = self.settings['normal_bg']  # 正常状态背景色
        self.normal_bg_alpha = self.settings['normal_bg_alpha']  # 正常状态背景透明度
        self.normal_fg = self.settings['normal_fg']  # 正常状态文字色
        self.normal_fg_alpha = self.settings['normal_fg_alpha']  # 正常状态文字透明度
        
        self.remind_bg = self.settings['remind_bg']  # 提醒状态背景色
        self.remind_bg_alpha = self.settings['remind_bg_alpha']  # 提醒状态背景透明度
        self.remind_fg = self.settings['remind_fg']  # 提醒状态文字色
        self.remind_fg_alpha = self.settings['remind_fg_alpha']  # 提醒状态文字透明度
        
        self.warning_bg = self.settings['warning_bg']  # 警告状态背景色
        self.warning_bg_alpha = self.settings['warning_bg_alpha']  # 警告状态背景透明度
        self.warning_fg = self.settings['warning_fg']  # 警告状态文字色
        self.warning_fg_alpha = self.settings['warning_fg_alpha']  # 警告状态文字透明度
        
        # 字体大小配置
        self.timer_font_size = self.settings['timer_font_size']  # 倒计时数字字体大小
        self.timeout_text_size = self.settings['timeout_text_size']  # 超时文字字体大小
        
        # 超时显示配置
        self.timeout_mode = self.settings['timeout_mode']  # 超时模式：负计时/自定义文字
        self.timeout_text = self.settings['timeout_text']  # 超时自定义文字
        self.timeout_text_color = self.settings['timeout_text_color']  # 超时文字颜色
        
        # 倒计时实时变量初始化
        self.total_seconds = self.original_total_seconds  # 实时倒计时秒数
        self.remind_seconds = self.remind_minutes * 60  # 提醒时间秒数
        self.negative_seconds = 0  # 超时后负计时秒数

    def init_ui(self):
        """初始化倒计时窗口UI"""
        if not self.root.winfo_exists():  # 检查主窗口是否存在，避免操作无效窗口
            return
            
        # 配置字体：黑体、指定大小、加粗
        self.timer_font = font.Font(family="SimHei", size=self.timer_font_size, weight="bold")
        self.timeout_text_font = font.Font(family="SimHei", size=self.timeout_text_size, weight="bold")
        
        # 创建倒计时标签（核心显示控件）
        self.timer_label = tk.Label(
            self.root,
            text=self.format_time(self.total_seconds),  # 格式化初始时间
            font=self.timer_font,
            bg=self.normal_bg,
            fg=self.normal_fg
        )
        self.timer_label.pack(expand=True, fill=tk.BOTH)  # 填充整个窗口
        
        # 窗口基础配置
        self.root.title("PPT倒计时")  # 窗口标题
        self.root.geometry("300x100")  # 窗口大小：宽300px，高100px
        self.root.attributes("-topmost", True)  # 窗口置顶
        self.root.overrideredirect(True)  # 隐藏窗口边框和标题栏（实现无边框拖拽）
        
        # 显示主窗口（设置确认后从隐藏变为显示）
        self.root.deiconify()

    def choose_color(self, current_color, title):
        """颜色选择器封装：返回选择的十六进制颜色值"""
        color = colorchooser.askcolor(title=title, initialcolor=current_color)  # 打开系统颜色选择器
        return color[1] if color[1] else current_color  # 选择失败则返回原颜色

    def show_settings_window(self):
        """显示参数设置窗口，返回用户配置的参数字典"""
        # 默认配置参数（用户未修改时使用）
        default = {
            'total': 10, 'remind': 2, 'warning': 30,
            'normal_bg': "#bdc3c7", 'normal_bg_alpha': 60,
            'normal_fg': "#3399ff", 'normal_fg_alpha': 100,
            'remind_bg': "#bdc3c7", 'remind_bg_alpha': 60,
            'remind_fg': "#EEEE00", 'remind_fg_alpha': 100,
            'warning_bg': "#EEEE00", 'warning_bg_alpha': 60,
            'warning_fg': "#ff0000", 'warning_fg_alpha': 100,
            'timer_font_size': 60,
            'timeout_mode': 'negative', 'timeout_text': "时间到！",
            'timeout_text_size': 60, 'timeout_text_color': "#ff0000"
        }
        
        # 创建设置窗口（顶层窗口，独立于主窗口）
        settings_window = tk.Toplevel(self.root)
        settings_window.title("参数设置")  # 设置窗口标题
        settings_window.geometry("750x800")  # 设置窗口大小
        settings_window.resizable(False, False)  # 禁止窗口缩放
        
        # 核心窗口属性配置（保证最小化按钮有效）
        settings_window.attributes("-toolwindow", False)  # 强制为普通窗口（显示系统标题栏）
        settings_window.attributes("-topmost", True)  # 窗口置顶（替代grab_set，避免阻塞系统操作）
        # 跨平台兼容：仅Linux系统设置窗口类型为普通，Windows忽略该属性
        if sys.platform == "linux":
            settings_window.attributes("-type", "normal")
        
        # 窗口关闭状态标识：用于判断用户是确认还是关闭窗口
        self.settings_closed = False
        def on_close():
            self.settings_closed = True  # 标记为主动关闭
            settings_window.destroy()  # 销毁设置窗口
        settings_window.protocol("WM_DELETE_WINDOW", on_close)  # 绑定关闭事件
        
        # ########## 变量定义：与UI控件绑定的动态变量 ##########
        total_var = tk.IntVar(value=default['total'])  # 总时间变量
        remind_var = tk.IntVar(value=default['remind'])  # 提醒时间变量
        warning_var = tk.IntVar(value=default['warning'])  # 警告时间变量
        
        # 颜色变量（StringVar存储十六进制颜色值）
        normal_bg_var = tk.StringVar(value=default['normal_bg'])
        normal_bg_alpha_var = tk.IntVar(value=default['normal_bg_alpha'])
        normal_fg_var = tk.StringVar(value=default['normal_fg'])
        normal_fg_alpha_var = tk.IntVar(value=default['normal_fg_alpha'])
        
        remind_bg_var = tk.StringVar(value=default['remind_bg'])
        remind_bg_alpha_var = tk.IntVar(value=default['remind_bg_alpha'])
        remind_fg_var = tk.StringVar(value=default['remind_fg'])
        remind_fg_alpha_var = tk.IntVar(value=default['remind_fg_alpha'])
        
        warning_bg_var = tk.StringVar(value=default['warning_bg'])
        warning_bg_alpha_var = tk.IntVar(value=default['warning_bg_alpha'])
        warning_fg_var = tk.StringVar(value=default['warning_fg'])
        warning_fg_alpha_var = tk.IntVar(value=default['warning_fg_alpha'])
        
        # 字体与超时配置变量
        timer_font_var = tk.IntVar(value=default['timer_font_size'])
        timeout_mode_var = tk.StringVar(value=default['timeout_mode'])
        timeout_text_var = tk.StringVar(value=default['timeout_text'])
        timeout_text_size_var = tk.IntVar(value=default['timeout_text_size'])
        timeout_text_color_var = tk.StringVar(value=default['timeout_text_color'])
        
        # ########## 时间验证函数：保证输入的时间逻辑合理 ##########
        def validate_remind(*args):
            """验证提醒时间：不能大于等于总时间"""
            try:
                total = total_var.get()
                remind = remind_var.get()
                if remind >= total:
                    remind_var.set(total - 1 if total > 1 else 1)  # 修正为合理值
            except:
                pass
        
        def validate_warning(*args):
            """验证警告时间：不能大于提醒时间的总秒数"""
            try:
                remind = remind_var.get()
                warning = warning_var.get()
                max_warning = remind * 60  # 提醒时间的总秒数
                if warning > max_warning:
                    warning_var.set(max_warning)  # 修正为合理值
            except:
                pass
        
        # 绑定变量追踪：变量值变化时触发验证
        total_var.trace_add("write", validate_remind)
        remind_var.trace_add("write", validate_remind)
        remind_var.trace_add("write", validate_warning)
        warning_var.trace_add("write", validate_warning)
        
        # 存储自定义文字区域控件：用于禁用/启用控件
        text_controls = []
        def update_timeout_frame_state():
            """根据超时模式，启用/禁用自定义文字控件"""
            state = 'normal' if timeout_mode_var.get() == 'text' else 'disabled'
            for control in text_controls:
                control.config(state=state)
        
        # ########## 时间设置区域UI ##########
        ttk.Label(settings_window, text="时间设置", font=("SimHei", 12, "bold")).pack(pady=10)
        time_frame = ttk.Frame(settings_window)
        time_frame.pack(fill=tk.X, padx=30)
        
        ttk.Label(time_frame, text="总计时间（分钟）：", width=20).grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Spinbox(time_frame, from_=1, to=60, textvariable=total_var, width=5).grid(row=0, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(time_frame, text="提醒时间（分钟）：", width=20).grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Spinbox(time_frame, from_=1, to=59, textvariable=remind_var, width=5).grid(row=1, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(time_frame, text="警告时间（秒）：", width=20).grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Spinbox(time_frame, from_=1, to=59, textvariable=warning_var, width=5).grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # ########## 阶段样式设置区域UI（复用函数） ##########
        ttk.Label(settings_window, text="\n阶段样式设置", font=("SimHei", 12, "bold")).pack(pady=5)
        
        def create_stage_frame(parent, stage_name, bg_var, bg_alpha_var, fg_var, fg_alpha_var):
            """创建阶段样式设置的复用框架：减少重复代码"""
            ttk.Label(parent, text=stage_name, font=("SimHei", 10)).pack(anchor=tk.W, padx=30)
            frame = ttk.Frame(parent)
            frame.pack(fill=tk.X, padx=30, pady=5)
            
            # 背景色设置
            ttk.Label(frame, text="背景色：", width=7).grid(row=0, column=0, sticky=tk.W, padx=(0,3))
            bg_btn = ttk.Button(frame, text="选择", width=5,command=lambda: bg_var.set(self.choose_color(bg_var.get(), f"{stage_name}背景色")))
            bg_btn.grid(row=0, column=1, padx=(0,3))
            bg_code = ttk.Label(frame, textvariable=bg_var, width=8, borderwidth=1, relief="solid")
            bg_code.grid(row=0, column=2, padx=(0,10))
            
            # 背景透明度设置
            ttk.Label(frame, text="背景透明度(%)：", width=12).grid(row=0, column=3, sticky=tk.W)
            ttk.Spinbox(frame, from_=0, to=100, textvariable=bg_alpha_var, width=5).grid(row=0, column=4, padx=(0,20))
            
            # 文字色设置
            ttk.Label(frame, text="文字色：", width=7).grid(row=0, column=5, sticky=tk.W, padx=(0,3))
            fg_btn = ttk.Button(frame, text="选择", width=5,command=lambda: fg_var.set(self.choose_color(fg_var.get(), f"{stage_name}文字色")))
            fg_btn.grid(row=0, column=6, padx=(0,3))
            fg_code = ttk.Label(frame, textvariable=fg_var, width=8, borderwidth=1, relief="solid")
            fg_code.grid(row=0, column=7, padx=(0,10))
            
            # 文字透明度设置
            ttk.Label(frame, text="文字透明度(%)：", width=12).grid(row=0, column=8, sticky=tk.W)
            ttk.Spinbox(frame, from_=0, to=100, textvariable=fg_alpha_var, width=5).grid(row=0, column=9, padx=5)
            
            return bg_code, fg_code
        
        # 创建三个阶段的样式框架
        normal_bg_code, normal_fg_code = create_stage_frame(settings_window, "正常阶段", normal_bg_var, normal_bg_alpha_var, normal_fg_var, normal_fg_alpha_var)
        remind_bg_code, remind_fg_code = create_stage_frame(settings_window, "提醒阶段", remind_bg_var, remind_bg_alpha_var, remind_fg_var, remind_fg_alpha_var)
        warning_bg_code, warning_fg_code = create_stage_frame(settings_window, "警告阶段", warning_bg_var, warning_bg_alpha_var, warning_fg_var, warning_fg_alpha_var)
        
        # ########## 字体设置区域UI ##########
        ttk.Label(settings_window, text="\n倒计时字体设置", font=("SimHei", 12, "bold")).pack(pady=10)
        font_frame = ttk.Frame(settings_window)
        font_frame.pack(fill=tk.X, padx=30)
        ttk.Label(font_frame, text="倒计时数字大小：", width=20).grid(row=0, column=0, sticky=tk.W)
        ttk.Spinbox(font_frame, from_=10, to=60, textvariable=timer_font_var, width=5).grid(row=0, column=1, sticky=tk.W)
        
        # ########## 超时显示设置区域UI ##########
        ttk.Label(settings_window, text="\n超时显示设置", font=("SimHei", 12, "bold")).pack(pady=5)
        frame8 = ttk.Frame(settings_window)
        frame8.pack(fill=tk.X, padx=30)
        
        # 超时模式单选按钮
        ttk.Radiobutton(frame8, text="负计时（显示-00:00及以上）", variable=timeout_mode_var, value='negative', command=update_timeout_frame_state).pack(anchor=tk.W)
        ttk.Radiobutton(frame8, text="显示自定义文字", variable=timeout_mode_var, value='text', command=update_timeout_frame_state).pack(anchor=tk.W, pady=2)
        
        # 自定义文字设置框架
        timeout_text_frame = ttk.LabelFrame(settings_window, text="自定义文字设置")
        timeout_text_frame.pack(fill=tk.X, padx=30, pady=5)
        
        # 自定义文字内容
        ttk.Label(timeout_text_frame, text="文字内容：", width=15).grid(row=0, column=0, sticky=tk.W, padx=5, pady=3)
        text_entry = ttk.Entry(timeout_text_frame, textvariable=timeout_text_var, width=20)
        text_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=3)
        text_controls.append(text_entry)
        
        # 自定义文字大小
        ttk.Label(timeout_text_frame, text="文字大小：", width=15).grid(row=1, column=0, sticky=tk.W, padx=5, pady=3)
        size_spin = ttk.Spinbox(timeout_text_frame, from_=10, to=60, textvariable=timeout_text_size_var, width=5)
        size_spin.grid(row=1, column=1, sticky=tk.W, padx=5, pady=3)
        text_controls.append(size_spin)
        
        # 自定义文字颜色
        ttk.Label(timeout_text_frame, text="文字颜色：", width=15).grid(row=2, column=0, sticky=tk.W, padx=5, pady=3)
        color_frame = ttk.Frame(timeout_text_frame)
        color_frame.grid(row=2, column=1, sticky=tk.W, pady=3)
        color_btn = ttk.Button(color_frame, text="选择", width=5, command=lambda: timeout_text_color_var.set(self.choose_color(timeout_text_color_var.get(), "超时文字颜色")))
        color_btn.grid(row=0, column=0, padx=0)
        text_controls.append(color_btn)
        color_code_label = ttk.Label(color_frame, textvariable=timeout_text_color_var, width=8, borderwidth=1, relief="solid")
        color_code_label.grid(row=0, column=1, padx=5)
        
        # 实时更新颜色预览块背景
        def update_timeout_color(*args):
            color_code_label.config(background=timeout_text_color_var.get())
        timeout_text_color_var.trace_add("write", update_timeout_color)
        update_timeout_color()  # 初始化颜色预览
        
        # ########## 确认按钮 ##########
        def on_confirm():
            """确认按钮事件：销毁设置窗口，返回配置参数"""
            settings_window.destroy()
        ttk.Button(settings_window, text="确认", command=on_confirm).pack(pady=15)
        
        # ########## 底部信息区域 ##########
        bottom_frame = ttk.Frame(settings_window)
        bottom_frame.pack(fill=tk.X, padx=30, pady=20)
        
        # 版权信息
        copyright_label = ttk.Label(bottom_frame, text="Copyright ©xian. All rights reserved.", font=("SimHei", 9))
        copyright_label.pack(pady=(0, 5))
        
        # GitHub链接（文字按钮，无图片依赖）
        github_frame = ttk.Frame(bottom_frame)
        github_frame.pack(pady=5)
        github_btn = ttk.Button(github_frame, text="countDowner", command=lambda: webbrowser.open("https://github.com/Daaaaxianer/countDowner"))
        github_btn.pack(side=tk.LEFT, padx=5)
        extra_label = ttk.Label(github_frame, text="倒计时工具 | 简洁高效", font=("SimHei", 9))
        extra_label.pack(side=tk.LEFT)
        
        # ########## 颜色预览块实时更新 ##########
        def update_color_code_bg(*args):
            """实时更新颜色编码标签的背景色，直观预览"""
            normal_bg_code.config(background=normal_bg_var.get())
            normal_fg_code.config(background=normal_fg_var.get())
            remind_bg_code.config(background=remind_bg_var.get())
            remind_fg_code.config(background=remind_fg_var.get())
            warning_bg_code.config(background=warning_bg_var.get())
            warning_fg_code.config(background=warning_fg_var.get())
        
        # 绑定颜色变量追踪
        normal_bg_var.trace_add("write", update_color_code_bg)
        normal_fg_var.trace_add("write", update_color_code_bg)
        remind_bg_var.trace_add("write", update_color_code_bg)
        remind_fg_var.trace_add("write", update_color_code_bg)
        warning_bg_var.trace_add("write", update_color_code_bg)
        warning_fg_var.trace_add("write", update_color_code_bg)
        
        update_color_code_bg()  # 初始化颜色预览
        update_timeout_frame_state()  # 初始化自定义文字控件状态
        
        # 等待设置窗口关闭后，再执行后续逻辑
        self.root.wait_window(settings_window)
        
        # 若用户主动关闭窗口，返回None
        if self.settings_closed:
            return None
        
        # 整理用户配置并返回字典
        return {
            'total': total_var.get(),
            'remind': min(remind_var.get(), total_var.get() - 1),
            'warning': min(warning_var.get(), remind_var.get() * 60),
            'normal_bg': normal_bg_var.get(),
            'normal_bg_alpha': normal_bg_alpha_var.get() / 100,  # 转换为0-1的透明度值
            'normal_fg': normal_fg_var.get(),
            'normal_fg_alpha': normal_fg_alpha_var.get() / 100,
            'remind_bg': remind_bg_var.get(),
            'remind_bg_alpha': remind_bg_alpha_var.get() / 100,
            'remind_fg': remind_fg_var.get(),
            'remind_fg_alpha': remind_fg_alpha_var.get() / 100,
            'warning_bg': warning_bg_var.get(),
            'warning_bg_alpha': warning_bg_alpha_var.get() / 100,
            'warning_fg': warning_fg_var.get(),
            'warning_fg_alpha': warning_fg_alpha_var.get() / 100,
            'timer_font_size': timer_font_var.get(),
            'timeout_mode': timeout_mode_var.get(),
            'timeout_text': timeout_text_var.get(),
            'timeout_text_size': timeout_text_size_var.get(),
            'timeout_text_color': timeout_text_color_var.get()
        }

    def create_right_menu(self):
        """创建右键菜单：包含倒计时的核心操作"""
        self.right_menu = tk.Menu(self.root, tearoff=0)  # tearoff=0 禁用菜单分离
        self.right_menu.add_command(label="重置", command=self.reset_timer)  # 重置倒计时
        self.right_menu.add_command(label="暂停/继续", command=self.pause_timer)  # 暂停/继续切换
        self.right_menu.add_command(label="停止", command=self.stop_timer)  # 停止倒计时
        self.right_menu.add_command(label="关闭", command=self.close_window)  # 关闭程序

    def show_right_menu(self, event):
        """显示右键菜单：在鼠标右键点击位置弹出"""
        try:
            self.right_menu.tk_popup(event.x_root, event.y_root)  # 在鼠标坐标处弹出菜单
        finally:
            self.right_menu.grab_release()  # 释放菜单焦点

    def start_drag(self, event):
        """拖拽开始：记录鼠标相对于窗口的初始坐标"""
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    def do_drag(self, event):
        """拖拽执行：计算窗口新坐标并移动"""
        dx = event.x - self.drag_data["x"]  # x轴偏移量
        dy = event.y - self.drag_data["y"]  # y轴偏移量
        x = self.root.winfo_x() + dx  # 窗口新x坐标
        y = self.root.winfo_y() + dy  # 窗口新y坐标
        self.root.geometry(f"+{x}+{y}")  # 移动窗口

    def end_drag(self, event):
        """拖拽结束：清空坐标缓存"""
        self.drag_data["x"] = 0
        self.drag_data["y"] = 0

    def reset_timer(self):
        """重置倒计时：恢复为初始总时间，重置状态"""
        self.is_paused = False
        self.is_stopped = False
        self.total_seconds = self.original_total_seconds  # 恢复原始总秒数
        self.negative_seconds = 0  # 重置负计时
        self.update_style()  # 更新样式为正常状态
        self.timer_label.config(text=self.format_time(self.total_seconds))  # 更新显示

    def pause_timer(self):
        """暂停/继续倒计时：切换暂停状态"""
        self.is_paused = not self.is_paused

    def stop_timer(self):
        """停止倒计时：设置停止状态，冻结显示"""
        self.is_stopped = True
        self.is_paused = False  # 同步暂停状态

    def close_window(self):
        """关闭程序：销毁主窗口"""
        self.root.destroy()

    def format_time(self, seconds):
        """时间格式化：将秒数转换为 MM:SS 格式"""
        mins = seconds // 60  # 分钟数：总秒数整除60
        secs = seconds % 60   # 秒数：总秒数取余60
        return f"{mins:02d}:{secs:02d}"  # 补零为两位数字

    def update_style(self):
        """更新倒计时样式：根据剩余时间切换正常/提醒/警告状态"""
        if self.total_seconds <= self.warning_seconds:
            # 警告状态：应用警告样式
            self.timer_label.config(bg=self.warning_bg, fg=self.warning_fg)
            self.root.configure(bg=self.warning_bg)
            self.root.attributes("-alpha", self.warning_bg_alpha)
        elif self.total_seconds <= self.remind_seconds:
            # 提醒状态：应用提醒样式
            self.timer_label.config(bg=self.remind_bg, fg=self.remind_fg)
            self.root.configure(bg=self.remind_bg)
            self.root.attributes("-alpha", self.remind_bg_alpha)
        else:
            # 正常状态：应用正常样式
            self.timer_label.config(bg=self.normal_bg, fg=self.normal_fg)
            self.root.configure(bg=self.normal_bg)
            self.root.attributes("-alpha", self.normal_bg_alpha)

    def update_timer(self):
        """倒计时核心更新循环：每秒执行一次，实现倒计时效果"""
        if self.is_stopped or not self.root.winfo_exists():  # 停止或窗口销毁则退出循环
            return
        
        if not self.is_paused:  # 未暂停时更新倒计时
            if self.total_seconds >= 0:
                self.update_style()  # 更新样式
                self.timer_label.config(text=self.format_time(self.total_seconds))  # 更新显示
                self.total_seconds -= 1  # 秒数减1
            else:
                # 超时后处理：负计时或自定义文字
                self.root.configure(bg=self.warning_bg)
                self.root.attributes("-alpha", self.warning_bg_alpha)
                if self.timeout_mode == 'negative':
                    self.negative_seconds += 1  # 负计时秒数加1
                    self.timer_label.config(text=f"-{self.format_time(self.negative_seconds)}", fg=self.warning_fg, bg=self.warning_bg)
                else:
                    self.timer_label.config(text=self.timeout_text, font=self.timeout_text_font, fg=self.timeout_text_color, bg=self.warning_bg)
        
        # 递归调用：1000毫秒（1秒）后再次执行，实现循环
        self.root.after(1000, self.update_timer)

if __name__ == "__main__":
    # 主程序入口：初始化主窗口并隐藏，仅显示设置窗口
    root = tk.Tk()  # 创建tkinter主窗口
    root.withdraw()  # 隐藏主窗口
    root.update_idletasks()  # 刷新事件循环，避免窗口状态异常
    app = PPTCountdown(root)  # 实例化倒计时类
    root.mainloop()  # 启动tkinter事件循环