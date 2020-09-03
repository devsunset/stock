##################################################
#
#          stock_closed_daytime program
#
##################################################

##################################################
# import

from datetime import date, datetime
import stock_constant

##################################################
# class

# 주식 시장 거래 시간 판단 
class ClosedDayTime():
    HOLIDAYS = ((1, 1),     #"new Year"
                (1, 24),    #"new Year"
                (1, 25),    #"new Year1"
                (1, 26),    #"new Year2"
                (3, 1),     #"3.1"
                (4, 30),    #"Buddha Day"
                (5, 5),     #"Children's Day"
                (6, 6),     #"Memorial Day"
                (8, 15),    #"Liberation Day"
                (8, 17),    #"Temp Liberation Day"
                (9, 30),    #"Thanksgiving"
                (10, 1),    #"Thanksgiving1"
                (10, 2),    #"Thanksgiving2"
                (10, 3),    #"National Foundation Day"
                (10, 9),    #"Hangul Day"
                (12, 25)    #"Christmas"
                )
 
    # 휴일 여부 판단 
    def is_holiday(self):
        now = datetime.now()
        daytuple = (str(now.month),str(now.day))
        HOLIDAYS = self.HOLIDAYS
        if daytuple in HOLIDAYS:
            return True
        else:
            return False

    # 주말 여부 판단
    def is_weekend(self):
        now = datetime.now()
        if now.weekday() >= 5:
            return True
        else:
            return False

    # 폐장 시간 여부 판단
    def is_closedTime(self):    
        nowTime = int(datetime.now().strftime("%H%M%S"))   
        if int(stock_constant.START_TIME) <=  nowTime and nowTime <= int(stock_constant.END_TIME):
            return False
        else:
            return True

    # 주식 거래 가능 시점 인지 판단
    def is_stockOpenDayTime(self):
        if self.is_holiday():
            return False

        if self.is_weekend():
            return False

        if self.is_closedTime():
            return False

        return True        

##################################################
# main     
 
if __name__=='__main__': 
    closed = ClosedDayTime()
    print('is_holiday : ',closed.is_holiday())
    print('is_weekend : ',closed.is_weekend())
    print('is_closedTime : ',closed.is_closedTime())
    print('is_stockOpenDayTime : ',closed.is_stockOpenDayTime())