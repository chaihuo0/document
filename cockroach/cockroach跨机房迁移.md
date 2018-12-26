##### cockroach跨机房迁移

1. 集群都用主机名访问
2. 集群不绑定内网端口
3. 集群都用主机名通信



查看cockroach证书

`docker exec -it roach ./cockroach cert list --certs-dir=/cockroach/certs`或访问`https://172.17.14.148:8088/#/reports/certificates/local`

如需要添加其他证书，需要重新生成节点证书

```shell
docker exec -it cocoroach ./cockroach cert create-node 172.17.14.145 172.17.14.146 172.17.14.147 172.17.14.148 172.17.14.150 node1.db.tgw360.com node2.db.tgw360.com node3.es1.tgw360.com node4.lvs1.tgw360.com node6.git.tgw360.com node134 node135 node136 node137 node138 node139 node140 node141 0.0.0.0 --certs-dir=/cockroach/certs --ca-key=/cockroach/certs/ca.key --overwrite
```

在`/etc/hsots`添加所有主机名对应的ip

```
172.17.14.145  node1.db.tgw360.com
172.17.14.146  node2.db.tgw360.com
172.17.14.147  node3.es1.tgw360.com
172.17.14.148  node4.lvs1.tgw360.com
172.17.14.149  node5.tg1.tgw360.com
172.17.14.150  node6.git.tgw360.com
172.17.14.152  fintech1.tgw360.com
172.17.14.153  fintech2.tgw360.com
172.17.14.157  node7.ha1.tgw360.com
14.18.189.136  node8.ha2.tgw360.com
14.18.189.132	node132
14.18.189.133   node133
14.18.189.134   node134
14.18.189.135	node135
14.18.189.136	node136
14.18.189.137   node137
14.18.189.138   node138
14.18.189.139   node139
14.18.189.140   node140
14.18.189.141   node141
```

将生成的证书拷贝到所有节点对应的目录，所有节点删除cockroach容器并重新生成cockroach容器，本次生成采用主机名的方式加入集群。

```shell
docker run --restart=always --name cockroach --net=host -e TZ="Asia/Shanghai" -v /fintech/data/cockroachdb/node:/cockroach/cockroach-data -v /fintech/data/cockroachdb/certs:/cockroach/certs -d  cockroachdb/cockroach:v2.0.5 start --certs-dir=/cockroach/certs --join=node4.lvs1.tgw360.com,node6.git.tgw360.com --http-host=0.0.0.0 --host=node6.git.tgw360.com --port=26257 --http-port=8088 --cache=10% --max-sql-memory=10% 
```

查看cockroach是否绑定内网IP段

`netstat -ntlp | grep 26257`

如绑定内网地址，需要先将cockroach重启安装一次

```shell
docker run --restart=always --name cockroach --net=host -e TZ="Asia/Shanghai" -v /fintech/data/cockroachdb/node:/cockroach/cockroach-data -v /fintech/data/cockroachdb/certs:/cockroach/certs -d  cockroachdb/cockroach:v2.0.5 start --certs-dir=/cockroach/certs --join=node4.lvs1.tgw360.com,node6.git.tgw360.com --http-host=0.0.0.0 --host=0.0.0.0 --advertise-host=node136 --port=26257 --http-port=8088 --cache=10% --max-sql-memory=10% 

# 参数解释
# --host		绑定主机ip
# --http-host	绑定监控IP，例如：http://172.17.14.150:8088
# --certs-dir	证书目录
# 
```

