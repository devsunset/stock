# - 거래량 분석을 통한 대박 종목 찾기 (대신증권 CYBOS Plus)
    # 1) 대량 거래(거래량이 1,000% 이상 급증) 종목
    # 2) 대량 거래 시점에서 PBR이 4보다 작아야 함
    # ex) 최근 60일간의 평균 거래량이 30,000주 정도인 종목이 있는데 
    #     금일 거래량이 300,000주라면 이 조건을 만족

# 출처 :  파이썬으로 배우는 알고리즘 트레이딩 - https://wikidocs.net/3835
# https://github.com/pystockhub/book

import win32com.client
import time

def CheckVolumn(instStockChart, code):
    # SetInputValue
    instStockChart.SetInputValue(0, code)
    instStockChart.SetInputValue(1, ord('2'))
    instStockChart.SetInputValue(4, 60)
    instStockChart.SetInputValue(5, 8)
    instStockChart.SetInputValue(6, ord('D'))
    instStockChart.SetInputValue(9, ord('1'))

    # BlockRequest
    instStockChart.BlockRequest()

    # GetData
    volumes = []
    numData = instStockChart.GetHeaderValue(3)
    for i in range(numData):
        volume = instStockChart.GetDataValue(0, i)
        volumes.append(volume)

    # Calculate average volume
    averageVolume = (sum(volumes) - volumes[0]) / (len(volumes) -1)

    if(volumes[0] > averageVolume * 10):
        return 1
    else:
        return 0

if __name__ == "__main__":
    instStockChart = win32com.client.Dispatch("CpSysDib.StockChart")
    instCpCodeMgr = win32com.client.Dispatch("CpUtil.CpCodeMgr")
    codeList = instCpCodeMgr.GetStockListByMarket(1)

    buyList = []
    for code in codeList:
        if CheckVolumn(instStockChart, code) == 1:
            buyList.append(code)
            print(code)
        time.sleep(1)