##### 搭建elasticsearch

###### 修改/etc/sysctl.conf，添加如下一行

```shell
[root@localhost ~]# vim /etc/sysctl.conf
vm.max_map_count=655360
[root@localhost ~]# sysctl -p			# 配置生效
```

###### 下载elasticsearch镜像，当前版本为5.6.9

```shell
[root@localhost ~]# docker pull elasticsearch:5.6.9
# 建立elasticsearch目录和配置文件，或者在rancher上建立elasticsearch容器，留意挂载目录
[root@localhost ~]# docker run –d –name es –v /data/docker/elasticsearch/data:/usr/share/elasticsearch/data –v /data/docker/elasticsearch/config/elasticsearch.yml:/usr/share/elasticsearch/config/elasticsearch.yml –v /etc/localtime:/etc/localtime elasticsearch:5.6.9
```

###### elasticsearch.yml配置文件

```yaml
cluster.name: esTest						#定义集群名字，所有机器名字都一样
node.name: node1  							#当前节点名字，每台机器的节点名字都要不一样
network.host: 172.17.14.58  				#绑定监听IP
http.port: 9200								#网络端口
transport.tcp.port: 9300					#设置节点间交互的tcp端口,默认是9300
discovery.zen.minimum_master_nodes: 1		#设置最小主节点数
http.cors.enabled: true						#head插件设置
http.cors.allow-origin: "*"					#设置可以访问的ip 这里全部设置通过
path.data: /path/data						#数据目录
path.log: /path/log							#日志目录
path.plugins: /path/plugins					#插件安装目录
gateway.recover_after_nodes: 2				#当集群有多少台机器启动后才开始数据恢复（集群重启有效）
gateway.expected_nodes: 3 					#集群机器数量（集群重启有效）
gateway.recover_after_time: 5m				#节点加入集群等待时间（集群重启有效）
```

###### es操作手册

```shell
# 副本分片可以用来查询，副本分片越多，查询效果越好，占用磁盘空间越大。

#移动分片位置，将索引为stkpooladjust，分片为1的数据从node-4节点移动到node-1
curl -XPOST "http://172.17.14.58:9200/_cluster/reroute" -d  '{"commands" : [ {"move" : {"index" : "stkpooladjust","shard" : 1,"from_node" : "node-4","to_node" : "node-1"}}]}'

#关闭node-4节点
curl -XPOST 'http://172.17.14.58:9200/_cluster/nodes/node-4/_shutdown'

#暂停集群shard自动均衡
curl -XPUT 'http://172.17.14.58:9200/_cluster/settings' -d '{"transient": {"cluster.routing.allocation.enable" : "none"}}'

#设置最小主节点数，一般设置为（机器数量/2）+1，3台设置2个，10台设置6
curl -XPUT http://172.17.14.58:9200/_cluster/settings {"persistent" : {"discovery.zen.minimum_master_nodes" : 2}}

# 修改elasticsearch副本数，如没有副本，可用这个设置，副本默认数量为1
curl -XPUT "http://172.17.14.58:9200/_settings?pretty"  -d '{ "index": {"number_of_replicas":1}}'
```



##### 搭建logstash

```shell
[root@localhost ~]# docker pull logstash:5.6.9
# 自行建立logstash目录及配置文件
[root@localhost ~]# docker run -d --name logstash --net host -v /data/docker/logstash/config:/config-dir -v /etc/localtime:/etc/localtime logstash:5.6.9
```

###### logstash.yml配置文件

```yaml
# 本配置为nginx-access访问成功日志的收集，input选项为beats，采用filebeat收集日志，最后有filebeat配置文件。input支持多种输入，可自行百度。
input { 
    beats {
        port => 5044
    } 
}

# 对nginx-access日志进行分词处理，logstash分词后会默认采用json格式，有利于kibana上查看和制作图表。
filter {
    if [type] == "nginx-access" {	# “nginx-access”在filebeat中指定，当有多个filebeat时用来区分
        grok {
            match => {		# 分词正则表达式，根据nginx配置文件调整
                "message" => "%{IPORHOST:clientip} (?:-|%{NOTSPACE:au}) (?:-|%{NOTSPACE:auth}) \[%{HTTPDATE:client_timestamp}\] %{QS:http_method} %{NUMBER:status_code:int} (?:%{NUMBER:body_bytes_sent}|-) (?:-|%{QS:http_referer}) %{QS:http_user_agent} (?:%{QS:request_time}|-)"
            }
        }
        date {
            match => [ "client_timestamp" , "yyyy-MM-dd HH:mm:ss Z" ]
        }
        mutate {
            remove_field => ["message"]			# 分词之后删除message，不会重复存储
        }
        urldecode {
            all_fields => true
        }
    }
}

# 输出到elasticsearch
output {
    if [type] == "nginx-access" {
        elasticsearch {
            hosts => ["172.17.14.58:9200"]
            manage_template => false
            # 配置es索引，格式为filebeat-nginx-access-2018.05.09，默认以天分割，也可自行调整。
            index => "%{[@metadata][beat]}-nginx-access-%{+YYYY.MM.dd}"
            document_type => "%{[@metadata][type]}"
        }
    }
}
```



##### 搭建kibana

```shell
[root@localhost ~]# docker pull kibana:5.6.9
[root@localhost ~]# docker run -d --net host --name kibana -v /data/docker/kibana/config/kibana.yml:/usr/share/kibana/config/kibana.yml kibana:5.6.9
```

###### kibana.yml配置文件

```yaml
server.port: 5601								#端口
server.host: '172.17.14.58'						#服务器IP
elasticsearch.url: 'http://172.17.14.58:9200'	#elasticsearch地址
```



##### 搭建filebeat

```shell
[root@localhost ~]# docker pull prima/filebeat:5.6.8
[root@localhost ~]# docker run -d --net host --name filebeat -v /data/docker/filebeat/config/filebeat.yml:/filebeat.yml -v /usr/share/zoneinfo/Asia/Shanghai:/etc/localtime -v /data/docker/nginx/logs:/var/log/nginx -v /data/docker/mysql/logs:/var/log/mysql prima/filebeat:5.6.8 
```

###### filebeat.yml配置文件

```yaml
filebeat.prospectors:
- input_type: log						# 输入类型，可以为stdin
  enabled: true
  paths:
    - /var/log/nginx/access.log
  encoding: plain						# 不对文件进行任何处理，有中文的话选用或使用utf8
  document_type: nginx-access			# 在logstash中用来判断的标识符

- input_type: log
  enabled: true
  paths:
    - /var/log/nginx/error.log
  encoding: plain
  document-type: nginx-error

- input_type: log
  enabled: true
  paths:
    - /var/log/mysql/error.log
  encoding: plain
  document-type: mysql-error

- input_type: log
  enabled: true
  paths:
    - /var/log/mysql/slow.log
  multiline:
    pattern: "^# User@Host:"			# 适用与多行日志，例如java，每行以“# User@Host:”开头
    negate: true
    match: after
  encoding: plain
  document-type: mysql-slow

output.logstash:
  hosts: ["172.17.14.58:5044"]
#output.elasticsearch:					# 可直接输入到elasticsearch，不能分词
#  hosts: ["172.17.14.58:9200"]
```

