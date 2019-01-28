#### CEPH添加删除监视器

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
ceph-deploy --overwrite-conf config push admin-node node1 node2 node3 node112
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

