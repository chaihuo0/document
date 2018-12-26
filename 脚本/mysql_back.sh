#!/bin/bash

mydate=`date -d "yesterday" +"%Y%m%d"`
docker exec -it mysql_containers /usr/bin/mysqldump -uroot -p'1111'  --all-databases  --hex-blob  --force --flush-logs --routines --log-error=/mysql/err${mydate}.log > /mysql/db${mydate}.sql
cd /tgwdb/backup/mysql/
tar -zcf db${mydate}.tar.gz db${mydate}.sql
rm -rf /tgwdb/backup/mysql/db${mydate}.sql
find /tgwdb/backup/mysql/ -type f -mtime +10 -exec  rm -rf {} \;
