# - 골든크로스, 데드크로스 - Zipline (test)
    # 골든크로스는 단기 이동평균선이 중·장기 이동평균선을 아래에서 위로 상향 돌파하면서 생기는 교차점입니다.
    # 이동평균선이 일정 기간의 주가의 평균값을 의미하므로 골든크로스가 발생했다는 것은 최근 주가의 흐름이 강세로 접어들었음을 의미합니다.

    # 데드크로스란 단기 이동평균선이 중·장기 이동평균선을 위에서 아래로 하향 돌파하면서 생기는 교차점을 의미합니다.
    # 데드크로스는 골든크로스와 반대로 최근 주가의 흐름이 약세로 접어들었음을 의미합니다.

    # 골든크로스와 데드크로스를 계산할 때 단기 이동평균선으로는 5일 주가 이동평균선을 사용하며 
    # 중·장기 이동평균선으로 20일 주가 이동평균선을 사용합니다. 또는 20일 주가 이동평균선과 60일 
    # 주가 이동평균선을 각각 단기와 중·장기 이동평균선으로 사용하기도 합니다.

    # 일반적인 골든크로스/데드크로스 전략은 골든크로스 지점에서 주식을 매수하고 매수한 주식을 데드크로스 지점에서 매도합니다.

# 출처 :  파이썬으로 배우는 알고리즘 트레이딩 - https://wikidocs.net/4583 , https://wikidocs.net/4584
# https://github.com/pystockhub/book

import pandas_datareader.data as web
import datetime
import matplotlib.pyplot as plt
from zipline.api import order_target, record, symbol
from zipline.algorithm import TradingAlgorithm

start = datetime.datetime(2010, 1, 1)
end = datetime.datetime(2016, 3, 29)
data = web.DataReader("AAPL", "yahoo", start, end)

data = data[['Adj Close']]
data.columns = ['AAPL']
data = data.tz_localize('UTC')

def initialize(context):
    context.i = 0
    context.sym = symbol('AAPL')
    context.hold = False

def handle_data(context, data):
    context.i += 1
    if context.i < 20:
        return

    buy = False
    sell = False

    ma5 = data.history(context.sym, 'price', 5, '1d').mean()
    ma20 = data.history(context.sym, 'price', 20, '1d').mean()

    if ma5 > ma20 and context.hold == False:
        order_target(context.sym, 100)
        context.hold = True
        buy = True
    elif ma5 < ma20 and context.hold == True:
        order_target(context.sym, -100)
        context.hold = False
        sell = True

    record(AAPL=data.current(context.sym, "price"), ma5=ma5, ma20=ma20, buy=buy, sell=sell)

algo = TradingAlgorithm(initialize=initialize, handle_data=handle_data)
result = algo.run(data)