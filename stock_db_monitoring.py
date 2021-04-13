##################################################
#
#          stock_db_monitoring program ( version stock_v3 after)
#
##################################################

##################################################
# import

import sqlite3
import unicodedata
import requests
import bs4
from apscheduler.schedulers.blocking import BlockingScheduler
import stock_constant

##################################################
# constant

# 현재 모니터링 테이블 버젼
table_version = 9
# 프로그램 실행 주기 
interval_seconds = 30

headers = {"User-Agent": stock_constant.USER_AGENT}

##################################################
# function

# stock current amt crawling
def getStocCurrentAmt(code):
    resp = None
    if stock_constant.PROXY_USE_FLAG :
        resp = requests.get(stock_constant.BASE_URL+stock_constant.CRAWLING_ITEM_URL+code,proxies=stock_constant.PROXY_DICT, headers=headers)        
    else:
        resp = requests.get(stock_constant.BASE_URL+stock_constant.CRAWLING_ITEM_URL+code, headers=headers)
        
    html = resp.text
    bs = bs4.BeautifulSoup(html, 'html.parser')    

    amt = bs.find("em",{"class":"no_up"}).find("span",{"class":"blind"}).get_text()

    if amt == None :
        amt = bs.find("em",{"class":"no_down"}).find("span",{"class":"blind"}).get_text()    
        
    return int(amt.replace(",",""))

# fill space
def fill_str_space(input_s="", max_size=10, fill_char=" "):
    l = 0 
    for c in input_s:
        if unicodedata.east_asian_width(c) in ['F', 'W']:
            l+=2
        else: 
            l+=1
    return input_s+fill_char*(max_size-l)    

# db table search    
def searchList(sqlText):
    columns = []
    result = []
    conn = sqlite3.connect("stock.db")
    with conn:
        cur = conn.cursor()   
        cur.execute(sqlText)
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

# set stock force sell
def setAllStockSell():
    for idx, data in enumerate(CRAWLING_TARGET_FROM_MODULE):
        print('---------- table : ',data['idx'],' : ',data['title'],'----------')    
        table_stock = 'stock_v'+str(table_version)+'_'+str(data['idx'])
        sqlText = 'update '+table_stock+' set status = "S" where status = "I"'
        executeDB(sqlText)      

    print('--- force stock all sell ---')  

# get current all data
def getLastCurrentAllData():
    for idx, data in enumerate(CRAWLING_TARGET_FROM_MODULE):
        print('---------- table : ',data['idx'],' : ',data['title'],'----------')  
        try:            
            table_stock = 'stock_v'+str(table_version)+'_'+str(data['idx'])+'_meta'
            table_stock_meta = 'stock_v'+str(table_version)+'_'+str(data['idx'])
            print(searchList("select * from "+table_stock))
            print(searchList("select * from "+table_stock_meta+ " where status IN ('I','C','S')  order by chg_dttm desc limit 1"))
        except Exception as err:
            print(err)          

