#!/bin/bash

while true
do
	curl --connect-timeout 10 http://
	if [ $? -eq 0 ]; then
		NUM1=$(curl http://)
		sleep 300
		NUM2=$(curl http://)
		CONTAINER=$(docker ps | grep 'cloud-service-provider' | awk 'print $1')
		MYDATE=$(date +'%Y%m%d-%H:%M:%S')

		if [ ${NUM2} -gt 0 && ${NUM2} -eq ${NUM1} ]; then
			docker restart ${CONTAINER}
			echo "\n-------------服务重启，时间：${MYDATE}---------------\n"
			sleep 90
		fi

		curl --connect-timeout 10 http://172.17.14.152:7006/info
		if [ $? -eq 0 ];then
			docker restart ${CONTAINER}
			echo "\n-------------服务重启，时间：${MYDATE}---------------\n"
			sleep 90
		fi
	else
		MYDATE=$(date +'%Y%m%d-%H:%M:%S')
		CONTAINER=$(docker ps | grep 'cloud-service-check' | awk 'print $1')
		docker restart ${CONTAINER}
		echo "\n-------------服务重启，时间：${MYDATE}---------------\n"
		sleep 90
	fi
done