##################################################
#
#          stock_v6 program
#
##################################################

##################################################
#
# 개요 - 프로세스 설명
#
# 프로그램 실행 유효 시간 : 09:05 ~ 15:00
#
# 네이버 주식 (https://finance.naver.com/) Site - Crawling
#
# 1.주식 사이트 정보를 Crawling 하여 대상 종목 선정
#
# 2.임시 저장 좀목 시세별 시세 모니터링 ( status : P )
# - 일별 / 시세별 데이타  거래량 모니터링 분석 
# - 투자자 보호 대상 종목 제외
# - 분석된 결과를 토대로 한 종목의 상태를 I 갱신 후 임시 항목 삭제
#
# 3.저장 종목 모니터링 및 매도/매수 알림 
# - stock_v6테이블 status 컬럼 값이 I 인 종목 대상
# - 배치 주기에 따른 종목별 상세 데이타 모니터링 
# - 등락율 SELL_UP_RATE , SELL_DOWN_RATE 시 매매 (status : C)
# - 매도/매수 처리 시 telegram 알림 전송
#
##################################################
#
# > seqlite3 install  && sqlite location PATH add
#
# > create table schema
#   - sqlite3 stock.db
# 
#   create table stock_v6_x_meta (current_amt text);
#   insert into stock_v6_x_meta (current_amt) values ('500000');
#
#   create table stock_v6_x (id integer primary key autoincrement, code text, item text, status text
#       , purchase_current_amt text , sell_current_amt text, purchase_count text
#       , purchase_amt text , sell_amt text, crt_dttm text, chg_dttm text);
#
# > telegram setting
#   BotFather -> /newbot -> devsunetstock -> devsunsetstock_bot - > get api key 
# 
##################################################
# import

import sys
import sqlite3
import datetime
import math
import unicodedata
import random
# install library
# $ pip install requests beautifulsoup4 apscheduler python-telegram-bot
import requests
import bs4
import telegram
from apscheduler.schedulers.blocking import BlockingScheduler
##################################################
# constant

# proxy use
PROXY_USE_FLAG = False
# Proxy info
HTTP_PROXY  = "http://xxx.xxx.xxx.xxx:xxxx"
HTTPS_PROXY = "http://xxx.xxx.xxx.xxx:xxxx"
PROXY_DICT = { 
              "http"  : HTTP_PROXY, 
              "https" : HTTPS_PROXY
            }
