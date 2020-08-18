##################################################
#
#          stock_db_monitoring program
#
##################################################
# import
import sqlite3
import unicodedata
# install library
# $ pip install requests beautifulsoup4
import requests
import bs4

##################################################
# constant
table_version = 7
current_amt = 500000
# crawling target
CRAWLING_TARGET = [
 {'table_version':0,'title':'검색상위 종목'}   
,{'table_version':1,'title':'시가총액 코스피'}   
,{'table_version':2,'title':'시가총액 코스닥'}
,{'table_version':3,'title':'상승 코스피'}
,{'table_version':4,'title':'상승 코스닥'}
,{'table_version':5,'title':'상한가 코스피/코스닥'}
,{'table_version':6,'title':'저가대비급등 코스피'}
,{'table_version':7,'title':'저가대비급등 코스닥'}
,{'table_version':8,'title':'거래상위 코스피'}
,{'table_version':9,'title':'거래상위 코스닥'}
,{'table_version':10,'title':'거래량 급증 코스피'}
,{'table_version':11,'title':'거래량 급증 코스닥'}
,{'table_version':12,'title':'신규상장종목 코스피'}
,{'table_version':13,'title':'신규상장종목 코스닥'}
,{'table_version':14,'title':'외국인보유현황 코스피'}
,{'table_version':15,'title':'외국인보유현황 코스닥'}
,{'table_version':16,'title':'골든크로스 종목'}
,{'table_version':17,'title':'갭상승 종목'}
,{'table_version':18,'title':'이격도과열 종목'}
,{'table_version':19,'title':'투자심리과열 종목'}
,{'table_version':20,'title':'상대강도과열 종목'}
] 
# proxy use
PROXY_USE_FLAG = False
# Proxy info
HTTP_PROXY  = "http://xxx.xxx.xxx.xxx:xxxx"
HTTPS_PROXY = "http://xxx.xxx.xxx.xxx:xxxx"
PROXY_DICT = { 
              "http"  : HTTP_PROXY, 
              "https" : HTTPS_PROXY
            }
# base url
BASE_URL = "https://finance.naver.com"            
CRAWLING_ITEM_URL = "/item/main.nhn?code="
##################################################
# function

# stock current amt crawling
def getStocCurrentAmt(code):
    resp = None
    if PROXY_USE_FLAG :
        resp = requests.get(BASE_URL+CRAWLING_ITEM_URL+code,proxies=PROXY_DICT)        
    else:
        resp = requests.get(BASE_URL+CRAWLING_ITEM_URL+code)
        
    html = resp.text
    bs = bs4.BeautifulSoup(html, 'html.parser')    

    current_Amt = bs.find("em",{"class":"no_up"}).find("span",{"class":"blind"}).get_text()

    if current_Amt == None :
        current_Amt = bs.find("em",{"class":"no_down"}).find("span",{"class":"blind"}).get_text()    
        
    return int(current_Amt.replace(",",""))

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
    for v in range(0,len(CRAWLING_TARGET)):
        print('---------- table : ',v,' : ',CRAWLING_TARGET[v]['title'],'----------')        
        table_stock = 'stock_v'+str(table_version)+'_'+str(v)
        sqlText = 'update '+table_stock+' set status = "S" where status = "I"'
        executeDB(sqlText)      

    print('--- force stock all sell ---')  

# get current all data
def getLastCurrentAllData():
    for v in range(0,len(CRAWLING_TARGET)):
        print('---------- table : ',v,' : ',CRAWLING_TARGET[v]['title'],'----------')  
        try:            
            table_stock = 'stock_v'+str(table_version)+'_'+str(v)+'_meta'
            table_stock_meta = 'stock_v'+str(table_version)+'_'+str(v)
            print(searchList("select * from "+table_stock))
            print(searchList("select * from "+table_stock_meta+ " where status IN ('I','C','S')  order by chg_dttm desc limit 1"))
        except Exception as err:
            print(err)          

# get current amt
def getCurrentAmtData():
    stockDataList = []
    for v in range(0,len(CRAWLING_TARGET)):
        # print('---------- table : ',v,' : ',CRAWLING_TARGET[v]['title'],'----------')  
        try:            
            table_stock_meta  = 'stock_v'+str(table_version)+'_'+str(v)+'_meta'
            table_stock = 'stock_v'+str(table_version)+'_'+str(v)
                        
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
                stockDataList.append((CRAWLING_TARGET[v]['title'],'매수대기','NONE','NONE',int(data_sub[0][0]),int(data_sub[0][0])))
            else:
                status = ""
                if data[0][0] == "I":
                    status = "진행중"
                    stockDataList.append((CRAWLING_TARGET[v]['title'],status,data[0][1],data[0][2],int(data[0][6]),int(data[0][3])+int(data[0][7])*getStocCurrentAmt(data[0][1])))
                elif  data[0][0] == "S":
                    status = "매도대기"
                    stockDataList.append((CRAWLING_TARGET[v]['title'],status,data[0][1],data[0][2],int(data[0][6]),int(data[0][3])+int(data[0][7])*getStocCurrentAmt(data[0][1])))
                else:                    
                    status = "매도완료"
                    stockDataList.append((CRAWLING_TARGET[v]['title'],status,data[0][1],data[0][2],int(data[0][6]),int(data[0][6])))            
        except Exception as err:
            print(err)

    stockDataList.sort(key = lambda element : element[5],reverse=True)

    print(fill_str_space('분류',25),fill_str_space('종목코드',10),fill_str_space('종목명',35),fill_str_space('상태',10),fill_str_space('최초자산',10),fill_str_space('현재자산',10),fill_str_space('이익',10),' --- ', fill_str_space('실시간 현재 자산',10),fill_str_space('살시간 이익',10))
    # stockList = []
    for x, stock in enumerate(stockDataList):
        # print(stock)
        print(fill_str_space('['+stock[0]+']',25),fill_str_space(stock[2],10),fill_str_space(stock[3],35),fill_str_space(stock[1],10),fill_str_space(format(current_amt,','),10),fill_str_space(format(int(stock[4]),','),10),fill_str_space('['+str(format(int(stock[4]) - current_amt,','))+']',10),' --- ',fill_str_space(format(stock[5],','),10),fill_str_space('['+str(format(int(stock[5]) - current_amt,','))+']',10))
        # stockList.append(('['+stock[0]+']',stock[2],stock[3],stock[1],format(current_amt,','),format(int(stock[4]),','),'['+str(format(int(stock[4]) - current_amt,','))+']',' --- ',format(stock[5],','),'['+str(format(int(stock[5]) - current_amt,','))+']'))


# main process
def main_process():
    # setAllStockSell()
    # getLastCurrentAllData()
    getCurrentAmtData()

if __name__ == '__main__':
    main_process()



