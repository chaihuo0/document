#### eureka搭建

##### 制作eureka镜像，Dockerfile文件

```yaml
# 基于哪个镜像
FROM java:8
VOLUME /root/springcloud/eureka
ADD microservice-discovery-eureka-1.0-SNAPSHOT.jar /root/springcloud/eureka/app.jar
# 开放8761端⼝
#EXPOSE 8761
# 配置容器启动后执⾏的命令
ENTRYPOINT ["java","-jar","/root/springcloud/eureka/app.jar","--spring.config.location=/root/springcloud/eureka/config/application.yml","--spring.profiles.active=eureka2"]
```

##### 启动命令

```shell
docker build -t eureka/2 .		# 通过Dockerfile制作镜像

docker run -d --name eureka2 --net host --mount type=bind,source=/root/springcloud/eureka/config/application.yml,target=/root/springcloud/eureka/config/application.yml --mount type=bind,source=/etc/localtime,target=/etc/localtime eureka/2
```

##### application.yml配置文件修改

```yaml
spring:
  profiles: eureka2
server:
  port: 8761
eureka:
  instance:
    hostname: 172.18.44.81			# 修改为本机IP
    instanceId: eureka2
  client:
    serviceUrl:
      defaultZone: http://172.18.44.120:8761/eureka/	# 另一台eureka地址
  server:
    enable-self-preservation: false            # 设为false，关闭自我保护
#    eviction-interval-timer-in-ms: 15000      # 清理间隔（单位毫秒，默认是60*1000）
```