# 선택 종목 금액 MAX
CURRENT_AMOUNT_MAX = 150000
# 프로그램 실행 주기 
INTERVAL_SECONDS = 60
# sell rate up 
SELL_UP_RATE = 1.5
# sell rate down
SELL_DOWN_RATE = -0.5   
# 최근 종가 체크 단위 일수 
RECENT_DAY_UNIT = 3
# 종목 체크 최대 갯수
MAX_STOCK_ITEM = 30
# 프로그램 시작 시간
START_TIME = "090005"
# 프로그램 종료 시간
END_TIME = "150000"
# base url
BASE_URL = "https://finance.naver.com"
# crawling target
CRAWLING_TARGET = [
 {'idx':0,'title':'검색상위 종목','url':'/sise/lastsearch2.nhn','css_class':'type_5','sortIdx':10 , 'reverse':False ,'checklength':12, 'codeNameIdx':1,'current_amtIdx':3,'uprateIdx':5}   
,{'idx':1,'title':'시가총액 코스피','url':'/sise/sise_market_sum.nhn?sosok=0','css_class':'type_2','sortIdx':10 , 'reverse':False ,'checklength':13, 'codeNameIdx':1,'current_amtIdx':2,'uprateIdx':4}   
,{'idx':2,'title':'시가총액 코스닥','url':'/sise/sise_market_sum.nhn?sosok=1','css_class':'type_2','sortIdx':10 , 'reverse':False ,'checklength':13, 'codeNameIdx':1,'current_amtIdx':2,'uprateIdx':4}
,{'idx':3,'title':'상승 코스피','url':'/sise/sise_rise.nhn?sosok=0','css_class':'type_2','sortIdx':10 , 'reverse':False ,'checklength':12, 'codeNameIdx':1,'current_amtIdx':2,'uprateIdx':4}
,{'idx':4,'title':'상승 코스닥','url':'/sise/sise_rise.nhn?sosok=1','css_class':'type_2','sortIdx':10 , 'reverse':False ,'checklength':12, 'codeNameIdx':1,'current_amtIdx':2,'uprateIdx':4}
,{'idx':5,'title':'상한가 코스피/코스닥','url':'/sise/sise_upper.nhn','css_class':'type_5','sortIdx':11 , 'reverse':False ,'checklength':12, 'codeNameIdx':3,'current_amtIdx':4,'uprateIdx':6}
,{'idx':6,'title':'저가대비급등 코스피','url':'/sise/sise_low_up.nhn?sosok=0','css_class':'type_2','sortIdx':10 , 'reverse':False ,'checklength':12, 'codeNameIdx':2,'current_amtIdx':3,'uprateIdx':5}
,{'idx':7,'title':'저가대비급등 코스닥','url':'/sise/sise_low_up.nhn?sosok=1','css_class':'type_2','sortIdx':10 , 'reverse':False ,'checklength':12, 'codeNameIdx':2,'current_amtIdx':3,'uprateIdx':5}
,{'idx':8,'title':'거래상위 코스피','url':'/sise/sise_quant.nhn?sosok=0','css_class':'type_2','sortIdx':10 , 'reverse':False ,'checklength':12, 'codeNameIdx':1,'current_amtIdx':2,'uprateIdx':4}
,{'idx':9,'title':'거래상위 코스닥','url':'/sise/sise_quant.nhn?sosok=1','css_class':'type_2','sortIdx':10 , 'reverse':False ,'checklength':12, 'codeNameIdx':1,'current_amtIdx':2,'uprateIdx':4}
,{'idx':10,'title':'거래량 급증 코스피','url':'/sise/sise_quant_high.nhn?sosok=0','css_class':'type_2','sortIdx':10 , 'reverse':False ,'checklength':11, 'codeNameIdx':2,'current_amtIdx':3,'uprateIdx':5}
,{'idx':11,'title':'거래량 급증 코스닥','url':'/sise/sise_quant_high.nhn?sosok=1','css_class':'type_2','sortIdx':10 , 'reverse':False ,'checklength':11, 'codeNameIdx':2,'current_amtIdx':3,'uprateIdx':5}
,{'idx':12,'title':'신규상장종목 코스피','url':'/sise/sise_new_stock.nhn?sosok=0','css_class':'type_2','sortIdx':10 , 'reverse':False ,'checklength':12, 'codeNameIdx':2,'current_amtIdx':3,'uprateIdx':5}
,{'idx':13,'title':'신규상장종목 코스닥','url':'/sise/sise_new_stock.nhn?sosok=1','css_class':'type_2','sortIdx':10 , 'reverse':False ,'checklength':12, 'codeNameIdx':2,'current_amtIdx':3,'uprateIdx':5}
,{'idx':14,'title':'외국인보유현황 코스피','url':'/sise/sise_foreign_hold.nhn?sosok=0','css_class':'type_2','sortIdx':8 , 'reverse':False ,'checklength':10, 'codeNameIdx':1,'current_amtIdx':2,'uprateIdx':4}
,{'idx':15,'title':'외국인보유현황 코스닥','url':'/sise/sise_foreign_hold.nhn?sosok=1','css_class':'type_2','sortIdx':8 , 'reverse':False ,'checklength':10, 'codeNameIdx':1,'current_amtIdx':2,'uprateIdx':4}
,{'idx':16,'title':'골든크로스 종목','url':'/sise/item_gold.nhn','css_class':'type_5','sortIdx':9 , 'reverse':False ,'checklength':11, 'codeNameIdx':1,'current_amtIdx':2,'uprateIdx':4}
,{'idx':17,'title':'갭상승 종목','url':'/sise/item_gap.nhn','css_class':'type_5','sortIdx':9 , 'reverse':False ,'checklength':11, 'codeNameIdx':1,'current_amtIdx':2,'uprateIdx':4}
,{'idx':18,'title':'이격도과열 종목','url':'/sise/item_igyuk.nhn','css_class':'type_5','sortIdx':9 , 'reverse':False ,'checklength':11, 'codeNameIdx':1,'current_amtIdx':2,'uprateIdx':4}
,{'idx':19,'title':'투자심리과열 종목','url':'/sise/item_overheating_1.nhn','css_class':'type_5','sortIdx':9 , 'reverse':False ,'checklength':11, 'codeNameIdx':1,'current_amtIdx':2,'uprateIdx':4}
,{'idx':20,'title':'상대강도과열 종목','url':'/sise/item_overheating_2.nhn','css_class':'type_5','sortIdx':9 , 'reverse':False ,'checklength':11, 'codeNameIdx':1,'current_amtIdx':2,'uprateIdx':4}
] 
CRAWING_EXCLUDE_TARGET =[
 {'idx':0,'title':'관리종목','url':'/sise/management.nhn'}
,{'idx':1,'title':'거래정지종목','url':'/sise/trading_halt.nhn'}
,{'idx':2,'title':'시장경보 - 투자 주의 종목','url':'/sise/investment_alert.nhn?type=caution'}
,{'idx':3,'title':'시장경보 - 투자 경보 종목','url':'/sise/investment_alert.nhn?type=warning'}
,{'idx':4,'title':'시장경보 - 투자 위험 종목','url':'/sise/investment_alert.nhn?type=risk'}
]      
CRAWLING_ITEM_URL = "/item/main.nhn?code="
CRAWLING_ITEM_DAY_URL = "/item/sise_day.nhn?page=1&code="
CRAWLING_ITEM_TIME_URL = "/item/sise_time.nhn?page=1&code="  
# telegram
TELEGRAM_TOKEN = '1280370073:AAHFwcNtcS9pvqF29zJJKEOY0SvnW8NH1do'
bot = telegram.Bot(token = TELEGRAM_TOKEN)
# telgram send flag
TELEGRAM_SEND_FLAG = False

