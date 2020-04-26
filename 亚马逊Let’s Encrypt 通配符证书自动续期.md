#### 亚马逊Let’s Encrypt 通配符证书自动续期



```shell
# 更新pip 和 setuptools
certbot/bin/pip install -U setuptools pip
pip list

# 安装AWS插件
pip install certbot-dns-route53

# 创建AWS证书文件，需要自己去申请AWS的密钥
mkdir ~/.aws/
vim ~/.aws/credentials
	[default]
	aws_access_key_id=xxx
	aws_secret_access_key=xxx

# 创建证书
certbot certonly -n --agree-tos --email xxx --dns-route53 -d "*.xxx.com"

# 更新
certbot renew --force-renewal

# 自动续期脚本
vi /root/certbot_renew.sh
#!/bin/bash
certbot renew --force-renew
nginx -s reload

# 添加执行权限
chmod a+x /root/certbot_renew.sh

# 设置定时任务自动更新证书，“At 01:01 on day-of-month 1.”
vim /etc/crontab
1 1 1 * * /root/certbot_renew.sh >/root/crontab.log 2>&1

# 如果需要记录日志可以这样写
1 1 1 * * echo `date -R` >> /var/log/certbot.crontab.log; certbot renew --force-renewal >> /var/log/certbot.crontab.log 2>&1; nginx -s reload

# certbot 官方使用 python 产生了一个分钟的随机数，让更新时间随机一些
echo "0 0,12 * * * root python -c'import random; import time; time.sleep(random.random() * 3600)'&& certbot renew" | sudo tee -a /etc/crontab > /dev/null

```



```shell
# 查看证书数量及过期时间
certbot-auto certificates
```

