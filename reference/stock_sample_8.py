# - matplotlib 

# matplotlib chart  basic
import pandas_datareader.data as web
import matplotlib.pyplot as plt

lg = web.DataReader("066570.KS", "yahoo")
samsung = web.DataReader("005930.KS", "yahoo")

plt.plot(lg.index, lg['Adj Close'], label='LG Electronics')
plt.plot(samsung.index, samsung['Adj Close'], label='Samsung Electronics')

plt.legend(loc='upper left')
plt.show()
# 출처 :  파이썬으로 배우는 알고리즘 트레이딩 - https://wikidocs.net/2875


# 수정 종가와 거래량 한번에 그리기
import pandas_datareader.data as web
import matplotlib.pyplot as plt

sk_hynix = web.DataReader("000660.KS", "yahoo")

fig = plt.figure(figsize=(12, 8))

top_axes = plt.subplot2grid((4,4), (0,0), rowspan=3, colspan=4)
bottom_axes = plt.subplot2grid((4,4), (3,0), rowspan=1, colspan=4)
bottom_axes.get_yaxis().get_major_formatter().set_scientific(False)

top_axes.plot(sk_hynix.index, sk_hynix['Adj Close'], label='Adjusted Close')
bottom_axes.plot(sk_hynix.index, sk_hynix['Volume'])

plt.tight_layout()
plt.show()
# 출처 :  파이썬으로 배우는 알고리즘 트레이딩 - https://wikidocs.net/4765


# - 봉차트 (캔들차트)

    # 일봉 차트를 구성하는 기본 단위인 ‘일봉’은 거래일 동안의 
    # 시가(장시작 가격), 고가(장중 최고가), 저가(장중 최저가), 종가(장마감 가격)의 
    # 네 가지 값을 한 개의 봉으로 표현

    # 일봉 중 종가가 시가보다 높은 경우를 양봉이라고 하며, 
    # 반대로 종가가 시가보다 낮은 경우를 음봉이라고 합니다. 
    # 증권사 HTS마다 다르지만 양봉은 보통 빨간색으로 표시하고 음봉은 파란색으로 표시합니다.

    # 종가와 고가 사이의 간격이 크다는 것은 하루 중에 주가가 크게 올랐다가 결국은 다시 떨어지는 것을 의미
    # 비슷하게 종가와 저가 사이의 간격이 크다는 것은 장중에 주가가 크게 떨어졌다가 
    # 장 종료 시점에는 일정 부분 상승한 채로 장이 종료됐음을 의미

    # 봉 차트에서는 시가와 종가 사이를 몸통이라고 부르고 몸통 윗부분을 머리, 몸통 아래를 꼬리라고 부릅니다.
    # 봉을 그릴 때 몸통은 두껍게 그리고 고가와 저가를 나타내는 머리나 꼬리는 얇은 실선으로 표시합니다.

    # 봉 차트를 바탕으로 주가가 약세시점에서 양봉 3개가 나타나는 것을 ‘적삼병’이라고 부르고 이를 주가 상승 장세의 시점으로 봅니다.
    # 반대로 주가가 상승 시점에 있다가 음봉 3개가 연달아서 나타나면 이를 ‘흑삼병’이라고 부르고 주가가 하락세로 전환되거나 하락세가 지속될 시점으로 판단합니다
import pandas_datareader.data as web
import datetime
import matplotlib.pyplot as plt
import mpl_finance
import matplotlib.ticker as ticker

start = datetime.datetime(2016, 3, 1)
end = datetime.datetime(2016, 3, 31)
skhynix = web.DataReader("000660.KS", "yahoo", start, end)

fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111)

day_list = []
name_list = []
for i, day in enumerate(skhynix.index):
    if day.dayofweek == 0:
        day_list.append(i)
        name_list.append(day.strftime('%Y-%m-%d') + '(Mon)')

ax.xaxis.set_major_locator(ticker.FixedLocator(day_list))
ax.xaxis.set_major_formatter(ticker.FixedFormatter(name_list))

mpl_finance.candlestick2_ohlc(ax, skhynix['Open'], skhynix['High'], skhynix['Low'], skhynix['Close'], width=0.5, colorup='r', colordown='b')
plt.grid()
plt.show()
# 출처 :  파이썬으로 배우는 알고리즘 트레이딩 - https://wikidocs.net/4766    


# Bar Chart
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager, rc
from matplotlib import style

font_name = font_manager.FontProperties(fname="c:/Windows/Fonts/malgun.ttf").get_name()
rc('font', family=font_name)
style.use('ggplot')

industry = ['통신업', '의료정밀', '운수창고업', '의약품', '음식료품', '전기가스업', '서비스업', '전기전자', '종이목재', '증권']
fluctuations = [1.83, 1.30, 1.30, 1.26, 1.06, 0.93, 0.77, 0.68, 0.65, 0.61]

fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111)

# 수평
ypos = np.arange(10)
rects = plt.barh(ypos, fluctuations, align='center', height=0.5)
plt.yticks(ypos, industry)

for i, rect in enumerate(rects):
    ax.text(0.95 * rect.get_width(), rect.get_y() + rect.get_height() / 2.0, str(fluctuations[i]) + '%', ha='right', va='center')

plt.xlabel('등락률')

# 수직
# pos = np.arange(10)
# rects = plt.bar(pos, fluctuations, align='center', width=0.5)
# plt.xticks(pos, industry)

# for i, rect in enumerate(rects):
#     ax.text(rect.get_x() + rect.get_width() / 2.0, 0.95 * rect.get_height(), str(fluctuations[i]) + '%', ha='center')

# plt.ylabel('등락률')

plt.show()
# 출처 :  파이썬으로 배우는 알고리즘 트레이딩 - https://wikidocs.net/4767


# Pie Chart
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager, rc
from matplotlib import style

font_name = font_manager.FontProperties(fname="c:/Windows/Fonts/malgun.ttf").get_name()
rc('font', family=font_name)
style.use('ggplot')

colors = ['gold', 'yellowgreen', 'lightcoral', 'lightskyblue', 'red']
labels = ['삼성전자', 'SK하이닉스', 'LG전자', '네이버', '카카오']
ratio = [50, 20, 10, 10, 10]
explode = (0.0, 0.1, 0.0, 0.0, 0.0)

plt.pie(ratio, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%', shadow=True, startangle=90)
plt.show()
# 출처 :  파이썬으로 배우는 알고리즘 트레이딩 - https://wikidocs.net/4768
# https://github.com/pystockhub/book