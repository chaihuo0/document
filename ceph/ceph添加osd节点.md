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