from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QLineEdit, \
                            QPushButton, QAbstractItemView, QHeaderView, QMessageBox
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
import pandas as pd
import numpy as  np
import stockstats
pd.set_option('mode.chained_assignment', None)
import yahoo_fin.stock_info as si
from data_processing.load_data import load_rawdata


class PositionCalculator(QWidget):
    def __init__(self):
        super(PositionCalculator, self).__init__()

        # 获取本地的etf名称列表
        try:
            self.etfs = np.load('./Data/etfs.npy').tolist()
        except FileNotFoundError:
            self.etfs = ['SPY', 'QQQ', 'TLT', 'GLD', 'IWM', 'EFA', 'HYG', 'XLV']

        # 创建atr列表
        self.atr_list = []


        # get ATR
        for etf in self.etfs:
            raw_data = load_rawdata(etf, 'weekly')
            if raw_data is None:
                continue
            data_stats = stockstats.StockDataFrame.retype(raw_data.copy())
            atr = round(data_stats['atr'].iloc[-1], 2)
            self.atr_list.append(atr)

        # 开始创建页面
        # 设置主要字体
        self.myfont = QFont('Arial', 12, QFont.Bold)
        # 页面的主要布局采用垂直布局
        self.main_layout = QVBoxLayout(self)

        # 创建顶部选择控件
        top_widget  = QWidget()
        # 采用水平布局
        top_layout = QHBoxLayout()

        # 创建控件
        capital_label = QLabel('Capital')
        capital_label.setFont(self.myfont)

        self.capital_lineedit = QLineEdit()
        self.capital_lineedit.setPlaceholderText('ex: 100000')
        self.capital_lineedit.setFont(self.myfont)

        risk_label = QLabel('Risk tolerance')
        risk_label.setFont(self.myfont)

        self.risk_lineedit = QLineEdit()
        self.risk_lineedit.setPlaceholderText('ex: 0.02')
        self.risk_lineedit.setFont(self.myfont)

        stop_coef_label = QLabel('Stop Coefficient')
        stop_coef_label.setFont(self.myfont)

        self.stop_coef_lineedit = QLineEdit()
        self.stop_coef_lineedit.setPlaceholderText('ex: 0.1')
        self.stop_coef_lineedit.setFont(self.myfont)


        self.calculate_btn = QPushButton('Calculate')
        self.calculate_btn.setFont(self.myfont)
        self.calculate_btn.setShortcut(Qt.Key_Return)
        self.calculate_btn.clicked.connect(self.show_position_table)

        # 将这些控件加入top_layout
        top_layout.addWidget(capital_label)
        top_layout.addWidget(self.capital_lineedit)
        top_layout.addWidget(risk_label)
        top_layout.addWidget(self.risk_lineedit)
        top_layout.addWidget(stop_coef_label)
        top_layout.addWidget(self.stop_coef_lineedit)
        top_layout.addWidget(self.calculate_btn)

        # 设置top_widget的layout
        top_widget.setLayout(top_layout)
        top_widget.setContentsMargins(0, 40, 0, 40)

        # 将top_widget加入到总的main_layout
        self.main_layout.addWidget(top_widget)

        # 创建显示position的表格
        self.position_table = QTableWidget()
        self.position_table.setRowCount(len(self.etfs))
        self.position_table.setColumnCount(7)
        # 设置宽度自由扩展
        self.position_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # 设置表头高度
        self.position_table.horizontalHeader().setMinimumHeight(60)
        self.position_table.horizontalHeader().setFont(QFont(self.myfont))
        # 设置默认行高
        self.position_table.verticalHeader().setDefaultSectionSize(42)
        # 设置表头内容
        self.position_table.setHorizontalHeaderLabels(
            ['ETF', 'Risk Exposure', 'ATR', 'Current Price', 'Stop Price', 'Position Size', 'Position Value'])

        # 禁止编辑
        self.position_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # 整行选择
        self.position_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.position_table.setSelectionMode(QAbstractItemView.NoSelection)
        # 自动调整行和列
        # price_table.resizeColumnsToContents()
        # price_table.resizeRowsToContents()
        # 隐藏纵向header
        self.position_table.verticalHeader().setVisible(False)

        # 将表格加入main_layout
        self.main_layout.addWidget(self.position_table)


        # 设置真个窗口的布局
        self.setLayout(self.main_layout)

    def get_cur_price(self):
        # 获取最新价格
        current_price = []
        for etf in self.etfs:
            live_price = si.get_live_price(etf)
            live_price = round(live_price, 2)
            current_price.append(live_price)

        return current_price


    def calculate_position(self, capital, risk_tolerance, stop_coef, data=None):
        if data is None:
            # 此时是由鼠标点击造成的
            current_price = self.get_cur_price()
        else:
            current_price = data

        # 计算风险敞口
        risk_exposure = round(capital * risk_tolerance, 2)

        # 计算stop price, position size, position value
        stop_prices = []
        position_sizes = []
        position_values = []

        for i in range(len(self.etfs)):
            stop_prices.append(round(current_price[i] - self.atr_list[i] * stop_coef, 2))
            position_sizes.append(int(risk_exposure/self.atr_list[i]))
            if position_sizes[i] * current_price[i] > capital:
                position_sizes[i] = int(capital/current_price[i])

            position_values.append(round(position_sizes[i]*current_price[i], 2))

        # 设置表格的值
        for i in range(len(self.etfs)):
            etf_item = QTableWidgetItem(self.etfs[i])
            etf_item.setTextAlignment(Qt.AlignCenter)
            etf_item.setFont(self.myfont)
            self.position_table.setItem(i, 0, etf_item)

            risk_item = QTableWidgetItem(str(risk_exposure))
            risk_item.setTextAlignment(Qt.AlignCenter)
            risk_item.setFont(self.myfont)
            self.position_table.setItem(i, 1, risk_item)

            atr_item = QTableWidgetItem(str(self.atr_list[i]))
            atr_item.setTextAlignment(Qt.AlignCenter)
            atr_item.setFont(self.myfont)
            self.position_table.setItem(i, 2, atr_item)

            cur_item = QTableWidgetItem(str(current_price[i]))
            cur_item.setTextAlignment(Qt.AlignCenter)
            cur_item.setFont(self.myfont)
            self.position_table.setItem(i, 3, cur_item)

            stop_item = QTableWidgetItem(str(stop_prices[i]))
            stop_item.setTextAlignment(Qt.AlignCenter)
            stop_item.setFont(self.myfont)
            self.position_table.setItem(i, 4, stop_item)

            size_item = QTableWidgetItem(str(position_sizes[i]))
            size_item.setTextAlignment(Qt.AlignCenter)
            size_item.setFont(self.myfont)
            self.position_table.setItem(i, 5, size_item)

            value_item = QTableWidgetItem(str(position_values[i]))
            value_item.setTextAlignment(Qt.AlignCenter)
            value_item.setFont(self.myfont)
            self.position_table.setItem(i, 6, value_item)

    def show_position_table(self):
        try:
            capital = float(self.capital_lineedit.text())
            risk_tolerance = float(self.risk_lineedit.text())
            stop_coef = float(self.stop_coef_lineedit.text())
        except Exception as ex:
            # 弹窗，必须输入数字
            QMessageBox.warning(self, 'Input Error',
                                'All inputs should be numerical')
        else:
            if capital <= 0 or risk_tolerance < 0 or risk_tolerance > 1 or stop_coef <= 0:
                QMessageBox.warning(self, 'Input Error',
                                    'Capital and Stop Coefficient must be biger than zero, \n Risk tolerance must be between zero and one')
            else:
                self.calculate_position(capital, risk_tolerance, stop_coef, data=None)


    def update_position_table(self, data):
        if self.capital_lineedit.text() == '' or \
                self.risk_lineedit.text() == '' or \
                self.stop_coef_lineedit.text() == '':
            return
        try:
            capital = float(self.capital_lineedit.text())
            risk_tolerance = float(self.risk_lineedit.text())
            stop_coef = float(self.stop_coef_lineedit.text())
        except Exception as ex:
            return
        else:
            if capital <= 0 or risk_tolerance < 0 or risk_tolerance > 1 or stop_coef <= 0:
                return
            else:
                # 这里就是保证所有输入都是没有问题的
                self.calculate_position(capital, risk_tolerance, stop_coef, data)


