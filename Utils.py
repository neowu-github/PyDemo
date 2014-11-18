#coding=utf-8
'''
Created on 2014-11-17

@author: NeoWu
'''
import os
import sqlite3
import xml.etree.ElementTree as ET
import urllib, urllib2
import StringIO
import gzip
import poster
import sys
import cookielib
import hashlib
import md5
import xlwt
import xlrd
from xlwt import *
from xlutils.copy import copy
import time
import smtplib
from email.mime.text import MIMEText  
import email.mime.multipart
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email import Encoders
import ftplib, socket
import paramiko
import ecdsa
import re
import json
import platform
import turtle
import math

'''
获取指定目录下的文件列表
'''
def GetFileList(dir, fileList):
    newDir = dir
    if os.path.isfile(dir):
        fileList.append(dir.decode('gbk'))
    elif os.path.isdir(dir):  
        for s in os.listdir(dir):
            #忽略某些文件夹
            if s == "xxxx":
                continue
            newDir=os.path.join(dir,s)
            GetFileList(newDir, fileList)  
    return fileList

'''
使用sqlite3连接数据库
'''
def getSubLibraryDB(path):
    if not os.path.exists(path):
        return None
    dbPath = os.path.join(path, 'library.db')
    try:
        connect = sqlite3.connect(dbPath)
    except Exception, e:
        print "ConnectSubLibraryDB Error! :%s"%e
        return None
    return connect 

'''
执行sql语句,返回结果
'''  
def execSubLibrarySql(path, sqlStr, whereTube=None):
    if not path or not os.path.exists(path):
        print "execSubLibrarySql None! path[%s]"%path
        return False
    ret = execSql(getSubLibraryDB(path), sqlStr, whereTube)
    return ret;  

'''
sql执行方法
'''
def execSql(conn, sqlStr, whereTube):
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
        print'_execSql Error:[%s], Reason:[%s]'%(sqlStr, e)
        ret = None
        
    cur.close()
    conn.close()
    return ret

'''
将指定目录下的xml文件转换为字典 dict
strXmlFileName ： xml 文件name
strElementPath ： xml 节点
dictSubElement ： dict 用于返回
eg.   my_dict = xml2dict('xxx.xml', 'node', my_dict)
'''
def xml2dict(strXmlFileName, strElementPath, dictSubElement):   
    elementList = []
    dictSubElement.clear()
    try:
        eTree=ET.parse(os.getcwd() + strXmlFileName)
    except Exception,errorinfo:
        print "xml2dict: ET.parse(%s) generate exception, errorinfo:%s" % ((os.getcwd() + strXmlFileName), errorinfo)
        raise errorinfo
    
    try:        
        elementList=eTree.findall(strElementPath)           
    except Exception,errorinfo:
        print "xml2dict: eTree.findall(%s) generate exception, errorinfo:%s" % (strElementPath, errorinfo)
        raise errorinfo
    
    pathList = []
    for element in elementList:
        for subelement in element.getchildren():
#                print "tag:%s, text:%s" % (subelement.tag, subelement.text.encode("utf-8"))           
            if subelement.text is not None:
                if subelement.tag in pathList:                        
                    dictSubElement[subelement.tag] = (os.getcwd() + subelement.text).encode('utf-8')
                else :
                    dictSubElement[subelement.tag] = subelement.text.encode('utf-8')
            else:
                dictSubElement[subelement.tag] = "" #将None赋值一串空字符串


'''
urllib2 get request
'''    
def OpenUrl(url, value, mothed):  
    
    if mothed == "1":
        req = urllib2.Request(url)
    else: 
        req = urllib2.Request(url, urllib.urlencode(value))
           
    err = HTTPError()
    try:
        opener=urllib2.build_opener(err)  
        fp = opener.open(req)
    except Exception, e:
        print "url:%s, value:%s, req failed." % (url, value)
        print err.getErrorMsg()
        raise e

    data = fp.read()
#        print fp.headers
    if 'gzip' == fp.headers.get('content-encoding', ''):
        compressedstream = StringIO.StringIO(data)
        gzipper = gzip.GzipFile(fileobj=compressedstream)
        data = gzipper.read()
        
    return data, fp.headers.get("Content-Type", '') 
                
class HTTPError(urllib2.HTTPDefaultErrorHandler):
    def __init__(self):
        self.errMsg = ''
        
    def getErrorMsg(self):
        return self.errMsg
    
    def http_error_default(self, req, fp, code, msg, hdrs):
        if code >= 400 :
            self.errMsg  = fp.read()        
        raise urllib2.HTTPError(req.get_full_url(), code, msg, hdrs, fp)
