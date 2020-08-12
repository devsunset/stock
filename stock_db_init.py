##################################################
#
#          stock_db_init program
#
##################################################

# install library
# $ pip install requests beautifulsoup4 apscheduler python-telegram-bot
import sqlite3

##################################################
# constant
current_amt = '500000'
table_version = 4

##################################################
# function
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

# main process
def main_process():
    for idx in range(table_version+1):
         
        try:
            try:
                sqlText = 'drop table stock_v'+str(idx+1)
                executeDB(sqlText)
            except Exception as err:
                pass

            try:
                sqlText = 'drop table stock_v'+str(idx+1)+'_meta'
                executeDB(sqlText)
            except Exception as err:
                pass
    
            sqlText = 'create table stock_v'+str(idx+1)+'_meta (current_amt text)'
            executeDB(sqlText)

            sqlText = 'insert into stock_v'+str(idx+1)+'_meta (current_amt) values ('+current_amt+')'
            executeDB(sqlText)

            sqlText = 'create table stock_v'+str(idx+1)+' (id integer primary key autoincrement, code text, item text, status text, purchase_current_amt text , sell_current_amt text, purchase_count text, purchase_amt text , sell_amt text, crt_dttm text, chg_dttm text)'
            executeDB(sqlText)

        except Exception as err:
            print(err)
        
        print('init stock_v'+str(idx+1) +'_meta and stock_v'+str(idx+1) +' table')   

if __name__ == '__main__':
    main_process()


