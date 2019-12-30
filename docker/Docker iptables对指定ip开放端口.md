# Docker防火墙对指定ip开放端口

```shell
# 查询当前策略
iptables -L -n
......
Chain DOCKER-USER (1 references)
target     prot opt source               destination         
RETURN     all  --  anywhere             anywhere            
......

# 删除当前策略
iptables -D DOCKER-USER 1
	数字1代表行号
	
# 允许192.168.1.249访问本机3307
iptables -A DOCKER-USER -s 192.168.1.249 -p tcp --dport 3307 -j ACCEPT

# 拒绝其他所有机器访问本机3307
iptables -A DOCKER-USER -p tcp --dport 3307 -j DROP
iptables -A DOCKER-USER -j RETURN

# 保存防火墙策略
iptables-save
```

