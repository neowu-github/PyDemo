#!/usr/bin/python3
#coding=utf-8
###############################################################################
# @file TF Run Script Library
#
# The file is the source code of running script library in Python
# language.
#
# Copyright (c) 2005-2015  Sigma Resources & Technologies, Inc.
#
# PROPRIETARY RIGHTS of Sigma Resources & Technologies are
# involved in the subject matter of this material. All manufacturing,
# reproduction, use, and sales rights pertaining to this subject matter are
# governed by the license agreement.  The recipient of this software
# implicitly accepts the terms of the license.
#
# Creation Date: 2015.3.13
# Author: Zhengzhou Wu
#
# @author zhwu@sigma-rt.com
#
###############################################################################

from run_top import *
import sys
import time
from tf_logger import *
from tf_postgres import *

class run_script():
    def __init__(self, testbed_name, script_name, testcase_name, clean = None, rtop = None, toppath = None):
        self.testbed_name = self.check_testbed(testbed_name)
        self.script_name = self.check_script(script_name)
        if self.script_name:
            self.testcase_name = self.check_testcase(testcase_name)
        self.clean = self.check_clean(clean)
        self.rtop = rtop
        if self.script_name and self.testcase_name:
            self.top = self.ts.gettopname()
            self.addr = self.ts.getaddrname()
            if toppath:
                self.top = toppath + '/' + self.top
                if self.addr:
                    self.addr = toppath + '/' + self.addr
    
    def check_testbed(self, testbed_name):
        '''check testbed is exist'''
        db = db_operation(testbed_name)
        if testbed not in db.db_get_testbed_list():
            userlog("ERROR","[Running abortted]:The testbed(%s) does not exist." % testbed_name)
            testbed_name = None
        db.db_close()
        
        return testbed_name
    
    def check_script(self, script_name):
        '''check script file is exist'''   
        if not os.path.exists(script_name):
            userlog('ERROR', "[IOError]:No such script file [%s]" % script_name)
            script_name = None
        if script_name and script_name[-3:] != '.py':
            userlog('ERROR', "[FileError]:The script file [%s] is not python file" % script_name)
            script_name = None
            
        return script_name
        
    def check_testcase(self, case):
        '''check testcase is exist''' 
        if '/opt/sigma-rt/tf/scripts' in sys.path:
            for i in range(0, len(sys.path)):
                if sys.path[i] == '/opt/sigma-rt/tf/scripts':
                    del sys.path[i]
                    break
        try:
            library = os.path.basename(self.script_name)[:-3]
            path = os.path.dirname(self.script_name)
            sys.path.append(path)
            mod = __import__(library)
            if case not in eval('mod').__dict__.keys():
                userlog('ERROR', "The testcase [%s] does not defined in script [%s]." % (case, self.script_name))
                case = None
        except Exception as e:
            userlog('ERROR', library + "||" +case)
            userlog('ERROR', e.__repr__())
            case = None
            
        if case:
            self.ts = eval('mod.%s' % case)()
        
        return case
    
    def check_clean(self, clean):
        '''check clean param'''
        if clean == None:
            clean = False
        elif clean != "--clean":
            userlog('ERROR', "[Error]Do not support this param [%s]." % clean)
            clean = 'NA'
        else:
            clean = True
        
        return clean
    
    def proc_abort(self):
        userlog("INFO","=========================== Script Abortting ===========================")
        return ""
    
    def main(self):
        if not self.testbed_name or not self.script_name or self.clean == "NA":
            return self.proc_abort()
        if not self.testcase_name:
            return self.proc_abort()
        if self.clean == "NA":
            return self.proc_abort()
        _rt_ = run_top(self.testbed_name, self.top, self.addr)
        if _rt_.top_name and _rt_.addr_name != None:
            if self.rtop:
                fl = _rt_.main()
            else:
                fl = _rt_.main_called_by_script()
            if fl:
                res = []
                _ts_ = self.ts
                args = ""
               # print(_rt_.dev_conn_list)
               # print(_rt_.do_list)
               # for key in tf.__dict__:
                    #print(key," "+str(tf.__dict__[key]))
                if 'control' in _ts_.__dict__.keys():
                    for func_name in _ts_.control:
                        userlog("INFO","========  Subcase : %s Start ========" % func_name)
                        func = eval('_ts_.%s' %(func_name))
                        try:
                            ret = func(args)
                            if ret == "FAIL":
                                res.append(ret)
                                userlog("INFO","========  Subcase : %s Finish , result(%s)========" % (func_name, ret))
                                if "exception" in dir(_ts_):
                                    userlog("INFO","========  Step.End : Call script 'exception' in test case ========")
                                    _ts_.exception(args)
                                break 
                        except Exception as e:
                            import traceback
                            ret = 'exception'
                            res.append(ret)
                            userlog("INFO","Excption: %s " % traceback.format_exc())
                            userlog("INFO","========  Subcase : %s Finish , result(%s)========" % (func_name, ret))
                            if "exception" in dir(_ts_):
                                userlog("INFO","========  Step.End : Call script 'exception' in test case ========")
                                _ts_.exception(args)
                            #raise(e)
                            break
                        
                        userlog("INFO","========  Subcase : %s Finish , result(%s)========" % (func_name, ret))
                        res.append(ret)
                        time.sleep(1)
                if "FAIL" not in res and "exception" not in res and "success" in dir(_ts_):
                    userlog("INFO","========  Step.End : Call script 'success' in test case ========")
                    _ts_.success(args)
                #===============================================================
                # if "FAIL" in res and "exception" not in res and "exception" in dir(_ts_):
                #     userlog("INFO","========  Step.End : Call script 'exception' in test case ========")
                #     _ts_.exception(args)
                #===============================================================
                if 'final' in dir(_ts_):
                    userlog("INFO","========  Step.End : Call script 'final' in test case ========")
                    _ts_.final(args)
                            
                time.sleep(1)
                if self.clean:
                    userlog("INFO","========  Step.End : Free Resource ========")
                    _rt_.free_resource()
                else:
                    userlog("INFO","========  Step.End : Keep Topology ========")
                    
                _rt_.dboperation.db_close()
                userlog("INFO","============================= Script Finish =============================")
                return 1
            else:
                self.proc_abort()
        else:
            return self.proc_abort()

