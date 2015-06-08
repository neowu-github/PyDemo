# encoding: UTF-8
'''
Created on 2014-9-29

@author: Sigma-WuZhengZhou
'''

import sys, os, ftplib, socket
import re
import time
import smtplib
import json
import sqlite3
from email.mime.text import MIMEText  

CONST_HOST = "xxxxx.com.cn"
CONST_USERNAME = "xxxx"
CONST_PWD = "xxxxx"
CONST_BUFFER_SIZE = 8192

mailto_list = ['zhwu@sigma-rt.com']#['support@sigma-rt.com', 'linzhang@sigma-rt.com', 'sgao@sigma-rt.com']# ['zhwu@sigma-rt.com']#
mail_host = "smtp.xxxxx.com"  # 设置服务器
# mail_user = "zhwu"  # 用户名
# mail_pass = "314159265"  # 口令 
mail_user = 'xxxxx'
mail_pass = 'xxxxxxxxxxxxx'
mail_postfix = 'sigma-rt.com' #邮箱后缀

def connect():
    try:
        ftp = ftplib.FTP(CONST_HOST)
        ftp.login(CONST_USERNAME, CONST_PWD)
        return ftp
    except socket.error, socket.gaierror:
        print("FTP is unavailable,please check the host,username and password!")
        sys.exit(0)

def disconnect(ftp):
    ftp.quit()

def download(ftp, filename):
    f = open(filename, "wb").write
    try:
        ftp.retrbinary("RETR %s" % filename, f, CONST_BUFFER_SIZE)
    except ftplib.error_perm:
        return False
    return True

def find(ftp, filename):
    ftp_f_list = ftp.nlst()
    if filename in ftp_f_list:
        return True
    else:
        return False

def send_mail(to_list, yestoday, ret, history5_0, history5_1, history5_2):  
    me = "TC Download" + "<" + mail_user + "@" + mail_postfix + ">"  # 这里的hello可以任意设置，收到信后，将按照设置显示
    
    content = getResult(yestoday, ret, history5_0, history5_1, history5_2)
    msg = MIMEText(content, _subtype='html', _charset='gb2312')  # 创建一个实例，这里设置为html格式邮件
    msg['Subject'] = "[" + yestoday + "]TC's Daily\All Download and Upgrade Info "  # 设置主题
    msg['From'] = me  
    msg['To'] = ";".join(to_list)  
    try:  
        s = smtplib.SMTP()  
        s.connect(mail_host)  # 连接smtp服务器
        s.login(mail_user, mail_pass)  # 登陆服务器
        s.sendmail(me, to_list, msg.as_string())  # 发送邮件
        s.close()  
        return True  
    except Exception, e:  
        print str(e)  
        return False

