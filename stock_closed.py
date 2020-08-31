from datetime import date, datetime

# 프로그램 시작 시간
START_TIME = "090005"
# 프로그램 종료 시간
END_TIME = "150000"
 
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
 
    def is_holiday(self):
        now = datetime.now()
        daytuple = (str(now.month),str(now.day))
        HOLIDAYS = self.HOLIDAYS
        if daytuple in HOLIDAYS:
            return True
        else:
            return False

    def is_weekend(self):
        now = datetime.now()
        if now.weekday() >= 5:
            return True
        else:
            return False

    def is_closedTime(self):    
        nowTime = int(datetime.now().strftime("%H%M%S"))   
        if int(START_TIME) <=  nowTime and nowTime <= int(END_TIME):
            return False
        else:
            return True

    def is_closedDayTime(self):
        if self.is_holiday():
            return False

        if self.is_weekend():
            return False

        if self.is_closedTime():
            return False

        return True        
 
if __name__=='__main__': 
    closed = ClosedDayTime()
    print(closed.is_holiday())
    print(closed.is_weekend())
    print(closed.is_closedTime())
    print(closed.is_closedDayTime())