##################################################
# function

# get db table all data
def searchAllData(table):
    columns = []
    result = []
    conn = sqlite3.connect("stock.db")
    with conn:
        cur = conn.cursor()   
        if table.find("_meta") > 0 :
            cur.execute("select * from "+table)
        else:
            cur.execute("select * from "+table+ " where status IN ('I','P','S') ")        
        columns = list(map(lambda x: x[0], cur.description))
        result = cur.fetchall()    
    return columns,result

# db table insert/update/delete
def executeDB(sqlText,sqlParam=None):
    conn = sqlite3.connect("stock.db")
    cur = conn.cursor()
    sql = sqlText
    if sqlParam == None:
        cur.execute(sql)
    else:
        cur.execute(sql, sqlParam)
    conn.commit()        
    conn.close()

# stock item list crawling
def getStocInfoItemList(RUN_CMD_INDEX,excludeData):
    resp = None    
    if PROXY_USE_FLAG :
        resp = requests.get(BASE_URL+CRAWLING_TARGET[RUN_CMD_INDEX]['url'],proxies=PROXY_DICT)       
    else:
        resp = requests.get(BASE_URL+CRAWLING_TARGET[RUN_CMD_INDEX]['url'])

    html = resp.text

    # 종목 데이타 구하기 
    infoData = []
    if RUN_CMD_INDEX !=5 :
        bs = bs4.BeautifulSoup(html, 'html.parser')       
        infoTable = bs.find("table",{"class":CRAWLING_TARGET[RUN_CMD_INDEX]['css_class']})    
        for a in infoTable.find_all("tr"):
            infolist = []
            for b in a.find_all("td"): 
                info = b.get_text().replace(",","").replace("%","").replace("\n","").replace("\t","")
                infolist.append(info)  
            if len(infolist) == CRAWLING_TARGET[RUN_CMD_INDEX]['checklength']:
                infoData.append(infolist)
        # print(infoData)
    else:
        bs = bs4.BeautifulSoup(html, 'html.parser')
        tags = bs.select('tr') 
        for i in range(len(tags)):    
            infolist = []
            for b in tags[i].find_all("td"): 
                info = b.get_text().replace(",","").replace("%","").replace("\n","").replace("\t","")
                infolist.append(info)  
            if len(infolist) == CRAWLING_TARGET[RUN_CMD_INDEX]['checklength']:
                infoData.append(infolist)
        # print(infoData)

    bs = bs4.BeautifulSoup(html, 'html.parser')
    tags = bs.select('a') 
    codeData = []
    for i in range(len(tags)):    
        txt = tags[i].get("href")
        if txt.find("main.nhn?code=") > 0 :
            codeData.append(txt)
    # print(codeData)    
    
    # 종목 데이타 정리 
    # - 현재가 CURRENT_AMOUNT_MAX 이하인 종목만 필터링 후 종목 코드 결합    
    if len(infoData) > MAX_STOCK_ITEM:
        infoData = infoData[0:MAX_STOCK_ITEM]

    filterData = []
    for idx, data in enumerate(infoData):
        # print(idx, data)
        # 현재가가 CURRENT_AMOUNT_MAX 이하 이며 등락율이 상승인 종목만 Filter
        if codeData[idx].replace("/item/main.nhn?code=","") not in excludeData and int(data[CRAWLING_TARGET[RUN_CMD_INDEX]['current_amtIdx']]) <= CURRENT_AMOUNT_MAX and data[CRAWLING_TARGET[RUN_CMD_INDEX]['uprateIdx']][0] == "+":
            # print(data)
            if data[CRAWLING_TARGET[RUN_CMD_INDEX]['sortIdx']] == 'N/A':
                 filterData.append((float(1) ,codeData[idx].replace("/item/main.nhn?code=","")
                , data[CRAWLING_TARGET[RUN_CMD_INDEX]['codeNameIdx']] ,data[CRAWLING_TARGET[RUN_CMD_INDEX]['current_amtIdx']]))
            else:
                filterData.append((float(data[CRAWLING_TARGET[RUN_CMD_INDEX]['sortIdx']]) ,codeData[idx].replace("/item/main.nhn?code=","")
                , data[CRAWLING_TARGET[RUN_CMD_INDEX]['codeNameIdx']] ,data[CRAWLING_TARGET[RUN_CMD_INDEX]['current_amtIdx']]))

    #정렬
    filterData.sort(key = lambda element : element[0],reverse=CRAWLING_TARGET[RUN_CMD_INDEX]['reverse'])
    # if len(filterData) > 0 :
    #     for idx, data in enumerate(filterData):
    #         print("추천 종목 ",idx,":",data)
    return filterData

