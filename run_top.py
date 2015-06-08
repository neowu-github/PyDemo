#!/usr/bin/python3
#coding=utf-8
###############################################################################
# @file TF Run Topology Library
#
# The file is the source code of topology auto-configuration library in Python
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
# Creation Date: 2015.2.4
# Author: Zhengzhou Wu
#
# @author zhwu@sigma-rt.com
#
###############################################################################

import os
import sys
import re
from xml.dom import minidom
from tf_logger import *
from tf_postgres import *
import builtins
import tf

class xml_parse():
    
    def __init__(self, top_name, addr_name):
        self.top_name = top_name
        self.addr_name = addr_name
        
    """
    Simple convert xml to dictionary.
    
    xml_to_dict("test.xml")
    
    return dictionary
    
    Todo:
    =====
     * convenience methods for getting elements and text.
    """
    def xml_to_dict(self, xmlFile):  
        xmlstr = self.get_xml_str(xmlFile)
        rs = re.subn(r'<!--.*?-->','',xmlstr,flags=re.DOTALL)
        ret = {}
        try:
            dom = minidom.parseString(xmlstr)        
        except Exception as e:
            return str(e)
        root = dom.firstChild 
        childs = root.childNodes 
        attrs = self.get_attrs(root.attributes.items())
        ret[root.nodeName] = {"attrs":attrs}
        for child in childs:  
            if not child.attributes: 
                continue
            if child.nodeType == child.TEXT_NODE:  
                pass  
            else:  
                s = 'child_' + child.nodeName
                if s in ret[root.nodeName].keys():
                    pass
                else:
                    ret[root.nodeName][s] = []
                children = {}
                attrs = self.get_attrs(child.attributes.items())
                if len(child.childNodes):
                    text = child.childNodes[0].data 
                else:
                    text = ""
                children[child.nodeName] = {"attrs":attrs,"text":text}
                ret[root.nodeName][s].append(children)
  
        return ret
    
    """
    get the attributes of the node, return a dictionary
    """  
    def get_attrs(self, attrs):
        ret = {}
        for i in range(0,len(attrs)):
            ret[attrs[i][0]] = attrs[i][1]
        
        return ret
    
    """
    get the string of xml according to the given xml file
    
    return the xml string
    """
    def get_xml_str(self, xmlFile):
        try:
            fp = open(xmlFile,'r')   
            xmlstr =  fp.read()
        except Exception as e:
            userlog('INFO', "[Error]:Open %s file failure, reason:[%s]" % (xmlFile, e))
            return None
        
        fp.close()
        return xmlstr
    
    """
    get the devices from the converted topology dictionary
    
    return an dictionary
    
    e.g. {
         "NODE": [{'type': 'NODE', 'model': 'windows', 'name': 'pc1'}], 
         "DUT": [{'type': 'DUT', 'model': 'ZyXelP334', 'name': 'dut'}],
         "SWITCH": [],
         "TS": [],
         "APC": []
         }
    """
    def get_top_devices(self):
        self.xmlDict = self.xml_to_dict(self.top_name)
        if not isinstance(self.xmlDict, dict):
            return self.xmlDict
        xmlDict = self.xmlDict
        ret = []
        res = {}
        type = []
        data = [] 
        if not isinstance(xmlDict, dict):
            return None
        if "Topology" in xmlDict.keys() and "child_Devices" in xmlDict["Topology"].keys():
            for i in range(0, len(xmlDict["Topology"]["child_Devices"])):
                ret.append(xmlDict["Topology"]["child_Devices"][i]["Devices"]["attrs"])
        for e in ret:
            if e["type"] not in type:
                type.append(e["type"])
                res[e["type"]] = []
            for t in type:
                if e["type"] == t:
                    res[t].append(e)
         
        for key in res:
            j = 0
            while len(res[key]) != len(data):
                for i in range(0, len(res[key])):
                    if j == 1:
                        if "extension" not in res[key][i].keys():
                            data.append(res[key][i])
                    else:
                        if "extension" in res[key][i].keys():
                            data.append(res[key][i])
                j += 1
            res[key] = data
            data = []
                
        return res
    
    """
    get the virtualints of devices from the converted topology dictionary
    
    return an dictionary
    
    e.g. {
         "devicename1": ['eth1', 'eth2'], 
         "devicename2": ['inf1', 'inf2']
         }
    """
    def get_top_virtualint(self):
        self.xmlDict = self.xml_to_dict(self.top_name)
        if not isinstance(self.xmlDict, dict):
            return self.xmlDict
        xmlDict = self.xmlDict
        ret = []
        data = [] 
        if not isinstance(xmlDict, dict):
            return None
        if "Topology" in xmlDict.keys() and "child_Devices" in xmlDict["Topology"].keys():
            if 'child_Virtualint' not in xmlDict["Topology"].keys():
                return {}
            for i in range(0, len(xmlDict["Topology"]["child_Virtualint"])):
                data.append(xmlDict["Topology"]["child_Virtualint"][i]["Virtualint"]["attrs"]['name'])
        for e in data:
            st = e.split(":")
            ret.append([st[0],st[1]])
                 
        return ret
    
    """
    get the connections from the converted topology dictionary
    
    return an ArrayList:
    
    e.g. [
            {'dest': 'pc2:eth1', 'source': 'pc1:eth1'},
            {'dest': 'pc2:eth2', 'source': 'pc1:eth2'}
        ]
    """
    def get_top_connection(self):
        xmlDict = self.xmlDict
        # print(xmlDict)
        ret = []
        res = []
        if not isinstance(xmlDict, dict):
            return None
        if "Topology" in xmlDict.keys() and "child_Connections" in xmlDict["Topology"].keys():
            for i in range(0, len(xmlDict["Topology"]["child_Connections"])):
                data = xmlDict["Topology"]["child_Connections"][i]["Connections"]["attrs"]
                if "dest" in data.keys():
                    ret.append([data["source"],data["dest"]])
                elif "trunk" in data.keys():
                    ret.append([data["source"],data["trunk"]])
       
        res = [[]]
        for i in range(0, len(ret)):
            if self.get_List_Length(res) == 0:
                res[0].append(ret[i])
            else:                
                flag = [True, 0]
                level = 0
                for k in res:
                    if ret[i] in k:
                        break
                    for j in k:
                        if ret[i][0] in j or ret[i][1] in j:
                            if not flag[0]:
                                res[level] = res[flag[1]] + k 
                                del res[flag[1]]
                                break
                            k.append(ret[i])
                            flag[0] = False
                            flag[1] = level
                            break
                    level += 1
                if flag[0]:
                    res.append([ret[i]])
        ret = []
        ret = self.get_data_list(res) 
        
        #=======================================================================
        # for e in ret:
        #     print(e)
        # for e in res:
        #     print(e)
        #=======================================================================
           
        return ret, res
    
    """
    get the length of the list which depth is 2 
    """
    def get_List_Length(self, ret):
        length = 0
        for e in ret:
            length += len(e)
        
        return length
    
    """
    get the data of the list which depth is 2
    """
    def get_data_list(self, ret):
        res = []
        for e in ret:
            for d in e:
                res.append(d)
                
        return res
    
    """
    get the address from the converted address dictionary
    
    return an ArrayList:
    
    e.g. [
            {'pc1': ['eth1=192.168.1.21/24']},
            {'pc2': ['eth1=192.168.1.3/24', 'gw=192.168.1.1']},
            {'pc2': ['ath0=11.1.1.3/24', ' essid="Wireless"', 
                    ' route=-dest 10.1.1.0/24 -gateway 11.1.1.1', 
                    ' route=-dest 192.168.1.0/24 -gateway 11.1.1.2'
                    ]
            }
        ]
    """
    def get_address(self):
        xmlDict = self.xml_to_dict(self.addr_name)
        if not isinstance(xmlDict, dict):
            return xmlDict
        ret = []
        res = {}
        if "Address" in xmlDict.keys() and "child_IPs" in xmlDict["Address"].keys():
            data = xmlDict["Address"]["child_IPs"][0]["IPs"]["text"]
            data = data.replace("\t", "").replace(", ", ",").split("\n")
            for e in data:
                e = e.strip()
                if e:
                    res['dev'] = e[0:e.index(":")]
                    res['int'] = e[e.index(":")+1:e.index("=")]
                    t = e[e.index("="):].split(",")
                    for m in t:
                        d = m.split("=")
                        if d[0] == "":
                            res['ip'] = d[1]
                        else:
                            res[d[0].strip()] = d[1]
                    ret.append(res)
                    t = ''
                res = {}
            
        return ret

