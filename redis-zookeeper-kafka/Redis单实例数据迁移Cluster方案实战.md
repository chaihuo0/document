# Redis单实例数据迁移Cluster方案实战

大部分应用在使用Redis的时候可能前期只使用一个实例，随着数据量和访问量增大，单实例逐渐捉襟见肘，就需要考虑上Cluster方案了，本文提供了一个方案，就是把单实例的数据完整的迁移到Cluster上。

**方案步骤**

1）获取原单实例节点D的持久化AOF文件

2）新准备三个节点A，B，C，建立集群，目前集群为空

3）把节点B，C上的slots，全部分配给A

4）把1）中获取的AOF文件SCP到A上

5）重启A节点，把数据全部加载到内存

6）把A节点上的slots再均匀分配给B，C

7）新准备A1，B1，C1，分别作为A，B，C的slave加入到集群

8）验证数据的完整性和集群状态

**方案实战**

目前我们的实战是这样的，单节点为 10.10.10.118:6379 ，数据量为 500多万

Cluster准备了3主3从，前期A，B，C构成一个空的集群，A1，B1，C1待数据分配好后，再加入集群

​                  A 10.10.10.126:7000 -> A1 10.10.10.126:7003

​                  B 10.10.10.126:7001 -> B1 10.10.10.126:7004

​                  C 10.10.10.126:7002 -> C1 10.10.10.126:7005

