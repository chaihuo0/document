[TOC]



##### ceph介绍

```
1、ceph共3台机器（172.17.14.111、172.17.14.113、172.17.14.121），osd3个，mon3个，对外都是ceph-radosgw@radosgw.gateway.service服务（172.17.14.111:80）对ceph集群进行操作。

2、ceph正常运行状态，所有PG都是active+clean状态，可用ceph -s命令查看

3、ceph-deploy目录在172.17.14.111:/my-cluster

```



##### ceph命令

###### 启动命令

```shell
# 启动所有ceph服务
systemctl start ceph.target

# 启动ceph-osd服务
systemctl start ceph-osd.target

# 启动前端服务（所有ceph请求都通过这个服务，在172.17.14.111上）
systemctl start ceph-radosgw@radosgw.gateway.service

# 查看ceph所有服务
systemctl -l | grep ceph
```

###### ceph操作命令

```shell 
# 查看ceph集群状态，如health显示HEALTH_OK,代表集群没有出现问题，显示HEALTH_WARN或HEALTH_ERR请检查ceph日志
ceph -s
ceph health detail

# 查看ceph日志
ceph -w

# 查看ceph-osd状态
ceph osd tree
ceph osd stat

# 查看ceph-mon状态
ceph mon stat

ceph osd set noout ： ceph stopping w/out rebalancing
ceph osd unset noout ： 解除ceph stopping w/out rebalancing
ceph osd set nodown ： ceph osd scrub的时候有thread timeout，可设置此参数
```



##### 增加OSD

1、登入 `ceph-deploy` 工具所在的 Ceph admin 节点，进入工作目录。

```
ssh {ceph-deploy-node}
cd /path/ceph-deploy-work-path
```

2、列举磁盘。

执行下列命令列举一节点上的磁盘：

```
ceph-deploy disk list {node-name [node-name]...}
```

3、格式化磁盘。

用下列命令格式化（删除分区表）磁盘，以用于 Ceph ：

```
ceph-deploy disk zap {osd-server-name}:{disk-name}
ceph-deploy disk zap osdserver1:sdb
```

**重要：** 这会删除磁盘上的所有数据。

4、准备 OSD。

```
ceph-deploy osd prepare {node-name}:{data-disk}[:{journal-disk}]
ceph-deploy osd prepare osdserver1:sdb:/dev/ssd
ceph-deploy osd prepare osdserver1:sdc:/dev/ssd
```

`prepare` 命令只准备 OSD 。在大多数操作系统中，硬盘分区创建后，不用 `activate` 命令也会自动执行 `activate` 阶段（通过 Ceph 的 `udev` 规则）。

前例假定一个硬盘只会用于一个 OSD 守护进程，以及一个到 SSD 日志分区的路径。我们建议把日志存储于另外的驱动器以最优化性能；你也可以指定一单独的驱动器用于日志（也许比较昂贵）、或者把日志放到 OSD 数据盘（不建议，因为它有损性能）。前例中我们把日志存储于分好区的固态硬盘。

**注意：** 在一个节点运行多个 OSD 守护进程、且多个 OSD 守护进程共享一个日志分区时，你应该考虑整个节点的最小 CRUSH 故障域，因为如果这个 SSD 坏了，所有用其做日志的 OSD 守护进程也会失效。

5、准备好 OSD 后，可以用下列命令激活它。

```
ceph-deploy osd activate {node-name}:{data-disk-partition}[:{journal-disk-partition}]
ceph-deploy osd activate osdserver1:/dev/sdb1:/dev/ssd1
ceph-deploy osd activate osdserver1:/dev/sdc1:/dev/ssd2
```

`activate` 命令会让 OSD 进入 `up` 且 `in` 状态。该命令使用的分区路径是前面 `prepare` 命令创建的。



##### 删除OSD

要想缩减集群尺寸或替换硬件，可在运行时删除 OSD 。在 Ceph 里，一个 OSD 通常是一台主机上的一个 `ceph-osd` 守护进程、它运行在一个硬盘之上。如果一台主机上有多个数据盘，你得逐个删除其对应 `ceph-osd` 。通常，操作前应该检查集群容量，看是否快达到上限了，确保删除 OSD 后不会使集群达到 `near full` 比率。

**警告：** 删除 OSD 时不要让集群达到 `full ratio` 值，删除 OSD 可能导致集群达到或超过 `full ratio`值。

1、停止需要剔除的 OSD 进程，让其他的 OSD 知道这个 OSD 不提供服务了。停止 OSD 后，状态变为 `down` 。

```
ssh {osd-host}
sudo stop ceph-osd id={osd-num}
```