class db_operation():
    
    def __init__(self, testbed_name, device_name = ''):
        self.db_handle = db_connect()
        self.testbed_name = testbed_name
        self.device_name = device_name
    
    def db_close(self):
        db_disconnect(self.db_handle)
        
    """
    db_get method
    
    get the current testbeds    
    """
    def db_get_testbed_list(self):
        sql = "SELECT name from stestbed"
        ret = db_select(self.db_handle,sql)
        rows = db_res_rows(ret)
        res = []
        for i in range(0, rows):
            res.append(db_cols_value(ret, i, 0))
            
        return res
    
    """
    db_get method
    
    get the devices list from the database by given self.testbed_name
    """    
    def db_get_dev_list(self):
        sql = "SELECT name,type,model,attr,stat,owner,active FROM sdevice_" + self.testbed_name
        ret = db_select(self.db_handle,sql)
        
        return self.get_detail(ret)
    
    """
    db_get method
    
    get the free vlan port in the testbed
    """
    def db_get_tb_vlan(self):
        sql = "SELECT vlanid FROM svlanid_%s WHERE stat='IDLE' ORDER BY vlanid" % self.testbed_name
        ret = db_select(self.db_handle,sql)
        rows = db_res_rows(ret)
        res = []
        for i in range(0, rows):
            res.append(db_cols_value(ret, i, 0))
            
        return res
    
    """
    get the detail result of the selected res
    """
    def get_detail(self, ret):
        rows = db_res_rows(ret)
        cols = db_res_cols(ret)
        res = []
        key = ['name', 'type', 'model', 'attr', 'stat', 'owner', 'active']        
        for i in range(0, rows):
            record = {}
            for j in range(0, cols):
                record[key[j]] = (db_cols_value(ret, i, j))
            res.append(record)
            
        return res
    
    """
    db_get method
    
    get the given type of device from the database 
    """ 
    def db_get_dev_by_params(self, params):
        if not isinstance(params, dict):
            return None
        keys = params.keys()
        if len(keys) == 1:
            sql = "SELECT name,type,model,attr,stat,owner,active FROM sdevice_" + self.testbed_name + \
                " WHERE %s = '%s'" % (list(keys)[0], params[list(keys)[0]])
        elif len(keys) == 2:
            sql = "SELECT name,type,model,attr,stat,owner,active FROM sdevice_" + self.testbed_name + \
                " WHERE %s = '%s' AND %s = '%s'" % (list(keys)[0], params[list(keys)[0]],
                                                    list(keys)[1], params[list(keys)[1]])
        elif len(keys) == 3:
            sql = "SELECT name,type,model,attr,stat,owner,active FROM sdevice_" + self.testbed_name + \
                " WHERE %s = '%s' AND %s = '%s' AND %s = '%s'" % \
                                                    (list(keys)[0], params[list(keys)[0]],
                                                    list(keys)[1], params[list(keys)[1]],
                                                    list(keys)[2], params[list(keys)[2]])

        ret = db_select(self.db_handle,sql)
        res = self.get_detail(ret)
        if not res:
            userlog("DEBUG", sql)
        
        return res
    
    """
    db_get method
    
    get the devices params from the database by given self.testbed_name, self.device_name, param_name
    """ 
    def db_get_dev_param(self, param_name, device_name=None):
        if not device_name:
            device_name = self.device_name
        if param_name == "type":
            sql = "SELECT type FROM sdevice_%s WHERE name='%s'" % (self.testbed_name, device_name)
    
        elif param_name == "model":
            sql = "SELECT model FROM sdevice_%s WHERE name='%s'" % (self.testbed_name, device_name)
    
        elif param_name == "attr":
            sql = "SELECT attr FROM sdevice_%s WHERE name='%s'" % (self.testbed_name, device_name)
        
        elif param_name == "stat":
            sql = "SELECT stat FROM sdevice_%s WHERE name='%s'" % (self.testbed_name, device_name)
    
        elif param_name == "owner":
            sql = "SELECT owner FROM sdevice_%s WHERE name='%s'" % (self.testbed_name, device_name)
    
        elif param_name == "active":
            sql = "SELECT active FROM sdevice_%s WHERE name='%s'" % (self.testbed_name, device_name)
    
        else:
            sql = "SELECT paramvalue FROM sdevpms_%s WHERE paramname='%s' AND devname='%s'" % (self.testbed_name, param_name, device_name )
    
        res_record = db_select(self.db_handle, sql)
        if 0 == db_res_rows(res_record):
            return ""
        
        value = db_cols_value(res_record, 0, 0)
    
        return value
    
    """
    db_get method
    
    get the devices classed from the database by given self.testbed_name and self.device_name
    """ 
    def db_get_dev_class(self, name = None):
        if name:
            device_name = name
        else:
            device_name = self.device_name
        sql = "SELECT classname FROM scontrollibrary WHERE EXISTS (SELECT type,model FROM\
         sdevice_%s WHERE name='%s' AND model=scontrollibrary.model)" % (self.testbed_name, device_name)
        res =db_select(self.db_handle, sql)
        return db_field_value(res, 0, "classname")
    
    """
    db_get method
    
    get the classes library from the database by given class_name
    """ 
    def db_get_class_library(self, class_name):
    
        sql = "SELECT library FROM scontrollibrary WHERE classname='%s'" % class_name
        res = db_select(self.db_handle, sql)
        return db_field_value(res, 0, "library")
    
    """
    db_get method
    
    get the switch name from the database by given self.testbed_name
    """ 
    def db_get_switch_name(self):
    
        sql = "SELECT name FROM sdevice_%s WHERE type='SWITCH' AND stat<>'BUSY' AND active=1" % self.testbed_name
        res_record = db_select(self.db_handle, sql)
        row_count = db_res_rows(res_record)
        if 0 == row_count:
            return ""
       
        switch_name = []
        row_count = db_res_rows(res_record)
        for i in range(0, row_count):    
            switch_name.append(db_cols_value(res_record, i, 0))
        
        return switch_name
    
    
    def db_get_dev_vlan(self, dname, dint):
        sql = "SELECT srcname, srcint FROM sconn_%s WHERE destname='%s' AND destint='%s'" % (self.testbed_name, dname, dint)
        res_record = db_select(self.db_handle, sql)
        row_count = db_res_rows(res_record)
        if row_count == 0:
            return ""
        if row_count == 1:
            return [db_cols_value(res_record, 0, 0), db_cols_value(res_record, 0, 1)]
        else:
            userlog("ERROR", "[db_get_dev_vlan](%s:%s) connected to more than 1 switches." % (dname, dint))
            return ""
        
    
    """
    db_get method
    
    get the switch conn from the database
    """ 
    def db_get_switch_conn(self, switch, source, dest, dic):
        if len(dest) == 2:
            s_phy_name = self.db_get_dev_intphyname(dic[source[0]], source[1])
            d_phy_name = self.db_get_dev_intphyname(dic[dest[0]], dest[1])
            if not s_phy_name:
                s_phy_name = source[1]
