#### CEPH-OSD状态flags



| Flag         | 说明                                                         |
| ------------ | ------------------------------------------------------------ |
| full         | 使集群到达设置的full_ratio值。会导致集群阻止写入操作         |
| pause        | 集群将会阻止读写操作，但不会影响集群的in、out、up或down状态。集群扔保持正常运行,就是客户端无法读写 |
| noup         | 防止osd进入up状态.一般和nodown对应使用,标记osd进程未启动     |
| nodown       | 防止osd进入down状态。无论osd是否真的down，都显示up的状态。如果我们确认osd进程是活跃状态，可以做nodown设置，避免达到间隔时间，导致osd被标记为down，然后导致数据迁移。切记服务正常后，勿忘取消该flag |
| noout        | 防止osd进入out状态。mon默认设置(mon_osd_down_out_interval),300秒后自动将down状态的OSD标记为out，一旦osd状态为out，那数据就会开始迁移。因此，建议在处理故障期间设置该标记，避免数据迁移。noout标记后，如果osd down了，该osd的主pg会飘到副本osd上 |
| noin         | 防止osd纳入ceph集群。有时候我们新加入OSD，并不想立马加入集群，可以设置该选项。一般和noout对应使用 |
| nobackfill   | 防止集群进行数据回填操作。ceph集群故障会出发backfill操作。如果临时的设置osd或者节点为down状态(如升级daemons),为了防止因为osd的down导致数据回填，可以设置nobackfill |
| norebalance  | 防止数据均衡操作。ceph集群在扩容时会出发rebalance操作。通常和nobackfill、norecover一起使用，用于防止数据发生恢复迁移等操作。切记操作完成取消该flag设置 |
| norecover    | 切记操作完成取消该flag设置                                   |
| noscrub      | 防止集群做清洗操作。在高负载、recovery, backfilling, rebalancing等期间，为了保证集群的稳定，可以做该设置和nodeep-scrub。切记完成后清除该flag |
| nodeep-scrub | 防止集群进行深度清洗操作。因为深度清洗会阻塞读写操作，影响性能，会被用户感知，所以有时候会做该设置。但通常不要做该设置。因为长时间坐该设置，一旦取消该设置，则会有大量的pg进行深度清洗，整个集群将不可用，切记。 |
| notieragent  | 集群将停止tier引擎查找 冷/脏 对象下刷到后端存储层            |

##### 设置命令

```
ceph osd set noscrub
ceph osd unset noscrub
```

