import tkinter as tk  # 导入 tkinter 库并重命名为 tk，用于图形界面开发
from tkinter import messagebox  # 从 tkinter 库中导入 messagebox 模块，用于弹出消息框
import time  # 导入 time 模块，用于处理时间相关的操作
import pandas as pd  # 导入 pandas 库并重命名为 pd，用于数据处理和分析
import os  # 导入 os 模块，用于文件和目录操作
import numpy as np  # 导入 numpy 库并重命名为 np，用于数值计算
import math  # 导入 math 模块，提供数学函数支持
import random  # 导入 random 模块，用于生成随机数
import colour  # 导入 colour 库，用于颜色转换操作（确保已安装该库）

# 定义颜色转换类，用于实现颜色格式之间的转换
class ColorConverter:
    @staticmethod
    def hex_to_rgb(hex_color):
        # 将十六进制颜色字符串转换为 RGB 格式
        hex_color = hex_color.lstrip('#')  # 去除颜色字符串前面的 '#' 符号
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))  # 每两位转换成十进制整数，返回 RGB 三元组

    @staticmethod
    def rgb_to_luv(r, g, b):
        # 将 RGB 颜色转换为 LUV 颜色空间中的 u, v 值
        rgb = [r / 255.0, g / 255.0, b / 255.0]  # 将 RGB 值归一化到 [0, 1] 范围
        xyz = colour.sRGB_to_XYZ(rgb)  # 将归一化的 RGB 转换为 XYZ 颜色空间
        luv = colour.XYZ_to_Luv(xyz)  # 将 XYZ 转换为 LUV 颜色空间
        return luv[1], luv[2]  # 返回 LUV 颜色空间中的 u 和 v 值

# 定义一个表示圆盘颜色的类，用于保存颜色信息及其在 LUV 空间中的 u, v 值
class DiscColor:
    def __init__(self, index, color):
        self.index = index  # 保存颜色在列表中的索引
        self.color = color  # 保存颜色数据（通常为 RGB 或十六进制颜色）
        self.u, self.v = ColorConverter.rgb_to_luv(*self.color)  # 将颜色转换为 LUV 空间的 u, v 值，并保存

# 定义一个向量类，用于计算两个颜色点之间在 LUV 空间的差值
class Vector:
    def __init__(self, spot0, spot1):
        self.u = spot1.u - spot0.u  # 计算两个点 u 坐标之差，得到向量的 u 分量
        self.v = spot1.v - spot0.v  # 计算两个点 v 坐标之差，得到向量的 v 分量

