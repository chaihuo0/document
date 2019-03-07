# -*- coding: UTF-8 -*-

import time
import requests
from dingtalkchatbot.chatbot import DingtalkChatbot


# 当天时间，格式20190302
es_time=time.strftime("%Y%m%d")
# 获取所有快照数据的URL
es_tgw_backup_url="http://172.17.14.150:9200/_snapshot/backup/_all"
# 存储快照日期
es_backup_list=[]
# 钉钉接口token
dingding_token = 'https://oapi.dingtalk.com/robot/send?access_token=fb50f719b7f9fa4750e5a266d069731552229e4fc2cc3d55b5f9060bb6ccc6ea'


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

# 判断elasticsearch快照添加状态
def getFailedNum(backupUrl):
    # 获取json数据，并且转换为dict
    result = requests.get(backupUrl).json()
    # 记录快照数据长度
    len_result=len(result['snapshots'])
    # 拿到最新一次快照数据
    tgw_date = result['snapshots'][len_result-1]
    # 判断快照状态
    if tgw_date['state'] == 'SUCCESS':
        print('TGW-ES添加快照成功------本次快照：'+tgw_date['snapshot'])
        ddapi('TGW-ES添加快照成功------本次快照：'+tgw_date['snapshot'])
    else:
        print('TGW-ES添加快照失败------错误状态：' + tgw_date['state'])
        ddapi('TGW-ES添加快照失败------错误状态：' + tgw_date['state'])
        # 打印备份快照错误详细内容
        for u in tgw_date['shards']:
            if int(u['failed'])>0:
                print('备份快照分片报错，分片错误数量：'+u['failed']+'；\n分片成功数量：'+u['successful']+'；\n分片总数：'+u['total'])
                ddapi('备份快照分片报错，分片错误数量：'+u['failed']+'；\n分片成功数量：'+u['successful']+'；\n分片总数：'+u['total'])

# 钉钉机器人API接口
def ddapi(info):
    dingding = DingtalkChatbot(dingding_token)
    dingding.send_text(msg=info)

if __name__ == '__main__':
    # 添加快照
    addBackup(es_time)

    # 本次添加的快照状态
    getFailedNum(es_tgw_backup_url)

    # 获取所有的快照数据
    getElasticsearchAllBackup(es_tgw_backup_url)

    # 快照超过30个，删除时间最久的快照
    if len(es_backup_list) > 30:
        deleteOldbackup(es_backup_list[0])
        print("删除TGW-ES快照------backup"+es_backup_list[0])
        ddapi("删除TGW-ES快照------backup"+es_backup_list[0])