##################################################
#
#          stock_v_1 program
#
##################################################

##################################################
#
# 개요 - 프로세스 설명
#
# 프로그램 실행 유효 시간 : 09:00 ~ 15:20
#
# 네이버 주식 인기 종목 페이지 분석 - Crawling
# - (https://finance.naver.com/sise/lastsearch2.nhn)
#
# 종목 선택 및 DB 저장 
# - stock_v1 테이블 status 컬럼 값이 모두 I가 없는 경우
# - 등락율 ▲ 
# - 현재가 100,000 이하
# - 위 조건 중 검색률 ▲ 순으로 Filter
# - Filter 된 종목 status I 상태로 DB 저장
#
# 저장 종목 모니터링 및 매도/매수 알림 
# - stock_v1 테이블 status 컬럼 값이 I 인 종목 대상
# - 배치 주기에 따른 종목별 상세 데이타 모니터링 
# - 등락율 +1.5% , -1% 시 매매 (status C 상태로 변경)
# - 매도/매수 처리 시 telegram 알림 전송
#
##################################################
#
# > seqlite3 install  && sqlite location PATH add
#
# > create table schema
#   - sqlite3 stock.db
# 
#   create table stock_v1_meta (init_amt text ,current_amt text);
#   insert into stock_v1_meta (init_amt,current_amt) values ('300000','300000');
#
#   create table stock_v1 (id integer primary key autoincrement, code text, item text, status text
#       , purchase_current_amt text , sell_current_amt text, purchase_count text
#       , purchase_amt text , sell_amt text, search_rate text, yesterday_rate text, up_down_rate text
#       , ps_cnt text, c_amt text, h_amt text, l_amt, crt_dttm text, chg_dttm text);
#
# > telegram setting
#   BotFather -> /newbot -> devsunetstock -> devsunsetstock_bot - > get api key 
# 
##################################################
# install library
# $ pip install requests beautifulsoup4 apscheduler python-telegram-bot
import sqlite3
import datetime
import math
import unicodedata
import requests
import bs4
import telegram
from apscheduler.schedulers.blocking import BlockingScheduler
##################################################
# constant

# proxy use
PROXY_USE_FLAG = True
# Proxy info
HTTP_PROXY  = "http://70.10.15.10:8080"
HTTPS_PROXY = "http://70.10.15.10:8080"
PROXY_DICT = { 
              "http"  : HTTP_PROXY, 
              "https" : HTTPS_PROXY
            }
# VERSION TABLE
STOCK_VERSION_META_TABLE = 'stock_v1_meta'
STOCK_VERSION_TABLE = 'stock_v1'
# 선택 종목 금액 MAX
CURRENT_AMOUNT_MAX = 100000
# 프로그램 실행 주기 
INTERVAL_SECONDS = 30
# 프로그램 시작 시간
START_TIME = "090000"
# 프로그램 종료 시간
END_TIME = "150000"
# base url
BASE_URL = "https://finance.naver.com"
# crawling url
CRAWLING_TOP_LIST_URL = "/sise/lastsearch2.nhn"
CRAWLING_ITEM_URL = "/item/main.nhn?code="

# sell rate up
SELL_UP_RATE = 1.5
# sell rate down
SELL_DOWN_RATE = -1
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
        if table == STOCK_VERSION_META_TABLE :
            cur.execute("select * from "+table)
        else:
            cur.execute("select * from "+table+ " where status = 'I' ")
        columns = list(map(lambda x: x[0], cur.description))
        result = cur.fetchall()    
    return columns,result

# db table insert/update/delete
def executeDB(sqlText,sqlParam):
    conn = sqlite3.connect("stock.db")
    cur = conn.cursor()
    sql = sqlText
    cur.execute(sql, sqlParam)
    conn.commit()        
    conn.close()

# stock info top list crawling
def getStocInfoTopList():
    resp = None
    if PROXY_USE_FLAG :
        resp = requests.get(BASE_URL+CRAWLING_TOP_LIST_URL,proxies=PROXY_DICT)       
    else:
        resp = requests.get(BASE_URL+CRAWLING_TOP_LIST_URL)

    html = resp.text

    # 종목 데이타 구하기 
    bs = bs4.BeautifulSoup(html, 'html.parser')
    infoTable = bs.find("table",{"class":"type_5"})
    infoData = []
    for a in infoTable.find_all("tr"):
        infolist = []
        for b in a.find_all("td"): 
            info = b.get_text().replace(",","").replace("%","").replace("\n","").replace("\t","")
            infolist.append(info)
        if len(infolist) == 12:
            infoData.append(infolist)
    # print(infoData)

    # 종목 코드 구하기 (To-Do 종목 데이타 구할때 href 태그 함께 구할수 없을까 ?)
    bs = bs4.BeautifulSoup(html, 'html.parser')
    tags = bs.select('a') 
    codeData = []
    for i in range(len(tags)):    
        txt = tags[i].get("href")
        if txt.find("main.nhn?code=") > 0 :
            codeData.append(txt)
    # print(codeData)

    # 종목 데이타 정리 
    # - 등락율 상승 종목 이며 현재가 CURRENT_AMOUNT_MAX 이하인 종목만 필터링 후 종목 코드 결합
    filterData = []
    for idx, data in enumerate(infoData):
        # print(idx, data)
        # 0 순위 | 1 종목명 | 2 검색비율 | 3 현재가 | 4 전일비 | 5 등락률 | 6 거래량 | 7 시가 | 8 고가 | 9 저가 | 10 PER | 11 ROE
        if int(data[3]) <= CURRENT_AMOUNT_MAX and data[5][0] == "+":
            # print(data)
            filterData.append((float(data[2]) ,codeData[idx].replace("/item/main.nhn?code=","")
            ,data[1] ,data[2] ,data[3] ,data[4] ,data[5]
            ,data[6] ,data[7] ,data[8] ,data[9]))
    # print(filterData)

    # 검색율 내림 차순 정렬
    filterData.sort(key = lambda element : element[0],reverse=True)
    # if len(filterData) > 0 :
    #     for idx, data in enumerate(filterData):
    #         print("추천 종목 ",idx,":",data)
    return filterData

