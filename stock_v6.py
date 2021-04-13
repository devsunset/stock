##################################################
#
#          stock_v6 program
#
##################################################

##################################################
#
# 개요 - 프로세스 설명
#
# 네이버 주식 (https://finance.naver.com/) Site - Crawling
#
# 1.주식 사이트 정보를 Crawling 하여 대상 종목 선정
# 종목 선택 및 DB 저장 
# - stock_vX_x 테이블 status 컬럼 값이 I가 없는 경우
# - 등락율 상승 항목
# - 현재가 값이 매수가 MAX 보다 이하인 항목
# - Filter 된 종목 status P 상태로 DB 저장
#
# 2.임시 저장 좀목 시세별 시세 모니터링 ( status : P )
# - 일별 / 시세별 데이타  거래량 모니터링 분석 
# - 투자자 보호 대상 종목 제외
# - 분석된 결과를 토대로 한 종목의 상태를 I 갱신 후 임시 항목 삭제
#
# 3.저장 종목 모니터링 및 매도/매수 알림 
# - stock_vX_x 테이블 status 컬럼 값이 I 인 종목 대상
# - 배치 주기에 따른 종목별 상세 데이타 모니터링 
# - 등락율 SELL_UP_RATE , SELL_DOWN_RATE 시 매매 (status : C)
# - 매도/매수 처리 시 telegram 알림 전송
#
##################################################

##################################################
# import

import sys
import sqlite3
import datetime
import math
import unicodedata
import random
import requests
import bs4
import telegram
from apscheduler.schedulers.blocking import BlockingScheduler
import stock_closed_daytime
import stock_constant

##################################################
# constant

# telegram
bot = telegram.Bot(token = stock_constant.TELEGRAM_TOKEN)

headers = {"User-Agent": stock_constant.USER_AGENT}

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
    if stock_constant.PROXY_USE_FLAG :
        resp = requests.get(stock_constant.BASE_URL+stock_constant.CRAWLING_TARGET[RUN_CMD_INDEX]['url'],proxies=stock_constant.PROXY_DICT, headers=headers)       
    else:
        resp = requests.get(stock_constant.BASE_URL+stock_constant.CRAWLING_TARGET[RUN_CMD_INDEX]['url'], headers=headers)

    html = resp.text

    # 종목 데이타 구하기 
    infoData = []
    if RUN_CMD_INDEX !=5 :
        bs = bs4.BeautifulSoup(html, 'html.parser')       
        infoTable = bs.find("table",{"class":stock_constant.CRAWLING_TARGET[RUN_CMD_INDEX]['css_class']})    
        for a in infoTable.find_all("tr"):
            infolist = []
            for b in a.find_all("td"): 
                info = b.get_text().replace(",","").replace("%","").replace("\n","").replace("\t","")
                infolist.append(info)  
            if len(infolist) == stock_constant.CRAWLING_TARGET[RUN_CMD_INDEX]['checklength']:
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
            if len(infolist) == stock_constant.CRAWLING_TARGET[RUN_CMD_INDEX]['checklength']:
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
    # - 현재가 stock_constant.CURRENT_AMOUNT_MAX 이하인 종목만 필터링 후 종목 코드 결합    
    if len(infoData) > stock_constant.MAX_STOCK_ITEM:
        infoData = infoData[0:stock_constant.MAX_STOCK_ITEM]

    filterData = []
    for idx, data in enumerate(infoData):
        # print(idx, data)
        # 현재가가 stock_constant.CURRENT_AMOUNT_MAX 이하 이며 등락율이 상승인 종목만 Filter
        if codeData[idx].replace("/item/main.nhn?code=","") not in excludeData and int(data[stock_constant.CRAWLING_TARGET[RUN_CMD_INDEX]['current_amtIdx']]) <= stock_constant.CURRENT_AMOUNT_MAX and data[stock_constant.CRAWLING_TARGET[RUN_CMD_INDEX]['uprateIdx']][0] == "+":
            # print(data)
            if data[stock_constant.CRAWLING_TARGET[RUN_CMD_INDEX]['sortIdx']] == 'N/A':
                 filterData.append((float(1) ,codeData[idx].replace("/item/main.nhn?code=","")
                , data[stock_constant.CRAWLING_TARGET[RUN_CMD_INDEX]['codeNameIdx']] ,data[stock_constant.CRAWLING_TARGET[RUN_CMD_INDEX]['current_amtIdx']]))
            else:
                filterData.append((float(data[stock_constant.CRAWLING_TARGET[RUN_CMD_INDEX]['sortIdx']]) ,codeData[idx].replace("/item/main.nhn?code=","")
                , data[stock_constant.CRAWLING_TARGET[RUN_CMD_INDEX]['codeNameIdx']] ,data[stock_constant.CRAWLING_TARGET[RUN_CMD_INDEX]['current_amtIdx']]))

    #정렬
    filterData.sort(key = lambda element : element[0],reverse=stock_constant.CRAWLING_TARGET[RUN_CMD_INDEX]['reverse'])
    # if len(filterData) > 0 :
    #     for idx, data in enumerate(filterData):
    #         print("추천 종목 ",idx,":",data)
    return filterData