def getResult(date, ret, history5_0, history5_1, history5_2):
    data = 'Hi, All<br><br>\
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Please refer to The Daily Download\Upgrade Info of Total Control as below:<br><br>\
             <table width="650" border="1" bordercolor="black" cellspacing="1"> \
                <tr align="center">\
                    <td colspan="6" style="background-color:#ACD6FF">' + date + '</td>\
                </tr>\
                <tr align="center" style="background-color:yellow">\
                    <td rowspan="2">Sites</td>\
                    <td colspan="4">Client</td>\
                </tr>\
                <tr align="center" style="background-color:yellow">\
                    <td>5.1.0 Version</td>\
                    <td>5.1.0 Upgrade</td>\
                    <td>5.2.0 Version</td>\
                    <td>5.2.0 Upgrade</td>\
                </tr>\
                <tr align="center">\
                    <td>Chinese</td>\
                    <td>' + str(ret['cn_c']) + '</td>\
                    <td rowspan="2">' + str(ret['c_u']) + '</td>\
                    <td>' + str(ret['cn_c_5.2']) + '</td>\
                    <td rowspan="2">' + str(ret['c_u_5.2']+ret['c_521_patch']) + '</td>\
                </tr>\
                <tr align="center">\
                    <td>English</td>\
                    <td>' + str(ret['com_c']) + '</td>\
                    <td>' + str(ret['com_c_5.2']) + '</td>\
                </tr>\
                <tr align="center" style="background-color:#D2E9FF">\
                    <td>Total</td>\
                    <td>' + str(ret['cn_c']+ret['com_c']) + '</td>\
                    <td>' + str(ret['c_u']) + '</td>\
                    <td>' + str(ret['cn_c_5.2']+ret['com_c_5.2']) + '</td>\
                    <td>' + str(ret['c_u_5.2']+ret['c_521_patch']) + '</td>\
                </tr>\
            </table>\
            <br><br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Please refer to The All Download\Upgrade Info of Total Control as below:<br><br>\
            <table width="530" border="1" bordercolor="black" cellspacing="1"> \
                <tr align="center">\
                    <td colspan="7" style="background-color:#ACD6FF">TC 2 Accumulative Total</td>\
                </tr>\
                <tr align="center" style="background-color:yellow">\
                    <td rowspan="2">Sites</td>\
                    <td colspan="6">Client</td>\
                </tr>\
                <tr align="center" style="background-color:yellow">\
                    <td>5.0.0 Version</td>\
                    <td>5.0.0 Upgrade</td>\
                    <td>5.1.0 Version</td>\
                    <td>5.1.0 Upgrade</td>\
                    <td>5.2.0 Version</td>\
                    <td>5.2.0 Upgrade</td>\
                </tr>\
                <tr align="center">\
                    <td>Chinese</td>\
                    <td>' + str(int(history5_0["client_down_ch"]) + ret['cn_l_c']) + '</td>\
                    <td rowspan="2">' + str(int(history5_0["client_upgrade"]) + ret['l_u']) + '</td>\
                    <td>' + str(ret['cn_c'] + history5_1["client_down_ch"]) + '</td>\
                    <td rowspan="2">' + str(ret['c_u'] + history5_1["client_upgrade"]) + '</td>\
                    <td>' + str(ret['cn_c_5.2'] + history5_2["client_down_ch"]) + '</td>\
                    <td rowspan="2">' + str(ret['c_u_5.2'] + history5_2["client_upgrade"]+ret['c_521_patch'] + history5_2["c_521_patch"]) + '</td>\
                </tr>\
                <tr align="center">\
                    <td>English</td>\
                    <td>' + str(int(history5_0["client_down_en"]) + ret['com_l_c']) + '</td>\
                    <td>' + str(ret['com_c'] + history5_1["client_down_en"]) + '</td>\
                    <td>' + str(ret['com_c_5.2'] + history5_2["client_down_en"]) + '</td>\
                </tr>\
                <tr align="center" style="background-color:#D2E9FF">\
                    <td>Total</td>\
                    <td>' + str(int(history5_0["client_down_ch"]) + ret['cn_l_c'] + int(history5_0["client_down_en"]) + ret['com_l_c']) + '</td>\
                    <td>' + str(int(history5_0["client_upgrade"]) + ret['l_u']) + '</td>\
                    <td>' + str(ret['cn_c'] + ret['com_c'] + history5_1["client_down_ch"] + history5_1["client_down_en"]) + '</td>\
                    <td>' + str(ret['c_u'] + history5_1["client_upgrade"]) + '</td>\
                    <td>' + str(ret['cn_c_5.2'] + ret['com_c_5.2'] + history5_2["client_down_ch"] + history5_2["client_down_en"]) + '</td>\
                    <td>' + str(ret['c_u_5.2'] + history5_2["client_upgrade"]+ret['c_521_patch'] + history5_2["c_521_patch"]) + '</td>\
                </tr>\
                <tr align="center" style="background-color:yellow">\
                    <td>Acc Total</td>\
                    <td colspan="2">' + str(int(history5_0["client_down_ch"]) + ret['cn_l_c'] + int(history5_0["client_down_en"]) + ret['com_l_c'] + int(history5_0["client_upgrade"]) + ret['l_u']) + '</td>\
                    <td colspan="2">' + str(ret['cn_c'] + ret['com_c'] + ret['c_u'] + history5_1["client_down_ch"] + history5_1["client_down_en"] + history5_1["client_upgrade"]) + '</td>\
                    <td colspan="2">' + str(ret['cn_c_5.2'] + ret['com_c_5.2'] + ret['c_u_5.2'] + history5_2["client_down_ch"] + history5_2["client_down_en"] + history5_2["client_upgrade"]+ret['c_521_patch'] + history5_2["c_521_patch"]) + '</td>\
                </tr>\
            </table>'
    return data