#                 userlog("ERROR", "[device_conf_conn]The device[%s] does not have port[%s]" % (source[0], source[1]))
#                 return ""
            if not d_phy_name:
                d_phy_name = dest[1]
#                 userlog("ERROR", "[device_conf_conn]The device[%s] does not have port[%s]" % (dest[0], dest[1]))
#                 return ""
            s_sql = "SELECT srcint FROM sconn_%s WHERE srcname='%s' AND destname='%s' AND destint='%s'" % (self.testbed_name, switch, dic[source[0]], source[1])
            d_sql = "SELECT srcint FROM sconn_%s WHERE srcname='%s' AND destname='%s' AND destint='%s'" % (self.testbed_name, switch, dic[dest[0]], dest[1])
            
            s_res_record = db_select(self.db_handle, s_sql)
            s_row_count = db_res_rows(s_res_record)
            if 0 == s_row_count:
                return ""
            
            d_res_record = db_select(self.db_handle, d_sql)
            d_row_count = db_res_rows(d_res_record)
            if 0 == d_row_count:
                return ""
            
            s_conn, d_conn = [], []
            s_row_count, d_row_count = db_res_rows(s_res_record), db_res_rows(d_res_record)
            if s_row_count == 1:    
                s_conn = [db_cols_value(s_res_record, 0, 0), source, dic[source[0]], s_phy_name]
            else:
                userlog('INFO', "[db_get_switch_conn]:The device in this testbed has 1 more connections")
                return ""
            if d_row_count == 1:    
                d_conn = [db_cols_value(d_res_record, 0, 0), dest, dic[dest[0]],d_phy_name]
            else:
                userlog('INFO', "[db_get_switch_conn]:The device in this testbed has 1 more connections")
                return ""
            
            if len(s_conn) == 0:
                return ""
            if len(d_conn) == 0:
                return ""  
             
            return {
                    "source" : s_conn,
                    "dest": d_conn
                    }
        else:
            s_phy_name = self.db_get_dev_intphyname(dic[source[0]], source[1])
            if not s_phy_name:
                s_phy_name = source[1]
#                 userlog("ERROR", "[device_conf_conn]The device[%s] does not have port[%s]" % (source[0], source[1]))
#                 return ""
            
            s_sql = "SELECT srcint FROM sconn_%s WHERE srcname='%s' AND destname='%s' AND destint='%s'" % (self.testbed_name, switch, dic[source[0]], source[1])
            
            #userlog('DEBUG', s_sql)
            s_res_record = db_select(self.db_handle, s_sql)
            s_row_count = db_res_rows(s_res_record)
            if 0 == s_row_count:
                return ""
            
            s_conn = []
            s_row_count = db_res_rows(s_res_record)
            if s_row_count == 1:    
                s_conn = [db_cols_value(s_res_record, 0, 0), source, dic[source[0]], s_phy_name]
            else:
                userlog('INFO', "[db_get_switch_conn]:The device in this testbed has 1 more connections")
                return ""
            
            if len(s_conn) == 0:
                return ""
             
             
            return {
                    "source" : s_conn,
                    "dest": {"trunk":dest[0]}
                    }
        
    """
    db_get method
    
    get the devices interface corresponding physical name from the database
    """     
    def db_get_dev_intphyname(self, dev_name, intshowname):
        sql = "SELECT intphyname FROM sdevints_%s WHERE devname='%s' AND intshowname='%s'" % (self.testbed_name, dev_name, intshowname)
        res_record = db_select(self.db_handle, sql)
        row_count = db_res_rows(res_record)
        physical_name = ""
        row_count = db_res_rows(res_record)
        if 0 == row_count:
            userlog('DEBUG', sql)
            return ""
        if row_count == 1:    
            physical_name = db_cols_value(res_record, 0, 0)
        else:
            userlog('INFO', "[db_get_dev_intphyname]:The device interface has 1 more physical names")
            return None
        
        return physical_name
      
    """
    db_get method
    
    get the devices configuration from the database by given self.testbed_name and self.device_name
    """ 
    def db_get_dev_config(self, device_name=None):
        protocol = ""
        if not device_name:
            device_name = self.device_name

        # Get device classname.
        classname = self.db_get_dev_class(device_name)
        if classname == "":
            userlog('INFO', "[db_get_dev_config]: Get class failed for device: %s" % device_name)
            return {}
        
    
        # Get device library.
        library = self.db_get_class_library(classname)
        if library == "" :
            userlog('INFO', "[db_get_dev_config]: Get library failed for device: %s" % device_name)
            return {}
        
        # Get device type.
        type = self.db_get_dev_param("type", device_name)
        if type == "" :
            userlog('INFO', "[db_get_dev_config]: Get type of device: %s failed" % device_name)
            return {}
        
        # Get device model.
        model = self.db_get_dev_param("model", device_name)
        if model=="" :
            userlog('INFO', "[db_get_dev_config]: Get model of device: %s failed" % device_name)
            return {}
    
        # Get device username.
        username = self.db_get_dev_param("user", device_name)
    
        # Get device password.
        password = self.db_get_dev_param("password", device_name)
    
        # Get device owner.
        owner = self.db_get_dev_param("owner", device_name)
        if owner=="" :
            userlog('INFO', "[db_get_dev_config]: Get owner of device: %s failed" % device_name)
            return {}
    
        # Get device stat.
        stat = self.db_get_dev_param("stat", device_name)
        if stat=="" :
            userlog('INFO', "[db_get_dev_config]: Get stat of device: %s failed" % device_name)
            return {}
    
        # Get device active.
        active = self.db_get_dev_param("active", device_name)
        if active=="" :
            userlog('INFO', "[db_get_dev_config]: Get active of device: %s failed" % device_name)
            return {}
        
        if type == "NODE" :
    
            # Get device ip address.
            ip = self.db_get_dev_param("ip", device_name)
            if ip=="" :
                userlog('INFO', "[db_get_dev_config]: Get ip address of device: %s failed" % device_name)
                return {}
        
            # Get device port.
            port = self.db_get_dev_param("port", device_name)
    
            return [self.device_name, library, classname, type, model, ip, port, username, password, protocol, "", "", "", owner, stat, active]
    
        elif type == "TS" :
        
            # Get device ip address.
            ip = self.db_get_dev_param("ip", device_name)
            if ip=="" :
                userlog('INFO', "[db_get_dev_config]: Get ip address of device: %s failed" % device_name)
                return {}
        
            # Get device port.
            port = 23
            protocol = "TELNET"
    
            return [device_name, library, classname, type, model, ip, port, username, password, protocol, "", "", "", owner, stat, active]
    
        elif type=="SWITCH" or type=="DUT":
    
            # Get device ts name.
            tsname = self.db_get_dev_param("ts", device_name)
            if tsname=="" :
                # Get device ip address.
                tsip = self.db_get_dev_param("ip", device_name)
                if tsip=="" :
                    userlog('INFO', "[db_get_dev_config]: Get ip address of device: %s failed" % device_name)
                    return {}
                
            else:
                # Get device ts ip address.
                tsip = self.db_get_dev_param("ip", tsname)
                if tsip=="" :
                    userlog('INFO', "[db_get_dev_config]: Get terminal server address for device: %s failed" % device_name)
                    return {}
    
            # Get device ts port
            tsport = self.db_get_dev_param("port", device_name)
            if tsport=="" :
                userlog('INFO', "[db_get_dev_config]: Get terminal server port for device: %s failed" % device_name)
                return {}
    
            # Get device mgt
            mgt = self.db_get_dev_param("mgt", device_name)
    
            # Get device mgtaddr
            mgtaddr = self.db_get_dev_param("mgtaddr", device_name)
    
            return [device_name, library, classname, type, model, tsip, tsport, username, password, protocol, tsname, mgt, mgtaddr, owner, stat, active]
    
        else:
            userlog('INFO', "[db_get_dev_config]: Unsupported type: %s of %s" % (type, device_name))
            return {}