# exclude stock item list crawling
def getExcludeStocInfoItemList():
    resp = None    
    codeData = []

    for idx, data in enumerate(stock_constant.CRAWING_EXCLUDE_TARGET):      
        if stock_constant.PROXY_USE_FLAG :
            resp = requests.get(stock_constant.BASE_URL+stock_constant.CRAWING_EXCLUDE_TARGET[idx]['url'],proxies=stock_constant.PROXY_DICT, headers=headers)       
        else:
            resp = requests.get(stock_constant.BASE_URL+stock_constant.CRAWING_EXCLUDE_TARGET[idx]['url'], headers=headers)

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
    if stock_constant.PROXY_USE_FLAG :
        resp = requests.get(stock_constant.BASE_URL+stock_constant.CRAWLING_ITEM_DAY_URL+stock_code,proxies=stock_constant.PROXY_DICT, headers=headers)       
    else:
        resp = requests.get(stock_constant.BASE_URL+stock_constant.CRAWLING_ITEM_DAY_URL+stock_code, headers=headers)       

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
    if stock_constant.PROXY_USE_FLAG :
        resp = requests.get(stock_constant.BASE_URL+stock_constant.CRAWLING_ITEM_TIME_URL+stock_code+"&thistime="+datetime.datetime.now().strftime("%Y%m%d%H%M%S"),proxies=stock_constant.PROXY_DICT, headers=headers)       
    else:
        resp = requests.get(stock_constant.BASE_URL+stock_constant.CRAWLING_ITEM_TIME_URL+stock_code+"&thistime="+datetime.datetime.now().strftime("%Y%m%d%H%M%S"), headers=headers)       

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
    if stock_constant.PROXY_USE_FLAG :
        resp = requests.get(stock_constant.BASE_URL+stock_constant.CRAWLING_ITEM_URL+data[1],proxies=stock_constant.PROXY_DICT, headers=headers)        
    else:
        resp = requests.get(stock_constant.BASE_URL+stock_constant.CRAWLING_ITEM_URL+data[1], headers=headers)
        
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
        # 현재 값  - 수수료 - 세금 
        now_amt = int(current_Amt.replace(",",""))*int(data[6])
        commission_amt = ((int(data[4])*stock_constant.STOCK_COMMISSION_RATE)/100) + (now_amt * stock_constant.STOCK_COMMISSION_RATE) / 100
        tax_amt = (now_amt * stock_constant.STOCK_TAX_RATE) / 100
        item_text +=" 수익금액 : "+fill_str_space(str(format(int((now_amt - commission_amt - tax_amt )- int(data[7])),',')))

        log(item_text,"N")
        processing = True

        if (round(((int(current_Amt.replace(",",""))*int(data[6])) - int(data[7])) / int(data[7]) * 100 ,2) >= stock_constant.SELL_UP_RATE) :
            sellStock(data,current_Amt,VERSION_META_TABLE,VERSION_TABLE,'▲ sell : '+item_text)
            processing = False

        if (round(((int(current_Amt.replace(",",""))*int(data[6])) - int(data[7])) / int(data[7]) * 100 ,2) <= stock_constant.SELL_DOWN_RATE) :
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
        # 현재 값  - 수수료 - 세금 
        now_amt = int(current_Amt.replace(",",""))*int(data[6])
        commission_amt = ((int(data[4])*stock_constant.STOCK_COMMISSION_RATE)/100) + (now_amt * stock_constant.STOCK_COMMISSION_RATE) / 100
        tax_amt = (now_amt * stock_constant.STOCK_TAX_RATE) / 100
        item_text +=" 수익금액 : "+fill_str_space(str(format(int((now_amt - commission_amt - tax_amt )- int(data[7])),',')))

        log(item_text,"N")

        sellStock(data,current_Amt,VERSION_META_TABLE,VERSION_TABLE,'force sell : '+item_text)
        
    return current_Amt