'''
urllib2 post request: eg. uploadfile
'''
def sendMultipartPost(url, params, files):
    posterParams = []
    for key in params:
        value = params[key]
        try:                
            posterParams.append(poster.encode.MultipartParam(key, value))
        except Exception, e:
            print e, key, value    
            raise e
        
    for key in files:
        value = files[key]
        try:
            value = value.encode(sys.getfilesystemencoding())
            posterParams.append(poster.encode.MultipartParam.from_file(key, value))
        except Exception, e:
            print e, key, value    
            raise e
    
    try:    
        datagen, headers = poster.encode.multipart_encode(posterParams)
    except Exception, e:
        print e, key, value    
        raise e

    if headers is None:
        headers = {}            
    
    try: 
        request = urllib2.Request(url, datagen, headers)   
        request.add_header('Accept-encoding', 'gzip')   
        request.add_header("Accept", "*/*")     
#             print request   
#             print request.get_data()
        opener,err = getUrllib2(True, False)
        response = opener.open(request)
    except Exception, e:
        print e, url, files
        print err.getErrorMsg()
        raise e
    data = response.read()
    '''
    data = response.read(16*1024)
    length = len(data)
    _data = None
    while length:
        if _data: data += _data
        _data = response.read(16*1024)
        length = len(_data)
    '''    
    if 'gzip' == response.headers.get('content-encoding', ''):
        compressedstream = StringIO.StringIO(data)
        gzipper = gzip.GzipFile(fileobj=compressedstream)
        data =gzipper.read()            
        
    return data

def getUrllib2(self, upload = False, redirect = False):
    if upload:
        handlers = poster.streaminghttp.get_handlers()
    else:
        handlers = []
    err = HTTPError() 
    handlers.append(err)  
    handlers.append(getCookie())
    
    try:
        opener = urllib2.build_opener(*handlers)
    except Exception, e:
        print err.getErrorMsg()
        raise e
    return opener,err

def getCookie():
    global _cookieProcessor
    cookiefile = "./cookies.txt"         
    try:
        httpcookie = cookielib.MozillaCookieJar(cookiefile)
        httpcookie.load(ignore_discard=True, ignore_expires=True)
        httpcookie = urllib2.HTTPCookieProcessor(httpcookie)
    except Exception, e:
        print e    
        httpcookie = _cookieProcessor
            
#    _cookieProcessor = urllib2.HTTPCookieProcessor(cookielib.CookieJar())    
    return httpcookie

'''
MD5 method
'''
def MD5_str(sStr):
    md5_sStr = hashlib.md5(sStr)
    md5_sStr.digest()
    md5_sStr.hexdigest()
    return md5_sStr.hexdigest() 

def getMd5OfFile(fname):
    if not os.path.exists(fname):
        return None

    try:
        f = file(fname, 'rb')
        m = md5.new()
        while True:
            d = f.read(16384)
            if not d:
                break
            m.update(d)
        f.close()
        return m.hexdigest()
    except Exception,e:
        print e
        return None

'''
excel 读写操作
'''
def saveData2Excel(path):
    file = os.getcwd()+ '\\[SRT-TC]User_Data_Count.xls'
    borders = xlwt.Borders()
    borders.left = 1
    borders.right = 1
    borders.top = 1
    borders.bottom = 1
    borders.bottom_colour=0x3A    
    alignment = xlwt.Alignment()
    alignment.horz = xlwt.Alignment.HORZ_CENTER
    alignment.vert = xlwt.Alignment.VERT_CENTER
    style = xlwt.XFStyle()
    style.borders = borders 
    style.alignment = alignment 
    try:
        oldWb = xlrd.open_workbook(file, formatting_info=True)
    except Exception,e:
        print "Exception :", e
        raw_input("Enter enter key to exit...")
        raise e
    newWb = copy(oldWb)
    if type == 'di':#device info
        sheetnum = 'sheet3'
        ret = {}
        rs = oldWb.sheet_by_name(u'sheet1')
        nrows = rs.nrows
        ncols = rs.ncols
        today = time.strftime("%Y\%m\%d", time.localtime()) 
        newWs = newWb.get_sheet(2)
        newWs.col(1).width = 8332
        newWs.col(2).width = 3000
        newWs.col(3).width = 6000
        newWs.col(4).width = 5000
        newWs.col(5).width = 2500
        newWs.col(6).width = 8332
        for i in range(0, nrows-1):
            for j in range(0, ncols):
                newWs.write(i+1, j, None)
        for i in range(0, ret.__len__()):
            newWs.write(i+1, 0, i+1,style)#行，列，值， style
            for j in range(0, ncols-1):
                newWs.write(i+1, j+1, ret[i][j].decode('gbk'), style)
  
    try:
        newWb.save(file)
    except Exception,e:
        print "Exception :", e
        raw_input("Enter enter key to exit...")
        raise e
    print 'save data 2 xls done:%s' % sheetnum
    
