#### redis集群添加节点

##### 新建redis集群目录

```
mkdir -p /fintech/springcloud/redis/redis-cluster
cd /fintech/springcloud/redis/redis-cluster
```

##### 编辑redis配置文件`vi redis.conf`

```
port 6379
bind 172.17.14.214
daemonize no
pidfile "/var/run/redis.pid"
cluster-enabled yes
cluster-config-file nodes.conf
cluster-node-timeout 15000
repl-timeout 6000
appendonly no

save 3600 1
save 1800 100
save 300 5000
save 60 30000

```

##### `vi start.sh`

```
docker run --restart=on-failure --name redis --net=host  -e TZ="Asia/Shanghai" -v /fintech/springcloud/redis/redis-cluster:/data -v /fintech/springcloud/redis/redis-cluster/redis.conf:/usr/local/etc/redis/redis.conf -d redis:4.0.6 redis-server /usr/local/etc/redis/redis.conf
```

##### 添加可执行权限

```
chmod +x start.sh
```

##### 启动`redis`

```
./start.sh
```

##### 添加`redis` `salve`节点

```
docker run --rm -it --net=host zvelo/redis-trib add-node --slave --master-id 396a64751ea86aa0049ca9834836b61e94c83dd5 172.17.14.105:6379 172.17.14.165:6379
```

##### 删除`redis` `salve`节点

```
docker run --rm -it --net=host zvelo/redis-trib del-node 172.17.14.150:6379 953637d8987ad9242b1ad3b350d01fcae4d1689d

# 从172.17.14.150:6379集群中删除ID为 953637d8987ad9242b1ad3b350d01fcae4d1689d 的节点
```