def execSql(conn, sqlStr, whereTube=None):
    if not sqlStr or not conn:
        return None

    onlyUpdate = False
    sqlStrSmall = sqlStr.lower()
    if not sqlStrSmall.startswith('select'):
        onlyUpdate = True

    if not onlyUpdate:
        conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    ret = None
    try:
        if whereTube:
            cur.execute(sqlStr, whereTube)
        else:
            cur.execute(sqlStr)
    
        if onlyUpdate:
            conn.commit()
        else:
            ret = cur.fetchall()
    except Exception, e:
        print '_execSql Error:[%s], Reason:[%s]' % (sqlStr, e)
        ret = None
        
    cur.close()
    conn.close()
    if ret:
        return ret[0]

def getDB(dbPath):
    if not dbPath: return None
    try:
        db_connect = sqlite3.connect(dbPath)
    except Exception, e:
        print e
        return None
    return db_connect

def getHistoryTotal(version,yes_yestoday):
    file = 'TC_Info.db'
    conn = getDB(file)
    if not conn: return
    ret = {}
    if version == '5.0':
        table = 'version5_0_0'
    elif version == '5.1':
        table = 'version5_1_0'
    elif version =='5.2':
        table = 'version5_2_0'
    try:
        sqlStr = "Select * from %s where date = '%s'" % (table, yes_yestoday)
#         print sqlStr
        data = execSql(conn, sqlStr)
    except Exception, e:
        print "select data from %s failure, Reason[%s]" % (table, e)
    if version == '5.0':
        ret['date'] = data[1]
        ret['client_down_ch'] = data[2]
        ret['client_upgrade'] = data[3]
        ret['client_down_en'] = data[4]
        ret['apk_down_ch'] = data[5]
        ret['apk_down_en'] = data[6]
    elif version == '5.1' or version == '5.2':
        ret['date'] = data[1]
        ret['client_down_ch'] = data[2]
        ret['client_upgrade'] = data[3]
        ret['client_down_en'] = data[4]
        if version == '5.2':
            ret['c_521_patch'] = data[5]
    
#     print ret
    return ret

