##### brook搭建

```
# 从github上下载brook文件
wget https://github.com/txthinking/brook/releases/download/v20180707/brook
# 给执行权限
chmod +x brook
# 开启服务
brook server -l :9999 -p 123456
# 多端口开启服务
brook servers -l ":9999 123456" -l ":9998 654321"
# 客户端连接
brook client -l 127.0.0.1:1080 -i 127.0.0.1 -s 1.2.3.4:9999 -p 123456 --http
```