'''
发送邮件
'''
def send_mail():  
    mailto_list = ['zhwu@sigma-rt.com']
    mail_host = "smtp.sigma-rt.com"  # 设置服务器
    mail_user = "zhwu"  # 用户名
    mail_pass = "314159265"  # 口令 
    mail_postfix = "sigma-rt.com"  # 发件箱的后缀
    me = "NeoWu" + "<" + mail_user + "@" + mail_postfix + ">"  # 这里的hello可以任意设置，收到信后，将按照设置显示
    content = 'Plz get the attachment!'#邮件正文
    msg = MIMEMultipart()
    body = MIMEText(content, _subtype='html', _charset='gb2312')  # 创建一个实例，这里设置为html格式邮件
    msg.attach(body)
    msg['Subject'] = "Subject Test"  # 设置主题
    msg['From'] = me  
    msg['To'] = ";".join(mailto_list)  
    
    part = MIMEBase('application', 'octet-stream')
    # 读入文件内容并格式化，此处文件为当前目录下，也可指定目录 例如：open(r'/tmp/123.txt','rb')
    part.set_payload(open('[SRT-TC]User_Data_Count.xls','rb').read())
    Encoders.encode_base64(part)
    ## 设置附件头
    part.add_header('Content-Disposition', 'attachment; filename="[SRT-TC]User_Data_Count.xls"')
    msg.attach(part)
    
    try:  
        s = smtplib.SMTP()  
        s.connect(mail_host)  # 连接smtp服务器
        s.login(mail_user, mail_pass)  # 登陆服务器
        s.sendmail(me, mailto_list, msg.as_string())  # 发送邮件
        s.close()  
        print 'send mail sucess'
        return True  
    except Exception, e:  
        print str(e)  
        return False  
 
'''
获取sftp的文件
'''    
def sftp_get(file):
    CONST_HOST = "10.11.24.21"
    CONST_USERNAME = "root"
    CONST_PWD = "SigmaR&DUpdateServer"
    CONST_PORT = 22
    CONST_BUFFER_SIZE = 8192
    try:
        t = paramiko.Transport((CONST_HOST,CONST_PORT))
        t.connect(username=CONST_USERNAME, password=CONST_PWD)
        sftp = paramiko.SFTPClient.from_transport(t)
        des = os.getcwd()+ '\\history_of_tc.json'
        sftp.get(file,des)
        t.close()
        print 'download %s to %s ok' % (file, des)
        return True
    except Exception , e:
        raise e

'''
FTP文件操作
'''
def connect():
    CONST_HOST = "tc.sigma-rt.com.cn"
    CONST_USERNAME = "sigma_log"
    CONST_PWD = "sigma-rt"
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
    CONST_BUFFER_SIZE = 8192
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
    
'''
about time
'''
def my_time():
    now = time.strftime("%a %b %d %H:%M:%S %Y", time.localtime()) 
    now = time.mktime(time.strptime(now, "%a %b %d %H:%M:%S %Y"))
    yestoday = time.strftime("%Y-%m-%d", time.gmtime(now - 57600))
    yes_yestoday = time.strftime("%Y-%m-%d", time.gmtime(now - 57600 - 86400))
    
'''
正则表达式
'''
def lambda_eg(s):
    latest_version = re.compile(r'GET /packages/srt-tc/update/\d+/Total_Control_(?:\d+.\d+.\d+|\d+.\d+.\d+.\d+)_Install.(?:exe|exe\?crazycache=1) HTTP/\d.\d" 20(?:0|6) 100284413')               
    all_version = re.compile(r'GET /packages/srt-tc/update/\d+/Total_Control_(?:\d+.\d+.\d+|\d+.\d+.\d+.\d+)_Install.(?:exe|exe\?crazycache=1) HTTP/\d.\d" 20(?:0|6) (?:100284413|46899363|16324862|16242981|16268138|16229255|13615186|13607367|13456618|24664723|24285154|24270312|23482193|25240269)')                      
    m = latest_version.search(s)
    n = all_version.search(s)
    print m, n
    
'''
json 文件的读写
'''
def rwJsonFile():
    #读
    file = 'history_of_tc.json'
    fp = open(file)
    data = fp.read()
    fp.close()
    data = json.loads(data)
    #写
    file = 'history_of_tc.json'
    fp = open(file, 'w+')
    fp.write(json.dumps({}))
    fp.close()
    
'''
执行 cmd命令
'''
def killAllDriver():
    cmd = 'taskkill /F /IM chromedriver.exe'
    os.system(cmd)
    
