##################################################
#
#          devsunsetstock_v_1 program
#
##################################################

##################################################
#
# 개요
#
# 프로그램 실행 : 09:00 ~ 15:20 실행
#
# 네이버 주식 인기 종목 페이지 분석 - Crawling
# - (https://finance.naver.com/sise/lastsearch2.nhn)
#
# 종목 선택 
# - 등락율 ▲ 최대 
# - 현재가 100,000 이하
#
# 선택 종목 DB 저장 (status I 상태)
# 
# 선택 종목 등락율 체크 및 알림
# - 등락율 알림 
# - 등락율 +2% , -1.5%시 매매 (status C 상태)
#
# * seqlite3 install  && sqlite location PATH add
#
# * create table
#
# create table stock (init_amt text ,current_amt text)
# insert into stock (init_amt,current_amt) values ('500000','500000')
#
# create table stock_v1 (id integer primary key autoincrement, code text, item text,status text
#       , purchase_current_amt text , sell_current_amt text, purchase_count text
#       , purchase_amount text , sell_amount text, crt_dttm text, chg_dttm text)
#
# * telegram setting
#  - BotFather -> /newbot -> devsunetstock -> devsunsetstock_bot - > get api key 
# 
##################################################
# install library
# $ pip install requests beautifulsoup4 apscheduler python-telegram-bot
import requests
import bs4
import sqlite3
import datetime
import math
import telegram
from apscheduler.schedulers.blocking import BlockingScheduler
##################################################
# constant

# proxy user
proxy_use_flag = False

# Proxy info
http_proxy  = "http://x.x.x.x:xxxx"
https_proxy = "http://x.x.x.x:xxxx"
proxyDict = { 
              "http"  : http_proxy, 
              "https" : https_proxy
            }
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
CRAWLING_URL = "/sise/lastsearch2.nhn"
# sell rate up
SELL_UP_RATE = 2.0
# sell rate down
SELL_DOWN_RATE = -1.5

# telegram
telegram_token = '1280370073:AAHFwcNtcS9pvqF29zJJKEOY0SvnW8NH1do'
bot = telegram.Bot(token = telegram_token)

##################################################
# function

# get db table all data
def searchAllData(table):
    columns = []
    result = []
    conn = sqlite3.connect("stock.db")
    with conn:
        cur = conn.cursor()   
        if table == 'stock' :
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
    if proxy_use_flag :
        resp = requests.get(BASE_URL+CRAWLING_URL,proxies=proxyDict)       
    else:
        resp = requests.get(BASE_URL+CRAWLING_URL)

    html = resp.text

    # 종목 데이타 구하기 
    bs = bs4.BeautifulSoup(html, 'html.parser')
    infoTable = bs.find("table",{"class":"type_5"})
    infoData = []
    for a in infoTable.find_all("tr"):
        infolist = []
        for b in a.find_all("td"): 
            info = b.get_text().replace("\n","").replace("\t","")
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
        # 순위 0|종목명 1|검색비율 2|현재가 3|전일비 4|등락률 5|거래량 6|시가 7|고가 8|저가 9|PER 10|ROE 11
        if int(data[3].replace(",","")) <= CURRENT_AMOUNT_MAX and data[5][0] == "+":
            # print(data)
            filterData.append((float(data[2].replace("+","").replace("%",""))
            ,codeData[idx],data[1],data[2].replace(",",""),data[3].replace(",",""),data[4]
            ,data[5].replace(",",""),data[6].replace(",",""),data[7].replace(",","")
            ,data[8].replace(",",""),data[9].replace(",","")))
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
    if proxy_use_flag :
        resp = requests.get(BASE_URL+data[1],proxies=proxyDict)        
    else:
        resp = requests.get(BASE_URL+data[1])
        
    html = resp.text
    bs = bs4.BeautifulSoup(html, 'html.parser')    

    arrow = "△"
    current_Amt = bs.find("em",{"class":"no_up"}).find("span",{"class":"blind"}).get_text()

    if current_Amt == None :
        arrow = "▼"
        current_Amt = bs.find("em",{"class":"no_down"}).find("span",{"class":"blind"}).get_text()


    item_text = arrow+" : 종목 : "+data[2] +" 구매수 : "+data[6]+" 구매가 : "+format(int(data[4]), ',')
    item_text +=" 현재가 : "+current_Amt +" 등락가 : "+str(format(int(current_Amt.replace(",",""))-int(data[4]),','))
    item_text +=" 구매금액 : "+str(format(int(data[7]), ','))+" 현재금액 : "+str(format(int(current_Amt.replace(",",""))*int(data[6]),','))
    item_text +=" 등락율 : "+ str(round(((int(current_Amt.replace(",",""))*int(data[6])) - int(data[7])) / int(data[7]) * 100 ,2))
    item_text +=" 수익금액 : "+str(format(int(current_Amt.replace(",",""))*int(data[6]) - int(data[7]),','))
    
    print(item_text)

    if (round(((int(current_Amt.replace(",",""))*int(data[6])) - int(data[7])) / int(data[7]) * 100 ,2) >= SELL_UP_RATE) :
        sellStock(data,current_Amt)
        alarm('▲ sell : '+item_text,"Y")

    if (round(((int(current_Amt.replace(",",""))*int(data[6])) - int(data[7])) / int(data[7]) * 100 ,2) <= SELL_DOWN_RATE) :
        sellStock(data,current_Amt)
        alarm('▼ sell : '+item_text,"Y")

    if status == "CLOSE":
        sellStock(data,current_Amt)
        alarm('close market - sell : '+item_text,"Y")
    
# pusrchase stock
def purchaseStock(stockData):
    if len(stockData) > 0 :
       fundCol,fundData = searchAllData('stock')         
       crt_dttm = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
       nowTime = int(datetime.datetime.now().strftime("%H%M%S"))       
       if int(START_TIME) <=  nowTime and nowTime <= int(END_TIME):
            if len(fundData) > 0 :
                for idx, data in enumerate(stockData):
                    if int(fundData[0][1]) >= int((data[4])) :
                        purchase_count = math.floor(int(fundData[0][1])/int(data[4]))
                        purchase_amount = purchase_count * int(data[4])  
                        sql = """insert into stock_v1 (code , item ,status , purchase_current_amt , 
                                    purchase_count , purchase_amount , crt_dttm) values (? , ? ,? , ? , ? , ? , ?)"""
                        sqlParam = (data[1] , data[2] ,'I' , data[4] , purchase_count , purchase_amount , crt_dttm)
                        executeDB(sql,sqlParam)
            alarm('--- stock info save ---',"N")
           
# sell stock
def sellStock(stockData,current_Amt):
    chg_dttm = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sell_amt = int(current_Amt.replace(",",""))*int(stockData[6]) - int(stockData[7])
    sql = "update stock_v1 set status= ?, sell_current_amt = ?, sell_amount = ? ,chg_dttm = ? where id = ?"
    sqlParam =  ('C' , current_Amt , sell_amt , chg_dttm , stockData[0])
    executeDB(sql,sqlParam)

# purchase stock monitoring
def purchaseStockMonitoring(purchaseData):
    alarm('--- stock info monitoring ---',"N")
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

# alarm 
def alarm(msg,push_yn):
    if push_yn == 'Y' :
        send_telegram_msg(msg)
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+" : "+msg)
    else:
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+" : "+msg)

# main process
def main_process():
    # serarch stock_v1 table data
    purchaseCol, purchaseData = searchAllData('stock_v1')
    alarm('--- stock info monitoring ---',"Y")
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