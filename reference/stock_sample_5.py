# - Zipline (test)

# 출처 :  파이썬으로 배우는 알고리즘 트레이딩 - https://wikidocs.net/4429
# https://github.com/pystockhub/book

import pandas_datareader.data as web
import datetime
import matplotlib.pyplot as plt
from zipline.api import order, symbol
from zipline.algorithm import TradingAlgorithm

# data
start = datetime.datetime(2010, 1, 1)
end = datetime.datetime(2016, 3, 19)
data = web.DataReader("AAPL", "yahoo", start, end)

data = data[['Adj Close']]
data.columns = ['AAPL']
data = data.tz_localize('UTC')

def initialize(context):
    pass

def handle_data(context, data):
    order(symbol('AAPL'), 1)

algo = TradingAlgorithm(initialize=initialize, handle_data=handle_data)
result = algo.run(data)

plt.plot(result.index, result.portfolio_value)
plt.show()