2、将 OSD 标记为 `out` 状态，这个一步是告诉 mon，这个 OSD 已经不能服务了，需要在其他的 OSD 上进行数据的均衡和恢复了。

```
ceph osd out {osd-num}
```

执行完这一步后，会触发数据的恢复过程。此时应该等待数据恢复结束，集群恢复到 `HEALTH_OK` 状态，再进行下一步操作。

3、删除 CRUSH Map 中的对应 OSD 条目，它就不再接收数据了。你也可以反编译 CRUSH Map、删除 device 列表条目、删除对应的 host 桶条目或删除 host 桶（如果它在 CRUSH Map 里，而且你想删除主机），重编译 CRUSH Map 并应用它。详情参见本手册第一部分 [9. 修改 Crushmap](https://lihaijing.gitbooks.io/ceph-handbook/Operation/modify_crushmap.md) 。

```
ceph osd crush remove {name}
```

该步骤会触发数据的重新分布。等待数据重新分布结束，整个集群会恢复到 `HEALTH_OK` 状态。

4、删除 OSD 认证密钥：

```
ceph auth del osd.{osd-num}
```

5、删除 OSD 。

```
ceph osd rm {osd-num}
#for example
ceph osd rm 1
```

6、卸载 OSD 的挂载点。

```
sudo umount /var/lib/ceph/osd/$cluster-{osd-num}
```

7、登录到保存 `ceph.conf` 主拷贝的主机。

```
ssh {admin-host}
cd /etc/ceph
vim ceph.conf
```

8、从 `ceph.conf` 配置文件里删除对应条目。

```
[osd.1]
        host = {hostname}
```

9、从保存 `ceph.conf` 主拷贝的主机，把更新过的 `ceph.conf` 拷贝到集群其他主机的 `/etc/ceph` 目录下。

如果在 `ceph.conf` 中没有定义各 OSD 入口，就不必执行第 7 ~ 9 步。



##### ceph添加监视器

###### 到admin-node节点，进入`/my-cluster`目录

需要在`ceph.conf`文件中添加`publish network`，修改`mon_initial_members`和`mon_host`

```
publish network = 172.17.14.0/24
mon_initial_members = admin-node,node1,node2,node112
mon_host = 172.17.14.111,172.17.14.113,172.17.14.121,172.17.14.112
```

将修改后的文件推动到所有节点

```
ceph-deploy --overwrite-conf config push admin-node node1 node2 node3 node1112
```

执行下面命令，如之前执行过需要将对应节点的`/var/lib/ceph/mon/ceph-node112/`里所有文件清空

```
cd /my-cluster
ceph-deploy mon create node112				# node112为主机名
ceph mon_status -f json-pretty				# 查看mon节点状态
```



##### ceph删除监视器

###### 到admin-node节点，进入`/my-cluster`目录

```
cd /my-cluster
ceph-deploy mon destroy node112				# node112为主机名
ceph mon_status -f json-pretty				# 查看mon节点状态
```

删除后修改`ceph.conf`文件

```
mon_initial_members = admin-node,node1,node112
mon_host = 172.17.14.111,172.17.14.113,172.17.14.112
```



##### 修改集群配置

启动 Ceph 存储集群时，各守护进程都从同一个配置文件（即默认的 `ceph.conf` ）里查找它自己的配置。`ceph.conf` 中可配置参数很多，有时我们需要根据实际环境对某些参数进行修改。

修改的方式分为两种：直接修改 `ceph.conf` 配置文件中的参数值，修改完后需要重启 Ceph 进程才能生效。或在运行中动态地进行参数调整，无需重启进程。

如果你的 Ceph 存储集群在运行，而你想看一个在运行进程的配置，用下面的命令：

```
ceph daemon {daemon-type}.{id} config show | less
```

如果你现在位于 osd.0 所在的主机，命令将是：

```
ceph daemon osd.0 config show | less
```



Ceph 配置文件可用于配置存储集群内的所有守护进程、或者某一类型的所有守护进程。要配置一系列守护进程，这些配置必须位于能收到配置的段落之下，比如：

###### **[global]**

描述： `[global]` 下的配置影响 Ceph 集群里的所有守护进程。
实例： `auth supported = cephx`

###### **[osd]**

描述： `[osd]` 下的配置影响存储集群里的所有 `ceph-osd` 进程，并且会覆盖 `[global]` 下的同一选项。
实例： `osd journal size = 1000`

###### **[mon]**

描述： `[mon]` 下的配置影响集群里的所有 `ceph-mon` 进程，并且会覆盖 `[global]` 下的同一选项。
实例： `mon addr = 10.0.0.101:6789`

###### **[mds]**

描述： `[mds]` 下的配置影响集群里的所有 `ceph-mds` 进程，并且会覆盖 `[global]` 下的同一选项。
实例： `host = myserver01`

###### **[client]**

描述： `[client]` 下的配置影响所有客户端（如挂载的 Ceph 文件系统、挂载的块设备等等）。
实例： `log file = /var/log/ceph/radosgw.log`

全局设置影响集群内所有守护进程的例程，所以 `[global]` 可用于设置适用所有守护进程的选项。但可以用这些覆盖 `[global]` 设置：

1. 在 `[osd]` 、 `[mon]` 、 `[mds]` 下更改某一类进程的配置。
2. 更改特定进程的设置，如 `[osd.1]` 。

覆盖全局设置会影响所有子进程，明确剔除的例外。

###### 

Ceph 可以在运行时更改 `ceph-osd` 、 `ceph-mon` 、 `ceph-mds` 守护进程的配置，此功能在增加/降低日志输出、启用/禁用调试设置、甚至是运行时优化的时候非常有用。Ceph 集群提供两种方式的调整，使用 `tell` 的方式和 `daemon` 设置的方式。

###### tell 方式设置

下面是使用 tell 命令的修改方法：

```
ceph tell {daemon-type}.{id or *} injectargs --{name} {value} [--{name} {value}]
```

用 `osd` 、 `mon` 、 `mds` 中的一个替代 `{daemon-type}` ，你可以用星号（ `*` ）更改一类进程的所有实例配置、或者更改某一具体进程 ID （即数字或字母）的配置。例如提高名为 `osd.0` 的 `ceph-osd` 进程之调试级别的命令如下：

```
ceph tell osd.0 injectargs --debug-osd 20 --debug-ms 1
```

在 `ceph.conf` 文件里配置时用空格分隔关键词；但在命令行使用的时候要用下划线或连字符（ `_` 或 `-`）分隔，例如 `debug osd` 变成 `debug-osd` 。

###### daemon 方式设置

除了上面的 tell 的方式调整，还可以使用 daemon 的方式进行设置。

1、获取当前的参数

```
ceph daemon osd.1 config get mon_osd_full_ratio

{
"mon_osd_full_ratio": "0.98"
}
```

2、修改配置

```
ceph daemon osd.1 config set mon_osd_full_ratio 0.97

{
"success": "mon_osd_full_ratio = '0.97' "
}
```

3、检查配置

```
ceph daemon osd.1 config get mon_osd_full_ratio

{
"mon_osd_full_ratio": "0.97"
}
```

**注意：** 重启进程后配置会恢复到默认参数，在进行在线调整后，如果这个参数是后续是需要使用的，那么就需要将相关的参数写入到配置文件 `ceph.conf` 当中。

###### 两种设置方式的使用场景

使用 tell 的方式适合对整个集群进行设置，使用 `*` 号进行匹配，就可以对整个集群的角色进行设置。而出现节点异常无法设置时候，只会在命令行当中进行报错，不太便于查找。

使用 daemon 进行设置的方式就是一个个的去设置，这样可以比较好的反馈，此方法是需要在设置的角色所在的主机上进行设置。



##### ceph重复启动集群，引发问题

ceph重复启动集群，可能导致集群自锁，此时`ceph-radosgw.target`启动失败，需要解锁ceph集群

`ceph osd unset pause`



##### 监视器时间不同步现象

执行 `ceph -s `会出现下面现象，此时只需要将时间重新同步一次就可以。`ntpdate 172.17.14.52`

```
clock skew detected on mon.node1
Monitor clock skew detected
```





##### ceph常见问题

###### slow requests

```
查看ceph日志，/var/log/ceph/，可能引起的原因有
	1、硬盘空间，网络，osd、mon服务有无正常启动
	2、ceph内部进行scrub/deep_scrub（一致性检查），默认全天都在检查，可在线调整为每晚凌晨执行几小时。deep_scrub每周检查一次，比scrub更消耗磁盘。一致性检查时会锁住PG，此时有服务调用改PG，就会出现slow requests问题。相关参数可如下设置：
	osd_scrub_chunk_min = 1
	osd_scrub_chunk_max = 1
	osd_scrub_sleep = 3
	osd_scrub_begin_hour = 22
	osd_scrub_end_hour = 7

```



##### PG状态表

| 状态             | 描述                                                         |
| ---------------- | ------------------------------------------------------------ |
| Activating       | Peering已经完成，PG正在等待所有PG实例同步并固化Peering的结果(Info、Log等) |
| Active           | 活跃态。PG可以正常处理来自客户端的读写请求                   |
| Backfilling      | 正在后台填充态。 backfill是recovery的一种特殊场景，指peering完成后，如果基于当前权威日志无法对Up Set当中的某些PG实例实施增量同步(例如承载这些PG实例的OSD离线太久，或者是新的OSD加入集群导致的PG实例整体迁移) 则通过完全拷贝当前Primary所有对象的方式进行全量同步 |
| Backfill-toofull | 某个需要被Backfill的PG实例，其所在的OSD可用空间不足，Backfill流程当前被挂起 |
| Backfill-wait    | 等待Backfill 资源预留                                        |
| Clean            | 干净态。PG当前不存在待修复的对象， Acting Set和Up Set内容一致，并且大小等于存储池的副本数 |
| Creating         | PG正在被创建                                                 |
| Deep             | PG正在或者即将进行对象一致性扫描清洗                         |
| Degraded         | 降级状态。Peering完成后，PG检测到任意一个PG实例存在不一致(需要被同步/修复)的对象，或者当前ActingSet 小于存储池副本数 |
| Down             | Peering过程中，PG检测到某个不能被跳过的Interval中(例如该Interval期间，PG完成了Peering，并且成功切换至Active状态，从而有可能正常处理了来自客户端的读写请求),当前剩余在线的OSD不足以完成数据修复 |
| Incomplete       | Peering过程中， 由于 a. 无非选出权威日志 b. 通过choose_acting选出的Acting Set后续不足以完成数据修复，导致Peering无非正常完成 |
| Inconsistent     | 不一致态。集群清理和深度清理后检测到PG中的对象在副本存在不一致，例如对象的文件大小不一致或Recovery结束后一个对象的副本丢失 |
| Peered           | Peering已经完成，但是PG当前ActingSet规模小于存储池规定的最小副本数(min_size) |
| Peering          | 正在同步态。PG正在执行同步处理                               |
| Recovering       | 正在恢复态。集群正在执行迁移或同步对象和他们的副本           |
| Recovering-wait  | 等待Recovery资源预留                                         |
| Remapped         | 重新映射态。PG活动集任何的一个改变，数据发生从老活动集到新活动集的迁移。在迁移期间还是用老的活动集中的主OSD处理客户端请求，一旦迁移完成新活动集中的主OSD开始处理 |
| Repair           | PG在执行Scrub过程中，如果发现存在不一致的对象，并且能够修复，则自动进行修复状态 |
| Scrubbing        | PG正在或者即将进行对象一致性扫描                             |
| Unactive         | 非活跃态。PG不能处理读写请求                                 |
| Unclean          | 非干净态。PG不能从上一个失败中恢复                           |
| Stale            | 未刷新态。PG状态没有被任何OSD更新，这说明所有存储这个PG的OSD可能挂掉, 或者Mon没有检测到Primary统计信息(网络抖动) |
| Undersized       | PG当前Acting Set小于存储池副本数                             |

#### ceph添加osd节点

##### 1、修改主机名

```shell
hostnamectl set-hostname node1
```

##### 2、修改/etc/hosts文件

```
172.17.14.111	admin-node
172.17.14.113	node1
172.17.14.121	node2
172.17.14.160   node3
```

##### 3、关闭防火墙、seliux

##### 4、将admin-node的~/.ssh/id_rsa.pub添加到新增服务器

```shell
scp ~/.ssh/id_rsa.pub 172.17.14.160:~/.ssh/authorized_keys
ssh node3
chown -R root:root ~/.ssh
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys

测试
ssh node3
```

##### 5、切换国内yum源

```shell
删除所有repo源
rm -rf /etc/yum.repos.d/*.repo

wget -O /etc/yum.repos.d/CentOS-Base.repo http://mirrors.aliyun.com/repo/Centos-7.repo

wget -O /etc/yum.repos.d/epel.repo http://mirrors.aliyun.com/repo/epel-7.repo

```

###### `vi /etc/yum.repos.d/ceph.repo`

```
[ceph]
name=ceph
baseurl=http://mirrors.aliyun.com/ceph/rpm-jewel/el7/x86_64/
gpgcheck=0
[ceph-noarch]
name=cephnoarch
baseurl=http://mirrors.aliyun.com/ceph/rpm-jewel/el7/noarch/
gpgcheck=0
```

###### 执行`yum makecache`

##### 6、安装ceph`yum install ceph`

##### 7、创建osd文件夹

```
mkdir -p /var/local/osd3
```

##### 8、在admin-node上添加osd节点

```
cd /my-cluster
ceph-deploy admin node3
ceph-deploy osd prepare node3:/var/local/osd3
ceph-deploy osd activate node3:/var/local/osd3
```

##### 9、观察ceph日志，看数据是否同步