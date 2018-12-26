##### cockroach部署

利用docker部署cockroach

```
docker pull cockroachdb/cockroach:v2.0.0
docker run -d --name cockroach --net host --mount type=bind,source=/root/springcloud/cockroach/node/n4/node4,target=/cockroach/cockroach-data --mount type=bind,source=/etc/localtime,target=/etc/localtime cockroachdb/cockroach:v2.0.0 start --insecure --host=172.18.44.81 --port=26257 --http-port=8080 --cache=5% --max-sql-memory=10% --store=node4 --join=172.18.44.120:26257
```

参数解释

```
start --insecure --host=172.18.44.81 --port=26257 --http-port=8080 --cache=5% --max-sql-memory=10% --store=node4
--store				指定存储位置
--http-port			指定web端口
--insecure --host	多集群部署时需要添加
--port				端口
--cache				缓存大小
--max-sql-memory	
--join				加入的集群某台机器IP
```

