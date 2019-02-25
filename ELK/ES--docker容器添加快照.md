#### ES--docker容器添加快照

##### 1、搭建nfs服务

选用其中一台服务器搭建nfs服务，用来做数据同步

###### 在服务端

```shell
yum install nfs-utils nfs-utils-lib
# 设置nfs相关服务在操作系统启动时启动
systemctl enable rpcbind
systemctl enable nfs-server
systemctl enable nfs-lock
systemctl enable nfs-idmap

# 启动nfs服务
systemctl start rpcbind
systemctl start nfs-server
systemctl start nfs-lock
systemctl start nfs-idmap
```

服务器端设置NFS卷输出，即编辑 `/etc/exports` 添加：

```
/data    172.17.14.0/24(rw,sync,no_root_squash,no_subtree_check)

/data – 共享目录
172.17.14.0/24 – 允许访问NFS的客户端IP地址段
rw – 允许对共享目录进行读写
sync – 实时同步共享目录
no_root_squash – 允许root访问
no_all_squash - 允许用户授权
no_subtree_check - 如果卷的一部分被输出，从客户端发出请求文件的一个常规的调用子目录检查验证卷的相应部分。如果是整个卷输出，禁止这个检查可以加速传输。
```

###### 在客户端

每台elasticsearch的机器都需要操作

```
yum install nfs-utils

mount -t nfs  172.17.14.12:/data /data

# 开机启动挂载nfs目录，配置 /etc/fstab 添加以下内容
172.17.14.12:/data    /data  nfs auto,rw,vers=3,hard,intr,tcp,rsize=32768,wsize=32768      0   0
```



##### 2、修改elasticsearch配置文件，添加相对应目录并授权

编辑配置文件`vi elasticsearch.yml`

```
path.repo: ["/opt/backup"]
```

在主机中添加对应的目录，挂载到容器的`/opt/backup`目录，需要重新生成容器

进入容器内，将`/opt/backup`赋权给elasticsearch用户

```
chown -R elasticsearch:elasticsearch /opt/backup
```



##### 3、添加快照

```
# 访问URL，查看有没有快照仓库
http://172.16.15.135:9200/_snapshot/
```

###### 新建快照仓库

```
curl -XPUT 'http://172.16.15.140:9200/_snapshot/backup' -H 'Content-Type: application/json' -d '{"type": "fs","settings": {"location": "/opt/backup","compress": true}'
```

###### 查询快照仓库

```
# 查看所有仓库
curl http://172.16.15.135:9200/_snapshot/
# 返回如下
{"my_backup":{"type":"fs","settings":{"location":"/opt/backup"}}}

# 查看my_backup仓库的快照
curl http://172.16.15.135:9200/_snapshot/my_backup/_all
```

###### 新建快照备份

```
curl -XPUT 'http://172.16.15.140:9200/_snapshot/my_backup/backup20190115?wait_for_completion=true'
```

###### 查询快照备份进度

```
curl -XGET 'http://172.16.15.140:9200/_snapshot/my_backup/backup20190115/_status'
```

###### 删除快照

```
curl -XDELETE 'http://172.16.15.140:9200/_snapshot/my_backup/backup20190115'
```

###### 删除快照仓库

```
curl -XDELETE 'http://172.16.15.140:9200/_snapshot/backup'
```



##### 4、恢复快照数据

###### 恢复所有索引，需删除所有同名索引

```
curl -XPOST 'http://172.16.15.140:9200/_snapshot/my_backup/backup20190115/_restore?wait_for_completion=true'
```

###### 恢复指定索引快照，可不删除现有索引

```
curl -XPOST 'http://172.16.15.140:9200/_snapshot/my_backup/backup20190115?wait_for_completion=true' -H 'Content-Type: application/json' -d '{"indices": "index_1","ignore_unavailable": true,"include_global_state":false,"rename_pattern": "index_(.+)","rename_replacement": "restored_index_$1"}'

"indices": "index_1"			# 只恢复 index_1 索引，忽略快照中存在的其余索引。
"rename_pattern": "index_(.+)",		# 查找所提供的模式能匹配上的正在恢复的索引
"rename_replacement": "restored_index_$1"		# 然后把它们重命名成替代的模式。
```

###### 查看索引恢复状态

```
curl -XGET 'http://172.16.15.140:9200/restored_index_3/_recovery'
```

###### 取消一个恢复

```
curl -XDELETE 'http://172.16.15.140:9200/restored_index_3'
# 这个删除命令会停止恢复，同时删除所有已经恢复到集群里的数据。
```