'''
关于platform
'''
def TestPlatform():
    print ("----------Operation System--------------------------")
    #Windows will be : (32bit, WindowsPE)
    #Linux will be : (32bit, ELF)
    print(platform.architecture())

    #Windows will be : Windows-XP-5.1.2600-SP3 or Windows-post2008Server-6.1.7600
    #Linux will be : Linux-2.6.18-128.el5-i686-with-redhat-5.3-Final
    print(platform.platform())

    #Windows will be : Windows
    #Linux will be : Linux
    print(platform.system())

    print ("--------------Python Version-------------------------")
    #Windows and Linux will be : 3.1.1 or 3.1.3
    print(platform.python_version())

def UsePlatform():
    sysstr = platform.system()
    if(sysstr =="Windows"):
        print ("Call Windows tasks")
    elif(sysstr == "Linux"):
        print ("Call Linux tasks")
    else:
        print ("Other System tasks")
        
def isWindowsSystem():
    return 'Windows' in platform.system()

def isLinuxSystem():
    return 'Linux' in platform.system()

'''
对于turtle类的一些封装方法，包括画正多边形，正多角形和五星红旗。
'''
def draw_polygon(aTurtle, size=50, n=3):
    ''' 绘制正多边形

    args:
        aTurtle: turtle对象实例
        size: int类型，正多边形的边长
        n: int类型，是几边形        
    '''
    for i in xrange(n):
        aTurtle.forward(size)
        aTurtle.left(360.0/n)

def draw_n_angle(aTurtle, size=50, num=5, color=None):
    ''' 绘制正n角形，默认为黄色

    args:
        aTurtle: turtle对象实例
        size: int类型，正多角形的边长
        n: int类型，是几角形    
        color: str， 图形颜色，默认不填色
    '''
    if color:
        aTurtle.begin_fill()
        aTurtle.fillcolor(color)
    for i in xrange(num):
        aTurtle.forward(size)
        aTurtle.left(360.0/num)
        aTurtle.forward(size)
        aTurtle.right(2*360.0/num)
    if color:
        aTurtle.end_fill()

def draw_5_angle(aTurtle=None, start_pos=(0,0), end_pos=(0,10), radius=100, color=None):
    ''' 根据起始位置、结束位置和外接圆半径画五角星

    args:
        aTurtle: turtle对象实例
        start_pos: int的二元tuple，要画的五角星的外接圆圆心
        end_pos: int的二元tuple，圆心指向的位置坐标点
        radius: 五角星外接圆半径
        color: str， 图形颜色，默认不填色    
    '''
    aTurtle = aTurtle or turtle.Turtle()
    size = radius * math.sin(math.pi/5)/math.sin(math.pi*2/5)
    aTurtle.left(math.degrees(math.atan2(end_pos[1]-start_pos[1], end_pos[0]-start_pos[0])))
    aTurtle.penup()
    aTurtle.goto(start_pos)
    aTurtle.fd(radius)
    aTurtle.pendown()
    aTurtle.right(math.degrees(math.pi*9/10))
    draw_n_angle(aTurtle, size, 5, color)

def draw_5_star_flag(times=20.0):
    ''' 绘制五星红旗

    args:
        times: 五星红旗的规格为30*20， times为倍数，默认大小为10倍， 即300*200
    '''
    width, height = 30*times, 20*times
    # 初始化屏幕和海龟
    window = turtle.Screen()
    aTurtle = turtle.Turtle()
    aTurtle.hideturtle()
    aTurtle.speed(10)
    # 画红旗
    aTurtle.penup()
    aTurtle.goto(-width/2, height/2)
    aTurtle.pendown()
    aTurtle.begin_fill()
    aTurtle.fillcolor('red')
    aTurtle.fd(width)
    aTurtle.right(90)
    aTurtle.fd(height)
    aTurtle.right(90)
    aTurtle.fd(width)
    aTurtle.right(90)
    aTurtle.fd(height)
    aTurtle.right(90)    
    aTurtle.end_fill()
    # 画大星星
    draw_5_angle(aTurtle, start_pos=(-10*times, 5*times), end_pos=(-10*times, 8*times), radius=3*times, color='yellow')  
    # 画四个小星星
    stars_start_pos = [(-5, 8), (-3, 6), (-3, 3), (-5, 1)]
    for pos in stars_start_pos:
        draw_5_angle(aTurtle, start_pos=(pos[0]*times, pos[1]*times), end_pos=(-10*times, 5*times), radius=1*times, color='yellow')  
    # 点击关闭窗口
    window.exitonclick()
    
'''
递归删除    
'''
def removeDir(dirPath):
    if not os.path.isdir(dirPath):
        return
    files = os.listdir(dirPath)
    try:
        for file in files:
            filePath = os.path.join(dirPath, file)
            if os.path.isfile(filePath):
                os.remove(filePath)
            elif os.path.isdir(filePath):
                removeDir(filePath)
        os.rmdir(dirPath)
    except Exception, e:
        print e