# exclude stock item list crawling
def getExcludeStocInfoItemList():
    resp = None    
    codeData = []

    for idx, data in enumerate(CRAWING_EXCLUDE_TARGET):      
        if PROXY_USE_FLAG :
            resp = requests.get(BASE_URL+CRAWING_EXCLUDE_TARGET[idx]['url'],proxies=PROXY_DICT)       
        else:
            resp = requests.get(BASE_URL+CRAWING_EXCLUDE_TARGET[idx]['url'])

        html = resp.text

        bs = bs4.BeautifulSoup(html, 'html.parser')
        tags = bs.select('a') 
        
        for i in range(len(tags)):    
            txt = tags[i].get("href")
            if txt.find("main.nhn?code=") > 0 :
                codeData.append(txt.replace("/item/main.nhn?code=",""))
        # print(codeData)    

    return codeData

# item day trend data crawling
def getStocItemDayInfo(stock_code):
    # log('--- stock item day trend ---'+stock_code,"N")
    resp = None
    if PROXY_USE_FLAG :
        resp = requests.get(BASE_URL+CRAWLING_ITEM_DAY_URL+stock_code,proxies=PROXY_DICT)       
    else:
        resp = requests.get(BASE_URL+CRAWLING_ITEM_DAY_URL+stock_code)       

    html = resp.text

    # 종목 일별 시세 구하기 
    bs = bs4.BeautifulSoup(html, 'html.parser')
    infoTable = bs.find("table",{"class":"type2"})
    infoData = []
    for a in infoTable.find_all("tr"):
        infolist = []
        for b in a.find_all("td"): 
            info = b.get_text().replace("\n","").replace("\t","")
            infolist.append(info)
            if len(infolist) == 7:
                infoData.append(infolist)
                # print(infolist)   

    return infoData             

# item time trend data crawling
def getStocItemTimeInfo(stock_code):
    # log('--- stock item time trend ---'+stock_code,"N")
    resp = None
    if PROXY_USE_FLAG :
        resp = requests.get(BASE_URL+CRAWLING_ITEM_TIME_URL+stock_code+"&thistime="+datetime.datetime.now().strftime("%Y%m%d%H%M%S"),proxies=PROXY_DICT)       
    else:
        resp = requests.get(BASE_URL+CRAWLING_ITEM_TIME_URL+stock_code+"&thistime="+datetime.datetime.now().strftime("%Y%m%d%H%M%S"))       

    html = resp.text

    # 종목 시간별 시세 구하기 
    bs = bs4.BeautifulSoup(html, 'html.parser')
    infoTable = bs.find("table",{"class":"type2"})
    infoData = []
    for a in infoTable.find_all("tr"):
        infolist = []
        for b in a.find_all("td"): 
            info = b.get_text().replace("\n","").replace("\t","")
            infolist.append(info)
            if len(infolist) == 7:
                infoData.append(infolist)
                # print(infolist)
    
    return infoData

