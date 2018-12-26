mysql慢查询日志文件

```shell
#!/bin/bash
slowlog=/mydata/data/slow.log
mv $slowlog /mydata/slowlog/slow.`date +%Y%m%d%H`.log
mysqladmin -uroot -pzabbix2017 --socket=/tmp/mysql.sock flush-logs
find /mydata/slowlog/slow.*.log -type f -mtime +5 -exec rm {} \; > /dev/null 2>&1
```

