# - SQLite

# 출처 :  파이썬으로 배우는 알고리즘 트레이딩 - https://wikidocs.net/5326
# https://github.com/pystockhub/book

import sqlite3
import pandas as pd
from pandas import Series, DataFrame

# create table , insert data , select
con = sqlite3.connect("test.db")
cursor = con.cursor()
cursor.execute("CREATE TABLE kakao(Date text, Open int, High int, Low int, Closing int, Volumn int)")
cursor.execute("INSERT INTO kakao VALUES('16.06.03', 97000, 98600, 96900, 98000, 321405)")
con.commit()

cursor.execute("SELECT * FROM kakao")
print(cursor.fetchone())
print(cursor.fetchall())

con.close()


# DataFrame -> Sqlite3 
raw_data = {'col0': [1, 2, 3, 4], 'col1': [10, 20, 30, 40], 'col2':[100, 200, 300, 400]}
df = DataFrame(raw_data)
con = sqlite3.connect("test.db")
df.to_sql('test', con)


# Sqlite3 -> DataFrame
con = sqlite3.connect("test.db")
df = pd.read_sql("SELECT * FROM test", con, index_col=None)
print(df)


# Pandas를 이용한 주가 데이터 저장
'''
import pandas as pd
import pandas_datareader.data as web
import datetime
import sqlite3

start = datetime.datetime(2010, 1, 1)
end = datetime.datetime(2016, 6, 12)
df = web.DataReader("078930.KS", "yahoo", start, end)

con = sqlite3.connect("kospi.db")
df.to_sql('078930', con, if_exists='replace')

readed_df = pd.read_sql("SELECT * FROM '078930'", con, index_col = 'Date')
'''

# 키움증권 OpenAPI+를 통해 일봉 데이터 SQLite에 저장 처리 
''' 
import sys
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
import time
import pandas as pd
import sqlite3

TR_REQ_TIME_INTERVAL = 0.2

class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        self._create_kiwoom_instance()
        self._set_signal_slots()

    def _create_kiwoom_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def _set_signal_slots(self):
        self.OnEventConnect.connect(self._event_connect)
        self.OnReceiveTrData.connect(self._receive_tr_data)

    def comm_connect(self):
        self.dynamicCall("CommConnect()")
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

    def _event_connect(self, err_code):
        if err_code == 0:
            print("connected")
        else:
            print("disconnected")

        self.login_event_loop.exit()

    def get_code_list_by_market(self, market):
        code_list = self.dynamicCall("GetCodeListByMarket(QString)", market)
        code_list = code_list.split(';')
        return code_list[:-1]

    def get_master_code_name(self, code):
        code_name = self.dynamicCall("GetMasterCodeName(QString)", code)
        return code_name

    def set_input_value(self, id, value):
        self.dynamicCall("SetInputValue(QString, QString)", id, value)

    def comm_rq_data(self, rqname, trcode, next, screen_no):
        self.dynamicCall("CommRqData(QString, QString, int, QString", rqname, trcode, next, screen_no)
        self.tr_event_loop = QEventLoop()
        self.tr_event_loop.exec_()

    def _comm_get_data(self, code, real_type, field_name, index, item_name):
        ret = self.dynamicCall("CommGetData(QString, QString, QString, int, QString", code,
                               real_type, field_name, index, item_name)
        return ret.strip()

    def _get_repeat_cnt(self, trcode, rqname):
        ret = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
        return ret

    def _receive_tr_data(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):
        if next == '2':
            self.remained_data = True
        else:
            self.remained_data = False

        if rqname == "opt10081_req":
            self._opt10081(rqname, trcode)

        try:
            self.tr_event_loop.exit()
        except AttributeError:
            pass

    def _opt10081(self, rqname, trcode):
        data_cnt = self._get_repeat_cnt(trcode, rqname)

        for i in range(data_cnt):
            date = self._comm_get_data(trcode, "", rqname, i, "일자")
            open = self._comm_get_data(trcode, "", rqname, i, "시가")
            high = self._comm_get_data(trcode, "", rqname, i, "고가")
            low = self._comm_get_data(trcode, "", rqname, i, "저가")
            close = self._comm_get_data(trcode, "", rqname, i, "현재가")
            volume = self._comm_get_data(trcode, "", rqname, i, "거래량")

            self.ohlcv['date'].append(date)
            self.ohlcv['open'].append(int(open))
            self.ohlcv['high'].append(int(high))
            self.ohlcv['low'].append(int(low))
            self.ohlcv['close'].append(int(close))
            self.ohlcv['volume'].append(int(volume))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    kiwoom = Kiwoom()
    kiwoom.comm_connect()

    kiwoom.ohlcv = {'date': [], 'open': [], 'high': [], 'low': [], 'close': [], 'volume': []}

    # opt10081 TR 요청
    kiwoom.set_input_value("종목코드", "039490")
    kiwoom.set_input_value("기준일자", "20170224")
    kiwoom.set_input_value("수정주가구분", 1)
    kiwoom.comm_rq_data("opt10081_req", "opt10081", 0, "0101")

    while kiwoom.remained_data == True:
        time.sleep(TR_REQ_TIME_INTERVAL)
        kiwoom.set_input_value("종목코드", "039490")
        kiwoom.set_input_value("기준일자", "20170224")
        kiwoom.set_input_value("수정주가구분", 1)
        kiwoom.comm_rq_data("opt10081_req", "opt10081", 2, "0101")

    df = pd.DataFrame(kiwoom.ohlcv, columns=['open', 'high', 'low', 'close', 'volume'], index=kiwoom.ohlcv['date'])

    con = sqlite3.connect("stock.db")
    df.to_sql('039490', con, if_exists='replace')
'''