# 定义惯性矩（Moment Of Inertia）类，用于计算颜色顺序的相关指标
class MomentOfInertia:
    def __init__(self, spots):
        self.spots = spots  # 保存所有颜色点（DiscColor 对象）的列表
        self.vectors = self.calculate_vectors()  # 计算并保存相邻颜色点之间的向量列表
        self.angle = self.calculate_angle()  # 计算最佳拟合角度
        self.moments = self.calculate_moments()  # 计算惯性矩（moments）
        self.c_index = None  # 初始化 C-index 指标
        self.s_index = None  # 初始化 S-index 指标
        self.tes = None  # 初始化 TES 指标

    def calculate_vectors(self):
        vecs = []  # 初始化一个列表存储计算得到的向量
        for i in range(1, len(self.spots)):
            vecs.append(Vector(self.spots[i-1], self.spots[i]))  # 计算相邻两个颜色点之间的向量，并添加到列表中
        return vecs  # 返回向量列表

    def calculate_angle(self):
        sum1 = 0  # 初始化累加器1，用于计算角度公式的分子部分
        sum2 = 0  # 初始化累加器2，用于计算角度公式的分母部分
        for vector in self.vectors:
            sum1 += 2 * vector.u * vector.v  # 累加每个向量中 2*u*v 的值
            sum2 += vector.u**2 - vector.v**2  # 累加每个向量中 u^2 - v^2 的值
        if sum2 == 0:
            return 0  # 如果分母为 0，返回角度 0，避免除零错误
        return math.atan(sum1 / sum2) / 2  # 根据公式计算最佳拟合角度，并返回该角度（除以2）

    def calculate_moments(self):
        moms = [0, 0]  # 初始化两个惯性矩值的列表
        angle1 = self.angle  # 主方向的角度
        angle2 = angle1 + (math.pi / 2)  # 次方向角度，主方向旋转 90 度

        for vector in self.vectors:
            # 根据投影公式计算每个向量在两个正交方向上的贡献，并累加求和
            moms[0] += (vector.v * math.cos(angle1) - vector.u * math.sin(angle1)) ** 2
            moms[1] += (vector.v * math.cos(angle2) - vector.u * math.sin(angle2)) ** 2

        moms[0] = math.sqrt(moms[0] / len(self.vectors))  # 计算第一个惯性矩的均方根值
        moms[1] = math.sqrt(moms[1] / len(self.vectors))  # 计算第二个惯性矩的均方根值

        if moms[0] > moms[1]:
            self.majorRadius = moms[0]  # 较大值作为主半径（Major Radius）
            self.minorRadius = moms[1]  # 较小值作为次半径（Minor Radius）
        else:
            self.majorRadius = moms[1]  # 否则交换赋值
            self.minorRadius = moms[0]

        return moms  # 返回计算得到的两个惯性矩值

    def calculate_c_index(self, calculated_max_radius):
        return self.majorRadius / calculated_max_radius  # 计算 C-index，为主半径与给定最大半径的比值

    def calculate_s_index(self):
        return self.majorRadius / self.minorRadius  # 计算 S-index，为主半径与次半径的比值

    def calculate_tes(self):
        return math.sqrt(self.majorRadius ** 2 + self.minorRadius ** 2)  # 计算 TES，取主半径和次半径平方和的平方根