# stock info deatail data crawling
def getStocInfoData(data,status,VERSION_META_TABLE,VERSION_TABLE):
    resp = None
    if PROXY_USE_FLAG :
        resp = requests.get(BASE_URL+CRAWLING_ITEM_URL+data[1],proxies=PROXY_DICT)        
    else:
        resp = requests.get(BASE_URL+CRAWLING_ITEM_URL+data[1])
        
    html = resp.text
    bs = bs4.BeautifulSoup(html, 'html.parser')    

    arrow = "△"
    current_Amt = bs.find("em",{"class":"no_up"}).find("span",{"class":"blind"}).get_text()

    if current_Amt == None :
        arrow = "▼"
        current_Amt = bs.find("em",{"class":"no_down"}).find("span",{"class":"blind"}).get_text()

    if data[3] == "I" :
        item_text = arrow+" : 종목 : "+fill_str_space(data[2],25) 
        item_text +=" 구매수 : "+fill_str_space(data[6])
        item_text +=" 구매가 : "+fill_str_space(format(int(data[4]), ','))
        item_text +=" 현재가 : "+fill_str_space(current_Amt)
        item_text +=" 등락가 : "+fill_str_space(str(format(int(current_Amt.replace(",",""))-int(data[4]),',')))
        item_text +=" 구매금액 : "+fill_str_space(str(format(int(data[7]), ',')))
        item_text +=" 현재금액 : "+fill_str_space(str(format(int(current_Amt.replace(",",""))*int(data[6]),',')))
        item_text +=" 등락율 : "+ fill_str_space(str(round(((int(current_Amt.replace(",",""))*int(data[6])) - int(data[7])) / int(data[7]) * 100 ,2))+"%")
        item_text +=" 수익금액 : "+fill_str_space(str(format(int(current_Amt.replace(",",""))*int(data[6]) - int(data[7]),',')))

        log(item_text,"N")
        processing = True

        if (round(((int(current_Amt.replace(",",""))*int(data[6])) - int(data[7])) / int(data[7]) * 100 ,2) >= SELL_UP_RATE) :
            sellStock(data,current_Amt,VERSION_META_TABLE,VERSION_TABLE,'▲ sell : '+item_text)
            processing = False

        if (round(((int(current_Amt.replace(",",""))*int(data[6])) - int(data[7])) / int(data[7]) * 100 ,2) <= SELL_DOWN_RATE) :
            sellStock(data,current_Amt,VERSION_META_TABLE,VERSION_TABLE,'▼ sell : '+item_text)
            processing = False

        if processing and status == "CLOSE":
            sellStock(data,current_Amt,VERSION_META_TABLE,VERSION_TABLE,'close market - sell : '+item_text)

    elif data[3] == "S" :
        item_text = arrow+" : 종목 : "+fill_str_space(data[2],25) 
        item_text +=" 구매수 : "+fill_str_space(data[6])
        item_text +=" 구매가 : "+fill_str_space(format(int(data[4]), ','))
        item_text +=" 현재가 : "+fill_str_space(current_Amt)
        item_text +=" 등락가 : "+fill_str_space(str(format(int(current_Amt.replace(",",""))-int(data[4]),',')))
        item_text +=" 구매금액 : "+fill_str_space(str(format(int(data[7]), ',')))
        item_text +=" 현재금액 : "+fill_str_space(str(format(int(current_Amt.replace(",",""))*int(data[6]),',')))
        item_text +=" 등락율 : "+ fill_str_space(str(round(((int(current_Amt.replace(",",""))*int(data[6])) - int(data[7])) / int(data[7]) * 100 ,2))+"%")
        item_text +=" 수익금액 : "+fill_str_space(str(format(int(current_Amt.replace(",",""))*int(data[6]) - int(data[7]),',')))

        log(item_text,"N")

        sellStock(data,current_Amt,VERSION_META_TABLE,VERSION_TABLE,'force sell : '+item_text)
        
    return current_Amt