def getDownloadInfo(type,yestoday):
    client = {'latest_client':[], 'all_client':[],'client':[], 'client_5_2':[], "client_5_2_u":[]}
    apk = {'latest_apk':[], 'all_apk':[]}
    ret = {}
    if (type == 'cn'):
        file = 'tc.sigma-rt.com.cn_access_log.' + yestoday + '-00_00_00-CST'
    elif (type == 'com'):
        file = 'tc.sigma-rt.com_access_log.' + yestoday + '-00_00_00-CST' 
    if not os.path.exists(file):
        ftp = connect()
        if find(ftp, file): 
            download(ftp, file)
            disconnect(ftp)
        else:
            print '[Error: ]' + file + ' is not exist!!!'
    fp = open(file)
    clien_5_2_2 = re.compile(r'(?:zip|zip\?crazycache=1) HTTP/\d.\d" 20(?:0|6) 102903841')
    clien_5_2_2_p = re.compile(r'(?:exe|exe\?crazycache=1) HTTP/\d.\d" 20(?:0|6) 102981552')
    clien_5_2_2_exe = re.compile(r'(?:exe|exe\?crazycache=1) HTTP/\d.\d" 20(?:0|6) 40736861')
    clien_12247_p = re.compile(r'HTTP/\d.\d" 20(?:0|6) 40838708')
    clien_12247 = re.compile(r'HTTP/\d.\d" 20(?:0|6) 103098423')
    clien_5_2_1 = re.compile(r'Total_Control_(?:\d+.\d+.\d+|\d+.\d+.\d+.\d+)_Install.(?:zip|zip\?crazycache=1) HTTP/\d.\d" 20(?:0|6) 103049794')
    clien_5_2 = re.compile(r'Total_Control_(?:\d+.\d+.\d+|\d+.\d+.\d+.\d+)_Install.(?:zip|zip\?crazycache=1) HTTP/\d.\d" 20(?:0|6) 103037033')
    clien_pattern = re.compile(r'Total_Control_(?:\d+.\d+.\d+|\d+.\d+.\d+.\d+)_Install.(?:zip|zip\?crazycache=1) HTTP/\d.\d" 20(?:0|6) 98634953')
    latest_clien_pattern = re.compile(r'Total_Control_(?:\d+.\d+.\d+|\d+.\d+.\d+.\d+)_Install.(?:zip|zip\?crazycache=1) HTTP/\d.\d" 20(?:0|6) 100238340')               
    all_clien_pattern = re.compile(r'GET /download/client/Total_Control_(?:\d+.\d+.\d+|\d+.\d+.\d+.\d+)_Install.(?:zip|zip\?crazycache=1) HTTP/\d.\d" 20(?:0|6) (?:100238340|46885253|16306282|16224388|13598887|13590999|13440231|24647540|23951026|24262002|24247223|23464313|25222986)')               
    latest_apk_pattern = re.compile(r'GET /download/apk/MobileAgent_(?:\d+.\d+.\d+|\d+.\d+.\d+.\d+).(?:zip|zip\?crazycache=1) HTTP/\d.\d" 20(?:0|6) 4216651') 
    all_apk_pattern = re.compile(r'GET /download/apk/MobileAgent_(?:\d+.\d+.\d+|\d+.\d+.\d+.\d+).(?:zip|zip\?crazycache=1) HTTP/\d.\d" 20(?:0|6) (?:4216651|2157715|1857079|1976751|1975466|1869274|1874383|1875528|1875239|1875253|1874538|1872969)')   
    while True:
        line = fp.readline() 
        m = latest_clien_pattern.search(line)
        m1 = all_clien_pattern.search(line)
        n = latest_apk_pattern.search(line)
        n1 = all_apk_pattern.search(line)
        k = clien_pattern.search(line)
        k1 = clien_5_2.search(line)
        k2 = clien_5_2_1.search(line)
        k3 = clien_12247.search(line)
        k4 = clien_12247_p.search(line)
        k5 = clien_5_2_2.search(line)
        k6 = clien_5_2_2_exe.search(line)
        k7 = clien_5_2_2_p.search(line)   
        if k7:
            str = line.split(' ')
            ret['ip'] = str[0]
            ret['time'] = str[3][1:]
            ret['package'] = str[6]
            ret['http'] = str[7]
            client['client_5_2_u'].append(ret)
            ret = {}
        if k6:
            str = line.split(' ')
            ret['ip'] = str[0]
            ret['time'] = str[3][1:]
            ret['package'] = str[6]
            ret['http'] = str[7]
            client['client_5_2_u'].append(ret)
            ret = {}
        if k5:
            str = line.split(' ')
            ret['ip'] = str[0]
            ret['time'] = str[3][1:]
            ret['package'] = str[6]
            ret['http'] = str[7]
            client['client_5_2'].append(ret)
            ret = {}     
        if k4:
            str = line.split(' ')
            ret['ip'] = str[0]
            ret['time'] = str[3][1:]
            ret['package'] = str[6]
            ret['http'] = str[7]
            client['client_5_2_u'].append(ret)
            ret = {}
        if k3:
            str = line.split(' ')
            ret['ip'] = str[0]
            ret['time'] = str[3][1:]
            ret['package'] = str[6]
            ret['http'] = str[7]
            client['client_5_2_u'].append(ret)
            ret = {}
        if k2:
            str = line.split(' ')
            ret['ip'] = str[0]
            ret['time'] = str[3][1:]
            ret['package'] = str[6]
            ret['http'] = str[7]
            client['client_5_2'].append(ret)
            ret = {}
        if k1:
            str = line.split(' ')
            ret['ip'] = str[0]
            ret['time'] = str[3][1:]
            ret['package'] = str[6]
            ret['http'] = str[7]
            client['client_5_2'].append(ret)
            ret = {}
        if k :
            str = line.split(' ')
            ret['ip'] = str[0]
            ret['time'] = str[3][1:]
            ret['package'] = str[6]
            ret['http'] = str[7]
            client['client'].append(ret)
            ret = {}
        if m :
            str = line.split(' ')
            ret['ip'] = str[0]
            ret['time'] = str[3][1:]
            ret['package'] = str[6]
            ret['http'] = str[7]
            client['latest_client'].append(ret)
            ret = {}
        if m1 :
            str = line.split(' ')
            ret['ip'] = str[0]
            ret['time'] = str[3][1:]
            ret['package'] = str[6]
            ret['http'] = str[7]
            client['all_client'].append(ret)
            ret = {}
        if n :
            str = line.split(' ')
            ret['ip'] = str[0]
            ret['time'] = str[3][1:]
            ret['package'] = str[6]
            ret['http'] = str[7]
            apk['latest_apk'].append(ret)
            ret = {}
        if n1 :
            str = line.split(' ')
            ret['ip'] = str[0]
            ret['time'] = str[3][1:]
            ret['package'] = str[6]
            ret['http'] = str[7]
            apk['all_apk'].append(ret)
            ret = {}
        if not line:
            break
        pass
    fp.close()
    #moveLog2Tmp(file, type)  
      
    return client, apk