# 定义主界面类 ColorPicker，用于实现颜色测试的 GUI 界面
class ColorPicker:
    def __init__(self, master):
        self.master = master  # 保存传入的主窗口对象
        self.master.title("Color Picker")  # 设置窗口标题
        self.master.attributes('-fullscreen', True)  # 设置窗口为全屏模式
        self.master.bind("<Escape>", self.exit_fullscreen)  # 绑定 Esc 键，按下时退出全屏模式
        self.master.configure(bg='black')  # 设置窗口背景颜色为黑色
        self.color_frames = []  # 初始化颜色列表，用于存储从文件加载的颜色
        self.selected_color = None  # 初始化当前选中的颜色为 None
        self.box_colors = []  # 初始化存储已填充颜色的方框颜色列表
        self.color_used = []  # 初始化记录颜色是否已被使用的列表
        self.start_time = None  # 初始化测试开始时间
        self.test_completed = False  # 标记测试是否已完成
        self.test_started = False  # 标记测试是否已开始
        self.current_color_order = []  # 初始化当前颜色顺序列表

        # 定义可选择的颜色文件选项（每个选项对应一个测试文件）
        self.file_options = ["Test1 15 8", "Test1 15 12", "Test1 15 16", "Test1 20 8", "Test1 20 12", "Test1 20 16", "Test2 15 8", "Test2 15 12", "Test2 15 16", "Test2 20 8", "Test2 20 12", "Test2 20 16", "Test3 15 8", "Test3 15 12", "Test3 15 16", "Test3 20 8", "Test3 20 12", "Test3 20 16", "Test4 15 8", "Test4 15 12", "Test4 15 16", "Test4 20 8", "Test4 20 12", "Test4 20 16", "Test5 15 8", "Test5 15 12", "Test5 15 16", "Test5 20 8", "Test5 20 12", "Test5 20 16", "Test6 15 8", "Test6 15 12", "Test6 15 16", "Test6 20 8", "Test6 20 12", "Test6 20 16", "Test7 15 8", "Test7 15 12", "Test7 15 16", "Test7 20 8", "Test7 20 12", "Test7 20 16", "Deutan4 4", "Deutan5 4", "Deutan6 4", "Protan5 16", "Protan6 16", "Protan7 16", "Protan5 8", "Protan6 8", "Protan7 8", "Protan5 4", "Protan6 4", "Protan7 4"]
        self.file_options.sort(key=lambda x: (x.split()[0], int(x.split()[1])))  # 根据字母和数字排序（GPT新加的一句）
    #    random.shuffle(self.file_options)  # 随机排列颜色文件选项的顺序
        self.available_files = self.file_options.copy()  # 可用的颜色文件列表（副本）
        self.completed_files = set()  # 初始化一个集合，记录已完成测试的文件
        self.color_file = tk.StringVar(value=self.available_files[0])  # 使用 tk.StringVar 保存当前选择的颜色文件，默认第一个

        self.create_widgets()  # 创建所有界面控件
        self.load_colors(self.color_file.get() + ".txt")  # 初始加载默认颜色文件（在 colors 文件夹下，文件名格式为 "<name>.txt"）
        self.create_color_boxes()  # 创建第一排颜色方块（隐藏状态，后续显示）
        self.create_color_squares()  # 创建第二排颜色方块，供用户操作

    def create_widgets(self):
        self.info_frame = tk.Frame(self.master, bg='black')  # 创建一个信息区域的 Frame，背景设为黑色
        self.info_frame.place(relx=0.5, rely=0.1, anchor='n')  # 在主窗口中定位信息区域（相对于窗口顶部中央）

        tk.Label(self.info_frame, text="姓名:", bg='black', fg='white').grid(row=0, column=0)  # 创建并定位显示“姓名:”的标签
        self.name_entry = tk.Entry(self.info_frame)  # 创建一个文本框供用户输入姓名
        self.name_entry.grid(row=0, column=1)  # 定位姓名输入框

        tk.Label(self.info_frame, text="年龄:", bg='black', fg='white').grid(row=1, column=0)  # 创建并定位显示“年龄:”的标签
        self.age_entry = tk.Entry(self.info_frame)  # 创建一个文本框供用户输入年龄
        self.age_entry.grid(row=1, column=1)  # 定位年龄输入框

        tk.Label(self.info_frame, text="色觉缺陷类型:", bg='black', fg='white').grid(row=2, column=0)  # 创建并定位显示“色觉缺陷类型:”的标签
        self.defect_type = tk.StringVar(value="正常")  # 定义一个变量保存色觉缺陷类型，默认值为“正常”
        defect_options = ["正常", "红色盲", "绿色盲", "红色弱", "绿色弱"]  # 定义可选的色觉缺陷类型列表
        self.defect_menu = tk.OptionMenu(self.info_frame, self.defect_type, *defect_options)  # 创建下拉菜单供用户选择色觉缺陷类型
        self.defect_menu.grid(row=2, column=1)  # 定位下拉菜单

        # 添加颜色文件选择组件
        tk.Label(self.info_frame, text="颜色文件选择:", bg='black', fg='white').grid(row=3, column=0)  # 创建并定位显示“颜色文件选择:”的标签
        self.file_menu = tk.OptionMenu(self.info_frame, self.color_file, *self.available_files, command=self.on_file_change)  # 创建颜色文件下拉菜单，选择时调用 on_file_change 方法
        self.file_menu.grid(row=3, column=1)  # 定位颜色文件下拉菜单

        self.start_button = tk.Button(self.master, text="开始测试", command=self.start_test)  # 创建“开始测试”按钮，并绑定点击事件调用 start_test 方法
        self.start_button.place(relx=0.5, rely=0.3, anchor='n')  # 定位开始测试按钮

        self.main_frame = tk.Frame(self.master, bg='black')  # 创建主操作区域的 Frame，背景设为黑色
        self.main_frame.place(relx=0.5, rely=0.5, anchor='center')  # 在窗口中定位主操作区域（中心位置）

        self.box_frame = tk.Frame(self.main_frame, bg='black')  # 创建第一排颜色方块所在的 Frame
        self.box_frame.grid(row=0, pady=20)  # 定位该区域并设置垂直间距

        self.squares_frame = tk.Frame(self.main_frame, bg='black')  # 创建第二排颜色方块所在的 Frame
        self.squares_frame.grid(row=1, pady=20)  # 定位该区域并设置垂直间距

        self.complete_button = tk.Button(self.master, text="完成测试", command=self.complete_test)  # 创建“完成测试”按钮，并绑定点击事件调用 complete_test 方法
        self.complete_button.place(relx=0.5, rely=0.9, anchor='s')  # 定位完成测试按钮（窗口底部中央）
        self.complete_button.config(state=tk.DISABLED)  # 初始时禁用“完成测试”按钮

    def on_file_change(self, selected_file):
        # 当颜色文件下拉菜单的选项发生改变时调用此方法
        if self.test_started:
            return  # 如果测试已经开始，则不允许更换文件，直接返回
        filename = selected_file + ".txt"  # 构造文件名（添加 .txt 后缀）
        self.load_colors(filename)  # 加载新的颜色文件
        # 重新创建颜色方块区域：先销毁现有的控件，再重建
        for widget in self.box_frame.winfo_children():
            widget.destroy()  # 销毁第一排所有颜色方块
        for widget in self.squares_frame.winfo_children():
            widget.destroy()  # 销毁第二排所有颜色方块
        self.create_color_boxes()  # 重新创建第一排颜色方块
        self.create_color_squares()  # 重新创建第二排颜色方块

    def load_colors(self, filename):
        # 从 colors 文件夹下加载指定的颜色文件
        file_path = os.path.join("colors", filename)  # 构造完整的文件路径
        try:
            with open(file_path, 'r') as file:
                self.color_frames = [line.strip() for line in file.readlines()]  # 读取文件中的每一行，去除空白字符后存入颜色列表
                self.color_used = [False] * len(self.color_frames)  # 初始化颜色使用标记列表，每个颜色标记为未使用
                self.box_colors = [None] * len(self.color_frames)  # 初始化每个方框的颜色记录，默认均为空
        except Exception as e:
            messagebox.showerror("加载错误", f"无法加载文件 {file_path}: {e}")  # 如果加载文件出错，弹出错误消息

    def create_color_boxes(self):
        self.color_boxes = []  # 初始化存储第一排颜色方块控件的列表
        # 第一排只显示除第一个颜色以外的颜色（测试开始后会以随机顺序显示）
        for idx, color in enumerate(self.color_frames):
            if idx == 0:
                continue  # 跳过第一个颜色
            frame = tk.Frame(self.box_frame, width=20, height=20, bg=color)  # 创建一个颜色方块 Frame，设置尺寸和背景颜色
            frame.grid(row=0, column=idx-1, padx=5, pady=5)  # 定位颜色方块，并设置边距
            frame.bind("<Button-1>", lambda e, color=color: self.select_color(color))  # 绑定鼠标点击事件，点击时选中该颜色
            self.color_boxes.append(frame)  # 将创建的颜色方块添加到列表中
        self.box_frame.grid_remove()  # 初始时隐藏第一排颜色方块区域

    def create_color_squares(self):
        self.color_squares = []  # 初始化存储第二排颜色方块控件的列表
        # 创建第二排颜色方块，固定第一个显示文件中第一个颜色，其余初始化为白色
        for idx in range(len(self.color_frames)):
            square = tk.Frame(self.squares_frame, width=20, height=20, bg='white', relief='solid')  # 创建颜色方块控件，带边框效果
            square.grid(row=0, column=idx, padx=2, pady=5)  # 定位控件，并设置内边距
            square.bind("<Button-1>", lambda e, idx=idx: self.place_color(idx) if self.test_started else None)  # 绑定单击事件，在测试开始后调用 place_color 方法
            if idx == 0:
                square.config(bg=self.color_frames[0])  # 将第一个方块的背景颜色设置为颜色文件中的第一个颜色
                self.color_used[0] = True  # 标记第一个颜色为已使用
            else:
                square.bind("<Double-Button-1>", lambda e, idx=idx: self.remove_color(idx) if self.test_started else None)  # 绑定双击事件，在测试开始后调用 remove_color 方法
            self.color_squares.append(square)  # 将创建的方块控件添加到列表中
        self.color_squares[0].unbind("<Double-Button-1>")  # 移除第一个方块的双击事件绑定（确保其颜色不能被删除）

    def start_test(self):
        name = self.name_entry.get()  # 获取用户输入的姓名
        age = self.age_entry.get()  # 获取用户输入的年龄

        if not name or not age.isdigit():
            messagebox.showerror("输入错误", "请填写有效的姓名和年龄。")  # 如果姓名为空或年龄不是数字，则弹出错误提示
            return

        # 检查所选颜色文件是否已完成测试
        if self.color_file.get() in self.completed_files:
            messagebox.showerror("文件已测试", f"文件 {self.color_file.get()} 已完成测试，不能重复测试。")  # 如果该文件已测试，则弹出错误提示
            return

        # 清空之前的状态（GPT新加的一段）
        self.selected_color = None  # 清空选中的颜色
        self.color_used = [False] * len(self.color_frames)  # 重置颜色使用状态
        self.box_colors = [None] * len(self.color_frames)  # 清空已使用的颜色记录
        self.test_completed = False  # 重置测试完成标记
        self.test_started = True  # 设置测试已开始标记


        self.start_time = time.time()  # 记录测试开始的时间戳
        self.start_button.config(state=tk.DISABLED)  # 禁用“开始测试”按钮，防止重复点击
        self.complete_button.config(state=tk.NORMAL)  # 启用“完成测试”按钮
    #    self.test_completed = False  # 设置测试未完成标记
    #    self.test_started = True  # 设置测试已开始标记

        # 随机排列除第一个之外的颜色，生成新的颜色顺序
        self.current_color_order = random.sample(self.color_frames[1:], len(self.color_frames) - 1)
        self.reset_colors()  # 更新第一排颜色方块的显示

    def reset_colors(self):
        # 重新生成第一排颜色方块（随机顺序显示除第一个外的颜色）
        for widget in self.box_frame.winfo_children():
            widget.destroy()  # 删除当前第一排中所有的颜色方块控件

        for idx, color in enumerate(self.current_color_order):
            frame = tk.Frame(self.box_frame, width=20, height=20, bg=color)  # 创建新的颜色方块控件
            frame.grid(row=0, column=idx, padx=5, pady=5)  # 定位新控件，并设置边距
            frame.bind("<Button-1>", lambda e, color=color: self.select_color(color))  # 绑定点击事件，点击后选中该颜色
        self.box_frame.grid()  # 显示第一排颜色方块区域

    def select_color(self, color):
        self.selected_color = color  # 设置当前选中的颜色为传入的颜色

    def place_color(self, idx):
        if self.selected_color:
            if self.color_squares[idx]['bg'] == 'white':  # 只有当目标方块未被填充颜色时，才允许放置颜色
                if self.selected_color in self.box_colors:
                    messagebox.showerror("颜色已使用", f"颜色 {self.selected_color} 已在其他方框中使用。")  # 如果颜色已被其他方框使用，弹出错误提示
                    return

                self.color_squares[idx].config(bg=self.selected_color)  # 将选中的颜色填充到目标方块中
                color_index = self.color_frames.index(self.selected_color)  # 获取选中颜色在颜色列表中的索引
                self.box_colors[idx] = self.selected_color  # 记录该方框使用的颜色
                self.color_used[color_index] = True  # 标记该颜色为已使用

                if self.selected_color in self.current_color_order:
                    self.current_color_order.remove(self.selected_color)  # 从当前颜色顺序中移除已使用的颜色
                self.reset_colors()  # 重新生成第一排颜色方块，更新显示

    def remove_color(self, idx):
        color_to_remove = self.color_squares[idx]['bg']  # 获取要移除的颜色（目标方框的背景颜色）
        if color_to_remove != 'white' and idx != 0:
            self.color_squares[idx].config(bg='white')  # 将目标方框重置为白色，表示无颜色
            color_index = self.color_frames.index(color_to_remove)  # 获取该颜色在颜色列表中的索引
            self.box_colors[idx] = None  # 清除该方框记录的颜色
            self.color_used[color_index] = False  # 标记该颜色为未使用

            self.current_color_order.append(color_to_remove)  # 将移除的颜色添加到当前颜色顺序末尾
            self.reset_colors()  # 重新生成第一排颜色方块，更新显示

    def complete_test(self):
        if self.test_completed:
            messagebox.showinfo("提示", "测试已完成，无法重复提交。")  # 如果测试已经完成，则弹出提示，防止重复提交
            return

        order = []  # 初始化一个列表用于保存颜色方块的顺序
        for idx in range(len(self.color_squares)):
            if self.color_squares[idx]['bg'] != 'white':
                color = self.color_squares[idx]['bg']  # 获取方框中的颜色（非白色）
                color_index = self.color_frames.index(color)  # 获取该颜色在颜色列表中的索引
                order.append(color_index + 1)  # 将索引（从1开始计数）添加到顺序列表中

        order_string = ", ".join(str(idx) for idx in order)  # 将颜色顺序列表转换为以逗号分隔的字符串
        end_time = time.time()  # 获取测试结束时的时间戳
        elapsed_time = end_time - self.start_time  # 计算测试耗时（秒）
        self.test_completed = True  # 标记测试已完成

        name = self.name_entry.get()  # 获取用户输入的姓名
        age = self.age_entry.get()  # 获取用户输入的年龄
        defect = self.defect_type.get()  # 获取用户选择的色觉缺陷类型

        metrics = self.calculate_and_display_metrics()  # 计算测试指标并返回指标数据
        metrics_message = (
            f"姓名: {name}\n"
            f"年龄: {age}\n"
            f"色觉缺陷类型: {defect}\n"
            f"选择的颜色文件: {self.color_file.get()}.txt\n"
            f"测试时间: {elapsed_time:.2f}秒\n"
            f"色块顺序: {order_string}\n\n"
            f"Calculated Maximum Radius: {metrics['Calculated Maximum Radius']:.2f}\n"
            f"Major Radius: {metrics['Major Radius']:.2f}\n"
            f"Minor Radius: {metrics['Minor Radius']:.2f}\n"
            f"TES: {metrics['TES']:.2f}\n"
            f"C-index: {metrics['C-index']:.2f}\n"
            f"S-index: {metrics['S-index']:.2f}"
        )  # 构造包含所有测试数据和指标的提示信息
        # 隐藏第一个弹窗：不再显示测试指标
        # messagebox.showinfo("测试指标", metrics_message)

        # 将除第一个方框外所有方框的颜色清空，重置为白色
        for idx in range(1, len(self.color_squares)):
            if self.color_squares[idx]['bg'] != 'white':
                color = self.color_squares[idx]['bg']
                color_index = self.color_frames.index(color)
                self.color_used[color_index] = False  # 重置颜色使用状态为未使用
                self.box_colors[idx] = None  # 清除该位置记录的颜色
                self.color_squares[idx].config(bg='white')  # 将该方框颜色重置为白色

        # 固定第二排第一个方块始终显示当前文件的第一个颜色
        if self.color_squares:
            self.color_squares[0].config(bg=self.color_frames[0])
            self.color_used[0] = True

        self.reset_colors()  # 更新第一排颜色方块的显示

        self.start_button.config(state=tk.NORMAL)  # 重新启用“开始测试”按钮
        self.complete_button.config(state=tk.DISABLED)  # 禁用“完成测试”按钮
        self.test_started = False  # 重置测试开始标记

        # 标记当前颜色文件为已完成测试，并从可选文件列表中移除
        current_file = self.color_file.get()
        self.completed_files.add(current_file)  # 添加当前文件到已完成测试集合中
        if current_file in self.available_files:
            self.available_files.remove(current_file)  # 从可用文件列表中移除该文件
            menu = self.file_menu["menu"]  # 获取颜色文件下拉菜单的菜单对象
            menu.delete(0, "end")  # 清空菜单中所有选项
            # 重新更新下拉菜单选项，并绑定更改事件（同时设置 self.color_file 并调用 on_file_change）
            for file in self.available_files:
                menu.add_command(label=file, command=lambda value=file: (self.color_file.set(value), self.on_file_change(value)))
                
        self.save_to_excel(name, age, defect, order_string, elapsed_time, metrics)  # 将测试结果保存到 Excel 文件中



    def calculate_and_display_metrics(self):
        # 将原始颜色文件中的颜色转换为 RGB 格式列表
        original_colors = [ColorConverter.hex_to_rgb(color) for color in self.color_frames]
        # 构建重新排序后的颜色列表：固定第二排第一个颜色，并追加其余非白色颜色
        reordered_colors = [ColorConverter.hex_to_rgb(self.color_squares[0]['bg'])]

        for idx in range(1, len(self.color_squares)):
            if self.color_squares[idx]['bg'] != 'white':
                color = self.color_squares[idx]['bg']
                rgb = ColorConverter.hex_to_rgb(color)  # 将颜色转换为 RGB 格式
                reordered_colors.append(rgb)  # 添加到重新排序的颜色列表中

        original_disc_colors = [DiscColor(i + 1, color) for i, color in enumerate(original_colors)]  # 构造原始颜色对应的 DiscColor 对象列表
        reordered_disc_colors = [DiscColor(i + 1, color) for i, color in enumerate(reordered_colors)]  # 构造重新排序后颜色的 DiscColor 对象列表

        original_moi = MomentOfInertia(original_disc_colors)  # 根据原始颜色顺序计算 MomentOfInertia
        calculated_max_radius = original_moi.majorRadius  # 记录原始顺序下计算得到的最大半径

        moment_of_inertia = MomentOfInertia(reordered_disc_colors)  # 根据用户排列后的颜色顺序计算 MomentOfInertia
        moment_of_inertia.c_index = moment_of_inertia.calculate_c_index(calculated_max_radius)  # 计算 C-index 指标
        moment_of_inertia.s_index = moment_of_inertia.calculate_s_index()  # 计算 S-index 指标
        moment_of_inertia.tes = moment_of_inertia.calculate_tes()  # 计算 TES 指标

        metrics = {
            "Calculated Maximum Radius": calculated_max_radius,
            "TES": moment_of_inertia.tes,
            "C-index": moment_of_inertia.c_index,
            "S-index": moment_of_inertia.s_index,
            "Major Radius": moment_of_inertia.majorRadius,
            "Minor Radius": moment_of_inertia.minorRadius
        }  # 构造一个字典存储所有计算得到的测试指标
        return metrics  # 返回包含指标的字典

    def save_to_excel(self, name, age, defect, order_string, elapsed_time, metrics):
        data = {
            "姓名": [name],
            "年龄": [age],
            "色觉缺陷类型": [defect],
            "色块顺序": [order_string],
            "测试时间 (秒)": [elapsed_time],
            "Calculated Maximum Radius": [metrics["Calculated Maximum Radius"]],
            "Major Radius": [metrics["Major Radius"]],
            "Minor Radius": [metrics["Minor Radius"]],
            "TES": [metrics["TES"]],
            "C-index": [metrics["C-index"]],
            "S-index": [metrics["S-index"]],
            "颜色文件": [self.color_file.get() + ".txt"]  # 记录所使用的颜色文件（带 .txt 后缀）
        }  # 构造一个字典存储所有测试数据
        df = pd.DataFrame(data)  # 使用 pandas 将数据转换为 DataFrame 格式

        file_name = "test_results.xlsx"  # 定义保存测试结果的 Excel 文件名
        if os.path.exists(file_name):
            with pd.ExcelWriter(file_name, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
                df.to_excel(writer, index=False, header=False, startrow=writer.sheets['Sheet1'].max_row)  # 如果文件存在则追加写入数据
        else:
            df.to_excel(file_name, index=False)  # 如果文件不存在则创建新文件写入数据

        messagebox.showinfo("保存成功", "测试结果已保存到 test_results.xlsx")  # 弹出消息框提示测试结果保存成功

    def exit_fullscreen(self, event=None):
        self.master.attributes('-fullscreen', False)  # 退出全屏模式
        self.master.geometry("800x600")  # 设置窗口大小为 800x600

if __name__ == "__main__":
    root = tk.Tk()  # 创建 Tk 主窗口对象
    app = ColorPicker(root)  # 实例化 ColorPicker 类，传入主窗口对象
    root.mainloop()  # 进入 Tkinter 事件循环，等待用户操作
