#### centos7搭建vsftpd

##### 安装必要包

```
yum -y install vsftpd
yum install -y db4 db4-utils	# 将明文密码加密
```

##### vsftpd主要文件

```
/etc/rc.d/init.d/vsftpd  	# 启动脚本
/etc/vsftpd/vsftpd.conf  	# 主配置文件
/etc/pam.d/vsftpd      		# PAM认证文件
/etc/vsftpd/ftpusers     	# 禁止使用vsftpd用户列表文件
/etc/vsftpd/user_list     	# 如vsftpd.conf的userlist_deny=NO则次文件为可以允许登录用户文件，反之不允许登录文件
/etc/vsftpd/chroot_list   	# 不能离开主目录的用户列表
/var/ftp               		# 匿名用户主目录
/var/ftp/pub        		# 匿名用户的下载目录
```

##### 修改主配置文件`/etc/vsftpd/vsftpd.conf`

```
anonymous_enable=NO							# 不允许匿名登录
local_enable=YES							# 设定本地用户可以访问，设置为NO，虚拟用户不能访问
write_enable=YES							# 写权限
local_umask=022								# 本地用户新建文件权限
dirmessage_enable=YES						# 进入目录时可以显示一些设定的信息
xferlog_enable=YES							# 开启上传下载日志
connect_from_port_20=YES					# 是否开启主动模式，主动连接的端口号
xferlog_std_format=YES						# 日志格式
listen=YES
listen_ipv6=YES								# 是否支持ipv6
pam_service_name=vsftpd						# pam认证文件名称
userlist_enable=YES							# 在/etc/vsftpd/user_list中的用户将不得使用FTP
tcp_wrappers=YES

ascii_upload_enable=YES						# 设定支持ASCII模式的上传和下载功能
ascii_download_enable=YES

chroot_local_user=YES						# 启用chroot_list文件设置
chroot_list_enable=YES						# 锁定用户目录
chroot_list_file=/etc/vsftpd/chroot_list	# 文件中添加的用户不能离开主目录
allow_writeable_chroot=YES					# 需添加这行，不添加可能虚拟用户目录权限失效
virtual_use_local_privs=YES					# 虚拟用户的权限符合他们的宿主用户
guest_enable=YES							# 开启虚拟用户功能
guest_username=ftpuser						# 虚拟用户依赖的系统用户
user_config_dir=/etc/vsftpd/vuser_conf		# 虚拟用户配置文件目录

pasv_enable=YES								# 是否开启被动模式，建议开启被动，关闭主动
pasv_min_port=40000  						# 最小端口号
pasv_max_port=40100  						# 最大端口号
pasv_promiscuous=YES

idle_session_timeout=600					# 用户会话空闲后10分钟
data_connection_timeout=120					# 将数据连接空闲2分钟断
max_clients=10								# 最大客户端连接数
max_per_ip=5								# 每个ip最大连接数
local_max_rate=0							# 限制上传速率，0为无限制
```

##### 修改虚拟用户文件`/etc/vsftpd/vuser_conf/test`，文件名需要和虚拟用户名称一致

```
local_root=/www/test			# 用户登录后的目录
write_enable=YES							# 开放写权限
anon_umask=022								# 子网掩码（777-022=755）
anon_world_readable_only=NO					# 显示文件目录
anon_upload_enable=YES						# 上传
anon_mkdir_write_enable=YES					# 创建文件权限
anon_other_write_enable=YES					# 删除和重命名文件
```

##### 新建虚拟账号及添加密码文件

```
# 新建虚拟帐号，单行为帐号，双行为密码
vi /etc/vsftpd/vuser_passwd.tx
	test
	111111

# 生成加密文件
db_load -T -t hash -f /etc/vsftpd/vuser_passwd.txt /etc/vsftpd/vuser_passwd.db
```

##### 修改pam认证文件`/etc/pam.d/vsftpd`

```
# 将所有的先注释掉
64位系统添加如下
auth required /lib64/security/pam_userdb.so db=/etc/vsftpd/vuser_passwd
account required /lib64/security/pam_userdb.so db=/etc/vsftpd/vuser_passwd

32位系统
auth sufficient /lib/security/pam_userdb.so db=/etc/vsftpd/vuser_passwd
account sufficient /lib/security/pam_userdb.so db=/etc/vsftpd/vuser_passwd
```

##### 新建系统用户

```
# 用户家目录最好和数据目录一致
useradd -g root -M -d /www -s /sbin/nologin ftpuser

# centos7中，需要删除目录的写权限
chmod -w /www

# 修改目录所属
chown -R ftpuser:root /www
```

##### 开启vsftpd服务

```
systemctl start vsftpd.service
systemctl enable vsftpd.service
```