def uniqMethod(dict):
    k = 1
    if (dict.__len__() == 0):
        k = 0
    for i in range(0, dict.__len__()):
        j = i+1
        if j<dict.__len__():
            if dict[i]['ip']==dict[j]['ip'] and dict[i]['time']==dict[j]['time'] \
                    and dict[i]['package']==dict[j]['package'] and dict[i]['http']==dict[j]['http']:
                pass
            else:
                k += 1
    return k

def getUpdateInfo(yestoday):
    latest_update = []
    all_update = []
    client_update = []
    client_5_2 = []
    client_5_2_1_patch = []
    ret = {}
    file = 'access_log.'+ yestoday +'-00_00_00-CST' 
    file1 = 'upgrade.sigma-rt.com.cn_access_log.'+ yestoday +'-00_00_00-CST'
    if not os.path.exists(file1):
        ftp = connect()
        if find(ftp, file1): 
            download(ftp, file1)
            disconnect(ftp)
        else:
            print '[Error: ]' + file1 + ' is not exist!!!'
    if os.path.exists(file1):
        fp1 = open(file1)
        clien_52 = re.compile(r'GET /packages/totalcontrol/update/Total_Control_(?:\d+.\d+.\d+|\d+.\d+.\d+.\d+)_Install.(?:exe|exe\?crazycache=1) HTTP/\d.\d" 20(?:0|6) 103114877')
        clien_521_patch = re.compile(r'GET /packages/totalcontrol/update/patchs/5.2.0/Total_Control_(?:\d+.\d+.\d+|\d+.\d+.\d+.\d+)_Patch_Install.(?:exe|exe\?crazycache=1) HTTP/\d.\d" 20(?:0|6) 40838708')
        while True:
            line1 = fp1.readline()
            s = clien_52.search(line1)
            t = clien_521_patch.search(line1)
            if s:
                str = line1.split(' ')
                ret['ip'] = str[0]
                ret['time'] = str[3][1:]
                ret['package'] = str[6]
                ret['http'] = str[7]
                client_5_2.append(ret)
                ret = {}
            if t:
                str = line1.split(' ')
                ret['ip'] = str[0]
                ret['time'] = str[3][1:]
                ret['package'] = str[6]
                ret['http'] = str[7]
                client_5_2_1_patch.append(ret)
                ret = {}
            if not line1:
                break
            pass
        fp1.close()
    else:
        raise IOError('no such file ['+ file1 +']')
    
    if os.path.exists(file):
        fp = open(file)
        clien_52 = re.compile(r'GET /packages/srt-tc/update/\d+/Total_Control_(?:\d+.\d+.\d+|\d+.\d+.\d+.\d+)_Install.(?:exe|exe\?crazycache=1) HTTP/\d.\d" 20(?:0|6) 103114877')
        clien_upgrade = re.compile(r'GET /packages/srt-tc/update/\d+/Total_Control_(?:\d+.\d+.\d+|\d+.\d+.\d+.\d+)_Install.(?:exe|exe\?crazycache=1) HTTP/\d.\d" 20(?:0|6) 98713320')
        latest_version = re.compile(r'GET /packages/srt-tc/update/\d+/Total_Control_(?:\d+.\d+.\d+|\d+.\d+.\d+.\d+)_Install.(?:exe|exe\?crazycache=1) HTTP/\d.\d" 20(?:0|6) 100284413')               
        all_version = re.compile(r'GET /packages/srt-tc/update/\d+/Total_Control_(?:\d+.\d+.\d+|\d+.\d+.\d+.\d+)_Install.(?:exe|exe\?crazycache=1) HTTP/\d.\d" 20(?:0|6) (?:100284413|46899363|16324862|16242981|16268138|16229255|13615186|13607367|13456618|24664723|24285154|24270312|23482193|25240269)')              
        while True:
            line = fp.readline() 
            m = latest_version.search(line)
            n = all_version.search(line)
            k = clien_upgrade.search(line)
            k1 = clien_52.search(line)
            if k1:
                str = line.split(' ')
                ret['ip'] = str[0]
                ret['time'] = str[3][1:]
                ret['package'] = str[6]
                ret['http'] = str[7]
                client_5_2.append(ret)
                ret = {}
            if k:
                str = line.split(' ')
                ret['ip'] = str[0]
                ret['time'] = str[3][1:]
                ret['package'] = str[6]
                ret['http'] = str[7]
                client_update.append(ret)
                ret = {}
            if m :
                str = line.split(' ')
                ret['ip'] = str[0]
                ret['time'] = str[3][1:]
                ret['package'] = str[6]
                ret['http'] = str[7]
                latest_update.append(ret)
                ret = {}
            if n:
                str = line.split(' ')
                ret['ip'] = str[0]
                ret['time'] = str[3][1:]
                ret['package'] = str[6]
                ret['http'] = str[7]
                all_update.append(ret)
                ret = {}
            if not line:
                break
            pass
        fp.close()
    else:
        raise IOError('no such file ['+ file +']')
    
    #moveLog2Tmp(file, 'upgrade')
    #moveLog2Tmp(file1, 'upgrade')
    
    return latest_update, all_update, client_update, client_5_2, client_5_2_1_patch

