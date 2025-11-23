import tkinter as tk
from tkinter import font, ttk, colorchooser, messagebox
import time
import webbrowser
import sys  # 跨平台系统判断+打包后路径兼容
import os  # 处理文件路径，获取ICO图标路径

def get_resource_path(relative_path):
    """
    适配PyInstaller打包后的资源路径
    :param relative_path: 资源的相对路径（如 "images/countDowner128.ico"）
    :return: 打包后/开发模式下的绝对路径
    """
    if hasattr(sys, '_MEIPASS'):
        # 打包后，PyInstaller会将资源解压到临时目录_MEIPASS
        base_path = sys._MEIPASS
    else:
        # 开发模式，使用脚本所在目录作为基准
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

class PPTCountdown:
    def __init__(self, root, ico_path):
        # 传入处理后的自定义图标路径
        self.root = root  # 主窗口对象
        self.ico_path = ico_path  # 保存自定义图标路径
        self.is_paused = False  # 倒计时暂停状态
        self.is_stopped = False  # 倒计时停止状态
        self.drag_x = 0  # 拖拽窗口的x坐标缓存
        self.drag_y = 0  # 拖拽窗口的y坐标缓存
        self.settings = None  # 存储参数设置窗口的配置结果
        self.after_id = None  # 倒计时循环的after任务ID
        self.right_menu = None  # 右键菜单对象，懒加载创建

        # 为主窗口设置自定义图标
        self._set_window_icon(self.root)

        # 尝试加载参数设置窗口，捕获异常并弹窗提示
        try:
            self.settings = self.show_settings_window()
        except Exception as e:
            messagebox.showerror("启动失败", f"设置窗口加载出错：{str(e)}")
            self.root.destroy()
            return

        # 未获取到设置则退出程序
        if not self.settings:
            self.root.destroy()
            return

        # 提取设置参数并初始化
        self.init_parameters()
        # 初始化倒计时窗口UI
        self.init_ui()
        # 绑定窗口事件
        self._bind_events()
        # 启动倒计时更新循环
        self.update_timer()

    def _set_window_icon(self, window):
        """封装窗口图标设置逻辑，增加异常捕获（跨平台兼容）"""
        if os.path.exists(self.ico_path):  # 检查图标文件是否存在
            try:
                # Windows下设置ICO图标，Linux/Mac可能不支持，需捕获异常
                window.iconbitmap(self.ico_path)
            except Exception as e:
                # 非Windows系统或图标格式不支持时，仅打印日志不崩溃
                print(f"设置窗口图标失败（跨平台兼容）：{str(e)}")
        else:
            print(f"自定义图标文件不存在：{self.ico_path}")

    def init_parameters(self):
        """提取设置参数并初始化倒计时核心变量"""
        # 基础时间参数
        self.total_minutes = self.settings['total']  # 总倒计时分钟数
        self.remind_minutes = self.settings['remind']  # 提醒时间分钟数
        self.warning_seconds = self.settings['warning']  # 最后警告秒数
        self.original_total_seconds = self.total_minutes * 60  # 原始总秒数（用于重置）

        # 颜色与透明度配置（已在设置窗口转换为0-1的透明度值）
        self.normal_bg = self.settings['normal_bg']
        self.normal_bg_alpha = self.settings['normal_bg_alpha']
        self.normal_fg = self.settings['normal_fg']
        self.normal_fg_alpha = self.settings['normal_fg_alpha']

        self.remind_bg = self.settings['remind_bg']
        self.remind_bg_alpha = self.settings['remind_bg_alpha']
        self.remind_fg = self.settings['remind_fg']
        self.remind_fg_alpha = self.settings['remind_fg_alpha']

        self.warning_bg = self.settings['warning_bg']
        self.warning_bg_alpha = self.settings['warning_bg_alpha']
        self.warning_fg = self.settings['warning_fg']
        self.warning_fg_alpha = self.settings['warning_fg_alpha']

        # 字体大小配置
        self.timer_font_size = self.settings['timer_font_size']
        self.timeout_text_size = self.settings['timeout_text_size']

        # 超时显示配置
        self.timeout_mode = self.settings['timeout_mode']
        self.timeout_text = self.settings['timeout_text']
        self.timeout_text_color = self.settings['timeout_text_color']

        # 倒计时实时变量
        self.total_seconds = self.original_total_seconds  # 实时倒计时秒数
        self.remind_seconds = self.remind_minutes * 60  # 提醒时间秒数
        self.negative_seconds = 0  # 超时后负计时秒数

    def init_ui(self):
        """初始化倒计时窗口UI（核心显示控件）"""
        if not self.root.winfo_exists():  # 避免操作已销毁的窗口
            return

        # 配置字体：黑体、指定大小、加粗（提前创建避免重复实例化）
        self.timer_font = font.Font(family="SimHei", size=self.timer_font_size, weight="bold")
        self.timeout_text_font = font.Font(family="SimHei", size=self.timeout_text_size, weight="bold")

        # 创建倒计时核心显示标签
        self.timer_label = tk.Label(
            self.root,
            text=self.format_time(self.total_seconds),  # 格式化初始时间
            font=self.timer_font,
            bg=self.normal_bg,
            fg=self.normal_fg
        )
        self.timer_label.pack(expand=True, fill=tk.BOTH)  # 填充整个窗口

        # 窗口基础配置（一次性设置，减少tkinter调用次数）
        self.root.title("PPT倒计时")
        self.root.geometry("300x100")
        self.root.attributes("-topmost", True)  # 窗口置顶
        self.root.overrideredirect(True)  # 隐藏边框，实现无边框拖拽
        self.root.deiconify()  # 显示主窗口

    def _bind_events(self):
        """统一绑定窗口事件（代码聚合，便于维护）"""
        self.root.bind("<ButtonPress-1>", self.start_drag)  # 拖拽开始
        self.root.bind("<B1-Motion>", self.do_drag)  # 拖拽执行
        self.root.bind("<ButtonRelease-1>", self.end_drag)  # 拖拽结束
        self.root.bind("<Button-3>", self.show_right_menu)  # 右键菜单

    def choose_color(self, current_color, title):
        """颜色选择器封装：返回选择的十六进制颜色值"""
        color = colorchooser.askcolor(title=title, initialcolor=current_color)
        return color[1] if color[1] else current_color  # 选择失败返回原颜色

    def show_settings_window(self):
        """显示参数设置窗口（主方法），拆分子方法减少冗余"""
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

        # 创建设置窗口（顶层窗口）
        settings_window = tk.Toplevel(self.root)
        settings_window.title("参数设置")
        settings_window.geometry("750x800")
        settings_window.resizable(False, False)
        settings_window.attributes("-topmost", True)  # 窗口置顶
        if sys.platform == "linux":  # 跨平台兼容：Linux下设置为普通窗口
            settings_window.attributes("-type", "normal")

        # 为设置窗口设置自定义图标
        self._set_window_icon(settings_window)

        # 窗口关闭状态标识（局部变量，替代实例变量，减少内存占用）
        settings_closed = [False]  # 用列表实现可变对象传递
        def on_close():
            settings_closed[0] = True
            settings_window.destroy()
        settings_window.protocol("WM_DELETE_WINDOW", on_close)

        # 初始化设置窗口的变量（统一管理）
        vars_dict = self._init_settings_vars(default)
        # 创建时间设置框架
        self._create_time_frame(settings_window, vars_dict)
        # 创建阶段样式设置框架
        style_labels = self._create_style_frames(settings_window, vars_dict)
        # 创建字体设置框架
        self._create_font_frame(settings_window, vars_dict)
        # 创建超时显示设置框架
        self._create_timeout_frame(settings_window, vars_dict)
        # 创建确认按钮
        self._create_confirm_btn(settings_window)
        # 创建底部信息框架
        self._create_bottom_frame(settings_window)
        # 绑定颜色预览更新事件
        self._bind_color_preview(settings_window, vars_dict, style_labels)

        # 等待设置窗口关闭
        self.root.wait_window(settings_window)
        if settings_closed[0]:  # 用户主动关闭窗口，返回None
            return None

        # 整理配置并返回（自动修正参数逻辑，避免无效值）
        return self._get_settings_result(vars_dict)

    def _init_settings_vars(self, default):
        """初始化设置窗口的变量（拆分子方法，减少主方法长度）"""
        vars_dict = {}
        # 时间变量
        vars_dict['total'] = tk.IntVar(value=default['total'])
        vars_dict['remind'] = tk.IntVar(value=default['remind'])
        vars_dict['warning'] = tk.IntVar(value=default['warning'])
        # 正常阶段颜色/透明度变量
        vars_dict['normal_bg'] = tk.StringVar(value=default['normal_bg'])
        vars_dict['normal_bg_alpha'] = tk.IntVar(value=default['normal_bg_alpha'])
        vars_dict['normal_fg'] = tk.StringVar(value=default['normal_fg'])
        vars_dict['normal_fg_alpha'] = tk.IntVar(value=default['normal_fg_alpha'])
        # 提醒阶段颜色/透明度变量
        vars_dict['remind_bg'] = tk.StringVar(value=default['remind_bg'])
        vars_dict['remind_bg_alpha'] = tk.IntVar(value=default['remind_bg_alpha'])
        vars_dict['remind_fg'] = tk.StringVar(value=default['remind_fg'])
        vars_dict['remind_fg_alpha'] = tk.IntVar(value=default['remind_fg_alpha'])
        # 警告阶段颜色/透明度变量
        vars_dict['warning_bg'] = tk.StringVar(value=default['warning_bg'])
        vars_dict['warning_bg_alpha'] = tk.IntVar(value=default['warning_bg_alpha'])
        vars_dict['warning_fg'] = tk.StringVar(value=default['warning_fg'])
        vars_dict['warning_fg_alpha'] = tk.IntVar(value=default['warning_fg_alpha'])
        # 字体与超时变量
        vars_dict['timer_font'] = tk.IntVar(value=default['timer_font_size'])
        vars_dict['timeout_mode'] = tk.StringVar(value=default['timeout_mode'])
        vars_dict['timeout_text'] = tk.StringVar(value=default['timeout_text'])
        vars_dict['timeout_text_size'] = tk.IntVar(value=default['timeout_text_size'])
        vars_dict['timeout_text_color'] = tk.StringVar(value=default['timeout_text_color'])
        return vars_dict

    def _create_time_frame(self, parent, vars_dict):
        """创建时间设置框架（拆分子方法）"""
        ttk.Label(parent, text="时间设置", font=("SimHei", 12, "bold")).pack(pady=10)
        time_frame = ttk.Frame(parent)
        time_frame.pack(fill=tk.X, padx=30)

        # 总计时间
        ttk.Label(time_frame, text="总计时间（分钟）：", width=20).grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Spinbox(time_frame, from_=1, to=60, textvariable=vars_dict['total'], width=5).grid(row=0, column=1, sticky=tk.W, pady=5)
        # 提醒时间
        ttk.Label(time_frame, text="提醒时间（分钟）：", width=20).grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Spinbox(time_frame, from_=1, to=59, textvariable=vars_dict['remind'], width=5).grid(row=1, column=1, sticky=tk.W, pady=5)
        # 警告时间
        ttk.Label(time_frame, text="警告时间（秒）：", width=20).grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Spinbox(time_frame, from_=1, to=59, textvariable=vars_dict['warning'], width=5).grid(row=2, column=1, sticky=tk.W, pady=5)

        # 绑定时间验证事件（仅捕获ValueError，避免吞掉所有异常）
        def validate_remind(*args):
            try:
                total = vars_dict['total'].get()
                remind = vars_dict['remind'].get()
                if remind >= total:
                    vars_dict['remind'].set(total - 1 if total > 1 else 1)
            except ValueError:
                pass

        def validate_warning(*args):
            try:
                remind = vars_dict['remind'].get()
                warning = vars_dict['warning'].get()
                max_warning = remind * 60
                if warning > max_warning:
                    vars_dict['warning'].set(max_warning)
            except ValueError:
                pass

        vars_dict['total'].trace_add("write", validate_remind)
        vars_dict['remind'].trace_add("write", validate_remind)
        vars_dict['remind'].trace_add("write", validate_warning)
        vars_dict['warning'].trace_add("write", validate_warning)

    def _create_stage_frame(self, parent, stage_name, bg_var, bg_alpha_var, fg_var, fg_alpha_var):
        """创建单个阶段的样式框架（复用方法，减少冗余）"""
        ttk.Label(parent, text=stage_name, font=("SimHei", 10)).pack(anchor=tk.W, padx=30)
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, padx=30, pady=5)

        # 背景色设置
        ttk.Label(frame, text="背景色：", width=7).grid(row=0, column=0, sticky=tk.W, padx=(0,3))
        bg_btn = ttk.Button(frame, text="选择", width=5,
                            command=lambda: bg_var.set(self.choose_color(bg_var.get(), f"{stage_name}背景色")))
        bg_btn.grid(row=0, column=1, padx=(0,3))
        bg_code = ttk.Label(frame, textvariable=bg_var, width=8, borderwidth=1, relief="solid")
        bg_code.grid(row=0, column=2, padx=(0,10))

        # 背景透明度
        ttk.Label(frame, text="背景透明度(%)：", width=12).grid(row=0, column=3, sticky=tk.W)
        ttk.Spinbox(frame, from_=0, to=100, textvariable=bg_alpha_var, width=5).grid(row=0, column=4, padx=(0,20))

        # 文字色设置
        ttk.Label(frame, text="文字色：", width=7).grid(row=0, column=5, sticky=tk.W, padx=(0,3))
        fg_btn = ttk.Button(frame, text="选择", width=5,
                            command=lambda: fg_var.set(self.choose_color(fg_var.get(), f"{stage_name}文字色")))
        fg_btn.grid(row=0, column=6, padx=(0,3))
        fg_code = ttk.Label(frame, textvariable=fg_var, width=8, borderwidth=1, relief="solid")
        fg_code.grid(row=0, column=7, padx=(0,10))

        # 文字透明度
        ttk.Label(frame, text="文字透明度(%)：", width=12).grid(row=0, column=8, sticky=tk.W)
        ttk.Spinbox(frame, from_=0, to=100, textvariable=fg_alpha_var, width=5).grid(row=0, column=9, padx=5)

        return bg_code, fg_code

    def _create_style_frames(self, parent, vars_dict):
        """创建所有阶段的样式框架（拆分子方法）"""
        ttk.Label(parent, text="\n阶段样式设置", font=("SimHei", 12, "bold")).pack(pady=5)
        # 创建三个阶段的样式框架
        normal_bg_code, normal_fg_code = self._create_stage_frame(
            parent, "正常阶段", vars_dict['normal_bg'], vars_dict['normal_bg_alpha'],
            vars_dict['normal_fg'], vars_dict['normal_fg_alpha']
        )
        remind_bg_code, remind_fg_code = self._create_stage_frame(
            parent, "提醒阶段", vars_dict['remind_bg'], vars_dict['remind_bg_alpha'],
            vars_dict['remind_fg'], vars_dict['remind_fg_alpha']
        )
        warning_bg_code, warning_fg_code = self._create_stage_frame(
            parent, "警告阶段", vars_dict['warning_bg'], vars_dict['warning_bg_alpha'],
            vars_dict['warning_fg'], vars_dict['warning_fg_alpha']
        )
        # 返回颜色预览标签，用于后续绑定更新事件
        return {
            'normal': (normal_bg_code, normal_fg_code),
            'remind': (remind_bg_code, remind_fg_code),
            'warning': (warning_bg_code, warning_fg_code)
        }

    def _create_font_frame(self, parent, vars_dict):
        """创建字体设置框架（拆分子方法）"""
        ttk.Label(parent, text="\n倒计时字体设置", font=("SimHei", 12, "bold")).pack(pady=10)
        font_frame = ttk.Frame(parent)
        font_frame.pack(fill=tk.X, padx=30)
        ttk.Label(font_frame, text="倒计时数字大小：", width=20).grid(row=0, column=0, sticky=tk.W)
        ttk.Spinbox(font_frame, from_=10, to=60, textvariable=vars_dict['timer_font'], width=5).grid(row=0, column=1, sticky=tk.W)

    def _create_timeout_frame(self, parent, vars_dict):
        """创建超时显示设置框架（拆分子方法）"""
        ttk.Label(parent, text="\n超时显示设置", font=("SimHei", 12, "bold")).pack(pady=5)
        frame8 = ttk.Frame(parent)
        frame8.pack(fill=tk.X, padx=30)

        # 超时模式单选按钮
        def update_timeout_state():
            """更新自定义文字控件的启用/禁用状态"""
            state = 'normal' if vars_dict['timeout_mode'].get() == 'text' else 'disabled'
            for ctrl in timeout_controls:
                ctrl.config(state=state)

        ttk.Radiobutton(frame8, text="负计时（显示-00:00及以上）", variable=vars_dict['timeout_mode'],
                        value='negative', command=update_timeout_state).pack(anchor=tk.W)
        ttk.Radiobutton(frame8, text="显示自定义文字", variable=vars_dict['timeout_mode'],
                        value='text', command=update_timeout_state).pack(anchor=tk.W, pady=2)

        # 自定义文字设置框架
        timeout_text_frame = ttk.LabelFrame(parent, text="自定义文字设置")
        timeout_text_frame.pack(fill=tk.X, padx=30, pady=5)

        # 自定义文字内容
        ttk.Label(timeout_text_frame, text="文字内容：", width=15).grid(row=0, column=0, sticky=tk.W, padx=5, pady=3)
        text_entry = ttk.Entry(timeout_text_frame, textvariable=vars_dict['timeout_text'], width=20)
        text_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=3)

        # 自定义文字大小
        ttk.Label(timeout_text_frame, text="文字大小：", width=15).grid(row=1, column=0, sticky=tk.W, padx=5, pady=3)
        size_spin = ttk.Spinbox(timeout_text_frame, from_=10, to=60, textvariable=vars_dict['timeout_text_size'], width=5)
        size_spin.grid(row=1, column=1, sticky=tk.W, padx=5, pady=3)

        # 自定义文字颜色
        ttk.Label(timeout_text_frame, text="文字颜色：", width=15).grid(row=2, column=0, sticky=tk.W, padx=5, pady=3)
        color_frame = ttk.Frame(timeout_text_frame)
        color_frame.grid(row=2, column=1, sticky=tk.W, pady=3)
        color_btn = ttk.Button(color_frame, text="选择", width=5,
                               command=lambda: vars_dict['timeout_text_color'].set(
                                   self.choose_color(vars_dict['timeout_text_color'].get(), "超时文字颜色")
                               ))
        color_btn.grid(row=0, column=0, padx=0)
        color_code_label = ttk.Label(color_frame, textvariable=vars_dict['timeout_text_color'], width=8, borderwidth=1, relief="solid")
        color_code_label.grid(row=0, column=1, padx=5)

        # 保存需要控制状态的控件
        timeout_controls = [text_entry, size_spin, color_btn]
        # 绑定超时文字颜色预览更新
        def update_timeout_color(*args):
            color_code_label.config(background=vars_dict['timeout_text_color'].get())
        vars_dict['timeout_text_color'].trace_add("write", update_timeout_color)
        update_timeout_color()  # 初始化颜色预览
        update_timeout_state()  # 初始化控件状态

    def _create_confirm_btn(self, parent):
        """创建确认按钮（拆分子方法）"""
        def on_confirm():
            parent.destroy()
        ttk.Button(parent, text="确认", command=on_confirm).pack(pady=15)

    def _create_bottom_frame(self, parent):
        """创建底部信息框架（拆分子方法）"""
        bottom_frame = ttk.Frame(parent)
        bottom_frame.pack(fill=tk.X, padx=30, pady=20)

        # 版权信息
        copyright_label = ttk.Label(bottom_frame, text="Copyright ©xian. All rights reserved.", font=("SimHei", 9))
        copyright_label.pack(pady=(0, 5))

        # GitHub链接
        github_frame = ttk.Frame(bottom_frame)
        github_frame.pack(pady=5)
        github_btn = ttk.Button(github_frame, text="countDowner",
                                command=lambda: webbrowser.open("https://github.com/Daaaaxianer/countDowner"))
        github_btn.pack(side=tk.LEFT, padx=5)
        extra_label = ttk.Label(github_frame, text="倒计时工具 | 简洁高效", font=("SimHei", 9))
        extra_label.pack(side=tk.LEFT)

    def _bind_color_preview(self, parent, vars_dict, style_labels):
        """绑定颜色预览更新事件（拆分子方法）"""
        def update_color_preview(*args):
            """统一更新所有阶段的颜色预览"""
            # 正常阶段
            style_labels['normal'][0].config(background=vars_dict['normal_bg'].get())
            style_labels['normal'][1].config(background=vars_dict['normal_fg'].get())
            # 提醒阶段
            style_labels['remind'][0].config(background=vars_dict['remind_bg'].get())
            style_labels['remind'][1].config(background=vars_dict['remind_fg'].get())
            # 警告阶段
            style_labels['warning'][0].config(background=vars_dict['warning_bg'].get())
            style_labels['warning'][1].config(background=vars_dict['warning_fg'].get())

        # 绑定所有颜色变量的更新事件
        for color_key in ['normal_bg', 'normal_fg', 'remind_bg', 'remind_fg', 'warning_bg', 'warning_fg']:
            vars_dict[color_key].trace_add("write", update_color_preview)
        update_color_preview()  # 初始化颜色预览

    def _get_settings_result(self, vars_dict):
        """整理设置窗口的配置结果（拆分子方法）"""
        total = vars_dict['total'].get()
        remind = vars_dict['remind'].get()
        warning = vars_dict['warning'].get()
        # 自动修正参数，确保逻辑合理性
        remind = min(remind, total - 1) if total > 1 else 1
        warning = min(warning, remind * 60)
        # 返回配置字典（透明度转换为0-1的浮点数）
        return {
            'total': total,
            'remind': remind,
            'warning': warning,
            'normal_bg': vars_dict['normal_bg'].get(),
            'normal_bg_alpha': vars_dict['normal_bg_alpha'].get() / 100,
            'normal_fg': vars_dict['normal_fg'].get(),
            'normal_fg_alpha': vars_dict['normal_fg_alpha'].get() / 100,
            'remind_bg': vars_dict['remind_bg'].get(),
            'remind_bg_alpha': vars_dict['remind_bg_alpha'].get() / 100,
            'remind_fg': vars_dict['remind_fg'].get(),
            'remind_fg_alpha': vars_dict['remind_fg_alpha'].get() / 100,
            'warning_bg': vars_dict['warning_bg'].get(),
            'warning_bg_alpha': vars_dict['warning_bg_alpha'].get() / 100,
            'warning_fg': vars_dict['warning_fg'].get(),
            'warning_fg_alpha': vars_dict['warning_fg_alpha'].get() / 100,
            'timer_font_size': vars_dict['timer_font'].get(),
            'timeout_mode': vars_dict['timeout_mode'].get(),
            'timeout_text': vars_dict['timeout_text'].get(),
            'timeout_text_size': vars_dict['timeout_text_size'].get(),
            'timeout_text_color': vars_dict['timeout_text_color'].get()
        }

    def _create_right_menu(self):
        """懒加载创建右键菜单（首次右键时创建，减少初始化开销）"""
        self.right_menu = tk.Menu(self.root, tearoff=0)
        self.right_menu.add_command(label="重置", command=self.reset_timer)
        self.right_menu.add_command(label="暂停/继续", command=self.pause_timer)
        self.right_menu.add_command(label="停止", command=self.stop_timer)
        self.right_menu.add_command(label="关闭", command=self.close_window)

    def show_right_menu(self, event):
        """显示右键菜单（懒加载创建菜单）"""
        if not self.right_menu:
            self._create_right_menu()
        try:
            self.right_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.right_menu.grab_release()

    def start_drag(self, event):
        """拖拽开始：记录鼠标相对于窗口的初始坐标"""
        self.drag_x = event.x
        self.drag_y = event.y

    def do_drag(self, event):
        """拖拽执行：计算窗口新坐标并移动"""
        dx = event.x - self.drag_x
        dy = event.y - self.drag_y
        new_x = self.root.winfo_x() + dx
        new_y = self.root.winfo_y() + dy
        self.root.geometry(f"+{new_x}+{new_y}")

    def end_drag(self, event):
        """拖拽结束：清空坐标缓存"""
        self.drag_x = 0
        self.drag_y = 0

    def reset_timer(self):
        """重置倒计时：恢复初始状态"""
        self.is_paused = False
        self.is_stopped = False
        self.total_seconds = self.original_total_seconds
        self.negative_seconds = 0
        self.update_style()
        self.timer_label.config(text=self.format_time(self.total_seconds))

    def pause_timer(self):
        """暂停/继续倒计时：切换暂停状态"""
        self.is_paused = not self.is_paused

    def stop_timer(self):
        """停止倒计时：冻结显示"""
        self.is_stopped = True
        self.is_paused = False

    def close_window(self):
        """关闭程序：终止倒计时循环并销毁窗口"""
        if self.after_id:
            self.root.after_cancel(self.after_id)  # 终止倒计时循环，避免内存泄漏
        self.root.destroy()

    def format_time(self, seconds):
        """时间格式化：秒数转换为 MM:SS 格式"""
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins:02d}:{secs:02d}"

    def update_style(self):
        """更新倒计时样式：根据剩余时间切换正常/提醒/警告状态"""
        if self.total_seconds <= self.warning_seconds:
            # 警告状态
            self.timer_label.config(bg=self.warning_bg, fg=self.warning_fg)
            self.root.configure(bg=self.warning_bg)
            self.root.attributes("-alpha", self.warning_bg_alpha)
        elif self.total_seconds <= self.remind_seconds:
            # 提醒状态
            self.timer_label.config(bg=self.remind_bg, fg=self.remind_fg)
            self.root.configure(bg=self.remind_bg)
            self.root.attributes("-alpha", self.remind_bg_alpha)
        else:
            # 正常状态
            self.timer_label.config(bg=self.normal_bg, fg=self.normal_fg)
            self.root.configure(bg=self.normal_bg)
            self.root.attributes("-alpha", self.normal_bg_alpha)

    def update_timer(self):
        """倒计时核心更新循环：每秒执行一次"""
        if self.is_stopped or not self.root.winfo_exists():
            return

        if not self.is_paused:
            if self.total_seconds >= 0:
                self.update_style()
                self.timer_label.config(text=self.format_time(self.total_seconds))
                self.total_seconds -= 1
            else:
                # 超时后处理
                self.root.configure(bg=self.warning_bg)
                self.root.attributes("-alpha", self.warning_bg_alpha)
                if self.timeout_mode == 'negative':
                    self.negative_seconds += 1
                    self.timer_label.config(text=f"-{self.format_time(self.negative_seconds)}", fg=self.warning_fg, bg=self.warning_bg)
                else:
                    self.timer_label.config(text=self.timeout_text, font=self.timeout_text_font, fg=self.timeout_text_color, bg=self.warning_bg)

        # 递归调用倒计时循环，保存任务ID用于终止
        self.after_id = self.root.after(1000, self.update_timer)

if __name__ == "__main__":
    # 主程序入口：初始化主窗口并隐藏，仅显示设置窗口
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    root.update_idletasks()  # 刷新事件循环，避免窗口状态异常

    # 核心修改：使用兼容函数获取ICO路径（适配开发/打包后模式）
    ico_relative_path = "images\\countDowner128.ico"  # 图标相对路径
    ico_path = get_resource_path(ico_relative_path)  # 处理后的绝对路径

    # 可选：打印路径用于调试
    print(f"图标实际加载路径：{ico_path}")

    # 实例化时传入处理后的ICO路径
    app = PPTCountdown(root, ico_path)
    root.mainloop()