# temp pusrchase stock
def tempPurchaseStock(stockData,VERSION_META_TABLE,VERSION_TABLE):
    if stock_closed_daytime.ClosedDayTime().is_stockOpenDayTime():
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
    log('['+stock_constant.CRAWLING_TARGET[int(tmpIdx)]['title']+'] purchase :'+str(stockData),"Y")     

# sell stock
def sellStock(stockData,current_Amt,VERSION_META_TABLE,VERSION_TABLE,msg):
    chg_dttm = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # 현재 값  - 수수료 - 세금 
    now_amt = int(current_Amt.replace(",",""))*int(stockData[6])
    commission_amt = ((int(stockData[4])*stock_constant.STOCK_COMMISSION_RATE)/100) + (now_amt * stock_constant.STOCK_COMMISSION_RATE) / 100
    tax_amt = (now_amt * stock_constant.STOCK_TAX_RATE) / 100
    sell_amt = int(now_amt - commission_amt - tax_amt)
    sql = "update "+VERSION_TABLE+" set status= ?, sell_current_amt = ?, sell_amt = ? ,chg_dttm = ? where id = ?"
    sqlParam =  ('C' , current_Amt , sell_amt , chg_dttm , stockData[0])
    executeDB(sql,sqlParam)

    sql = "update "+VERSION_META_TABLE+" set current_amt = current_amt + "+str(sell_amt)
    executeDB(sql)

    tmpIdx = VERSION_META_TABLE
    tmpIdx = tmpIdx.replace("stock_v6_","").replace("_meta","")
    log('['+stock_constant.CRAWLING_TARGET[int(tmpIdx)]['title']+'] '+msg,"Y")

# delete temp stock
def deleteTempStock(VERSION_TABLE):
    chg_dttm = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = "delete from  "+VERSION_TABLE+" where status = ? "
    sqlParam =  ("P")
    executeDB(sql,sqlParam)
    log('--- temp stock info delete ---',"N")

# stock monitoring
def stockMonitoring(purchaseData,VERSION_META_TABLE,VERSION_TABLE):       
    if stock_closed_daytime.ClosedDayTime().is_stockOpenDayTime():
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
    if stock_constant.TELEGRAM_SEND_FLAG:
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
    for idx, data in enumerate(stock_constant.CRAWLING_TARGET):  
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
        # 일별 시세 종가 값이 최근 stock_constant.RECENT_DAY_UNIT 일 동안 증가 중인 항목
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

                            if i == stock_constant.RECENT_DAY_UNIT:
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
# main

if __name__ == '__main__':
    scheduler = BlockingScheduler()
    scheduler.add_job(main_process, 'interval', seconds=stock_constant.INTERVAL_SECONDS)
    main_process()
    try:
        scheduler.start()
    except Exception as err:
        print(err)