class tf_via():
    def __init__(self):
        self.job = {}
        self.case = {}
        pass
    
    def create_dev_via(self, dev, cl, ac, dcl, tb, db, vint):
        exec("self.%s = {}" % dev['name'])
        exec("self.%s['type'] = '%s'" % (dev['name'], dev['type']))
        exec("self.%s['model'] = '%s'" % (dev['name'], dev['model']))
        if 'extension' in dev.keys():
            exec("self.%s['extension'] = '%s'" % (dev['name'], dev['extension']))
        else:
            exec("self.%s['extension'] = ''" % dev['name'])
        exec("self.%s['physical'] = '%s'" % (dev['name'], cl[dev['name']]))
        exec("self.%s['testbed'] = '%s'" % (dev['name'], tb))
        from random import Random 
        num =  Random()
        exec("self.job['id'] = str(Random.randint(num,0, 20))")
        exec("self.case['id'] = str(Random.randint(num,0, 20))")
        for e in dcl:
            for t in e:
                n = t.split(":")
                if len(n)==2:
                    if n[0] == dev["name"]:
                        exec("self.%s['%s,ip'] = '%s'" % (dev['name'], n[1], ''))
                        if not db.db_get_dev_intphyname(cl[dev['name']], n[1]):
                            exec("self.%s['%s,physical'] = '%s'" % (dev['name'], n[1], n[1]))
                        else:
                            exec("self.%s['%s,physical'] = '%s'" % (dev['name'], n[1], db.db_get_dev_intphyname(cl[dev['name']], n[1])))
                        ret = db.db_get_dev_vlan(cl[dev['name']], n[1])
                        if ret:
                            exec("self.%s['%s,sw'] = '%s'" % (dev['name'], n[1], ret[0]))
                            exec("self.%s['%s,id'] = '%s'" % (dev['name'], n[1], ret[1]))
        for key in ac:
            if key['dev'] == dev['name']:
                exec("self.%s['%s,ip'] = '%s'" % (dev['name'], key['int'], key['ip']))
                if 'gateway' in key.keys():
                    exec("self.%s['%s,gateway'] = '%s'" % (dev['name'], key['int'], key['gateway']))
                if 'route' in key.keys():
                    exec("self.%s['%s,route'] = '%s'" % (dev['name'], key['int'], key['route']))
                if not db.db_get_dev_intphyname(cl[dev['name']], key['int']):
                    exec("self.%s['%s,physical'] = '%s'" % (dev['name'], key['int'], key['int']))
                else:
                    exec("self.%s['%s,physical'] = '%s'" % (dev['name'], key['int'], db.db_get_dev_intphyname(cl[dev['name']], key['int'])))
                ret = db.db_get_dev_vlan(cl[dev['name']], key['int'])
                if ret:
                    exec("self.%s['%s,sw'] = '%s'" % (dev['name'], key['int'], ret[0]))
                    exec("self.%s['%s,id'] = '%s'" % (dev['name'], key['int'], ret[1]))
#                 break
#             else:
#                 exec("self.%s['%s,ip'] = ''" % (dev['name'], key['int']))
#                 if 'gateway' in key.keys():
#                     exec("self.%s['%s,gateway'] = ''" % (dev['name'], key['int']))
#                 if 'route' in key.keys():
#                     exec("self.%s['%s,route'] = ''" % (dev['name'], key['int']))
#                 exec("self.%s['%s,physical'] = ''" % (dev['name'], key['int']))
#                 exec("self.%s['%s,id'] = ''" % (dev['name'], key['int']))
#                 exec("self.%s['%s,sw'] = ''" % (dev['name'], key['int']))
        for vi in vint:
            if dev['name'] == vi[0]:
                if not db.db_get_dev_intphyname(cl[dev['name']], vi[1]):
                    exec("self.%s['%s,physical'] = '%s'" % (dev['name'], vi[1], vi[1]))
                else:
                    exec("self.%s['%s,physical'] = '%s'" % (dev['name'], vi[1], db.db_get_dev_intphyname(cl[dev['name']], vi[1])))
                
        
        exec("tf.__dict__['%s'] = self.%s" % (dev['name'], dev['name']))
        exec("tf.__dict__['job'] = self.job")
        exec("tf.__dict__['case'] = self.case")
            
    def set_tf_via(self, top_device_list, create_list, addr_conf, dev_conn_list, testbed, db, vint):
        for key in top_device_list:
            for e in top_device_list[key]:
                self.create_dev_via(e, create_list, addr_conf, dev_conn_list, testbed, db, vint)
            
                
class run_top():
    
    def __init__(self, testbed_name, top_name, addr_name): 
        self.top_name = self.check_top(top_name)
        self.addr_name = self.check_addr(addr_name)
        self.testbed_name = testbed_name
        self.dboperation = db_operation(self.testbed_name) 
        if self.testbed_name not in self.dboperation.db_get_testbed_list():
            self.testbed_name = None
        if self.top_name and self.testbed_name:
            self.xmlparse = xml_parse(self.top_name , self.addr_name)
            self.top_device_list = self.xmlparse.get_top_devices()
            if not isinstance(self.top_device_list, str):
                self.dev_conn_list, self.do_list = self.xmlparse.get_top_connection()
                self.vlanid = self.dboperation.db_get_tb_vlan()
                self.create_list = self.resource_compare()
                self.todo = {}
                if len(self.do_list) > len(self.vlanid):
                    userlog('ERROR', "[device_conf_conn]:Resered vlan (%s) <-> Need vlan (%s)." % (len(self.vlanid), len(self.do_list)))   
                    return "1008"
                for i in range(0, len(self.do_list)):
                    self.todo['id'+str(i)] = self.vlanid[i]
                    self.todo['list'+str(i)] = self.do_list[i]
                    self.todo['conn'+str(i)] = []
                    self.todo['switch'+str(i)] = ""
                
#                 userlog("INFO", "self.do_list:" + self.do_list.__repr__())
#                 userlog("INFO", "self.to_do:" +  self.todo.__repr__())    
                self.virtualint = self.xmlparse.get_top_virtualint()
            else:
                self.dev_conn_list, self.do_list = '', ''
                self.create_list = ''
            self.obj_ret = {}
            self.obj_res = {}
            self.testbed_device_list = self.dboperation.db_get_dev_list() 
#             userlog("INFO", "self.top_device_list:" + self.top_device_list.__repr__())
#             userlog("INFO", "self.create_list:" + self.create_list.__repr__())
#             userlog("INFO", "self.dev_conn_list:" + self.dev_conn_list.__repr__())
            if self.addr_name:
                self.addr_conf = self.xmlparse.get_address()
            else:
                self.addr_conf = ""
