### nginx定义多个location



#### 定义多个location

```
    location ~ /transfer/api/(.*) {
        proxy_pass http://testwebapiTransfer/$1?$args;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $remote_addr;
    }

	localtion ~* /gateway/(.*) {
        proxy_pass        http://testwebapiGateway/$1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $remote_addr;
	} 

    location / {
        proxy_pass        http://testwebapi;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $remote_addr;
    }
```

##### 正则匹配中如url中带有参数，需要在变量后添加`?$args`参数。