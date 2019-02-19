#### CEPH退役osd节点

##### 调整osd的crush weight

```
ceph osd crush reweight osd.0 0.1
```

说明：这个地方如果想慢慢的调整就分几次将crush 的weight 减低到0 ，这个过程实际上是让数据不分布在这个节点上，让数据慢慢的分布到其他节点上，直到最终为没有分布在这个osd，并且迁移完成。
这个地方不光调整了osd 的crush weight ，实际上同时调整了host 的 weight ，这样会调整集群的整体的crush 分布，在osd 的crush 为0 后， 再对这个osd的任何删除相关操作都不会影响到集群的数据的分布。



##### 停止osd进程

```
/etc/init.d/ceph stop osd.0
```

停止到osd的进程，这个是通知集群这个osd进程不在了，不提供服务了，因为本身没权重，就不会影响到整体的分布，也就没有迁移。



##### 将节点状态标记为out

```
ceph osd out osd.0
```

停止到osd的进程，这个是通知集群这个osd不再映射数据了，不提供服务了，因为本身没权重，就不会影响到整体的分布，也就没有迁移。



##### 从crush中移除节点

```
ceph osd crush remove osd.0
```

这个是从crush中删除，因为已经是0了 所以没影响主机的权重，也就没有迁移了。



##### 删除节点

```
ceph osd rm osd.0
```

这个是从集群里面删除这个节点的记录。



##### 删除节点认证（不删除编号会占住）

```
ceph auth del osd.0
```

这个是从认证当中去删除这个节点的信息