# temp pusrchase stock
def tempPurchaseStock(stockData,VERSION_META_TABLE,VERSION_TABLE):
    nowTime = int(datetime.datetime.now().strftime("%H%M%S"))   

    if int(START_TIME) <=  nowTime and nowTime <= int(END_TIME):
        if len(stockData) > 0 :
            fundCol,fundData = searchAllData(VERSION_META_TABLE)         
            crt_dttm = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")          
            if len(fundData) > 0 :
                for idx, data in enumerate(stockData):
                    if int(fundData[0][0]) >= int((data[3])) :
                        sql = """insert into """+VERSION_TABLE+""" (code, item, status, crt_dttm) values (?, ?, ?, ?)"""
                        sqlParam = (data[1], data[2], "P" , crt_dttm)
                        executeDB(sql,sqlParam)
            log('--- temp stock info save ---',"N")

            purchaseCol, purchaseData = searchAllData(VERSION_TABLE)    
            if len(purchaseData) > 0:
                stockMonitoring(purchaseData,VERSION_META_TABLE,VERSION_TABLE)
        else:
            log('--- stock item list empty ---',"N")  
    else:
        log('--- stock market close ---',"N")  

# purchase stock
def purchaseStock(stockData,current_Amt,VERSION_META_TABLE,VERSION_TABLE):
    current_Amt = current_Amt.replace(",","")
    chg_dttm = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")    
    fundCol,fundData = searchAllData(VERSION_META_TABLE)      
    purchase_count = math.floor(int(fundData[0][0])/int(current_Amt))
    purchase_amt = purchase_count * int(current_Amt)  
    sql = "update "+VERSION_TABLE+" set status= ?, purchase_current_amt =? , purchase_count = ?, purchase_amt = ?, chg_dttm = ? where id = ?"
    sqlParam =  ("I" , current_Amt , purchase_count, purchase_amt , chg_dttm , stockData[0])
    executeDB(sql,sqlParam)    

    sql = "update "+VERSION_META_TABLE+" set current_amt = current_amt - "+str(purchase_amt)
    executeDB(sql)   

    tmpIdx = VERSION_META_TABLE
    tmpIdx = tmpIdx.replace("stock_v6_","").replace("_meta","")
    log('['+CRAWLING_TARGET[int(tmpIdx)]['title']+'] purchase :'+str(stockData),"Y")     

# sell stock
def sellStock(stockData,current_Amt,VERSION_META_TABLE,VERSION_TABLE,msg):
    chg_dttm = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sell_amt = int(current_Amt.replace(",",""))*int(stockData[6])
    sql = "update "+VERSION_TABLE+" set status= ?, sell_current_amt = ?, sell_amt = ? ,chg_dttm = ? where id = ?"
    sqlParam =  ('C' , current_Amt , sell_amt , chg_dttm , stockData[0])
    executeDB(sql,sqlParam)

    sql = "update "+VERSION_META_TABLE+" set current_amt = current_amt + "+str(sell_amt)
    executeDB(sql)

    tmpIdx = VERSION_META_TABLE
    tmpIdx = tmpIdx.replace("stock_v6_","").replace("_meta","")
    log('['+CRAWLING_TARGET[int(tmpIdx)]['title']+'] '+msg,"Y")

# delete temp stock
def deleteTempStock(VERSION_TABLE):
    chg_dttm = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = "delete from  "+VERSION_TABLE+" where status = ? "
    sqlParam =  ("P")
    executeDB(sql,sqlParam)
    log('--- temp stock info delete ---',"N")

# stock monitoring
def stockMonitoring(purchaseData,VERSION_META_TABLE,VERSION_TABLE):   
    nowTime = int(datetime.datetime.now().strftime("%H%M%S"))
    if int(START_TIME) <=  nowTime and nowTime <= int(END_TIME):
        log('--- stock monitoring ---',"N")
        initStock = False    
        for idx, data in enumerate(purchaseData):
            if "P" == data[3]:
                initStock = True
                break

        if initStock == True:
            choiceStock(purchaseData,VERSION_META_TABLE,VERSION_TABLE)
        else:         
            for idx, data in enumerate(purchaseData):
                getStocInfoData(data,"ING",VERSION_META_TABLE,VERSION_TABLE)
    else:
        log('--- stock market close ---',"N")
        for idx, data in enumerate(purchaseData):
            getStocInfoData(data,"CLOSE",VERSION_META_TABLE,VERSION_TABLE)