#             userlog("INFO", "self.addr_conf:" + self.addr_conf.__repr__())
        self.error_node = {"1001" : "[Running abortted]:The device in testbed is not available.",
                           "1002" : "[Running abortted]:The device in testbed can not be connected.",
                           "1003" : "[Running abortted]:The status of device in testbed is busy.",
                           "1004" : "[Running abortted]:There is no switch in testbed.",
                           "1005" : "[Running abortted]:The devices need to connect are not connect to the same switch.",
                           "1006" : "[Running abortted]:There are not enough devices on testbed for the top.",
                           "1007" : "[Running abortted]:Run Top has occurred an error, abortted!",
                           "1008" : "[Running abortted]:There is no reserved vlan in this testbed.",
                           "1009" : "[Running abortted]:The defined device in top or addr are not match.",
                           "1010" : "[Running abortted]:The testbed(%s) does not exist." % testbed_name
                           }  
        
        
        
        
    """
    check the devices that defined in top and addr
    """
    def check_top_addr(self):
        top_device_name, addr_device_name, conn_device_name = [], [], []
        for key in self.top_device_list:
            for i in range(0, len(self.top_device_list[key])):
                top_device_name.append(self.top_device_list[key][i]['name'])
        if self.addr_conf:
            for e in self.addr_conf:
                addr_device_name.append(e['dev'].strip())
            
            for m in addr_device_name:      
                if m not in top_device_name:
                    userlog("ERROR","[check_top_addr]Device [%s] defined in [%s], but not defined in [%s]" % (m, self.addr_name, self.top_name))
                    return "1009"
            
        for t in self.dev_conn_list:
            conn_device_name.append(t[0].split(":")[0])
            if len(t[1].split(":")) == 2:
                conn_device_name.append(t[1].split(":")[0])
            
        for n in conn_device_name:
            if n not in top_device_name:
                userlog("ERROR","[check_top_addr]Device [%s] defined in [%s] connections, but not defined in [%s] devices" % (n, self.top_name, self.top_name))
                return "1009"
        
        return None
    
    """
    configure the topology according to the top file
    """
    def configure_top(self):
        for key in self.create_list:
            device_name = self.create_list[key]
            userlog('INFO', '[create_dev_object]:Construct object [' + key + ']')
            userlog('INFO', '[create_dev_object]:Construct object %s which physical name is %s on testbed %s' % (key, device_name, self.testbed_name))
            dboperation = db_operation(self.testbed_name, device_name)
            self.obj_ret[key] = self.create_dev_object(dboperation, device_name, key)
            if self.obj_ret[key] in self.error_node.keys():
                return self.obj_ret[key]
            dboperation.db_close()
        
        #=======================================================================
        # userlog('INFO', "[create obj result]:")
        # for key in self.obj_ret:
        #     userlog('INFO', "[%s] -> [%s]" % (key, self.obj_ret[key]))
        #=======================================================================
            
        for key in self.create_list:
            device_name = self.create_list[key]
            dboperation = db_operation(self.testbed_name, device_name)
            self.obj_res[key] = self.check_dev_available(dboperation, device_name, self.obj_ret[key])
            if self.obj_res[key] in self.error_node.keys():
                return self.obj_res[key]
            dboperation.db_close()
        
        userlog('INFO', "[create obj current result]:")
        for key in self.obj_res:
            userlog('INFO', "[%s] -> [%s]" % (key, self.obj_res[key]))
        
        return None
        
    """
    check the resource by testbed
    config the topology
    @top_device_list
    @testbed_device_list
    """
    def main(self, clean=False):
        if self.testbed_name not in self.dboperation.db_get_testbed_list():
            userlog("ERROR",self.error_node["1010"])
            return {}
        if isinstance(self.top_device_list, str):
            userlog("ERROR","[Parsing xml][%s]%s" % (self.top_name,str(self.top_device_list)))
            return {}
        if self.addr_name and isinstance(self.addr_conf, str):
            userlog("ERROR","[Parsing xml][%s]%s" % (self.addr_name,str(self.addr_conf)))
            return {}
        
        check = self.check_top_addr()
        if check in self.error_node.keys():
            userlog("ERROR", self.error_node[check])
            return {}
        userlog("INFO","========  Step.Resource : Resource Mapping ========")    
        if isinstance(self.create_list, str) and self.create_list in self.error_node.keys():
            userlog("ERROR", self.error_node[self.create_list])
            return {}
        if self.create_list:
            tv = tf_via()
            tv.set_tf_via(self.top_device_list, self.create_list, self.addr_conf, self.dev_conn_list, self.testbed_name, self.dboperation, self.virtualint)
            #for key in self.create_list.keys():
                #userlog("INFO", key + ":" + tf.__dict__[key].__repr__())
            res = self.configure_top() 
            if res and res in self.error_node.keys():
                userlog("ERROR", self.error_node[res])
                return {}
            userlog("INFO","========  Step.Topology : Set Topology ========")
            ret = self.device_conf_conn()          
            if ret and ret in self.error_node.keys():
                userlog("ERROR", self.error_node[ret])
                return {}    
        
        conf = self.configure_dev_addr()
        if conf in self.error_node.keys():
            userlog("ERROR", self.error_node[conf])
            return {}
        
        '''puts all objects in '__builtin__' so the objects can be access'''
        for key in self.obj_res:
            builtins.__dict__[key] = self.obj_res[key]
        
        if clean:
            self.free_resource()
        
        return True
 
    """
    this method will be called by run_script 
    """
    def main_called_by_script(self, clean=False):
        if self.testbed_name not in self.dboperation.db_get_testbed_list():
            userlog("ERROR",self.error_node["1010"])
            return {}
        if isinstance(self.top_device_list, str):
            userlog("ERROR","[Parsing xml][%s]%s" % (self.top_name,str(self.top_device_list)))
            return {}
        if self.addr_name and isinstance(self.addr_conf, str):
            userlog("ERROR","[Parsing xml][%s]%s" % (self.addr_name,str(self.addr_conf)))
            return {}
        
        check = self.check_top_addr()
        if check in self.error_node.keys():
            userlog("ERROR", self.error_node[check])
            return {}
        userlog("INFO","========  Step.Resource : Resource Mapping ========")    
        if isinstance(self.create_list, str) and self.create_list in self.error_node.keys():
            userlog("ERROR", self.error_node[self.create_list])
            return {}
        if self.create_list:
            tv = tf_via()
            tv.set_tf_via(self.top_device_list, self.create_list, self.addr_conf, self.dev_conn_list, self.testbed_name, self.dboperation, self.virtualint)
            #for key in self.create_list.keys():
                #userlog("INFO", key + ":" + tf.__dict__[key].__repr__())
            res = self.configure_top() 
            if res and res in self.error_node.keys():
                userlog("ERROR", self.error_node[res])
                return {}
            #===================================================================
            # userlog("INFO","========  Step.Topology : Set Topology ========")
            # ret = self.device_conf_conn()          
            # if ret and ret in self.error_node.keys():
            #     userlog("ERROR", self.error_node[ret])
            #     return {}    
            #===================================================================
        
        #=======================================================================
        # conf = self.configure_dev_addr()
        # if conf in self.error_node.keys():
        #     userlog("ERROR", self.error_node[conf])
        #     return {}
        #=======================================================================
        
        '''puts all objects in '__builtin__' so the objects can be access'''
        for key in self.obj_res:
            builtins.__dict__[key] = self.obj_res[key]
        
        if clean:
            self.free_resource()
        
        return True
 
    def free_resource(self):
        for i in range(0, len(self.addr_conf)):
            userlog("INFO", "[free_resource]Free address on '%s : %s'" % (self.addr_conf[i]['dev'], self.addr_conf[i]['int']))
            try:
                self.obj_res[self.addr_conf[i]['dev']].clear_ip(self.addr_conf[i]['int'])
                if 'route' in self.addr_conf[i].keys():
                    self.obj_res[self.addr_conf[i]['dev']].clear_route(self.addr_conf[i]['int'])
            except:
                continue
        id = 0
        while True:
            key = "id" + str(id)
            if key not in self.todo.keys():
                break
            elif key in self.todo.keys():
                data = self.todo['conn'+str(id)]
                for i in range(0, len(data)):
                    try:
                        if isinstance(data[i]['dest'], dict):
                            userlog("INFO", "[free_resource]Free access trunk '%s' for '%s'" % (data[i]['dest']['trunk'],data[i]['source'][1].__repr__()))
                            self.obj_res[self.todo['switch'+str(id)]].clean_trunk(data[i]['source'][0], data[i]['dest']['trunk'])
                        else:
                            userlog("INFO", "[free_resource]Free access vlan '%s' for '%s'" % (self.todo['id'+str(id)],data[i]['source'][1].__repr__()))
                            self.obj_res[self.todo['switch'+str(id)]].clean_vlan(data[i]['source'][0], self.todo['id'+str(id)])
                            userlog("INFO", "[free_resource]Free access vlan '%s' for '%s'" % (self.todo['id'+str(id)],data[i]['dest'][1].__repr__()))
                            self.obj_res[self.todo['switch'+str(id)]].clean_vlan(data[i]['dest'][0], self.todo['id'+str(id)])
                    except:
                        continue
                id += 1
                #self.obj_res[self.todo['switch'+str(id)]].disconnect()
        from collections import OrderedDict
        self.obj_res = OrderedDict(sorted(self.obj_res.items(), key=lambda t: t[0]))    
        keys = []
        for key in self.obj_res:
            keys.append(key)
        for key in keys:
            userlog("INFO","[free_resource]Free object '%s'" % key)
            del self.obj_res[key]
        
    """
    configure dev addr
    """    
    def configure_dev_addr(self):
        userlog("INFO","========  Step.Topology : Set Address ========")
        if len(self.addr_conf) == 0:
            userlog("INFO","[configure_dev_addr]There is no dev address need to configure.")
            return True
        else:
            for i in range(0, len(self.addr_conf)):
                result = self.set_addr(self.addr_conf[i])
                if result in self.error_node.keys():
                    return result
        return True
    
    def set_addr(self, conf):
        if 'dev' in conf.keys() and 'int' in conf.keys() and 'ip' in conf.keys():
            userlog("INFO","[configure_dev_addr]Set device(%s : %s -> ip = %s)" % (conf['dev'],conf['int'],conf['ip']))
            result = self.obj_res[conf['dev']].set_ip(conf['int'], conf['ip'])
