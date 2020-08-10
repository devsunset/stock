# - PER(Price Earning Ratio, 주가 이익 비율) (대신증권 CYBOS Plus)
    # 주가를 주당순이익(EPS)으로 나눈 값 (주가의 수익성 지표)
    # 높은 PER은 주가가 고평가 , 낮은 PER은 주가가 저평가
    # ex)A사의 주가가 5만 원이고 1주당 순이익이 1만 원이면 PER은 5

# - 업종별 PER 분석을 통한 유망 종목 찾기
    # 종목이 속하는 업종의 평균 PER을 구한 후 평균값보다 낮다면 상대적으로 저평가 돼 
    # 있다고 판단하고, 평균보다 높다면 고평가돼 있다고 판단
    # 투자하려는 종목과 비슷한 규모의 회사 위주로 평가 그룹을 정하고 해당 그룹에 대한 평균 PER 값을 분석

# 출처 :  파이썬으로 배우는 알고리즘 트레이딩 - https://wikidocs.net/3836
# https://github.com/pystockhub/book

import win32com.client

instCpCodeMgr = win32com.client.Dispatch("CpUtil.CpCodeMgr")
instMarketEye = win32com.client.Dispatch("CpSysDib.MarketEye")

tarketCodeList = instCpCodeMgr.GetGroupCodeList(5)

# Get PER
instMarketEye.SetInputValue(0, 67)
instMarketEye.SetInputValue(1, tarketCodeList)

# BlockRequest
instMarketEye.BlockRequest()

# GetHeaderValue
numStock = instMarketEye.GetHeaderValue(2)

# GetData
sumPer = 0
for i in range(numStock):
    sumPer += instMarketEye.GetDataValue(0, i)

print("Average PER: ", sumPer / numStock)