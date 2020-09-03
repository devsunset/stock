# stock(python)
--------------------------------------------------------------------------
네이버 주식 (https://finance.naver.com/) - Crawling
--------------------------------------------------------------------------

- 1. install python library

     $ pip install requests beautifulsoup4 apscheduler python-telegram-bot

- 2. seqlite3 install  && sqlite location PATH add

- 3. create db schema (stock_db_init.py)

     sqlite3 stock.db
 
     * version 1 ~ 3
     
     create table stock_vX_meta (current_amt text);
     
     insert into stock_vX_meta (current_amt) values ('현재자금 ex) 500000');

     create table stock_vX (id integer primary key autoincrement, code text, item text, status text
       , purchase_current_amt text , sell_current_amt text, purchase_count text
       , purchase_amt text , sell_amt text, search_rate text, yesterday_rate text, up_down_rate text
       , ps_cnt text, c_amt text, h_amt text, l_amt, crt_dttm text, chg_dttm text);

     * version 4 ~ 9
     
     create table stock_vX_x_meta (current_amt text);
     
     insert into stock_vX_x_meta (current_amt) values ('현재자금 ex) 500000');

     create table stock_vX_x (id integer primary key autoincrement, code text, item text, status text
       , purchase_current_amt text , sell_current_amt text, purchase_count text
       , purchase_amt text , sell_amt text, crt_dttm text, chg_dttm text);

- 4. telegram setting   
     BotFather -> /newbot -> devsunetstock -> devsunsetstock_bot - > get api key 

--------------------------------------------------------------------------
reference

- 파이썬으로 배우는 알고리즘 트레이딩

https://wikidocs.net/book/110

https://github.com/pystockhub/book


- 손가락 하나 까딱하지 않는 주식 거래 시스템 구축

https://www.youtube.com/watch?v=1lHzaihEb48&list=PLDtzZPtOGenaSknTbsb6x6L39V0VPz_rS

https://github.com/programgarden/book

--------------------------------------------------------------------------
