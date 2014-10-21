#encoding=utf-8
'''
Created on 2014-10-14

@author: Neo
'''
import Image
import ImageEnhance
import ImageFilter
import sys
import os
from pytesser import *
from XmlParseFunc import XmlParseFunc

#由于都是数字
#对于识别成字母的 采用该表进行修正
rep={'O':'0',
    'I':'1',
    'L':'1',
    'E':'8',
    'P':'8',
    'S':'8',
    'R':'4'
    };
xmlParse = XmlParseFunc()

def imageHandle(name):
    #打开图片
    im = Image.open(name)
    im = im.convert("RGBA")
    
    pixdata = im.load()
    
    #二值化
    
    for y in xrange(im.size[1]):
        for x in xrange(im.size[0]):
            if pixdata[x,y][0] < 90 :#or y < 5 or y > 16 or x < 7 or x > 42:
                pixdata[x, y] = (0, 0, 0, 255)
    
    for y in xrange(im.size[1]):
        for x in xrange(im.size[0]):
            if pixdata[x,y][1] < 136 :#or y < 5 or y > 16 or x < 7 or x > 42:
                pixdata[x, y] = (0, 0, 0, 255)
    
    for y in xrange(im.size[1]):
        for x in xrange(im.size[0]):
            if pixdata[x,y][2] > 0 :#or y < 5 or y > 16 or x < 7 or x > 42:
                pixdata[x, y] = (255, 255, 255, 255)
    
    im = im.convert("L")            
    im.save("temp.png",'png')
    #识别
    text = image_to_string(im)
    #识别对吗
    text = text.strip()
    text = text.upper();
    for r in rep:
        text = text.replace(r,rep[r])
        text = text.replace(' ','')
    text = text.replace('ﬂ','0')
    print text
#     os.remove("temp.png")
    
def test():
    file = 'temp.bmp'
    url = 'http://ap.189store.com/RegisterInfo/getImage'
    data = xmlParse.OpenUrl(url)
    fp = open(file,'wb')
    fp.write(data)
    fp.close()
    imageHandle(file)
    
    
# for i in range(0,8):
#     file = str(i+1) + '.jpg'
#     imageHandle(file)
imageHandle('hiCaptcha.jpg')
print image_to_string(Image.open('1.jpg'))
# test()