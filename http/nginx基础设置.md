#### General Settings

##### 监听端口(`listen`)

```
server {
  # standard HTTP protocol
  listen 80;
  
  # standard HTTPS protocol
  listen 443 ssl;
  
  # listen on 80 using IPv6
  listen [::]:80;
  
  # listen only on IPv6
  listen [::]:80 ipv6only=on;
}
```

##### 配置域名(`server_name`)

```
server {
  # Listen to yourdomain.com
  server_name yourdomain.com;
  
  # Listen to multiple domains
  server_name yourdomain.com www.yourdomain.com;
  
  # Listen to all sub-domains
  server_name *.yourdomain.com;
  
  # Listen to all top-level domains
  server_name yourdomain.*;
  
  # Listen to unspecified hostnames (listens to IP address itself)
  server_name "";
}
```

##### 开启访问日志 (`access_log`)

```
server {
  # Relative or full path to log file
  access_log /path/to/file.log;
  
  # Turn 'on' or 'off'
  access_log on;
}
```

##### 打开gizp压缩 (`gzip`, `client_max_body_size`)

```
server {
  # Turn gzip compression 'on' or 'off'
  gzip on;
  
  # Limit client body size to 10mb
  client_max_body_size 10M;
}
```

##### 静态页面

传统的WEB服务器

```
server {
  listen 80;
  server_name yourdomain.com;
  
  location / {
  	root /path/to/website;
  }
}
```

##### 具有HTML5历史模式的静态资产

适用于Vue，React，Angular等单页应用程序。

```
server {
  listen 80;
  server_name yourdomain.com;
  root /path/to/website;
  
  location / {
  	try_files $uri $uri/ /index.html;
  }
}
```

#### 重定向

##### `301` 永久

```
server {
  listen 80;
  server_name www.yourdomain.com;
  return 301 http://yourdomain.com$request_uri;
}
```

##### `302` 临时

```
server {
  listen 80;
  server_name yourdomain.com;
  return 302 http://otherdomain.com;
}
```

##### 重定向URL

可以是永久(`301`)或临时 (`302`)

```
server {
  listen 80;
  server_name yourdomain.com;
  
  location /redirect-url {
	return 301 http://otherdomain.com;  
  }
}
```

#### 反向代理

##### 基本

```
server {
  listen 80;
  server_name yourdomain.com;
  
  location / {
    proxy_pass http://0.0.0.0:3000;
    # where 0.0.0.0:3000 is your Node.js Server bound on 0.0.0.0 listing on port 3000
  }
}
```

##### 基本+

```
upstream node_js {
  server 0.0.0.0:3000;
  # where 0.0.0.0:3000 is your Node.js Server bound on 0.0.0.0 listing on port 3000
}

server {
  listen 80;
  server_name yourdomain.com;
  
  location / {
    proxy_pass http://node_js;
  }
}
```

##### WebSockets连接

```
upstream node_js {
  server 0.0.0.0:3000;
}

server {
  listen 80;
  server_name yourdomain.com;
  
  location / {
    proxy_pass http://node_js;
    proxy_redirect off;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
	
    # not required but useful for applications with heavy WebSocket usage
    # as it increases the default timeout configuration of 60
    proxy_read_timeout 80;
  }
}
```

#### TLS/SSL (HTTPS)

##### HTTP和HTTPS混用

```
server {
  listen              80;
  listen              443 ssl;
  server_name         www.example.com;

  ssl_certificate     /path/to/cert.pem;
  ssl_certificate_key /path/to/privkey.pem;
  
  ssl_stapling on;
  ssl_stapling_verify on;
  ssl_trusted_certificate /path/to/fullchain.pem;

  ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
  ssl_session_timeout 1d;
  ssl_session_cache shared:SSL:50m;
  add_header Strict-Transport-Security max-age=15768000;
}
```

##### HTTP转HTTPS

```
server {
  listen 443 ssl;
  server_name yourdomain.com;
  
  ssl on;
  
  ssl_certificate /path/to/cert.pem;
  ssl_certificate_key /path/to/privkey.pem;
  
  ssl_stapling on;
  ssl_stapling_verify on;
  ssl_trusted_certificate /path/to/fullchain.pem;

  ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
  ssl_session_timeout 1d;
  ssl_session_cache shared:SSL:50m;
  add_header Strict-Transport-Security max-age=15768000;
}

# Permanent redirect for HTTP to HTTPS
server {
  listen 80;
  server_name yourdomain.com;
  return 301 https://$host$request_uri;
}
```

#### 反向代理

有`ip_hash`和`weight`区别

```
upstream node_js {
  ip_hash;
  server 0.0.0.0:3000;
  server 0.0.0.0:4000;
  server 123.131.121.122;
}

server {
  listen 80;
  server_name yourdomain.com;
  
  location / {
    proxy_pass http://node_js;
  }
}
```