def moveLog2Tmp(file, type):
    des = None
    cmd = None
    if type == 'com':
        des = '/root/log/tmp/com/'
    elif type == 'cn':
        des = '/root/log/tmp/cn/'
    elif type == 'upgrade':
        des = '/root/log/tmp/upgrade/'
    if des:
        cmd = 'mv %s %s' % (file, des)
    if cmd:
        os.system(cmd)

def saveData2History(yestoday, ret, history5_0, history5_1, history5_2):
    num1 = int(history5_0["client_down_ch"]) + ret['cn_l_c']
    num2 = int(history5_0["client_down_en"]) + ret['com_l_c']
    num3 = int(history5_0["client_upgrade"]) + ret['l_u']
    num4 = int(history5_0["apk_down_ch"]) + ret['cn_l_a']
    num5 = int(history5_0["apk_down_en"]) + ret['com_l_a']
    num6 = int(history5_1["client_down_ch"]) + ret['cn_c']
    num7 = int(history5_1["client_down_en"]) + ret['com_c']
    num8 = int(history5_1["client_upgrade"]) + ret['c_u']
    num9 = int(history5_2["client_down_ch"]) + ret['cn_c_5.2']
    num10 = int(history5_2["client_down_en"]) + ret['com_c_5.2']
    num11 = int(history5_2["client_upgrade"]) + ret['c_u_5.2']
    num12 = int(history5_2["c_521_patch"]) + ret['c_521_patch']
    sqlStr1 = "insert into version5_0_0(date, client_down_ch, client_upgrade, client_down_en, apk_down_ch, apk_down_en) values(?, ?, ?, ?, ?, ?)"
    whereTube1  = (yestoday, num1, num3, num2, num4, num5)
    sqlStr2 = "insert into version5_1_0(date, client_down_ch, client_upgrade, client_down_en) values(?, ?, ?, ?)" 
    whereTube2  = (yestoday, num6, num8, num7)
    sqlStr3 = "insert into version5_2_0(date, client_down_ch, client_upgrade, client_down_en, client_5_2_1_12247_patch) values(?, ?, ?, ?, ?)" 
    whereTube3  = (yestoday, num9, num11, num10, num12)
#     print sqlStr1
#     print sqlStr2
    insert2DB(sqlStr1, whereTube1)
    insert2DB(sqlStr2, whereTube2)
    insert2DB(sqlStr3, whereTube3)
    
def insert2DB(sqlStr, whereTube):
    file = 'TC_Info.db'
    conn = getDB(file)
    if not conn: return
    try:
        execSql(conn, sqlStr, whereTube)
    except Exception, e:
        print "insert data to db failure, Reason[%s]" %  e
        raise e

