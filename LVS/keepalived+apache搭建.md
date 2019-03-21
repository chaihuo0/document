#### keepalived+apache搭建

##### 下载`keepalived`

```
yum install keepalived
```

##### 编辑`/etc/keepalived/keepalived.conf`

```
bal_defs {
    router_id LVS_1  # 设置lvs的id，在一个网络内应该是唯一的
}

vrrp_instance VI_1 {	# 实例1
    state MASTER		# 角色 master
    interface em1		# 网卡
    virtual_router_id 51	# id，具有唯一性
    priority 100
    advert_int 1
    authentication {
        auth_type PASS
        auth_pass 1111
    }
    virtual_ipaddress {
        14.18.189.161		# 在em1网卡上虚拟的ip地址，可以添加多个，每行一个IP
    }
}

vrrp_instance VI_2 {	#--实例2
    state MASTER
    interface em2			#--第二个服务网卡，也是我的内网
    lvs_sync_daemon_interface em2	#--第二个心跳网卡
    virtual_router_id 52		#--换一个router_id
    priority 100
    advert_int 1
    authentication {
        auth_type PASS
        auth_pass 1111
    }
    virtual_ipaddress {	
        172.17.14.161	# 这样写就实现了14.18.189.161这个VIP在em1，172.17.14.161这个VIP在em2
    }
}


virtual_server 172.17.14.161 80 {
    delay_loop 6	# 轮训检查real_server是否活着，6秒一次
    lb_algo wlc		# 使用wlc调度算法
    lb_kind DR		# DR模式
    nat_mask 255.255.255.0		# 子网掩码，同一个子网掩码的ip访问同一个real_server，默认子网掩码为255.255.255.255
    persistence_timeout 7300		# 在7300秒之后，客户端没有重复连接相同地址，重新分发连接，7300秒之内有过连接，重新计时7300秒。如没有session会话机制，可调整为60
    protocol TCP


    real_server 172.17.14.71 80 {		# 真实IP地址和端口
        weight 1			# 权重
        TCP_CHECK {			# TCP 检查
            connect_timeout 3		# 超时3秒
            nb_get_retry 3			# 故障重试秒数
            delay_before_retry 3	# 重试延迟
            connect_port 80			# 端口
        }
    }

    real_server 172.17.14.73 80 {
        weight 1
        TCP_CHECK {
            connect_timeout 3
            nb_get_retry 3
            delay_before_retry 3
            connect_port 80
        }
    }
}
```

##### 启动`keepalived`

```
systemctl start keepalived

ip a   # 查看IP是否添加成功
```

##### 在`172.17.14.71`上添加`realserver`文件，一般放到`/etc/init.d/`下

```
#!/bin/bash
VIP=172.17.14.161
function start() {
    ifconfig lo:0 $VIP netmask 255.255.255.255 broadcast $VIP
    echo 1 >/proc/sys/net/ipv4/conf/lo/arp_ignore
    echo 2 >/proc/sys/net/ipv4/conf/lo/arp_announce
    echo 1 >/proc/sys/net/ipv4/conf/all/arp_ignore
    echo 2 >/proc/sys/net/ipv4/conf/all/arp_announce
    echo “Real Server $(uname -n) started”
}
function stop() {
    ifconfig lo:0 down
    ifconfig lo:0 $VIP netmask 255.255.255.255 broadcast $VIP
    echo 0 >/proc/sys/net/ipv4/conf/lo/arp_ignore
    echo 0 >/proc/sys/net/ipv4/conf/lo/arp_announce
    echo 0 >/proc/sys/net/ipv4/conf/all/arp_ignore
    echo 0 >/proc/sys/net/ipv4/conf/all/arp_announce
    echo “Real Server $(uname -n) stopped”
}
case $1 in
    start)
        start
    ;;
    stop)
        stop
    ;;
    *)
        echo “Usage: $0 {start|stop}”
        exit 1
esac
```

##### 启动`realserver`

```
/etc/init.d/realserver start

ip a    # 查看lo网卡是否有VIP
```

##### 下载`apache`

```
yum install httpd
```

##### 修改`/etc/httpd/conf/httpd.conf`，将`VirtualHost`的IP都换成VIP

```
sed -i 's/172.17.14.71/172.17.14.161/g' /etc/httpd/conf/httpd.conf
sed -i 's/172.17.14.71/172.17.14.161/g' /etc/httpd/conf.d/ssl.conf	# 文件位置自己查找

例如：
<VirtualHost 172.17.14.161>
  DocumentRoot /var/tgw/investment
  ServerName tg.tgw99.cn
  ErrorLog logs/tg.tgw99.cn_error_log
  CustomLog logs/tg.tgw99.cn_access_log common
  <Directory "/var/tgw/investment">
    Options FollowSymLinks
    AllowOverride All
    Order allow,deny
    Allow from all
  </Directory>
</VirtualHost>
```

##### 重新启动`httpd`

```
systemctl restart httpd
```

##### 测试访问网址