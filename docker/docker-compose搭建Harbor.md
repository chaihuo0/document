#### 搭建Harbor

##### 安装docker-compose有两种安装方法如下

```shell
curl -L https://github.com/docker/compose/releases/download/1.3.1/docker-compose-`uname -s`-`uname -m` > /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

##### 下载Harbor安装包

```
#在线安装
wget https://github.com/vmware/harbor/releases/download/1.6.2/harbor-online-installer-v1.6.2.tgz

#离线安装包
wget https://github.com/vmware/harbor/releases/download/1.6.2/harbor-online-installer-v1.6.2.tgz
```

##### 解压安装包

```
tar xvf harbor-online-installer-v1.6.2.tgz
cd harbor
```

##### 修改配置

```
vi harbor.cfg
# 修改域名等
hostname = harbor.tgw360.com
ui_url_protocol = https
nginx ssl = on
ssl_cert = /data/cert/214474460280345.crt
ssl_cert_key = /data/cert/214474460280345.key

vi docker-compose.yml
# 修改nginx端口等
```

##### 安装

```
./install.sh
```

##### 修改配置重新安装

```
cd /root/harbor
docker-compose down -v
./prepare
docker-compose up -d
```

##### 配置证书

```
cat 214474460280345.pem >> harbor.tgw360.com.crt
cp harbor.tgw360.com.crt /etc/pki/ca-trust/source/anchors/harbor.tgw360.com.crt
update-ca-trust
```

##### docker登录harbor

```
docker login harbor.tgw360.com:port

#验证
```



##### 错误排查

```
1、Error response from daemon: Get https://harbor.tgw360.com:1443/v2/: Get https://harbor.tgw360.com/service/token?account=admin&client_id=docker&offline_token=true&service=harbor-registry: x509: certificate is valid for ingress.local, not harbor.tgw360.com
```

修改 `/root/harbor/common/templates/registry/config.yml`，强制改成https

```
auth:
  token:
    issuer: registry-token-issuer
    #realm: $ui_url/service/token
    realm: https://harbor.tgw360.com:1443/service/token
    rootcertbundle: /etc/registry/root.crt
    service: token-service
```