def getData(yestoday):
    #cn means statistics from Chinese Website
    #com means statistics from US Website
    cn_client_num , cn_apk_num = getDownloadInfo('cn',yestoday)
    com_client_num , com_apk_num = getDownloadInfo('com',yestoday) 
    
    #statistics the upgrade num
    l_update, a_update, c_update, c_5_2, c_521_patch= getUpdateInfo(yestoday)
    
    ret = {}
    ret['cn_l_c'] = cn_client_num['latest_client'].__len__()
    ret['cn_a_c'] = cn_client_num['all_client'].__len__()
    ret['cn_l_a'] = cn_apk_num['latest_apk'].__len__()
    ret['cn_a_a'] = cn_apk_num['all_apk'].__len__()
    ret['com_l_c'] = com_client_num['latest_client'].__len__()
    ret['com_a_c'] = com_client_num['all_client'].__len__()
    ret['com_l_a'] = com_apk_num['latest_apk'].__len__()
    ret['com_a_a'] = com_apk_num['all_apk'].__len__()
    ret['l_u'] = l_update.__len__()
    ret['a_u'] = a_update.__len__()
    ret['c_u'] = c_update.__len__()
    ret['cn_c'] = cn_client_num['client'].__len__()
    ret['com_c'] = com_client_num['client'].__len__()
    ret['c_u_5.2'] = c_5_2.__len__() + cn_client_num["client_5_2_u"].__len__()
    ret['cn_c_5.2'] = cn_client_num['client_5_2'].__len__()
    ret['com_c_5.2'] = com_client_num['client_5_2'].__len__()
    ret['c_521_patch'] = c_521_patch.__len__()
    print "[%d,%d,%d,%d]" % (ret['c_u_5.2'],ret['cn_c_5.2'],ret['com_c_5.2'],ret['c_521_patch'])
    
    ret['c_u_5.2'] = uniqMethod(c_5_2) + uniqMethod(cn_client_num["client_5_2_u"])
    ret['cn_c_5.2'] = uniqMethod(cn_client_num['client_5_2'])
    ret['com_c_5.2'] = uniqMethod(com_client_num['client_5_2'])
    ret['c_521_patch'] = uniqMethod(c_521_patch)
    print "[%d,%d,%d,%d]" % (ret['c_u_5.2'],ret['cn_c_5.2'],ret['com_c_5.2'],ret['c_521_patch'])
    
    return ret

def main(yestoday=None, yes_yestoday=None):  
    #get the time str, such as '2015-01-01'
    now = time.strftime("%a %b %d %H:%M:%S %Y", time.localtime()) 
    now = time.mktime(time.strptime(now, "%a %b %d %H:%M:%S %Y"))
    if not yestoday and not yes_yestoday:
        yestoday = time.strftime("%Y-%m-%d", time.gmtime(now - 57600))
        yes_yestoday = time.strftime("%Y-%m-%d", time.gmtime(now - 57600 - 86400))
    
    #get the download and upgrade num
    ret = getData(yestoday)
    
    #get the history data of 5.0 and 5.1 from the database 
    history5_0 = getHistoryTotal('5.0',yes_yestoday)
    history5_1 = getHistoryTotal('5.1',yes_yestoday)
    history5_2 = getHistoryTotal('5.2',yes_yestoday)
    #store the new data into the database
    saveData2History(yestoday, ret, history5_0, history5_1, history5_2)
    
    #send email to TC support team
    if send_mail(mailto_list, yestoday, ret, history5_0, history5_1, history5_2):  
        print "success"  
    else:  
        print "fail" 
          
if __name__ == "__main__":
    print 'param:',sys.argv
    yestoday = None
    yes_yestoday = None
    if len(sys.argv) == 3:
        if sys.argv[1] and sys.argv[2]:
            print sys.argv[1],sys.argv[2]
            yestoday = sys.argv[1]
            yes_yestoday = sys.argv[2]
    if yestoday and yes_yestoday:
        main(yestoday, yes_yestoday)
    else:
        main()
        
    #===========================================================================
    # today = time.strftime("%a %b %d %H:%M:%S %Y", time.localtime()) 
    # print today
    # today = time.mktime(time.strptime(today, "%a %b %d %H:%M:%S %Y"))
    # print time.strftime("%a %b %d %H:%M:%S %Y", time.gmtime(today - 57600)) 
    # print time.strftime("%a %b %d %H:%M:%S %Y", time.gmtime(today - 86400*1 - 57600)) 
    # print time.strftime("%a %b %d %H:%M:%S %Y", time.gmtime(today - 86400*2 - 57600)) 
    # print time.strftime("%a %b %d %H:%M:%S %Y", time.gmtime(today - 86400*3 - 57600)) 
    # yestoday = time.strftime("%Y-%m-%d", time.gmtime(today - 57600))
    #===========================================================================
