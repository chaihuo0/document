#### centos添加静态路由

##### **1、显示路由表** 

```
[root@centos7 tmp]# ip route show|column -t
default           via  192.168.150.254  dev    enp0s3  proto  static  metric  1024
192.168.150.0/24  dev  enp0s3           proto  kernel  scope  link    src     192.168.150.110
```

##### **2、添加静态路由** 

```
[root@centos7 ~]# ip route add 10.15.150.0/24 via 192.168.150.253 dev enp0s3
```

##### 3、**删除静态路由** 

```
[root@centos7 ~]# ip route del 10.15.150.0/24
```

**二、设置永久的静态路由** 

##### **1、添加永久静态路由** 

```
[root@centos7 ~]# vi /etc/sysconfig/network-scripts/route-enp0s3
10.15.150.0/24 via 192.168.150.253 dev enp0s3
10.25.250.0/24 via 192.168.150.253 dev enp0s3
```

###### 重启计算机，或者重新启用设备enp0s3才能生效。 

##### **2、清除永久静态路由** 

```
可以删除 ifcfg-enp0s3文件或者注释掉文件里的相应静态路由条目，重启计算机。
想要让修改后的静态路由立即生效，只能用 ip route del 手工删除静态路由条目。
```

