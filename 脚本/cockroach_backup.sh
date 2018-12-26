#!/bin/bash

mydate = $(date -d "yesterday" +"%Y%m%d")
cockroach dump oauthcenter --host=172.17.14.150 -p 26257 --certs-dir=/fintech/data/certs/certs --user=root > /backup/oauthcenter${mydate}.sql
cd /backup/
tar -zcf oauthcenter${mydate}.tar.gz oauthcenter${mydate}.sql
rm -rf oauthcenter${mydate}.sql
find /backup/ -type f -mtime +10 -exec  rm -rf {} \;