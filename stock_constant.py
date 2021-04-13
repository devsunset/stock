##################################################
#
#          stock_constant program
#
##################################################

# 생성 테이블 버젼 
CREATE_TABLE_VERSION = 9

# 현재 버젼 테이블만 생성할지 여부 
CURRENT_TABLE_CREATE_FLAG = False

# stock market 시작 시간
START_TIME = "090500"

# stock market 종료 시간
END_TIME = "152500"

# 프로그램 실행 주기 
INTERVAL_SECONDS = 30

# 현재 자금
CURRENT_AMT = 500000

# 매수가 MAX 금액
CURRENT_AMOUNT_MAX = 150000

# sell rate up
SELL_UP_RATE = 1.5

# sell rate down
SELL_DOWN_RATE = -0.5

# stock commission rate 
STOCK_COMMISSION_RATE = 0.015

# stock tax rate - 세금 (현재값 * 0.25 / 100)
STOCK_TAX_RATE = 0.25

# 최근 종가 체크 단위 일수 
RECENT_DAY_UNIT = 3

# 최근 하락 매도 횟수
SELL_DOWN_CNT = 2

# 종목 체크 최대 갯수
MAX_STOCK_ITEM = 30

# proxy 서버 사용 환경 여부 
PROXY_USE_FLAG = False

# Proxy 서버 정보 
HTTP_PROXY  = "http://xxx.xxx.xxx.xxx:xxxx"
HTTPS_PROXY = "http://xxx.xxx.xxx.xxx:xxxx"
PROXY_DICT = { 
              "http"  : HTTP_PROXY, 
              "https" : HTTPS_PROXY
            }

# naver stock crawling base url
BASE_URL = "https://finance.naver.com"    

# naver stock crawling search top list url
CRAWLING_TOP_LIST_URL = "/sise/lastsearch2.nhn"

# naver stock crawling item url
CRAWLING_ITEM_URL = "/item/main.nhn?code="

# naver stock crawling item daily url
CRAWLING_ITEM_DAY_URL = "/item/sise_day.nhn?page=1&code="

# naver stock crawling item time url
CRAWLING_ITEM_TIME_URL = "/item/sise_time.nhn?page=1&code="  