# get current amt
def getCurrentAmtData():
    stockDataList = []
    for idx, dataTarget in enumerate(CRAWLING_TARGET_FROM_MODULE):
        # print('---------- table : ',data['idx'],' : ',data['title'],'----------') 
        try:            
            table_stock_meta  = 'stock_v'+str(table_version)+'_'+str(dataTarget['idx'])+'_meta'
            table_stock = 'stock_v'+str(table_version)+'_'+str(dataTarget['idx'])
                        
            sqlText = '''select b.status
                        , b.code
                        , b.item  
                        , a.current_amt                    
                        , b.purchase_amt                        
                        , b.sell_amt
                        , (case b.status 
                          when 'I' then a.current_amt+b.purchase_amt
                          when 'S' then a.current_amt+b.purchase_amt
                          else a.current_amt end ) as current_money
                        , b.purchase_count
                        from '''+table_stock_meta+''' a 
                        inner join '''+table_stock+''' b 
                        where b.status in ('I','C','S') 
                        order by chg_dttm desc limit 1'''

            col, data = searchList(sqlText)
            # print(data)            
            if len(data) == 0:
                sqlText = 'select current_amt from '+table_stock_meta
                col_sub, data_sub = searchList(sqlText)
                # print(data_sub)                
                stockDataList.append((dataTarget['title'],'매수대기','NONE','NONE',int(data_sub[0][0]),int(data_sub[0][0])))
            else:
                status = ""
                if data[0][0] == "I":
                    status = "진행중"
                    # 현재 값  - 수수료 - 세금 
                    now_amt = getStocCurrentAmt(data[0][1])*int(data[0][7])
                    commission_amt = ((int(data[0][4])*stock_constant.STOCK_COMMISSION_RATE)/100) + (now_amt * stock_constant.STOCK_COMMISSION_RATE) / 100
                    tax_amt = (now_amt * stock_constant.STOCK_TAX_RATE) / 100
                    sell_amt = int(now_amt - commission_amt - tax_amt)                    
                    stockDataList.append((dataTarget['title'],status,data[0][1],data[0][2],int(data[0][6]),int(data[0][3])+sell_amt))
                elif  data[0][0] == "S":
                    status = "매도대기"
                    # 현재 값  - 수수료 - 세금 
                    now_amt = getStocCurrentAmt(data[0][1])*int(data[0][7])
                    commission_amt = ((int(data[0][4])*stock_constant.STOCK_COMMISSION_RATE)/100) + (now_amt * stock_constant.STOCK_COMMISSION_RATE) / 100
                    tax_amt = (now_amt * stock_constant.STOCK_TAX_RATE) / 100
                    sell_amt = int(now_amt - commission_amt - tax_amt)        
                    stockDataList.append((dataTarget['title'],status,data[0][1],data[0][2],int(data[0][6]),int(data[0][3])+sell_amt))
                else:                    
                    status = "매도완료"
                    stockDataList.append((dataTarget['title'],status,data[0][1],data[0][2],int(data[0][6]),int(data[0][6])))            
        except Exception as err:
            print(err)

    stockDataList.sort(key = lambda element : element[5],reverse=True)

    print('--------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
    print(fill_str_space('분류',25),fill_str_space('종목코드',10),fill_str_space('종목명',35),fill_str_space('상태',10),fill_str_space('최초자산',10),fill_str_space('현재자산',10),fill_str_space('이익',10),' --- ', fill_str_space('실시간현재 자산',20),fill_str_space('실시간 이익',10))
    print('--------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
    
    for x, stock in enumerate(stockDataList):    
        print(fill_str_space('['+stock[0]+']',25),fill_str_space(stock[2],10),fill_str_space(stock[3],35),fill_str_space(stock[1],10),fill_str_space(format(stock_constant.CURRENT_AMT,','),10),fill_str_space(format(int(stock[4]),','),10),fill_str_space('['+str(format(int(stock[4]) - stock_constant.CURRENT_AMT,','))+']',10),' --- ',fill_str_space(format(stock[5],','),20),fill_str_space('['+str(format(int(stock[5]) - stock_constant.CURRENT_AMT,','))+']',10))
        
    
# main process
def main_process():
    # setAllStockSell()
    # getLastCurrentAllData()
    getCurrentAmtData()

if __name__ == '__main__':
    global CRAWLING_TARGET_FROM_MODULE
    CRAWLING_TARGET_FROM_MODULE = []

    for idx, data in enumerate(stock_constant.CRAWLING_TARGET):
        if data['skip'] == False:
            CRAWLING_TARGET_FROM_MODULE.append(data)

    scheduler = BlockingScheduler()
    scheduler.add_job(main_process, 'interval', seconds=interval_seconds)
    main_process()
    try:
        scheduler.start()
    except Exception as err:
        print(err)