#             userlog("INFO", "ddd:" + str(self.obj_res[conf['dev']].get_ip(conf['int'])))
            if not result:
                userlog("ERROR","[configure_dev_addr]Set ip failure.")
                return "1007"
            if 'gw' in conf.keys():
                userlog("INFO","[configure_dev_addr]Set device(%s : %s -> gw = %s)" % (conf['dev'],conf['int'],conf['gw']))
                result = self.obj_res[conf['dev']].set_gw(conf['int'], conf['gw'])
#                 userlog("INFO", "ddd:" + str(self.obj_res[conf['dev']].get_gw(conf['int'])))
                if not result:
                    userlog("ERROR","[configure_dev_addr]Set ip failure.")
                    return "1007"
            if 'route' in conf.keys():
                userlog("INFO","[configure_dev_addr]Set device(%s : %s -> route = %s)" % (conf['dev'],conf['int'],conf['route']))
#                 self.obj_ret[conf['dev']].clear_route(conf['int'])
                result = self.obj_res[conf['dev']].set_route(conf['int'], conf['route'])
#                 userlog("INFO", "ddd:" + str(self.obj_res[conf['dev']].get_route(conf['int'],"-dest")))
#                 userlog("INFO", "ddd:" + str(self.obj_res[conf['dev']].get_route(conf['int'],"-gateway")))
                if not result:
                    userlog("ERROR","[configure_dev_addr]Set ip failure.")
                    return "1007"
                
        else:
            userlog("ERROR","[configure_dev_addr]Can not configure the address of device(%s),please check the addr file." % conf['dev'])
            return '1007'
        
        return True
    
    """
    compare method
    testbed_device_list as tb_dl
    top_device_list as tp_dl
    """
    def resource_compare(self):
        tb_dl, tp_dl = self.dev_list_handle()
        hashlist = {}
        for key in tp_dl:
            """the top resources r more than testbed resources"""
            if len(tp_dl[key]) > len(tb_dl[key]):
                userlog('ERROR', "The %s device in testbed %s can not meet the topology" % (key, self.testbed_name))
                return "1006"
            elif len(tp_dl[key]) <= len(tb_dl[key]):
                """need to compare the device's model"""
                for e in tp_dl[key]:
                    params = {}
                    params['type'] = key
                    if 'model' in e.keys():
                        params['model'] = e['model']
                        if params['model'].lower() == 'linux' or params['model'].lower() == 'windows':
                            params['model'] = params['model'].lower()
                    if 'extension' in e.keys():
                        params['attr'] = e['extension']
                        ext = "with '%s'" % e['extension']
                    else:
                        ext = ''
                    hashlist[e['name']] = ''
                    res = self.dboperation.db_get_dev_by_params(params)
                    for i in range(len(res)):
                        if res[i]['name'] not in hashlist.values():
                            hashlist[e['name']] = res[i]['name']
                            userlog("INFO", "[Device Mapping]:%s (%s:%s) %s: %s" % (e['name'],params['type'],params['model'],ext,res[i]['name']))
                            break
                    if hashlist[e['name']] == '':
                        userlog('ERROR', "Can not find the proper device %s (%s:%s) in testbed %s" % (e['name'],params['type'], params['model'], self.testbed_name))
                        userlog('DEBUG', params.__repr__())
                        userlog('DEBUG', res.__repr__())
                        return "1006"
    
        return hashlist
     
    """
    configure the top connection
    """
    def device_conf_conn(self):
        """
        First, we need to confirm whether it needs to connect two devices 
                connected to the same switch
        use tb_conn_check()
        """
        dev_conn_list = self.dev_conn_list
        do_list = self.do_list
        switch_name_list = self.dboperation.db_get_switch_name()
        todo = {}
        if len(do_list) > len(self.vlanid):
            userlog('ERROR', "[device_conf_conn]:Resered vlan (%s) <-> Need vlan (%s)." % (len(self.vlanid), len(do_list)))   
            return "1008"
        for i in range(0, len(do_list)):
            todo['id'+str(i)] = self.vlanid[i]
            todo['list'+str(i)] = do_list[i]
            todo['conn'+str(i)] = []
            todo['switch'+str(i)] = ""
        self.todo = todo
        if isinstance(switch_name_list, list):
            pass
        else:
            userlog('ERROR', "[device_conf_conn]: switch_name_list data type error ",type(switch_name_list))    
            return "1007"
        if isinstance(dev_conn_list, list):
            if len(dev_conn_list) == 0:
                userlog('WARNING', "[device_conf_conn]:This topology(%s) does not contain any connections." % self.top_name)
            else:
                if len(switch_name_list) == 0:
                    userlog('ERROR', "[device_conf_conn]:This testbed(%s) does not contain any switchs." % self.testbed_name)
                    return "1004"
                elif len(switch_name_list) >= 1:
                    for s in switch_name_list:
                        dboperation = db_operation(self.testbed_name, s)
                        switch_obj = self.create_dev_object(dboperation, s, s)
                        if switch_obj in self.error_node.keys():
                            return switch_obj
                        switch_obj = self.check_dev_available(dboperation, s, switch_obj)
                        if switch_obj in self.error_node.keys():
                            return switch_obj
                        self.obj_res[s] = switch_obj
                        userlog('INFO', "[device_conf_conn]:Create the switch obj [%s] to set the top connection." % str(switch_obj))        
                else:
                    return "1007"
                
                id = 0
                while True:
                    #userlog("INFO","id-------:"+str(id))
                    if "list"+str(id) not in todo.keys():
                        break
                    for e in todo["list"+str(id)]:
                        for sw in self.obj_res.keys():
                            if e[1].find(":"):
                                switch_conn = self.dboperation.db_get_switch_conn(sw, e[0].split(":"), e[1].split(":"), self.create_list)
                            else:
                                switch_conn = self.dboperation.db_get_switch_conn(sw, e[0].split(":"), e[1], self.create_list)
                            if switch_conn:
                                break
                            
                        if not switch_conn:
                            return "1007"
                        
                        """
                        If needs to connect two devices connected to the same switch
                        Comply with the requirements for connection
                        """
                        result = self.set_conn(todo["id"+str(id)], sw, switch_conn, self.obj_res[sw])
