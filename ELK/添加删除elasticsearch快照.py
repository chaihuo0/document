# -*- coding: UTF-8 -*-

import time
import requests

# 当天时间，格式20190302
es_time=time.strftime("%Y%m%d")
# 获取所有快照数据的URL
es_tgw_backup_url="http://172.17.14.150:9200/_snapshot/backup/_all"
# 存储快照日期
es_backup_list=[]


# 添加快照
def addBackup(addTime):
    requests.put("http://172.17.14.150:9200/_snapshot/backup/backup"+str(addTime)+"?wait_for_completion=true")

# 删除快照
def deleteOldbackup(deleteTime):
    requests.delete("http://172.17.14.150:9200/_snapshot/backup/backup"+str(deleteTime))

# 获取backup仓库的快照
def getElasticsearchAllBackup(backupUrl):
    # 获取json数据，并且转换为dict
    result=requests.get(backupUrl).json()
    global es_backup_list
    # 遍历dict
    for i in result['snapshots']:
        # 取到对应的字段，截取后8位日期
        tgw_date=i['snapshot'][-8:]
        # 将日期追加到数组
        es_backup_list.append(tgw_date)

if __name__ == '__main__':
    # 添加快照
    addBackup(es_time)

    # 获取所有的快照数据
    getElasticsearchAllBackup(es_tgw_backup_url)

    # 快照超过30个，删除时间最久的快照
    if len(es_backup_list) > 30:
        deleteOldbackup(es_backup_list[0])
        print("删除TGW-ES快照------backup"+es_backup_list[0])