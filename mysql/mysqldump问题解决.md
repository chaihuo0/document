#### mysqldump备份问题解决

##### 在脚本中使用mysqldump时，直接输入密码，会出现如下警告

```shell
mysqldump: [Warning] Using a password on the command line interface can be insecure.
```

##### 解决办法1

修改/etc/my.cnf，在`client`模块中添加如下几行，重启MySQL服务

```
[client]
host =localhost
user =mysql_backup
password="123456"
```

备份命令如下

```shell
mysqldump --defaults-extra-file=/etc/my.cnf my_database | gzip > db_backup.tar.gz
```

##### 解决办法2（建议使用）

设置加密密码文件，会生成`~/.mylogin.cnf`文件

```shell
mysql_config_editor set --login-path=local --host=localhost --user=db_user --password
```

bash脚本`mysqldump`改用如下

```shell
mysqldump --login-path=local my_database | gzip > db_backup.tar.gz
```

##### 备份脚本

```shell
#!/bin/bash

DBS=(mysql omipay_riskmanage)
DB_DIR="/opt/mysql_backup/"
DATATIME=$(date "+%Y%m%d")

for db in "${DBS[@]}"
do
    if [ ! -d "${DB_DIR}/${DATATIME}" ];then
        mkdir ${DB_DIR}/${DATATIME}
    fi

    #mysqldump --login-path=backup --single-transaction --opt --skip-lock-tables --databases ${db} | gzip > ${DB_DIR}${DATATIME}/${db}.sql.gz
    mysqlpump --login-path=backup --single-transaction --databases ${db} | gzip > ${DB_DIR}${DATATIME}/${db}.sql.gz
done

# 自动删除15天之前数据
find /opt/mysql_backup/ -type d -mtime +15 -exec rm -rf {} \;

# mysqlpump是mysql5.7版本新增的备份工具。
```