# stock info deatail data crawling
def getStocInfoData(data,status):
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

    item_text = arrow+" : 종목 : "+fill_str_space(data[2],25) 
    item_text +=" 구매수 : "+fill_str_space(data[6])
    item_text +=" 구매가 : "+fill_str_space(format(int(data[4]), ','))
    item_text +=" 현재가 : "+fill_str_space(current_Amt)
    item_text +=" 등락가 : "+fill_str_space(str(format(int(current_Amt.replace(",",""))-int(data[4]),',')))
    item_text +=" 구매금액 : "+fill_str_space(str(format(int(data[7]), ',')))
    item_text +=" 현재금액 : "+fill_str_space(str(format(int(current_Amt.replace(",",""))*int(data[6]),',')))
    item_text +=" 등락율 : "+ fill_str_space(str(round(((int(current_Amt.replace(",",""))*int(data[6])) - int(data[7])) / int(data[7]) * 100 ,2))+"%")
    item_text +=" 수익금액 : "+fill_str_space(str(format(int(current_Amt.replace(",",""))*int(data[6]) - int(data[7]),',')))
    
    print(item_text)

    if (round(((int(current_Amt.replace(",",""))*int(data[6])) - int(data[7])) / int(data[7]) * 100 ,2) >= SELL_UP_RATE) :
        sellStock(data,current_Amt)
        log('▲ sell : '+item_text,"Y")

    if (round(((int(current_Amt.replace(",",""))*int(data[6])) - int(data[7])) / int(data[7]) * 100 ,2) <= SELL_DOWN_RATE) :
        sellStock(data,current_Amt)
        log('▼ sell : '+item_text,"Y")

    if status == "CLOSE":
        sellStock(data,current_Amt)
        log('close market - sell : '+item_text,"Y")
    
# pusrchase stock
def purchaseStock(stockData):
    if len(stockData) > 0 :
       fundCol,fundData = searchAllData(STOCK_VERSION_META_TABLE)         
       crt_dttm = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
       nowTime = int(datetime.datetime.now().strftime("%H%M%S"))       
       if int(START_TIME) <=  nowTime and nowTime <= int(END_TIME):
            if len(fundData) > 0 :
                for idx, data in enumerate(stockData):
                    if int(fundData[0][1]) >= int((data[4])) :
                        purchase_count = math.floor(int(fundData[0][1])/int(data[4]))
                        purchase_amt = purchase_count * int(data[4])  

                        sql = """insert into """+STOCK_VERSION_TABLE+""" (code, item, status
                        , purchase_current_amt , purchase_count, purchase_amt,  search_rate, yesterday_rate
                        , up_down_rate, ps_cnt, c_amt, h_amt, l_amt, crt_dttm) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""

                        sqlParam = (data[1], data[2], "I"
                        , data[4] , purchase_count, purchase_amt,  data[3], data[5]
                        , data[6], data[7], data[8], data[9], data[10], crt_dttm)

                        executeDB(sql,sqlParam)

            log('--- stock info save ---',"N")
           
# sell stock
def sellStock(stockData,current_Amt):
    chg_dttm = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sell_amt = int(current_Amt.replace(",",""))*int(stockData[6]) - int(stockData[7])
    sql = "update "+STOCK_VERSION_TABLE+" set status= ?, sell_current_amt = ?, sell_amt = ? ,chg_dttm = ? where id = ?"
    sqlParam =  ('C' , current_Amt , sell_amt , chg_dttm , stockData[0])
    executeDB(sql,sqlParam)

# purchase stock monitoring
def purchaseStockMonitoring(purchaseData):
    log('--- stock info monitoring ---',"N")
    nowTime = int(datetime.datetime.now().strftime("%H%M%S"))
    if int(START_TIME) <=  nowTime and nowTime <= int(END_TIME):
        for idx, data in enumerate(purchaseData):
            getStocInfoData(data,"ING")
    else:
        for idx, data in enumerate(purchaseData):
            getStocInfoData(data,"CLOSE")

# telegram message send
def send_telegram_msg(msg):
  try:
    bot.deleteWebhook()
    chat_id = bot.getUpdates()[-1].message.chat.id
    # print(chat_id)  1203202572
    # bot sendMessage
    bot.sendMessage(chat_id = chat_id, text=msg)

    # http request sendMessage
    # teleurl = "https://api.telegram.org/bot1280370073:AAHFwcNtcS9pvqF29zJJKEOY0SvnW8NH1do/sendMessage"
    # params = {'chat_id': chat_id, 'text': msg} 
    # res = requests.get(teleurl, params=params)
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
    # serarch stock version table table data
    purchaseCol, purchaseData = searchAllData(STOCK_VERSION_TABLE)    
    # pusrchase stock empty
    if len(purchaseData) == 0:
        stockData = getStocInfoTopList()
        # purchase stock save
        purchaseStock(stockData)
    else:    
        # purchase stock monitoring
        purchaseStockMonitoring(purchaseData)

##################################################

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