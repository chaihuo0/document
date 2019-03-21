#### `sentinel`搭建

##### 所有节点操作一样，配置文件一致

##### 创建目录

```
mkdir -p /fintech/springcloud/sentinel
cd /fintech/springcloud/sentinel
```

##### `vi Dockerfile`

```
FROM centos:7
VOLUME /fintech/springcloud/sentinel
ADD redis-sentinel /fintech/springcloud/sentinel/redis-sentinel
ENTRYPOINT /bin/bash -c '/fintech/springcloud/sentinel/start.sh'
```

##### `vi start.sh`

```
#!/bin/bash

/fintech/springcloud/sentinel/redis-sentinel /fintech/springcloud/sentinel/sentinel.conf
```

##### 生成镜像

```
docker build -t redis-sentinel:20190112 .
```

##### `vi sentinel.conf`配置文件都保持一致

```
port 26379
# 守护进程模式
daemonize no
# 关闭保护模式，在这种模式下，连接只接受回环接口，导致java客户端连接不上
protected-mode no
# 指明日志文件名 最好写绝对路劲
logfile "/fintech/springcloud/sentinel/sentinel.log"

dir "/"
# sentinel监听172.17.14.150:7379这个redis，在sentinel中名字为market，需要2个sentinel投票成功才可以切换redis主从，投票人数要大于sentinel个数的一半。
sentinel monitor market 172.17.14.150 7379 2
sentinel monitor mymaster 172.17.14.150 8379 2
```

##### `vi start-docker.sh`

```
#!/bin/bash

docker run --restart=always -d --name sentinel --net host -v /fintech/springcloud/sentinel:/fintech/springcloud/sentinel redis-sentinel:20190112
```

##### 运行sentinel

```
./start-docker.sh
```

##### 通过redis客户端连接`sentinel`，查看状态

```
redis-cli -h 172.17.14.150 -p 26379

输入  info

最后出现如下2行，sentinel集群添加成功
master0:name=mymaster,status=ok,address=172.17.14.150:8379,slaves=1,sentinels=3
master1:name=market,status=ok,address=172.17.14.150:7379,slaves=1,sentinels=3
```

