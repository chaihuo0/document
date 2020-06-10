# Redis集群数据迁移-redis-shake

redis-shake是阿里云自研的开源工具，支持对Redis数据进行解析（decode）、恢复（restore）、备份（dump）、同步（sync/rump）。在sync模式下，redis-shake使用**SYNC**或**PSYNC**命令将数据从源端Redis同步到目的端Redis，支持全量数据同步和增量数据同步，增量同步在全量同步完成后自动开始。本文以使用sync模式将自建Codis/Redis集群版数据库上云为例进行说明。

官方地址：

<https://help.aliyun.com/document_detail/125941.html?spm=a2c4g.11186623.6.702.2d245d3eyN74QU>

### !!!此文档使用场景为Redis Cluster to Redis Cluster







1、下载redis-shake工具，以redis-shake-v2.0.2.tar.gz为例

```
tar -zxvf redis-shake-v2.0.2.tar.gz
```

2、修改配置文件redis-shake.conf，由于配置文件内容过多，主要需要修改的地方就这几个

```
......
source.type = cluster #数据源改为集群模式
source.address = 172.16.16.50:6379;172.16.16.51:6379;172.16.16.52:6379 #数据源3个master
target.type = cluster #目标改为集群模式
target.address = 172.16.22.52:6379;172.16.22.53:6379;172.16.22.55:6379 #目标3个master
......
#其他参数默认即可，若需要开启请参考配置文件里面的注释
```

3、启动同步

```
./redis-shake.linux -type=sync -conf=redis-shake.conf
#启动之后会一直从数据源处同步数据到目标集群，同步完成之后还会持续实时同步数据。
```

