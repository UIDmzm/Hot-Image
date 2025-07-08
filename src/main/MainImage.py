import sys
import os
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QLineEdit, QComboBox, QFileDialog, QMessageBox,
    QListWidget, QListWidgetItem, QAbstractItemView, QGroupBox, QSplitter,
    QCheckBox
)
from PyQt5.QtCore import Qt
import xlrd
from matplotlib import font_manager
import src.module.read_files as read_files
import src.module.handle_datas as handle_datas

# Times New Roman
font_files = [
    "/usr/share/fonts/truetype/custom/TIMES.TTF",
    "/usr/share/fonts/truetype/custom/TIMESBD.TTF",
    "/usr/share/fonts/truetype/custom/TIMESI.TTF",
    "/usr/share/fonts/truetype/custom/TIMESBI.TTF"
]

for file in font_files:
    font_manager.fontManager.addfont(file)

class HeatmapApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("热图数据分析工具")
        self.setGeometry(100, 100, 1400, 800)
        
        # 设置全局字体为Times New Roman
        plt.rcParams['font.family'] = 'Times New Roman'
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.titlesize'] = 12
        plt.rcParams['axes.labelsize'] = 10
        plt.rcParams['xtick.labelsize'] = 8
        plt.rcParams['ytick.labelsize'] = 8
        
        # 初始化变量
        self.raw_data = None
        self.cut_current_data = None
        self.data_matrix = None
        self.selected_folder = ""
        self.current_heatmap_data = None
        self.current_file_row_counts = {}  # 存储每个文件的行数
        self.min_row_count = 0  # 存储最小行数
        
        # 创建主控件和布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧：绘图区域 (70%)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # 绘图区域
        self.figure, self.ax = plt.subplots(figsize=(10, 8))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumSize(800, 600)
        left_layout.addWidget(self.canvas)
        
        splitter.addWidget(left_widget)
        
        # 右侧：控制面板和文件列表 (30%)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 5, 5, 5)
        
        # 创建控制面板
        control_panel = self.create_control_panel()
        right_layout.addWidget(control_panel)
        
        # 创建文件列表区域
        file_group = self.create_file_list_group()
        right_layout.addWidget(file_group)
        
        splitter.addWidget(right_widget)
        
        # 设置分割器比例
        splitter.setSizes([1000, 400])
        
        # 设置初始值
        self.row_edit.setText("20")
        self.col_edit.setText("10")
        self.column_edit.setText("3")
        self.start_row_edit.setText("1")
        self.process_combo.setCurrentIndex(0)
        self.cmap_combo.setCurrentIndex(0)  # 默认选择 viridis
        
        # 应用样式
        self.apply_styles()
    
    def apply_styles(self):
        """应用样式表"""
        self.setStyleSheet("""
            QWidget {
                font-family: "Times New Roman", Times, serif;
                font-size: 12px;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                padding: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
                background-color: transparent;
                font-family: "Times New Roman", Times, serif;
            }
            QPushButton {
                background-color: #4a86e8;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
                font-family: "Times New Roman", Times, serif;
            }
            QPushButton:hover {
                background-color: #3a76d8;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QListWidget {
                background-color: white;
                border: 1px solid #cccccc;
                border-radius: 3px;
                font-family: "Times New Roman", Times, serif;
            }
            QLineEdit {
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 3px;
                font-family: "Times New Roman", Times, serif;
            }
            QLabel {
                color: #333333;
                font-family: "Times New Roman", Times, serif;
            }
            QCheckBox {
                spacing: 5px;
                font-family: "Times New Roman", Times, serif;
            }
            QComboBox {
                font-family: "Times New Roman", Times, serif;
            }
        """)
    
    def create_control_panel(self):
        """创建控制面板"""
        panel = QGroupBox("控制面板")
        layout = QGridLayout(panel)
        layout.setSpacing(10)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 1)
        layout.setColumnStretch(3, 1)
        layout.setColumnStretch(4, 1)
        layout.setColumnStretch(5, 1)
        
        # 行 0: 文件夹选择
        self.import_btn = QPushButton("选择文件夹")
        self.import_btn.clicked.connect(self.select_folder)
        layout.addWidget(self.import_btn, 0, 0, 1, 2)
        
        self.folder_label = QLabel("未选择文件夹")
        self.folder_label.setStyleSheet("color: gray; font-size: 10px; font-family: 'Times New Roman';")
        layout.addWidget(self.folder_label, 0, 2, 1, 4)
        
        # 行 1: 数据列设置
        layout.addWidget(QLabel("数据列号:"), 1, 0)
        self.column_edit = QLineEdit()
        self.column_edit.setFixedWidth(50)
        self.column_edit.setToolTip("要读取的数据列索引（0-based）")
        layout.addWidget(self.column_edit, 1, 1)
        
        # 行 2: 热图行列设置
        layout.addWidget(QLabel("热图行数:"), 2, 0)
        self.row_edit = QLineEdit()
        self.row_edit.setFixedWidth(50)
        self.row_edit.setToolTip("生成热图的行数")
        layout.addWidget(self.row_edit, 2, 1)
        
        layout.addWidget(QLabel("热图列数:"), 2, 2)
        self.col_edit = QLineEdit()
        self.col_edit.setFixedWidth(50)
        self.col_edit.setToolTip("生成热图的列数")
        layout.addWidget(self.col_edit, 2, 3)
        
        # 行 3: 数据范围设置
        layout.addWidget(QLabel("数据起始行:"), 3, 0)
        self.start_row_edit = QLineEdit()
        self.start_row_edit.setFixedWidth(50)
        self.start_row_edit.setToolTip("数据起始行（1-based）")
        layout.addWidget(self.start_row_edit, 3, 1)
        
        layout.addWidget(QLabel("数据结束行:"), 3, 2)
        self.end_row_edit = QLineEdit()
        self.end_row_edit.setFixedWidth(50)
        self.end_row_edit.setToolTip("数据结束行（1-based）")
        layout.addWidget(self.end_row_edit, 3, 3)
        
        # 行 4: 行数信息和智能设置
        self.row_info_label = QLabel("文件行数: -")
        self.row_info_label.setStyleSheet("color: #666666; font-size: 10px; font-family: 'Times New Roman';")
        layout.addWidget(self.row_info_label, 3, 4, 1, 2)
        
        self.auto_end_row_btn = QPushButton("智能设置结束行")
        self.auto_end_row_btn.setToolTip("使用所有文件中数据行数的最小值作为结束行")
        self.auto_end_row_btn.clicked.connect(self.set_min_end_row)
        self.auto_end_row_btn.setEnabled(False)
        layout.addWidget(self.auto_end_row_btn, 4, 4, 1, 2)
        
        # 行 5: 数据处理方法
        layout.addWidget(QLabel("数据处理方法:"), 5, 0)
        self.process_combo = QComboBox()
        self.process_combo.addItems([
            "标准处理", 
            "数据采样", 
            "RMS降采样", 
            "均值缩减"
        ])
        self.process_combo.setToolTip("选择数据处理方法")
        layout.addWidget(self.process_combo, 5, 1, 1, 5)
        
        # 行 6: 颜色条选择
        layout.addWidget(QLabel("颜色条:"), 6, 0)
        self.cmap_combo = QComboBox()
        # 添加更多纯色选项
        self.cmap_combo.addItems([
            "viridis", "plasma", "inferno", "magma", "cividis",
            "coolwarm", "jet", "rainbow", "seismic", "hot",
            "Reds", "Blues", "Greens", "Oranges", "Purples",
            "Greys", "RdPu", "YlOrBr", "YlGnBu", "PuBuGn"
        ])
        self.cmap_combo.setToolTip("选择热图颜色方案")
        layout.addWidget(self.cmap_combo, 6, 1, 1, 3)
        
        # 行 7: 坐标显示控制
        self.show_x_label_cb = QCheckBox("显示X轴标题")
        self.show_x_label_cb.setChecked(False)
        self.show_x_label_cb.setToolTip("控制是否显示X轴标题")
        layout.addWidget(self.show_x_label_cb, 7, 0, 1, 2)
        
        self.show_y_label_cb = QCheckBox("显示Y轴标题")
        self.show_y_label_cb.setChecked(False)
        self.show_y_label_cb.setToolTip("控制是否显示Y轴标题")
        layout.addWidget(self.show_y_label_cb, 7, 2, 1, 2)
        
        self.show_ticks_cb = QCheckBox("显示刻度标签")
        self.show_ticks_cb.setChecked(False)
        self.show_ticks_cb.setToolTip("控制是否显示刻度标签")
        layout.addWidget(self.show_ticks_cb, 7, 4, 1, 2)
        
        # 行 8: 绘图按钮和保存按钮
        btn_layout = QHBoxLayout()
        
        # 绘图按钮
        self.plot_btn = QPushButton("绘制热图")
        self.plot_btn.clicked.connect(self.plot_heatmap)
        self.plot_btn.setEnabled(False)
        self.plot_btn.setMinimumHeight(40)
        btn_layout.addWidget(self.plot_btn)
        
        # 保存图片按钮
        self.save_btn = QPushButton("保存图片")
        self.save_btn.clicked.connect(self.save_image)
        self.save_btn.setEnabled(False)
        self.save_btn.setMinimumHeight(40)
        btn_layout.addWidget(self.save_btn)
        
        layout.addLayout(btn_layout, 8, 0, 1, 6)
        
        # 行 9: 状态标签
        self.status_label = QLabel("请选择包含Excel文件的文件夹")
        self.status_label.setStyleSheet("color: #666666; font-style: italic; font-family: 'Times New Roman';")
        layout.addWidget(self.status_label, 9, 0, 1, 6)
        
        return panel
    
    def create_file_list_group(self):
        """创建文件列表区域"""
        group = QGroupBox("文件列表")
        layout = QVBoxLayout(group)
        layout.setSpacing(5)
        
        # 文件计数标签
        file_count_layout = QHBoxLayout()
        file_count_layout.addWidget(QLabel("已选文件:"))
        self.file_count_label = QLabel("0 个")
        self.file_count_label.setStyleSheet("color: #4a86e8; font-weight: bold; font-family: 'Times New Roman';")
        file_count_layout.addWidget(self.file_count_label)
        
        # 最小行数标签
        file_count_layout.addSpacing(20)
        file_count_layout.addWidget(QLabel("最小行数:"))
        self.min_row_label = QLabel("-")
        self.min_row_label.setStyleSheet("color: #e84a4a; font-weight: bold; font-family: 'Times New Roman';")
        file_count_layout.addWidget(self.min_row_label)
        
        file_count_layout.addStretch()
        layout.addLayout(file_count_layout)
        
        # 文件列表
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.file_list.setMinimumHeight(300)
        layout.addWidget(self.file_list)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        
        # 移除选中按钮
        self.remove_btn = QPushButton("移除选中文件")
        self.remove_btn.clicked.connect(self.remove_selected_files)
        self.remove_btn.setEnabled(False)
        btn_layout.addWidget(self.remove_btn)
        
        # 清除所有按钮
        self.clear_btn = QPushButton("清除所有文件")
        self.clear_btn.clicked.connect(self.clear_file_list)
        self.clear_btn.setEnabled(False)
        btn_layout.addWidget(self.clear_btn)
        
        layout.addLayout(btn_layout)
        
        # 连接选择变化信号
        self.file_list.itemSelectionChanged.connect(self.update_button_state)
        self.file_list.itemSelectionChanged.connect(self.update_row_info)
        
        return group
    
    def update_button_state(self):
        """根据选择状态更新按钮状态"""
        has_selection = len(self.file_list.selectedItems()) > 0
        self.remove_btn.setEnabled(has_selection)
    
    def update_row_info(self):
        """更新行数信息"""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            return
        
        # 只取第一个选中的文件
        item = selected_items[0]
        file_name = item.data(Qt.UserRole)
        
        if file_name in self.current_file_row_counts:
            row_count = self.current_file_row_counts[file_name]
            self.row_info_label.setText(f"文件行数: {row_count}")
    
    def set_min_end_row(self):
        """设置结束行为最小行数"""
        if self.min_row_count > 0:
            self.end_row_edit.setText(str(self.min_row_count))
            self.status_label.setText(f"已设置结束行为最小行数: {self.min_row_count}")
    
    def select_folder(self):
        """选择文件夹"""
        folder = QFileDialog.getExistingDirectory(
            self, "选择包含Excel文件的文件夹", ""
        )
        
        if not folder:
            return
        
        self.selected_folder = folder
        self.folder_label.setText(os.path.basename(folder))
        self.status_label.setText("正在扫描文件夹中的Excel文件...")
        
        # 扫描文件夹中的Excel文件
        self.scan_excel_files()

    def scan_excel_files(self):
        """扫描文件夹中的Excel文件并添加到列表"""
        if not self.selected_folder:
            return

        # 清空文件列表
        self.file_list.clear()
        self.current_file_row_counts = {}
        self.min_row_count = 0
        self.min_row_label.setText("-")

        try:
            # 获取文件信息
            files_info = read_files.get_excel_files_info(self.selected_folder)

            if not files_info:
                self.status_label.setText("未找到Excel文件")
                self.plot_btn.setEnabled(False)
                self.clear_btn.setEnabled(False)
                self.auto_end_row_btn.setEnabled(False)
                return

            # 用于计算最小行数的列表
            row_counts = []

            # 添加到文件列表
            for file_name, file_path, row_count in files_info:
                self.current_file_row_counts[file_path] = row_count
                row_counts.append(row_count)

                item = QListWidgetItem(f"{file_name} ({row_count}行)")
                item.setData(Qt.UserRole, file_path)  # 存储文件路径
                self.file_list.addItem(item)

            file_count = len(files_info)
            self.file_count_label.setText(f"{file_count} 个")
            self.status_label.setText(f"找到 {file_count} 个Excel文件")
            self.plot_btn.setEnabled(True)
            self.clear_btn.setEnabled(True)
            self.auto_end_row_btn.setEnabled(True)

            # 计算最小行数
            if row_counts:
                self.min_row_count = min(row_counts)
                self.min_row_label.setText(str(self.min_row_count))

            # 设置起始行和结束行的默认值
            self.start_row_edit.setText("1")
            if self.min_row_count > 0:
                self.end_row_edit.setText(str(self.min_row_count))
            else:
                self.end_row_edit.setText("50")

        except Exception as e:
            QMessageBox.critical(self, "扫描错误", f"扫描文件夹时出错:\n{str(e)}")
            self.status_label.setText("扫描失败")
    
    def remove_selected_files(self):
        """移除选中的文件"""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            return
        
        # 更新最小行数
        remaining_row_counts = []
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            if item not in selected_items:
                file_name = item.data(Qt.UserRole)
                if file_name in self.current_file_row_counts:
                    remaining_row_counts.append(self.current_file_row_counts[file_name])
        
        # 移除选中的文件
        for item in selected_items:
            row = self.file_list.row(item)
            self.file_list.takeItem(row)
        
        # 更新文件计数和最小行数
        file_count = self.file_list.count()
        self.file_count_label.setText(f"{file_count} 个")
        
        if remaining_row_counts:
            self.min_row_count = min(remaining_row_counts)
            self.min_row_label.setText(str(self.min_row_count))
        else:
            self.min_row_count = 0
            self.min_row_label.setText("-")
        
        self.status_label.setText(f"已移除 {len(selected_items)} 个文件")
    
    def clear_file_list(self):
        """清除所有文件"""
        self.file_list.clear()
        self.file_count_label.setText("0 个")
        self.min_row_label.setText("-")
        self.min_row_count = 0
        self.status_label.setText("文件列表已清空")
        self.plot_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
        self.auto_end_row_btn.setEnabled(False)
    
    def get_selected_files(self):
        """获取选择的文件列表（完整路径）"""
        files = []
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            file_name = item.data(Qt.UserRole)
            file_path = os.path.join(self.selected_folder, file_name)
            files.append(file_path)
        return files
    
    def plot_heatmap(self):
        """绘制热图"""
        files = self.get_selected_files()
        if not files:
            QMessageBox.warning(self, "数据缺失", "请先选择文件")
            return
        
        try:
            # 获取参数
            length = int(self.row_edit.text())
            data_groups = int(self.col_edit.text())
            column_index = int(self.column_edit.text())
            start_row = int(self.start_row_edit.text())
            end_row = int(self.end_row_edit.text())
            
            if start_row >= end_row:
                QMessageBox.warning(self, "参数错误", "起始行必须小于结束行")
                return
            
            # 读取数据 - 使用新的函数，传入文件路径列表
            self.raw_data = read_files.read_column_from_xls(
                files,  # 传入文件路径列表
                column_index,
                start_row=start_row,  # 1-based索引,排除每一组数据中第一个索引，即数据名称
                end_row=end_row
            )
            
            if not self.raw_data:
                QMessageBox.warning(self, "数据错误", "未能从文件中读取有效数据")
                return
            
            # 处理数据
            self.cut_current_data = handle_datas.cut_data(self.raw_data)
            self.cut_current_data = handle_datas.Normalized_data(self.cut_current_data)
            # self.cut_current_data = handle_datas.Subtract_dark_current(self.cut_current_data)
            
            # 检查数据组数是否足够
            if len(self.cut_current_data) < data_groups:
                QMessageBox.warning(
                    self, "数据不足", 
                    f"需要 {data_groups} 组数据，但只有 {len(self.cut_current_data)} 组可用"
                )
                return
            
            # 根据选择的方法处理数据
            method_index = self.process_combo.currentIndex()
            processed_data = []
            
            if method_index == 0:  # 标准处理
                processed_data = [handle_datas.process_data(data, length) for data in self.cut_current_data]
            elif method_index == 1:  # 数据采样
                processed_data = [handle_datas.data_sampling(data, length) for data in self.cut_current_data]
            elif method_index == 2:  # RMS降采样
                processed_data = [handle_datas.rms_downsample(data, length) for data in self.cut_current_data]
            elif method_index == 3:  # 均值缩减
                processed_data = [handle_datas.reduce_data(data, length, method='mean') for data in self.cut_current_data]
            
                        
            # 更新数据矩阵
            self.data_matrix = np.zeros((0, length))  # 初始化为空矩阵
            
            # 使用修改后的update_heatmap函数
            for data in processed_data[:data_groups]:
                self.data_matrix = handle_datas.update_heatmap(
                    self.data_matrix, 
                    data, 
                    length, 
                    data_groups
                )
            
            # 存储当前热图数据
            self.current_heatmap_data = self.data_matrix.copy()
            
            # 绘制热图 - 清除之前的绘图
            self.figure.clear()
            self.ax = self.figure.add_subplot(111)
            
            # 获取选择的颜色条
            cmap = self.cmap_combo.currentText()
            
            # 绘制新热图
            sns.heatmap(
                self.data_matrix, 
                ax=self.ax, 
                cmap=cmap, 
                annot=False, 
                fmt=".2f",
                xticklabels=self.show_ticks_cb.isChecked(),
                yticklabels=self.show_ticks_cb.isChecked()
            )
            
            # 设置标题 - 使用Times New Roman字体
            # self.ax.set_title(f"热图 - {self.process_combo.currentText()}", fontname="Times New Roman")
            
            # 根据复选框设置坐标轴标签
            if self.show_x_label_cb.isChecked():
                self.ax.set_xlabel("X轴", fontname="Times New Roman")
            else:
                self.ax.set_xlabel("")
            
            if self.show_y_label_cb.isChecked():
                self.ax.set_ylabel("Y轴", fontname="Times New Roman")
            else:
                self.ax.set_ylabel("")
            
            # 设置刻度标签字体
            for label in self.ax.get_xticklabels():
                label.set_fontname("Times New Roman")
            for label in self.ax.get_yticklabels():
                label.set_fontname("Times New Roman")
            
            # 调整布局
            self.figure.tight_layout()
            
            # 更新画布
            self.canvas.draw()
            
            self.status_label.setText(f"已绘制热图: 方法={self.process_combo.currentText()}, 文件={len(files)}个")
            self.save_btn.setEnabled(True)
            
        except ValueError:
            QMessageBox.warning(self, "输入错误", "请输入有效的数值")
        except Exception as e:
            QMessageBox.critical(self, "绘图错误", f"绘制热图时出错:\n{str(e)}")
            import traceback
            print(traceback.format_exc())
    
    def save_image(self):
        """保存当前热图为图片文件"""
        if self.current_heatmap_data is None:
            QMessageBox.warning(self, "无数据", "没有可保存的热图数据")
            return
        
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存热图", "热图分析结果", 
            "PNG 图片 (*.png);;JPEG 图片 (*.jpg);;所有文件 (*)", 
            options=options
        )
        
        if not file_path:
            return
        
        try:
            # 创建新图形保存
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # 获取选择的颜色条
            cmap = self.cmap_combo.currentText()
            
            # 绘制热图并获取颜色条
            heatmap = sns.heatmap(
                self.current_heatmap_data, 
                ax=ax, 
                cmap=cmap, 
                annot=False, 
                fmt=".2f",
                xticklabels=self.show_ticks_cb.isChecked(),
                yticklabels=self.show_ticks_cb.isChecked(),
                cbar_kws={"shrink": 1.2}  # 控制颜色条大小
            )
            
            # 设置标题 - 使用Times New Roman字体
            ax.set_title(f"热图 - {self.process_combo.currentText()}", 
                        fontname="Times New Roman", 
                        fontsize=24,  # 增大标题字体
                        fontweight='bold',  # 加粗
                        pad=20)  # 增加上边距
            
            # 根据复选框设置坐标轴标签
            if self.show_x_label_cb.isChecked():
                ax.set_xlabel("X轴", 
                            fontname="Times New Roman", 
                            fontsize=20,  # 增大X轴标签字体
                            labelpad=15)  # 增加标签与坐标轴的间距
            else:
                ax.set_xlabel("")
            
            if self.show_y_label_cb.isChecked():
                ax.set_ylabel("Y轴", 
                            fontname="Times New Roman", 
                            fontsize=20,  # 增大Y轴标签字体
                            labelpad=15)  # 增加标签与坐标轴的间距
            else:
                ax.set_ylabel("")
            
            # 设置刻度标签字体
            for label in ax.get_xticklabels():
                label.set_fontname("Times New Roman")
                label.set_fontsize(18)  # 增大刻度标签字体
            
            for label in ax.get_yticklabels():
                label.set_fontname("Times New Roman")
                label.set_fontsize(18)  # 增大刻度标签字体
            
            # 设置颜色条的字体（这才是热图的"图例"）
            if heatmap.collections[0].colorbar is not None:
                cbar = heatmap.collections[0].colorbar
                # 设置颜色条标签
                cbar.set_label('数值', 
                            fontname="Times New Roman", 
                            fontsize=40,  # 增大字体
                            fontweight='bold')  # 加粗
                
                # 设置颜色条刻度标签
                cbar.ax.tick_params(labelsize=24)  # 增大刻度标签字体
                for label in cbar.ax.get_yticklabels():
                    label.set_fontname("Times New Roman")
            
            # 保存图片
            fig.savefig(file_path, bbox_inches='tight', dpi=300)
            plt.close(fig)
            
            self.status_label.setText(f"热图已保存到: {os.path.basename(file_path)}")
        except Exception as e:
            QMessageBox.critical(self, "保存错误", f"保存图片时出错:\n{str(e)}")
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HeatmapApp()
    window.show()
    sys.exit(app.exec_())