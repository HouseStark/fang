import requests
import re
import os
import time
import db

from pymysql.err import IntegrityError

#URL = 'http://210.75.213.188/shh/portal/bjjs2016/list.aspx'
URL = "http://210.75.213.188/shh/portal/bjjs2016/list.aspx?pagenumber={page}&pagesize=7"
HEADERS = {"Pragma": "no-cache",
         "Origin": "http://210.75.213.188",
         "Accept-Encoding": "gzip, deflate",
         "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
         "Upgrade-Insecure-Requests": "1",
         "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36",
         "Content-type": "amultipart/form-data; boundary=----WebKitFormBoundary1Ict5sBrJz8yHYuj",
         "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
         "Cache-Control": "no-cache",
         "Referer": "http://210.75.213.188/shh/portal/bjjs2016/list.aspx?pagenumber=2&pagesize=7",
         "Cookie": "ASP.NET_SessionId=o0qvynzk2cfnkf55aaryft45",
         "Connection":"keep-alive",
        }
 
PAYLOAD = {"district_id":'', "plot":'', "sell_money_from":"", "sell_money_to":"","set_type":"",
         "organize_type":"","broker_title":"","buildarea_from":"","buildarea_to":"","house_from_cert_id":"",
         "audit_on":"",}

PAGE_S=1
PAGE_E=4000+1
try_num = 7
_DIR=os.path.dirname(os.path.realpath(__file__))


 
#转换成localtime
time_local = time.localtime(time.time())
#转换成新的时间格式(2016-05-05 20:28:54)
#dt = time.strftime("%Y-%m-%d %H:%M:%S",time_local)
dt = time.strftime("%Y%m%d",time_local)
if not os.path.exists(os.path.join(_DIR,dt)):
    os.mkdir(os.path.join(_DIR,dt))

dbinfo={'host':'127.0.0.1', 'user':'root', 'passwd':'123', 'db':'data', 'port':3306, 'charset':'utf8'}

conn=db.Connection(**dbinfo)

#r = requests.post(URL, headers=HEADERS, data=PAYLOAD)
#for page in range(PAGE_S,PAGE_E):
for page in range(PAGE_S,PAGE_E):
    r = requests.post(URL.format(page=page), headers=HEADERS)
    if r.status_code!=200:
        print(r.status_code)
        print("error:page:{}".format(page))

        continue
    if len(r.text)==0:
        print(len(r.text))    
        print("error:page:{},done".format(page))
        continue

#    with open(os.path.join(_DIR,dt,"{}.html".format(page)), 'wb') as fd:
#        for chunk in r.iter_content(4096):
#            fd.write(chunk)    
    if 'audit_house_detail' not in r.text:
        break

    original_html={"html":r.text, "date":dt, "url":URL.format(page=page)}
    conn.insert('html_archive_fang', **original_html) 

    print("page:{},done".format(page))

    pattern=re.compile(r'<tr>\s*?<td>(\d*?)</td>\s*?<td>(.*?)</td>\s*?<td>(.*?)</td>.*?<td>(.*?)</td>.*?<td>([0-9.]*?)</td>.*?<td>([0-9.]*?)万元</td>.*?<td class="left">(.*?)</td>.*?<td>(.*?)</td>.*?<td class="r"><a href="(.*?)" target="_blank">.*?</a></td>.*?</tr>',re.I|re.S)
    items = re.findall(pattern, r.text)
    for item in items:
        cols=('id','district','xiaoqu','huxing','mianji','jiaqian','jigou','date','url')
        data=dict(zip(cols,item))
        data['url']='http://210.75.213.188/shh/portal/bjjs2016/'+data['url'] 
        data['jigou']= data['jigou'].replace('&nbsp;','')
        try:
            conn.insert('fang', **data)
        except IntegrityError as e:
            print("dup",e)
	    try_num+=1
            if try_num >3:
                exit() 

       
        
#    break
 
 
