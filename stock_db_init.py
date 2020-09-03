##################################################
#
#          stock_db_init program
#
##################################################

##################################################
#
# > seqlite3 install  && sqlite location PATH add
#
# > create table schema
#   - sqlite3 stock.db
# 
# > version 1 ~ 3
#   create table stock_vX_meta (current_amt text);
#   insert into stock_vX_meta (current_amt) values ('현재자금 ex) 500000');
#
#   create table stock_vX (id integer primary key autoincrement, code text, item text, status text
#       , purchase_current_amt text , sell_current_amt text, purchase_count text
#       , purchase_amt text , sell_amt text, search_rate text, yesterday_rate text, up_down_rate text
#       , ps_cnt text, c_amt text, h_amt text, l_amt, crt_dttm text, chg_dttm text);
#
# > version 4 ~ 9
#   create table stock_vX_x_meta (current_amt text);
#   insert into stock_vX_x_meta (current_amt) values ('현재자금 ex) 500000');
#
#   create table stock_vX_x (id integer primary key autoincrement, code text, item text, status text
#       , purchase_current_amt text , sell_current_amt text, purchase_count text
#       , purchase_amt text , sell_amt text, crt_dttm text, chg_dttm text);
#
##################################################

##################################################
# import

import sqlite3
import stock_constant

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
    for idx in range(stock_constant.CREATE_TABLE_VERSION):

        if stock_constant.CURRENT_TABLE_CREATE_FLAG == True:
            if(idx+1 != stock_constant.CREATE_TABLE_VERSION):
                continue
         
        if idx >= 3 :
            for idxF in range(0,21):
                try:
                    try:
                        sqlText = 'drop table stock_v'+str(idx+1)+'_'+str(idxF)
                        executeDB(sqlText)
                    except Exception as err:
                        pass

                    try:
                        sqlText = 'drop table stock_v'+str(idx+1)+'_'+str(idxF)+'_meta'
                        executeDB(sqlText)
                    except Exception as err:
                        pass
            
                    sqlText = 'create table stock_v'+str(idx+1)+'_'+str(idxF)+'_meta (current_amt text)'
                    executeDB(sqlText)

                    sqlText = 'insert into stock_v'+str(idx+1)+'_'+str(idxF)+'_meta (current_amt) values ('+str(stock_constant.CURRENT_AMT)+')'
                    executeDB(sqlText)

                    sqlText = 'create table stock_v'+str(idx+1)+'_'+str(idxF)+' (id integer primary key autoincrement, code text, item text, status text, purchase_current_amt text, sell_current_amt text, purchase_count text, purchase_amt text, sell_amt text, up_amt text, crt_dttm text, chg_dttm text)'
                    executeDB(sqlText)

                except Exception as err:
                    print(err)
            
                print('init stock_v'+str(idx+1) +'_meta and stock_v'+str(idx+1)+'_'+str(idxF) +' table')               
        else:
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

                sqlText = 'insert into stock_v'+str(idx+1)+'_meta (current_amt) values ('+str(stock_constant.CURRENT_AMT)+')'
                executeDB(sqlText)

                if idx == 0 :
                     sqlText = 'create table stock_v1 (id integer primary key autoincrement, code text, item text, status text, purchase_current_amt text , sell_current_amt text, purchase_count text, purchase_amt text , sell_amt text, search_rate text, yesterday_rate text, up_down_rate text, ps_cnt text, c_amt text, h_amt text, l_amt, crt_dttm text, chg_dttm text)'
                else:
                    sqlText = 'create table stock_v'+str(idx+1)+' (id integer primary key autoincrement, code text, item text, status text, purchase_current_amt text , sell_current_amt text, purchase_count text, purchase_amt text , sell_amt text, crt_dttm text, chg_dttm text)'
                    
                executeDB(sqlText)

            except Exception as err:
                print(err)
            
            print('init stock_v'+str(idx+1) +'_meta and stock_v'+str(idx+1) +' table')   

##################################################
# main     

if __name__ == '__main__':
    main_process()