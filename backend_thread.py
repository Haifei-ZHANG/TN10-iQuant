import time
import numpy as np
import yahoo_fin.stock_info as si
from PyQt5.QtCore import QThread, pyqtSignal
from data_processing.download_data import download_data


class GetLivePrice(QThread):
    # 产生信号, 用于传输数据和通知UI进行更改
    update_data = pyqtSignal(list)

    # 从本地读取etf名称
    etfs = np.load('./Data/etfs.npy').tolist()

    def run(self):
        while True:
            live_price_array = []
            for etf in self.etfs:
                live_price = si.get_live_price(etf)
                live_price = round(live_price, 2)
                live_price_array.append(live_price)

                print(live_price)

            # 通过emit发送信号
            self.update_data.emit(live_price_array)

            # 每十秒更新一次数据
            time.sleep(30)


class UpdateHistData(QThread):
    etfs = np.load('./Data/etfs.npy').tolist()
    tfs = ['1d', '1wk', '1mo']
    update_hist_data_signal = pyqtSignal(str)

    def run(self):
        download_data(self.etfs, self.tfs)
        self.update_hist_data_signal.emit('finish')