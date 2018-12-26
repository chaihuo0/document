#!/bin/bash

while true
do
    # 检查 cloud-push-provider
    curl --connect-timeout 5 http://172.17.14.153:7006/info
    if [ $? != 0 ];then
        conName=$(docker ps | grep 'cloud-push-provider' | awk '{print $1}')
        docker restart ${conName}
        mydate=`date +"%Y%m%d-%H:%M:%S"`
        echo "\n${mydate}-----------服务重启--------------\n"
        sleep 90
    fi
	
	# 检查 cloud-service-push	
	curl --connect-timeout 5 http://172.17.14.153:7008/info
	if [ $? != 0 ]; then
		conName=$(docker ps | grep 'cloud-service-push' | awk '{print $1}')
		docker restart ${conName}
		mydate=`date +"%Y%m%d-%H:%M:%S"`
        echo "\n${mydate}-----------服务重启--------------\n"
        sleep 90
	fi
	
	# 检查 cloud-push-job
	curl --connect-timeout 5 http://172.17.14.153:7007/info
	if [ $? != 0 ]; then
		conName=$(docker ps | grep 'cloud-push-job' | awk '{print $1}')
		docker restart ${conName}
		mydate=`date +"%Y%m%d-%H:%M:%S"`
        echo "\n${mydate}-----------服务重启--------------\n"
        sleep 90
	fi
	sleep 30
done
