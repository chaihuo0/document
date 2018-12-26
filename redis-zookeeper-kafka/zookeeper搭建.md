#### zookeeper搭建

##### 运行命令

```
[root@localhost zookeeper]# docker pull zookeeper
[root@localhost zookeeper]# docker run -d --name zk --net host -e "ZOO_MY_ID=4" -e "ZOO_SERVERS=server.1=172.18.44.120:2883:3883" -e "ZOO_SERVERS=server.2=172.18.44.128:2884:3884" -e "ZOO_SERVERS=server.3=172.18.44.120:2885:3885" -e "ZOO_SERVERS=server.4=172.18.44.81:2886:3886" --mount type=bind,source=/root/springcloud/zookeeper/zoo.cfg,target=/conf/zoo.cfg --mount type=bind,source=/root/springcloud/zookeeper/myid,target=/data/myid --mount type=bind,source=/etc/localtime,target=/etc/localtime zookeeper
```

##### zookeeper配置文件	

```
clientPort=2880				client连接的端口
dataDir=/data				存放内存数据库快照的位置
dataLogDir=/datalog			事务日志目录a
tickTime=2000				基本事件单元，控制心跳和超时
initLimit=5					初始化连接时最长能忍受多少个心跳时间间隔数
syncLimit=2					leader和follower初始化连接最长能忍受多少个心跳时间间隔数
server.1=172.18.44.120:2883:3883	2883集群交换信息端口，3883选举leader端口
server.2=172.18.44.128:2884:3884
server.3=172.18.44.123:2885:3885
server.4=172.18.44.81:2886:3886		本行为新添加，旧的zookeeper配置文件中没有
```

##### zookeeper  myid文件

```
# 在相应位置添加myid文本文件，数字要大于目前集群中最大的数字，如目前集群是3，则新添加的为4
4
```

##### 测试是否添加成功

```
[root@node2 zookeeper]#  echo status | nc 172.18.44.81 2880
Mode: follower

# nc命令用yum安装
yum -y install nc
```