# telegram message send
def send_telegram_msg(msg):
  try:
    bot.deleteWebhook()
    chat_id = bot.getUpdates()[-1].message.chat.id
    # bot sendMessage
    bot.sendMessage(chat_id = chat_id, text=msg)
  except Exception as err:
    print(err)

# log 
def log(msg,push_yn):
    if TELEGRAM_SEND_FLAG:
        push_yn = push_yn
    else:
        push_yn = "N"

    if push_yn == 'Y' :
        send_telegram_msg(msg)
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+" : "+msg)
    else:
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+" : "+msg)

# fill space
def fill_str_space(input_s="", max_size=10, fill_char=" "):
    l = 0 
    for c in input_s:
        if unicodedata.east_asian_width(c) in ['F', 'W']:
            l+=2
        else: 
            l+=1
    return input_s+fill_char*(max_size-l)

# main process
def main_process():   
    excludeData = getExcludeStocInfoItemList()
    for idx, data in enumerate(CRAWLING_TARGET):  
        print('python stock_v6.py ',idx ,data['title'])
        RUN_CMD_INDEX = idx
        VERSION_META_TABLE = 'stock_v6_'+str(idx)+'_meta'
        VERSION_TABLE = 'stock_v6_'+str(idx)
        # serarch stock version table table data
        purchaseCol, purchaseData = searchAllData(VERSION_TABLE)    
        # pusrchase stock empty
        if len(purchaseData) == 0:
            stockData = getStocInfoItemList(RUN_CMD_INDEX,excludeData)
            # Temp purchase stock save
            tempPurchaseStock(stockData,VERSION_META_TABLE,VERSION_TABLE)
        else:    
            # stock monitoring
            stockMonitoring(purchaseData,VERSION_META_TABLE,VERSION_TABLE)

##################################################

# choice stock (To-Do)          
def choiceStock(stockData,VERSION_META_TABLE,VERSION_TABLE):
    selectStocks = []
    if len(stockData) > 0 :
    # ----------------------------------------------------------------
    # Filter Condition
        # 일별 시세 종가 값이 최근 RECENT_DAY_UNIT 일 동안 증가 중인 항목
        # 시간별 시세 체결가 값이 어제의 종가 보다 높은 항목        
    # ----------------------------------------------------------------        
        for idx, data in enumerate(stockData):                 
                dayData = getStocItemDayInfo(data[1])    
                timeData = getStocItemTimeInfo(data[1])  

                if len(dayData) > 1:
                    filter_yn = True 
                    # 어제 종가 
                    yesterday_end_amt = int(dayData[1][1].replace(",",""))

                    for j, time in enumerate(timeData):    
                        try:
                            if int(time[1].replace(",","")) >= yesterday_end_amt:
                                filter_yn = True 
                            else:
                                filter_yn = False
                                break
                        except:
                           filter_yn = False   
                                                         
                    if filter_yn == True:
                        # 최종 종가  
                        try:
                            end_amt = int(dayData[0][1].replace(",",""))
                        except:
                           filter_yn = False   

                        for i, day in enumerate(dayData):
                            try:
                                if end_amt >= int(day[1].replace(",","")):
                                    filter_yn = True
                                    end_amt = int(day[1].replace(",",""))
                                else:
                                    filter_yn = False
                                    break
                            except:
                                filter_yn = False     

                            if i == RECENT_DAY_UNIT:
                                break
                        
                        if filter_yn == True:
                            selectStocks.append(data)

        # print(selectStocks)
            
    # purchase stock
    if len(selectStocks) > 0:
        # randomIdx = random.randint(1,len(selectStocks)) -1
        randomIdx = 0
        current_amt =  getStocInfoData(selectStocks[randomIdx],"ING",VERSION_META_TABLE,VERSION_TABLE)
        purchaseStock(selectStocks[randomIdx],current_amt,VERSION_META_TABLE,VERSION_TABLE)      

    # delete temp stock
    deleteTempStock(VERSION_TABLE)

##################################################
if __name__ == '__main__':
    scheduler = BlockingScheduler()
    scheduler.add_job(main_process, 'interval', seconds=INTERVAL_SECONDS)
    main_process()
    try:
        scheduler.start()
    except Exception as err:
        print(err)
##################################################

