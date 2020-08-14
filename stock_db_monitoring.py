##################################################
#
#          stock_db_monitoring program
#
##################################################

# install library
# $ pip install requests beautifulsoup4 apscheduler python-telegram-bot
import sqlite3

##################################################
# constant
table_version = 6
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
##################################################
# function

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

# get current all data
def getLastCurrentAllData():
    for v in range(0,len(CRAWLING_TARGET)):
        print('---------- table : ',v,' : ',CRAWLING_TARGET[v]['title'],'----------')  
        try:            
            table_stock = 'stock_v'+str(table_version)+'_'+str(v)+'_meta'
            table_stock_meta = 'stock_v'+str(table_version)+'_'+str(v)
            print(searchList("select * from "+table_stock))
            print(searchList("select * from "+table_stock_meta+ " where status IN ('I','C')  order by chg_dttm desc limit 1"))
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
                stockDataList.append((CRAWLING_TARGET[v]['title'],'매수대기','NONE','NONE',data_sub[0][0]))
            else:
                status = ""
                if data[0][0] == "I":
                    status = "진행중"
                elif  data[0][0] == "I":
                    status = "매도대기"
                else:                    
                    status = "매도완료"
                stockDataList.append((CRAWLING_TARGET[v]['title'],status,data[0][1],data[0][2],data[0][6]))            
        except Exception as err:
            print(err)

    stockDataList.sort(key = lambda element : element[4],reverse=True)

    print('분류','종목코드','종목명','최초자산','현재자산','이익')
    for x, stock in enumerate(stockDataList):
        # print(stock)
        print('['+stock[0]+']',stock[2],stock[3],format(current_amt,','),format(int(stock[4]),','),'['+str(format(int(stock[4]) - current_amt,','))+']')

# main process
def main_process():
    # setAllStockSell()
    # getLastCurrentAllData()
    getCurrentAmtData()

if __name__ == '__main__':
    main_process()



# 분류 종목코드 종목명 최초자산 현재자산 이익
# [거래상위 코스닥] 053700 삼보모터스 500,000 624,105 [124,105]
# [저가대비급등 코스닥] 060230 이그잭스 500,000 537,480 [37,480]
# [시가총액 코스닥] 035760 CJ ENM 500,000 518,350 [18,350]
# [갭상승 종목] 036000 예림당 500,000 511,085 [11,085]
# [상대강도과열 종목] 226320 잇츠한불 500,000 509,885 [9,885]
# [골든크로스 종목] 530004 삼성 화장품 테마주 ETN 500,000 504,120 [4,120]
# [거래량 급증 코스피] 100220 비상교육 500,000 502,690 [2,690]
# [검색상위 종목] 002630 오리엔트바이오 500,000 500,000 [0]
# [시가총액 코스피] NONE NONE 500,000 500,000 [0]
# [상한가 코스피/코스닥] 002630 오리엔트바이오 500,000 500,000 [0]
# [신규상장종목 코스닥] 351340 IBKS제13호스팩 500,000 500,000 [0]
# [외국인보유현황 코스피] 075180 새론오토모티브 500,000 500,000 [0]
# [외국인보유현황 코스닥] NONE NONE 500,000 500,000 [0]
# [신규상장종목 코스피] 354350 HANARO 글로벌럭셔리S&P(합성) 500,000 499,800 [-200]
# [투자심리과열 종목] 287330 KBSTAR 200생활소비재 500,000 498,820 [-1,180]
# [이격도과열 종목] 105630 한세실업 500,000 496,600 [-3,400]
# [상승 코스피] 001529 동양3우B 500,000 487,950 [-12,050]
# [상승 코스닥] 053700 삼보모터스 500,000 470,735 [-29,265]
# [거래상위 코스피] 037270 YG PLUS 500,000 467,170 [-32,830]
# [거래량 급증 코스닥] 028080 휴맥스홀딩스 500,000 460,830 [-39,170]
# [저가대비급등 코스피] 001529 동양3우B 500,000 457,950 [-42,050]