管理集群，我们仍然使用官方提供的工具redis-trib.rb，具体redis-trib.rb如何使用，请参考[Cluster实战](https://www.18188.org/articles/2016/04/19/1461054842671.html)的那篇文章。

1）**持久化文件**

此次操作以RDB持久化文件操作

2）**创建集群**

2.1）启动A，B，C节点

/data/apps/redis-cluster/7000/bin/redis-server /data/apps/redis-cluster/7000/redis.conf
/data/apps/redis-cluster/7001/bin/redis-server /data/apps/redis-cluster/7001/redis.conf
/data/apps/redis-cluster/7002/bin/redis-server /data/apps/redis-cluster/7002/redis.conf

2.2）3个Master节点构成集群

[root@test1 bin]# ./redis-trib.rb create 10.10.10.126:7000 10.10.10.126:7001 10.10.10.126:7002
>>> Creating cluster
>>> Performing hash slots allocation on 3 nodes...
>>> Using 3 masters:
>>> 10.10.10.126:7000
>>> 10.10.10.126:7001
>>> 10.10.10.126:7002
>>> M: 6a85d385b2720fd463eccaf720dc12f495a1baa3 10.10.10.126:7000
>>>    slots:0-5460 (5461 slots) master
>>> M: bbb2b1b060b440a56d07a16ee7f87f9379767d61 10.10.10.126:7001
>>>    slots:5461-10922 (5462 slots) master
>>> M: e7005711bc55315caaecbac2774f3c7d87a13c7a 10.10.10.126:7002
>>>    slots:10923-16383 (5461 slots) master
>>> Can I set the above configuration? (type 'yes' to accept): yes
>>> Nodes configuration updated
>>> Assign a different config epoch to each node
>>> Sending CLUSTER MEET messages to join the cluster
>>> Waiting for the cluster to join.
>>> Performing Cluster Check (using node 10.10.10.126:7000)
>>> M: 6a85d385b2720fd463eccaf720dc12f495a1baa3 10.10.10.126:7000
>>>    slots:0-5460 (5461 slots) master
>>> M: bbb2b1b060b440a56d07a16ee7f87f9379767d61 10.10.10.126:7001
>>>    slots:5461-10922 (5462 slots) master
>>> M: e7005711bc55315caaecbac2774f3c7d87a13c7a 10.10.10.126:7002
>>>    slots:10923-16383 (5461 slots) master
>>> [OK] All nodes agree about slots configuration.
>>> Check for open slots...
>>> Check slots coverage...
>>> [OK] All 16384 slots covered.

2.3）查看集群状态，看slots分布情况

[root@test1 bin]#./redis-cli -c -p 7000
127.0.0.1:7000> cluster nodes
bbb2b1b060b440a56d07a16ee7f87f9379767d61 10.10.10.126:7001 master - 0 1461378773614 2 connected 5461-10922
e7005711bc55315caaecbac2774f3c7d87a13c7a 10.10.10.126:7002 master - 0 1461378772614 3 connected 10923-16383
6a85d385b2720fd463eccaf720dc12f495a1baa3 10.10.10.126:7000 myself,master - 0 0 1 connected 0-5460
127.0.0.1:7000> 

3）**把B、C上slots移到A节点上**

[root@test1 bin]# ./redis-trib.rb check 10.10.10.126:7000

>>> Performing Cluster Check (using node 10.10.10.126:7000)
M: 6a85d385b2720fd463eccaf720dc12f495a1baa3 10.10.10.126:7000
   slots:0-5460 (5461 slots) master
   0 additional replica(s)
M: bbb2b1b060b440a56d07a16ee7f87f9379767d61 10.10.10.126:7001
   slots:5461-10922 (5462 slots) master
   0 additional replica(s)
M: e7005711bc55315caaecbac2774f3c7d87a13c7a 10.10.10.126:7002
   slots:10923-16383 (5461 slots) master
   0 additional replica(s)
[OK] All nodes agree about slots configuration.
>>> Check for open slots...
>>> Check slots coverage...
[OK] All 16384 slots covered.

从刚才的集群状态得知

A节点 10.10.10.126:7000 的runid为 6a85d385b2720fd463eccaf720dc12f495a1baa3 ，其有 5461 个slots

B节点 10.10.10.126:7001 的runid为 bbb2b1b060b440a56d07a16ee7f87f9379767d61 ，其有 5462 个slots

C节点 10.10.10.126:7002 的runid为 e7005711bc55315caaecbac2774f3c7d87a13c7a ，其有 5461 个slots



把B节点上5462个slots移动A节点上

./redis-trib.rb reshard --from bbb2b1b060b440a56d07a16ee7f87f9379767d61  --to 6a85d385b2720fd463eccaf720dc12f495a1baa3  --slots 5462 --yes 10.10.10.126:7000



把C节点上的5461个slots移动A节点上

./redis-trib.rb reshard --from e7005711bc55315caaecbac2774f3c7d87a13c7a    --to 6a85d385b2720fd463eccaf720dc12f495a1baa3  --slots 5461 --yes 10.10.10.126:7000

可以看到A节点拥有了全部16384个slots，B、C节点上已经没有slots了

[root@test1 bin]#  ./redis-trib.rb check 10.10.10.126:7000
>>> Performing Cluster Check (using node 10.10.10.126:7000)
>>> M: 6a85d385b2720fd463eccaf720dc12f495a1baa3 10.10.10.126:7000
>>>    **slots:0-16383 (16384 slots) master
>>> **   0 additional replica(s)
>>> M: bbb2b1b060b440a56d07a16ee7f87f9379767d61 10.10.10.126:7001
>>>    **slots: (0 slots) master
>>> **   0 additional replica(s)
>>> M: e7005711bc55315caaecbac2774f3c7d87a13c7a 10.10.10.126:7002
>>>    **slots: (0 slots) master
>>> **   0 additional replica(s)
>>> [OK] All nodes agree about slots configuration.
>>> Check for open slots...
>>> Check slots coverage...
>>> [OK] All 16384 slots covered.

4）**把1）中持久化RDB文件SCP到A上**

ps：rdb文件的目录在配置文件里面有写！

文件拷贝到redis目录之后强制关闭Redis再启动

暴力停止命令	kill -9 `ps -ef | grep redis | awk {'print $2'}`

温柔启动命令	/data/apps/redis-cluster/7000/bin/redis-server /data/apps/redis-cluster/7000/redis.conf

启动后使用客户端或者命令查询，确认所有数据都在A上

6）**把A节点上的slots再均匀分配给B，C**（最好原路返回，之前去了多少现在就回来多少）

# stop！！！！

由于接下来要使用官方redis-trib.rb工具，但是有坑，所以先解决这个bug

Redis的工具一般在安装目录的src目录下面，直接vi redis-trib.rb

```

while true
            keys = source.r.cluster("getkeysinslot",slot,o[:pipeline])
            break if keys.length == 0
            begin
#1下面一行需替换               source.r.client.call(["migrate",target.info[:host],target.info[:port],"",0,@timeout,"replace",:keys,*keys])
				STDOUT.flush
            rescue => e
                if o[:fix] && e.to_s =~ /BUSYKEY/
                    xputs "*** Target key exists. Replacing it for FIX."
#2下面一行需替换                    source.r.client.call(["migrate",target.info[:host],target.info[:port],"",0,@timeout,:replace,:keys,*keys])
                else
                    puts ""
                    xputs "[ERR] Calling MIGRATE: #{e}"
                    exit 1
                end
            end
```

1替换为

```
source.r.call(["migrate",target.info[:host],target.info[:port],"",0,@timeout,"replace",:keys,*keys])
```

2替换为

```
source.r.call(["migrate",target.info[:host],target.info[:port],"",0,@timeout,:replace,:keys,*keys])
```

保存文件！

# 继续！

把A节点上5462个slots移动B节点上

./redis-trib.rb reshard --from 6a85d385b2720fd463eccaf720dc12f495a1baa3  --to bbb2b1b060b440a56d07a16ee7f87f9379767d61  --slots 5462 --yes 10.10.10.126:7000



把A节点上的5461个slots移动C节点上

./redis-trib.rb reshard --from 6a85d385b2720fd463eccaf720dc12f495a1baa3  --to e7005711bc55315caaecbac2774f3c7d87a13c7a    --slots 5461 --yes 10.10.10.126:7000



可以看到slots都已经成功转移了

127.0.0.1:7000>  cluster nodes
6a85d385b2720fd463eccaf720dc12f495a1baa3 10.10.10.126:7000 myself,master - 0 0 4 connected 10923-16383
bbb2b1b060b440a56d07a16ee7f87f9379767d61 10.10.10.126:7001 master - 0 1461381943938 5 connected 0-5461
e7005711bc55315caaecbac2774f3c7d87a13c7a 10.10.10.126:7002 master - 0 1461381944938 6 connected 5462-10922
127.0.0.1:7000> 

**注意：在实际操作中，看数据量情况，如果量大的话，slots不要一次性移过去，要一部分一部分的转移。**

7）**给A、B、C节点添加slave节点**

7.1）启动A1节点，并把A1节点加入集群，成为A节点的从节点

启动：/data/apps/redis-cluster/7003/bin/redis-server /data/apps/redis-cluster/7003/redis.conf

A1加入集群：

[root@test1 bin]#  ./redis-trib.rb add-node --slave --master-id 6a85d385b2720fd463eccaf720dc12f495a1baa3 10.10.10.126:7003 10.10.10.126:7000
>>> Adding node 10.10.10.126:7003 to cluster 10.10.10.126:7000
>>> Performing Cluster Check (using node 10.10.10.126:7000)
M: 6a85d385b2720fd463eccaf720dc12f495a1baa3 10.10.10.126:7000
   slots:10923-16383 (5461 slots) master
   0 additional replica(s)
M: bbb2b1b060b440a56d07a16ee7f87f9379767d61 10.10.10.126:7001
   slots:0-5461 (5462 slots) master
   0 additional replica(s)
M: e7005711bc55315caaecbac2774f3c7d87a13c7a 10.10.10.126:7002
   slots:5462-10922 (5461 slots) master
   0 additional replica(s)
[OK] All nodes agree about slots configuration.
>>> Check for open slots...
>>> Check slots coverage...
[OK] All 16384 slots covered.
>>> Send CLUSTER MEET to node 10.10.10.126:7003 to make it join the cluster.
Waiting for the cluster to join.
>>> Configure node as replica of 10.10.10.126:7000.
[OK] New node added correctly.
[root@test1 bin]# 

看集群节点信息情况：

127.0.0.1:7000> cluster nodes
afbe63bcf2f3418db48ea9a2749dd0b1bf24f0f3 10.10.10.126:7003 slave 6a85d385b2720fd463eccaf720dc12f495a1baa3 0 1461387526639 4 connected
6a85d385b2720fd463eccaf720dc12f495a1baa3 10.10.10.126:7000 myself,master - 0 0 4 connected 10923-16383
bbb2b1b060b440a56d07a16ee7f87f9379767d61 10.10.10.126:7001 master - 0 1461387527640 5 connected 0-5461
e7005711bc55315caaecbac2774f3c7d87a13c7a 10.10.10.126:7002 master - 0 1461387526239 6 connected 5462-10922
127.0.0.1:7000> 



7.2）启动B1节点，并把B1节点加入集群，成为B节点的从节点

启动：/data/apps/redis-cluster/7004/bin/redis-server /data/apps/redis-cluster/7004/redis.conf

B1加入集群：

[root@test1 bin]# ./redis-trib.rb add-node --slave --master-id bbb2b1b060b440a56d07a16ee7f87f9379767d61 10.10.10.126:7004 10.10.10.126:7000
>>> Adding node 10.10.10.126:7004 to cluster 10.10.10.126:7000
>>> Performing Cluster Check (using node 10.10.10.126:7000)
M: 6a85d385b2720fd463eccaf720dc12f495a1baa3 10.10.10.126:7000
   slots:10923-16383 (5461 slots) master
   1 additional replica(s)
S: afbe63bcf2f3418db48ea9a2749dd0b1bf24f0f3 10.10.10.126:7003
   slots: (0 slots) slave
   replicates 6a85d385b2720fd463eccaf720dc12f495a1baa3
M: bbb2b1b060b440a56d07a16ee7f87f9379767d61 10.10.10.126:7001
   slots:0-5461 (5462 slots) master
   0 additional replica(s)
M: e7005711bc55315caaecbac2774f3c7d87a13c7a 10.10.10.126:7002
   slots:5462-10922 (5461 slots) master
   0 additional replica(s)
[OK] All nodes agree about slots configuration.
>>> Check for open slots...
>>> Check slots coverage...
[OK] All 16384 slots covered.
>>> Send CLUSTER MEET to node 10.10.10.126:7004 to make it join the cluster.
Waiting for the cluster to join.
>>> Configure node as replica of 10.10.10.126:7001.
[OK] New node added correctly.
[root@test1 bin]# 
看集群节点信息情况：

127.0.0.1:7000> cluster nodes
afbe63bcf2f3418db48ea9a2749dd0b1bf24f0f3 10.10.10.126:7003 slave 6a85d385b2720fd463eccaf720dc12f495a1baa3 0 1461387826504 4 connected
6fbc4a2a0239bc876bed4cf854846717d9543477 10.10.10.126:7004 slave bbb2b1b060b440a56d07a16ee7f87f9379767d61 0 1461387827004 5 connected
e7005711bc55315caaecbac2774f3c7d87a13c7a 10.10.10.126:7002 master - 0 1461387826004 6 connected 5462-10922
6a85d385b2720fd463eccaf720dc12f495a1baa3 10.10.10.126:7000 myself,master - 0 0 4 connected 10923-16383
bbb2b1b060b440a56d07a16ee7f87f9379767d61 10.10.10.126:7001 master - 0 1461387827504 5 connected 0-5461
127.0.0.1:7000> 



7.3）启动C1节点，并把C1节点加入集群，成为C节点的从节点

启动：/data/apps/redis-cluster/7005/bin/redis-server /data/apps/redis-cluster/7005/redis.conf

C1加入集群：

[root@test1 bin]# ./redis-trib.rb add-node --slave --master-id e7005711bc55315caaecbac2774f3c7d87a13c7a 10.10.10.126:7005 10.10.10.126:7000
>>> Adding node 10.10.10.126:7005 to cluster 10.10.10.126:7000
>>> Performing Cluster Check (using node 10.10.10.126:7000)
M: 6a85d385b2720fd463eccaf720dc12f495a1baa3 10.10.10.126:7000
   slots:10923-16383 (5461 slots) master
   1 additional replica(s)
S: afbe63bcf2f3418db48ea9a2749dd0b1bf24f0f3 10.10.10.126:7003
   slots: (0 slots) slave
   replicates 6a85d385b2720fd463eccaf720dc12f495a1baa3
S: 6fbc4a2a0239bc876bed4cf854846717d9543477 10.10.10.126:7004
   slots: (0 slots) slave
   replicates bbb2b1b060b440a56d07a16ee7f87f9379767d61
M: e7005711bc55315caaecbac2774f3c7d87a13c7a 10.10.10.126:7002
   slots:5462-10922 (5461 slots) master
   0 additional replica(s)
M: bbb2b1b060b440a56d07a16ee7f87f9379767d61 10.10.10.126:7001
   slots:0-5461 (5462 slots) master
   1 additional replica(s)
[OK] All nodes agree about slots configuration.
>>> Check for open slots...
>>> Check slots coverage...
[OK] All 16384 slots covered.
>>> Send CLUSTER MEET to node 10.10.10.126:7005 to make it join the cluster.
Waiting for the cluster to join.
>>> Configure node as replica of 10.10.10.126:7002.
[OK] New node added correctly.
[root@test1 bin]# 
看集群节点信息情况：

127.0.0.1:7000>  cluster nodes
afbe63bcf2f3418db48ea9a2749dd0b1bf24f0f3 10.10.10.126:7003 slave 6a85d385b2720fd463eccaf720dc12f495a1baa3 0 1461388245893 4 connected
6fbc4a2a0239bc876bed4cf854846717d9543477 10.10.10.126:7004 slave bbb2b1b060b440a56d07a16ee7f87f9379767d61 0 1461388247693 5 connected
e7005711bc55315caaecbac2774f3c7d87a13c7a 10.10.10.126:7002 master - 0 1461388246893 6 connected 5462-10922
6a85d385b2720fd463eccaf720dc12f495a1baa3 10.10.10.126:7000 myself,master - 0 0 4 connected 10923-16383
bbb2b1b060b440a56d07a16ee7f87f9379767d61 10.10.10.126:7001 master - 0 1461388247893 5 connected 0-5461
356df8094ad9906911d2ab6313cdc882a495b4eb 10.10.10.126:7005 slave e7005711bc55315caaecbac2774f3c7d87a13c7a 0 1461388246493 6 connected
127.0.0.1:7000> 

8）**验证数据的完整性**

从7.3）中，也可以看出集群目前是3主3从，slots分配正常，集群状态OK

127.0.0.1:7000> cluster info
cluster_state:ok
cluster_slots_assigned:16384
cluster_slots_ok:16384
cluster_slots_pfail:0
cluster_slots_fail:0
cluster_known_nodes:6
cluster_size:3
cluster_current_epoch:6
cluster_my_epoch:4
cluster_stats_messages_sent:18863
cluster_stats_messages_received:18863
127.0.0.1:7000> 



验证key的数量，我们把A，B，C节点上的key的数量加起来的总量和我们单实例上的数量比照一下。

[root@test1 redis-cluster]# redis-cli -c -p 7000 dbsize
(integer) 1720056
[root@test1 redis-cluster]# redis-cli -c -p 7001 dbsize
(integer) 1720529
[root@test1 redis-cluster]# redis-cli -c -p 7002 dbsize
(integer) 1720117
[root@test1 redis-cluster]# 

1720056+1720529+1720117=**5160702**

可以看出集群中key的总数量和单实例中数量完全一致。

提醒：Redis在创建集群的时候，各节点的数据必须是空的。