# crawling target
CRAWLING_TARGET = [
 {'idx':0,'skip':False,'title':'검색상위 종목','url':'/sise/lastsearch2.nhn','css_class':'type_5','sortIdx':10 , 'reverse':False ,'checklength':12, 'codeNameIdx':1,'current_amtIdx':3,'uprateIdx':5}   
,{'idx':1,'skip':True,'title':'시가총액 코스피','url':'/sise/sise_market_sum.nhn?sosok=0','css_class':'type_2','sortIdx':10 , 'reverse':False ,'checklength':13, 'codeNameIdx':1,'current_amtIdx':2,'uprateIdx':4}   
,{'idx':2,'skip':True,'title':'시가총액 코스닥','url':'/sise/sise_market_sum.nhn?sosok=1','css_class':'type_2','sortIdx':10 , 'reverse':False ,'checklength':13, 'codeNameIdx':1,'current_amtIdx':2,'uprateIdx':4}
,{'idx':3,'skip':False,'title':'상승 코스피','url':'/sise/sise_rise.nhn?sosok=0','css_class':'type_2','sortIdx':10 , 'reverse':False ,'checklength':12, 'codeNameIdx':1,'current_amtIdx':2,'uprateIdx':4}
,{'idx':4,'skip':False,'title':'상승 코스닥','url':'/sise/sise_rise.nhn?sosok=1','css_class':'type_2','sortIdx':10 , 'reverse':False ,'checklength':12, 'codeNameIdx':1,'current_amtIdx':2,'uprateIdx':4}
,{'idx':5,'skip':False,'title':'상한가 코스피/코스닥','url':'/sise/sise_upper.nhn','css_class':'type_5','sortIdx':11 , 'reverse':False ,'checklength':12, 'codeNameIdx':3,'current_amtIdx':4,'uprateIdx':6}
,{'idx':6,'skip':False,'title':'저가대비급등 코스피','url':'/sise/sise_low_up.nhn?sosok=0','css_class':'type_2','sortIdx':10 , 'reverse':False ,'checklength':12, 'codeNameIdx':2,'current_amtIdx':3,'uprateIdx':5}
,{'idx':7,'skip':False,'title':'저가대비급등 코스닥','url':'/sise/sise_low_up.nhn?sosok=1','css_class':'type_2','sortIdx':10 , 'reverse':False ,'checklength':12, 'codeNameIdx':2,'current_amtIdx':3,'uprateIdx':5}
,{'idx':8,'skip':True,'title':'거래상위 코스피','url':'/sise/sise_quant.nhn?sosok=0','css_class':'type_2','sortIdx':10 , 'reverse':False ,'checklength':12, 'codeNameIdx':1,'current_amtIdx':2,'uprateIdx':4}
,{'idx':9,'skip':True,'title':'거래상위 코스닥','url':'/sise/sise_quant.nhn?sosok=1','css_class':'type_2','sortIdx':10 , 'reverse':False ,'checklength':12, 'codeNameIdx':1,'current_amtIdx':2,'uprateIdx':4}
,{'idx':10,'skip':False,'title':'거래량 급증 코스피','url':'/sise/sise_quant_high.nhn?sosok=0','css_class':'type_2','sortIdx':10 , 'reverse':False ,'checklength':11, 'codeNameIdx':2,'current_amtIdx':3,'uprateIdx':5}
,{'idx':11,'skip':False,'title':'거래량 급증 코스닥','url':'/sise/sise_quant_high.nhn?sosok=1','css_class':'type_2','sortIdx':10 , 'reverse':False ,'checklength':11, 'codeNameIdx':2,'current_amtIdx':3,'uprateIdx':5}
,{'idx':12,'skip':True,'title':'신규상장종목 코스피','url':'/sise/sise_new_stock.nhn?sosok=0','css_class':'type_2','sortIdx':10 , 'reverse':False ,'checklength':12, 'codeNameIdx':2,'current_amtIdx':3,'uprateIdx':5}
,{'idx':13,'skip':True,'title':'신규상장종목 코스닥','url':'/sise/sise_new_stock.nhn?sosok=1','css_class':'type_2','sortIdx':10 , 'reverse':False ,'checklength':12, 'codeNameIdx':2,'current_amtIdx':3,'uprateIdx':5}
,{'idx':14,'skip':True,'title':'외국인보유현황 코스피','url':'/sise/sise_foreign_hold.nhn?sosok=0','css_class':'type_2','sortIdx':8 , 'reverse':False ,'checklength':10, 'codeNameIdx':1,'current_amtIdx':2,'uprateIdx':4}
,{'idx':15,'skip':True,'title':'외국인보유현황 코스닥','url':'/sise/sise_foreign_hold.nhn?sosok=1','css_class':'type_2','sortIdx':8 , 'reverse':False ,'checklength':10, 'codeNameIdx':1,'current_amtIdx':2,'uprateIdx':4}
,{'idx':16,'skip':False,'title':'골든크로스 종목','url':'/sise/item_gold.nhn','css_class':'type_5','sortIdx':9 , 'reverse':False ,'checklength':11, 'codeNameIdx':1,'current_amtIdx':2,'uprateIdx':4}
,{'idx':17,'skip':False,'title':'갭상승 종목','url':'/sise/item_gap.nhn','css_class':'type_5','sortIdx':9 , 'reverse':False ,'checklength':11, 'codeNameIdx':1,'current_amtIdx':2,'uprateIdx':4}
,{'idx':18,'skip':False,'title':'이격도과열 종목','url':'/sise/item_igyuk.nhn','css_class':'type_5','sortIdx':9 , 'reverse':False ,'checklength':11, 'codeNameIdx':1,'current_amtIdx':2,'uprateIdx':4}
,{'idx':19,'skip':False,'title':'투자심리과열 종목','url':'/sise/item_overheating_1.nhn','css_class':'type_5','sortIdx':9 , 'reverse':False ,'checklength':11, 'codeNameIdx':1,'current_amtIdx':2,'uprateIdx':4}
,{'idx':20,'skip':False,'title':'상대강도과열 종목','url':'/sise/item_overheating_2.nhn','css_class':'type_5','sortIdx':9 , 'reverse':False ,'checklength':11, 'codeNameIdx':1,'current_amtIdx':2,'uprateIdx':4}
] 

# crawling exclude target
CRAWING_EXCLUDE_TARGET =[
 {'idx':0,'title':'관리종목','url':'/sise/management.nhn'}
,{'idx':1,'title':'거래정지종목','url':'/sise/trading_halt.nhn'}
,{'idx':2,'title':'시장경보 - 투자 주의 종목','url':'/sise/investment_alert.nhn?type=caution'}
,{'idx':3,'title':'시장경보 - 투자 경보 종목','url':'/sise/investment_alert.nhn?type=warning'}
,{'idx':4,'title':'시장경보 - 투자 위험 종목','url':'/sise/investment_alert.nhn?type=risk'}
]   

# telegram token
TELEGRAM_TOKEN = '1280370073:AAHFwcNtcS9pvqF29zJJKEOY0SvnW8NH1do'

# telgram send flag
TELEGRAM_SEND_FLAG = False

# user agent
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'