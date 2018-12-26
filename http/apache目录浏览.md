##### apache目录浏览

###### 下载httpd	yum install httpd -y

编辑配置文件/etc/httpd/conf/httpd.conf，添加

```
LoadModule autoindex_module modules/mod_autoindex.so
LoadModule dir_module modules/mod_dir.so
```

修改

```
DocumentRoot "/data/httpd"
<Directory "/data/httpd">
    Options Indexes FollowSymLinks ExecCGI
    IndexOptions NameWidth=25 Charset=UTF-8
    AllowOverride None
    Require all granted
</Directory>
```

编辑配置文件/etc/httpd/conf.d/welcome.conf，修改

```
Options -Indexes	更改为 Options +Indexes
```



##### 注意

Apache2.*版本后弃用如下配置

```
Order allow,deny
Allow from all
```

应改为

```
Require all granted
```

