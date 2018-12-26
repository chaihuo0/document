#!/usr/bin/python
# -*- coding: utf-8 -*-  
import os
import re
import subprocess
import sys
try:
    import simplejson as json
except:
    import json
##获取集群状态 HEALTH_ERR、HEALTH_WARN、HEALTH_OK
def get_ceph_status():
    p = subprocess.Popen("ceph -s -f json", shell=True,stdout=subprocess.PIPE)
    j_data = json.loads(p.stdout.read())
    status = j_data.get('health').get('overall_status')
    mark = 0  ##正常
    if status == 'HEALTH_ERR':
        mark = 1
    if status == 'HEALTH_WARN':
        mark = 2
    if status == 'HEALTH_OK':
        mark = 0
    print {'HEALTH':mark}
    return {'HEALTH':mark}
##检查osd使用率
def get_osd_usage():
    p = subprocess.Popen("ceph osd df | awk '{print $1,$7}'", shell=True, stdout=subprocess.PIPE)
    osds = p.stdout.readlines()
    dicts = {}
    for o in osds:
        array = o.strip().split(" ")
        try:
            id = int(array[0])
            dicts[array[0]]=array[1]
        except ValueError:
            print "Not number"
    j_data = json.dumps(dicts, indent=4)
    print j_data
    return j_data
##获取osd状态 0表示没有down的osd, 1表示有down
def get_osd_status():
    ##p = subprocess.Popen("ceph osd tree | awk '{print $4}' |grep down", shell=True, stdout=subprocess.PIPE)
    ##osds_len = len(p.stdout.read())
    ##print osds_len
    ##if osds_len == 0:
    ##    return 0
    ##else:
    ##    return 1
    p = subprocess.Popen("ceph osd stat -f json", shell=True, stdout=subprocess.PIPE)
    data = json.loads(p.stdout.read())
    if data.get('num_osds') == data.get('num_up_osds') == data.get("num_in_osds"):
        print 0
        return 0
    else:
        print 1    
        return 1
##获取pg状态 0表示 active+clean, 1表示有问题
def get_pg_status():
    p = subprocess.Popen("ceph pg stat -f json", shell=True, stdout=subprocess.PIPE)
    data = json.loads(p.stdout.read())
    if len(data.get("num_pg_by_state")) > 1:
        print 1
        return 1
    else:
        print 0
        return 0
    
##获取osd延迟信息
def get_osd_latency():
    p = subprocess.Popen("ceph osd perf |awk '{print $1,$3}'", shell=True, stdout=subprocess.PIPE)
    return _change_data_format(p)
##数据格式转换
def _change_data_format(p):
    osds = p.stdout.readlines()
    dicts = {}
    for o in osds:
        array = o.strip().split(" ")
        try:
            id = int(array[0])
            dicts[array[0]]=array[1]
        except ValueError:
            print "Not number"
    j_data = json.dumps(dicts, indent=4)
    print j_data
    return j_data
##mon 状态
def get_mon_status():
    p = subprocess.Popen("ceph mon_status", shell=True, stdout=subprocess.PIPE)
    usage = p.stdout.read()
    json_usage = json.loads(usage)
    print json_usage
    return json_usage
##ceph集群所有磁盘使用率
def get_ceph_disk_usage():
    p = subprocess.Popen("ceph df -f json", shell=True, stdout=subprocess.PIPE)
    usage = p.stdout.read()
    json_usage = json.loads(usage)
    print json_usage
    return json_usage
if __name__ == '__main__':
    inputs = sys.argv[1]
    if inputs == '1':
        get_ceph_status()
    if inputs == '2':
        get_osd_usage()
    if inputs == '3':
        get_osd_status()
    if inputs == '4':
        get_osd_latency()
    if inputs == '5':
        get_pg_status()
    if inputs == '6':
        get_mon_status()
    if inputs == '7':
        get_ceph_disk_usage()