def parse_param(argv):
    support = ["--clean", "--run_top", "--top_path"]
    testbed = argv[1]
    script = argv[2]
    if not os.path.isabs(script):
        script = os.getcwd() + '/' + script
    case = argv[3]
    clean = None
    rtop = None
    top_path = None
    if len(argv) >= 5:
        for i in range(4, len(argv)):
            if argv[i] == support[2]:
                break
            if argv[i] not in support:
                userlog('ERROR', "[Error Message]:Donot support this param(%s), plz use(%s)" % (argv[i], support.__repr__()))
                return None
            
    if "--clean" in argv:
        clean = "--clean"
    if "--run_top" in argv:
        rtop = "--run_top" 
    if "--top_path" in argv:
        try:
            top_path = argv[argv.index("--top_path")+1]
        except:
            userlog('ERROR', "[Error Message]:Use param(--top_path), plz give the directory of top file.")
            return None

    if top_path:
        if not os.path.exists(top_path):
            userlog('ERROR', "[Error Message]:The given path does not exists(%s)" % top_path)
            return None
        if not os.path.isdir(top_path):
            userlog('ERROR', "[Error Message]:Use [-top] param, plz give the dir of the top file, not(%s)" % top_path)
            return None
            
    return [testbed, script, case, clean, rtop, top_path]
    
if __name__ == '__main__':
    """
    U can run the script/case on the given testbed with the command below:
    
    python tf_run_script.py <testbed_name> <script_name> <testcase_name> [--clean] [--run_top] [--top_path path]
    
    PS:
    U should give the script-file and the testbed name.
    e.g., python tf_run_script.py tb1 test.py step1_example --clean --run_top --top_path /home/test/top
    """
    
    """set tf_logger output to the command line"""
    set_log_flag(1)
    if len(sys.argv) >= 4:
        params = parse_param(sys.argv)
        if params:
            userlog("INFO","============================ Script Running ============================")
            testbed = params[0]
            script = params[1]
            case = params[2]
            clean = params[3]
            rtop = params[4]
            top_path = params[5]
            _rs_ = run_script(testbed, script, case, clean, rtop, top_path)
            _rs_.main()
        else:
            userlog('ERROR', "[Error Message]:CMD error!You should run like this: ")
            userlog('INFO', "[e.g.]python tf_run_script.py <testbed_name> <script_name> <testcase_name> [--clean] [--run_top] [--top_path path].")
    else:
        userlog('ERROR', "[Error Message]:CMD error!You should run like this: ")
        userlog('INFO', "[e.g.]python tf_run_script.py <testbed_name> <script_name> <testcase_name> [--clean] [--run_top] [--top_path path].")
        
