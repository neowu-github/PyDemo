#coding=utf-8
'''
Created on 2014-10-20

@author: NeoWu
'''
from distutils.core import setup 
from glob import glob  
import py2exe 
import os, sys
import shutil

if len(sys.argv) == 1:
    sys.argv.append("py2exe")
    
includes = ["encodings", "encodings.*"]  
options = {"py2exe":  
             {   "compressed": 1,  
                 "optimize": 2,  
                 "includes": includes,  
                 "dist_dir": "bin", 
                 "bundle_files": 1  
             }  
           }  
setup(     
     version = "1.0",  
     description = u'Total Control 用户使用统计',  
     name = "TC User&Dev Data Count",  
     options = options,  
     zipfile = None,  
     console=[{"script": "GetUserAndDevCount.py"}],    
     ) 
os.remove("bin//w9xpopen.exe")     
shutil.rmtree("build")