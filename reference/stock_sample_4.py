# - 이동평균선
    # 일정 기간 동안의 주가를 산술 평균한 값인 주가이동평균을 차례로 연결해 만든 선

# 출처 :  파이썬으로 배우는 알고리즘 트레이딩 - https://wikidocs.net/4375
# https://github.com/pystockhub/book

import pandas as pd
import pandas_datareader.data as web
import matplotlib.pyplot as plt

# Get GS Data from Yahoo
gs = web.DataReader("078930.KS", "yahoo", "2014-01-01", "2016-03-06")
new_gs = gs[gs['Volume']!=0]

# Moving average
ma5 = new_gs['Adj Close'].rolling(window=5).mean()
ma20 = new_gs['Adj Close'].rolling(window=20).mean()
ma60 = new_gs['Adj Close'].rolling(window=60).mean()
ma120 = new_gs['Adj Close'].rolling(window=120).mean()

# Insert columns
new_gs.insert(len(new_gs.columns), "MA5", ma5)
new_gs.insert(len(new_gs.columns), "MA20", ma20)
new_gs.insert(len(new_gs.columns), "MA60", ma60)
new_gs.insert(len(new_gs.columns), "MA120", ma120)

# Plot
plt.plot(new_gs.index, new_gs['Adj Close'], label='Adj Close')
plt.plot(new_gs.index, new_gs['MA5'], label='MA5')
plt.plot(new_gs.index, new_gs['MA20'], label='MA20')
plt.plot(new_gs.index, new_gs['MA60'], label='MA60')
plt.plot(new_gs.index, new_gs['MA120'], label='MA120')

plt.legend(loc="best")
plt.grid()
plt.show()