# Nginx：http请求修改成 https

让启用 Nginx 启用 SSL，两种方法，单一支持HTTPS，或者同时支持 HTTP 和 HTTPS 两种协议。

***备注\*** Nginx 默认没有安装 SSL 模块，安装时需要手动添加 `--with-http_ssl_module` 参数。（如果您使用LNMP安装包，可以忽视，默认已安装了）

### 强制 HTTPS 协议

```
# 普通 HTTP 服务器，HTTP 就是用端口80
server{
    listen 80;
    server_name example.com;

    return 301 https://example.com$request_uri; # 这就是把所有的 request 转跳到 https
}

# 普通的 HTTPS 服务器
server {

    listen 443 ssl;
    server_name example.com

ssl_certificate /mywebsite/pathToSSLCert/server.crt;
ssl_certificate_key /mywebsite/pathToSSLCert/server.key;

    ...
}
```

**代码解释：**

**listen 443 ssl** = 监听 443 端口和启用 SSL

**ssl_certificate**，**ssl_certificate_key** = SSL证件

### 同时支持两个协议

```
server {
    listen              80;
    listen              443 ssl;
    server_name         www.example.com;

    ssl_certificate     www.example.com.crt;
    ssl_certificate_key www.example.com.key;
    ...
}
```

注意：有些程序可能产生“普通的HTTP请求被发送到HTTPS端口”这些问题。解决方法请看[这里](https://blog.justwd.net/snippets/nginx/the-plain-http-request-was-sent-to-https-port/)