#                         print("result:", result)
                        if result in self.error_node.keys():
                            return result
                        self.todo['conn'+str(id)].append(switch_conn)
                        continue
                    id += 1         
        else:
            userlog('ERROR', "[device_conf_conn]: dev_conn_list data type error [%s]" % str(type(dev_conn_list)))
            return "1007"
        
        return {}
    
    
    """
    set the connection by the object of switch and top file
    """
    def set_conn(self, vlanid, switch, conn, obj): 
        if isinstance(conn['dest'],dict):  
            userlog("INFO", "[device_conf_conn]:Begin to verify physical connections.")
            userlog("INFO", "[device_conf_conn]:Connection:Access trunk (%s) { %s }" % (conn['dest']['trunk'], conn['source'][1]))
            userlog("INFO", "[device_conf_conn]:Verify connection logical point:%s" % conn['source'][1][0])
            s_phyname = conn['source'][2]
            s_phyintname = conn['source'][3]
            userlog("INFO", "[device_conf_conn]:Physical connection: (Logic)%s:%s <--> (Physical)%s:%s <--> (Switch)%s:%s)" % 
                      (conn['source'][1][0], conn['source'][1][1], s_phyname, s_phyintname, switch, conn['source'][0]))
            obj.set_trunk(conn['source'][0], conn['dest']['trunk'])
        else:     
            userlog("INFO", "[device_conf_conn]:Begin to verify physical connections.")
            userlog("INFO", "[device_conf_conn]:Connection:Access vlan (%s) { %s,%s }" % (vlanid, conn['source'][1], conn['dest'][1]))
            userlog("INFO", "[device_conf_conn]:Verify connection logical point:%s" % conn['source'][1][0])
            s_phyname = conn['source'][2]
            s_phyintname = conn['source'][3]
            userlog("INFO", "[device_conf_conn]:Physical connection: (Logic)%s:%s <--> (Physical)%s:%s <--> (Switch)%s:%s)" % 
                      (conn['source'][1][0], conn['source'][1][1], s_phyname, s_phyintname, switch, conn['source'][0]))
            
            userlog("INFO", "[device_conf_conn]:Verify connection logical point:%s" % conn['dest'][1][0])
            d_phyname = conn['dest'][2]
            d_phyintname = conn['dest'][3]
            userlog("INFO", "[device_conf_conn]:Physical connection: (Logic)%s:%s <--> (Physical)%s:%s <--> (Switch)%s:%s)" % 
                      (conn['dest'][1][0], conn['dest'][1][1], d_phyname, d_phyintname, switch, conn['dest'][0]))
            
            userlog("INFO", "[device_conf_conn]:Verify physical connections ok")
            userlog("INFO", "[Set_Topology]Destroy_Vlan:%s" % vlanid)
            obj.destroy_vlan(vlanid)
            userlog("INFO", "[Set_Topology]Device %s connect to switch %s:%s" % (conn['source'][1], switch, conn['source'][0]))
            userlog("INFO", "[Set_Topology]Creating access vlan '%s' for '%s'" % (vlanid, conn['source'][1]))
            obj.create_vlan(vlanid)
            userlog("INFO", "[Set_Topology]Set_Vlan:%s for %s" % (vlanid, conn['source'][0]))
            if not obj.set_vlan(conn['source'][0], vlanid):
                userlog("ERROR","[Set_Topology]: Can not set vlan(%s) on %s." % (vlanid, switch))
                return "1007"
            
            userlog("INFO", "[Set_Topology]Device %s connect to switch %s:%s" % (conn['dest'][1], switch, conn['dest'][0]))
            userlog("INFO", "[Set_Topology]Creating access vlan '%s' for '%s'" % (vlanid, conn['dest'][1]))
    #         obj.create_vlan(vlanid)
            userlog("INFO", "[Set_Topology]Set_Vlan:%s for %s" % (vlanid, conn['dest'][0]))
            if not obj.set_vlan(conn['dest'][0], vlanid):
                userlog("ERROR","[Set_Topology]: Can not set vlan(%s) on %s." % (vlanid, switch))
                return "1007"
            
            return True
    """
    print the detail of topology/testbed devices list
    testbed_device_list as tb_dl
    top_device_list as tp_dl
    """
    def dev_list_handle(self):
        tb_dl, tp_dl = {}, self.top_device_list
        tb_type = tp_dl.keys()
        name, tp_num, tb_num = "", "", ""
        for t in tb_type:
            i = 0
            name += '{}\t'.format(t)
            res = self.dboperation.db_get_dev_by_params({'type':t})
            tb_num += '{}\t'.format(len(res))
            tp_num += '{}\t'.format(len(tp_dl[t]))
            tb_dl[t] = res
            
        userlog('INFO', "testbed %s contains those resources:" % self.testbed_name)
        userlog('INFO', name)
        userlog('INFO', tb_num)
        userlog('INFO', "topology %s contains those resources:" % self.top_name)
        userlog('INFO', name)
        userlog('INFO', tp_num)
        
        return tb_dl, tp_dl 
    
    """
    create device object
    """
    def create_dev_object(self, dboperation, device_name, dt_name):
        device_class = dboperation.db_get_dev_class(device_name)
        device_library = dboperation.db_get_class_library(device_class)
        device_stat = dboperation.db_get_dev_param("stat", device_name)
        
        #=======================================================================
        # userlog('INFO', "[create_dev_object]:[%s] which class_name is [%s]" % (device_name, device_class))
        # userlog('INFO', "[create_dev_object]:[%s] which dev_control_lib_name is [%s]" % (device_name, device_library))
        # userlog('INFO', "[create_dev_object]:[%s] which current status is [%s]" % (device_name, device_stat))
        #=======================================================================
        
        try: 
            mod = __import__(device_library)
            device_object = eval('mod.%s' % device_class)(dt_name)
        except ImportError:
            userlog('ERROR', "[create_dev_object]: The library [" + device_library + "] for the device "
                   + device_name + " not found: [ImportError: No module named " + device_library + "]")
            return "1007"
        
        if not isinstance(device_object, eval('mod.%s' % device_class)):
            userlog('ERROR', "[create_dev_object]: Create object instance of class: [%s], failed for device: [%s]" + (device_class, device_name))
            return "1007"
        
        return device_object


    """
    check the status of the devices in testbed
    """
    def check_dev_available(self, dboperation, device_name, device_object):
