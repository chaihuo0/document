#### 搭建shadowsocks

##### 1、检查Python版本

```
python –version

CentOS6.5默认安装的Python版本是2.6.6，返回值为：Python 2.6.6
```

##### 2、安装setuptools

```
yum install -y python-setuptools
```

##### 3、安装万能源

```
yum install epel-release -y
```

##### 4、安装pip

```
yum install python-pip -y
```

##### 5、安装shadowsocks

```
pip install shadowsocks
```

##### 6、Shadowsocks的配置和使用

```
vi /root/shadowsocks.json

{
	"server":"自己服务器IP地址",
	"server_port":8388,
	"local_address": "127.0.0.1",
	"local_port":1080,
	"password":"密码",
	"timeout":3000,
	"method":"aes-256-cfb",
	"fast_open": false,
	"workers": 1
}
```

##### 7、启动命令

```
# 启动
ssserver -c /root/shadowsocks.json --user nobody -d start
# 停止
ssserver -c /root/shadowsocks.json --user nobody -d stop	
# 重启
ssserver -c /root/shadowsocks.json --user nobody -d restart	
```

##### 8、设置开机自启

```
vi /root/rc.local 在最后添加一行

ssserver -c /root/shadowsocks.json --user nobody -d start
```

