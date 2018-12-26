#### redis

##### 信息

```
本次为平滑迁移redis集群，先添加一个redis节点，再删除一个redis节点，需要注意节点是否为主节点。如果为主节点，查看是否有从节点，有从节点，先添加一个节点为当前主节点的从节点，再关闭主节点。无从节点，添加节点，然后迁移slot，再删除当前主节点，或让添加节点 成为当前主节点的从节点。
```

##### 安装redis

```
docker pull redis

# redis容器启动命令
docker run -d --name redis6 --net host -e TZ="Asia/Shanghai" --mount type=bind,source=/root/springcloud/redis-6/redis.conf,target=/usr/local/etc/redis/redis.conf --mount type=bind,source=/root/springcloud/redis-6/data,target=/data --mount type=bind,source=/etc/localtime,target=/etc/localtime redis redis-server /usr/local/etc/redis/redis.conf
```

###### 配置文件

```
port 6380											端口
bind 172.18.44.81									IP地址
daemonize no										是否在后台运行
pidfile "/var/run/redis.pid"						pid文件路径
cluster-enabled yes									启用集群模式
cluster-config-file nodes.conf						集群状态下的文件
cluster-node-timeout 15000							时间
appendonly no										
```

###### redis加入集群

```
# redis集群添加节点，集群节点不能少于6个，3个master，3个slave，集群少于3个master节点可能会导致集群不可用，一个master可以有多个slave

# 进入容器，将172.18.44.81:6380加入到172.18.44.128:6380这个集群中
root@hx:/data# redis-cli -h 172.18.44.128 -p 6380
172.18.44.128:6380> CLUSTER MEET 172.18.44.81 6380

# 查看集群所有节点
172.18.44.128:6380> cluster nodes
....

# 让当前节点成为某个master(主节点)的slave（从节点）
172.18.44.81:6380> CLUSTER REPLICATE 380ef9ba73dac4c220feade43da1c298b9d58cba //主节点ID

# 忘记节点
172.18.44.81:6380> cluster forget 9c240333476469e8e2c8e80b089c48f389827265

# 删除从节点，先将新节点加入和这个节点一样的主节点，再删除这个节点。redis-trib.rb命令在120这台机器上，redis容器没有这个命令，可自行在本地机安装。redis.tar.gz安装包有
redis-trib.rb del-node 172.18.44.81:6380 '9c240333476469e8e2c8e80b089c48f389827265'

# 删除主节点，如果主节点有从节点，将从节点转移到其他主节点，如果主节点有slot，去掉分配的slot，然后再删除主节点
redis-trib.rb del-node 172.18.44.81:6380 '9c240333476469e8e2c8e80b089c48f389827265'
```

###### 重新分配slot

```
# redis-trib.rb reshard 172.18.44.81:6380 //下面是主要过程  
  
How many slots do you want to move (from 1 to 16384)? 1000 //设置slot数1000  
What is the receiving node ID? 03ccad2ba5dd1e062464bc7590400441fafb63f2 //新节点node id  
Please enter all the source node IDs.  
 Type 'all' to use all the nodes as source nodes for the hash slots.  
 Type 'done' once you entered all the source nodes IDs.  
Source node #1:all //表示全部节点重新洗牌  
Do you want to proceed with the proposed reshard plan (yes/no)? yes //确认重新分 
```



##### redis集群操作指令

```
//集群(cluster)  
CLUSTER INFO 打印集群的信息  
CLUSTER NODES 列出集群当前已知的所有节点（node），以及这些节点的相关信息。   
  
//节点(node)  
CLUSTER MEET <ip> <port> 将 ip 和 port 所指定的节点添加到集群当中，让它成为集群的一份子。  
CLUSTER FORGET <node_id> 从集群中移除 node_id 指定的节点。  
CLUSTER REPLICATE <node_id> 将当前节点设置为 node_id 指定的节点的从节点。  
CLUSTER SAVECONFIG 将节点的配置文件保存到硬盘里面。   
  
//槽(slot)  
CLUSTER ADDSLOTS <slot> [slot ...] 将一个或多个槽（slot）指派（assign）给当前节点。  
CLUSTER DELSLOTS <slot> [slot ...] 移除一个或多个槽对当前节点的指派。  
CLUSTER FLUSHSLOTS 移除指派给当前节点的所有槽，让当前节点变成一个没有指派任何槽的节点。  
CLUSTER SETSLOT <slot> NODE <node_id> 将槽 slot 指派给 node_id 指定的节点，如果槽已经指派给另一个节点，那么先让另一个节点删除该槽>，然后再进行指派。  
CLUSTER SETSLOT <slot> MIGRATING <node_id> 将本节点的槽 slot 迁移到 node_id 指定的节点中。  
CLUSTER SETSLOT <slot> IMPORTING <node_id> 从 node_id 指定的节点中导入槽 slot 到本节点。  
CLUSTER SETSLOT <slot> STABLE 取消对槽 slot 的导入（import）或者迁移（migrate）。   
  
//键 (key)  
CLUSTER KEYSLOT <key> 计算键 key 应该被放置在哪个槽上。  
CLUSTER COUNTKEYSINSLOT <slot> 返回槽 slot 目前包含的键值对数量。  
CLUSTER GETKEYSINSLOT <slot> <count> 返回 count 个 slot 槽中的键。
```