#         print(dboperation, device_name, device_object)
        userlog("INFO", "[check_dev_available]:Begin to check device(%s) available." % device_name) 
        device_config = dboperation.db_get_dev_config()
        
        if device_config == {}:
            userlog('INFO', "[check_dev_available]: Create object failed for device: " + device_name)
        
        #userlog('INFO', "[check_dev_available]: " + device_config.__repr__())
        
        device_library = device_config[1]
        device_class = device_config[2]
        device_type = device_config[3]
        device_model = device_config[4]
        device_ip = device_config[5]
        device_port = device_config[6]
        device_username = device_config[7]
        device_password = device_config[8]
        device_protocol = device_config[9]
        device_tsname = device_config[10]
        device_mgt = device_config[11]
        device_mgtaddr = device_config[12]
        device_owner = device_config[13]
        device_stat = device_config[14]
        device_active = device_config[15]
        
        if device_stat != "IDLE":
            if device_type == "SWITCH" and device_stat == 'HOLD':
                pass
            else:
                userlog('WARNING', "[check_dev_available]: The device: [" + device_name + "] is [" + device_stat + "].")
                return "1003"
        
        if device_type == "NODE":
            dev_conf_option = "-ip %s -model %s -syslog true -user %s -password %s" % (device_ip, device_model, device_username, device_password)
        elif device_type == "DUT" or device_type == "SWITCH":
            if device_tsname:
                #should get device ts configurations
                ts_config  = dboperation.db_get_dev_config(device_tsname)
                if ts_config == {} :
                    userlog('INFO', "[check_dev_available]: Create object failed for device: " + device_tsname)
                    return {}
            
                ts_library = ts_config[1]
                ts_class = ts_config[2]
                ts_type = ts_config[3]
                ts_model = ts_config[4]
                ts_ip = ts_config[5]
                ts_port = ts_config[6]
                ts_username = ts_config[7]
                ts_password = ts_config[8]
                ts_protocol = ts_config[9]
                ts_name = ts_config[10]
                ts_mgt = ts_config[11]
                ts_mgtaddr = ts_config[12]
                ts_owner = ts_config[13]
                ts_stat = ts_config[14]
                ts_active = ts_config[15]
                
                #userlog('INFO', "[create_dev_object]: " + ts_config.__repr__())
        
                try:
                    mod = __import__(ts_library)
                    ts_object = eval('mod.%s' % ts_class)(device_tsname)
                except ImportError:
                    userlog('INFO', "[create_dev_object]: The library " + ts_library + " for the device " + device_tsname 
                          + " not found: [ImportError: No module named " + ts_library + "]")
                    return {}
            
                if not isinstance(ts_object, eval('mod.%s' % ts_class)):
                    userlog('INFO', "[create_dev_object]: Create object instance of class: " + ts_class + " failed for device: " + ts_name)
                    return {}
                
                
                ts_conf_option = "-model %s -ip %s -port %s -ts %s -tsport %s -user %s -password %s -mgt %s -mgtaddr %s -syslog true" % (ts_model, ts_ip, ts_port, ts_ip, ts_port, ts_username, ts_password, ts_mgt, ts_mgtaddr)
                if not ts_object.set_conf(ts_conf_option):
                    userlog("ERROR","[check_dev_available]: %s is not available." % device_name)
                    return "1001"
                dev_conf_option = ("-ts %s -tsport %s -user %s -password %s -mgt %s -mgtaddr %s") % (ts_ip, ts_port, ts_username, ts_password, ts_mgt, ts_mgtaddr)
            else:
                dev_conf_option = ("-ip %s -port %s -user %s -password %s") % (device_ip, device_port, device_username, device_password)
                           
        device_object.set_conf(dev_conf_option)
#         print(device_object.get_conf('-ip'))
        try:
            device_object.set_timeout(10)
        except:
            pass
        
        if device_type == 'NODE':
            try:
                avail = device_object.is_available()
            except:
                userlog("ERROR","[check_dev_available]: %s is not available." % device_name)
                return "1001"
        elif device_type == "DUT" or device_type == "SWITCH":
            if not device_tsname:
                userlog('WARNING', "[check_dev_available]:Device [%s] has not define terminal server." % device_name)
            
            for i in range(0, 3):
                flag = False
                avail = 0
                try:
                    avail = device_object.connect()
                    break
                except Exception as e:
                    userlog("ERROR", "[check_dev_available]:%s" % e)
#                     print(dev_conf_option)
                    flag = True
                finally:
                    device_object.disconnect()
                    if flag:
                        userlog("WARNING", "[check_dev_available]: (ret:" + str(avail) + ")Connect to device [" + device_name + "] failed, clear line and reconnect...")
                                                                
                    # Clean line.
                    if device_tsname:
                        try:
                            ts_object.clear_line(device_port)
                        except Exception:
                            userlog('INFO', "[check_dev_available]: Connect to terminal server [" + ts_name + "] failed.")
                    else:
                        try:
                            device_object.clear_line(device_port)
                        except Exception:
                            userlog('INFO', "[check_dev_available]: Connect to device [" + device_name + "] failed.")
            
            if device_tsname:
                del ts_object
            
            if not avail:
                userlog("ERROR","[check_dev_available]: %s is not available." % device_name)
                return "1001"
            
            if i>=2:
                device_object.disconnect()
                del device_object                            
                userlog('INFO', "[check_dev_available]: Connect to device [" + device_name + "] over maximum failure, aborted.")
                return "1002"
            
            userlog("INFO","[check_dev_available]: After %s times to connect to device [%s] successfully." % (str(i+1),device_name))
            
        
        return device_object
    
    def check_testbed(self, testbed_name):
        '''check testbed is exist'''
        db = db_operation(testbed_name)
        if testbed not in db.db_get_testbed_list():
            userlog("ERROR","[Running abortted]:The testbed(%s) does not exist." % testbed_name)
            testbed_name = None
        db.db_close()
        
        return testbed_name
    
    def check_top(self, top):
        '''check top'''
        if not os.path.isabs(top):
            top = '/var/sigma-rt/tf/tops/' + top
        if not os.path.exists(top):
            userlog('ERROR', "[IOError]:No such top file [%s]" % top)
            top = None
        if top and os.path.isfile(top) and os.path.splitext(top)[1] != '.top':
            userlog('ERROR', "[FileError]:This is not top file [%s]" % top)
            top = None
        if top:
            userlog('INFO', "Parse Topology File '%s'" % top)
            
        return top
    
    def check_addr(self, addr):
        '''check addr'''
        if addr == "":
            pass
        elif addr:
            if not os.path.isabs(addr):
                addr = '/var/sigma-rt/tf/tops/' + addr
            if not os.path.exists(addr):
                userlog('ERROR', "[IOError]:No such addr file [%s]" % addr) 
                addr = None
            if addr and os.path.isfile(addr) and os.path.splitext(addr)[1] != '.addr':
                userlog('ERROR', "[FileError]:This is not top file [%s]" % addr)
                addr = None 
        if addr:
            userlog('INFO', "Parse Address File '%s'" % addr)
            
        return addr
 
 
                 
if __name__ == '__main__':
    """
    U can configure the topology with the command below:
    
    python tf_run_top.py <testbed_name> <top_name> [addr_name]
    
    PS:
    U should give the top-file and addr-file name, also the testbed name
    e.g., python tf_run_top.py tb1 test.top test.addr
    """
    
    """set tf_logger output to the command line"""
    set_log_flag(1) 
    if len(sys.argv) == 3 or len(sys.argv) == 4:
        testbed = sys.argv[1]
        top = sys.argv[2]
        if len(sys.argv) == 4:
            addr = sys.argv[3]
        else:
            addr = ""
        userlog("INFO","========= Try To Create Testing Environment On TESTBED %s =========" % testbed)               
        _rt_ = run_top(testbed, top, addr)
        if _rt_.top_name and _rt_.addr_name != None:
            ret = _rt_.main()
            _rt_.dboperation.db_close()
        else:
            ret = False
        if ret:
            userlog("INFO","======== Finish Creating Testing Environment On TESTBED %s ========" % testbed)
        else:
            userlog("INFO","=========================== Script Abortting ===========================")
    else:
        userlog('ERROR', "[Error Message]:CMD error!You should run like this: python tf_run_top.py <testbed_name> <top_name> [addr_name].")
        userlog('INFO', "[Attention]:The given name of top and addr file like 'test.top' or 'test.addr' is OK.")
        
