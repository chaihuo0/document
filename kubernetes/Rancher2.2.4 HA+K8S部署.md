# Rancher2.2.4 HA+K8S部署

本文主要目的在于记录rancher ha集群搭建步骤，内容包括系统配置、docker安装、k8s安装、rancher ha安装等。

#### 服务器环境信息：

| 节点名称 | IP           | OS                                   | 角色              |
| -------- | ------------ | ------------------------------------ | ----------------- |
| node9    | 172.16.17.72 | CentOS Linux release 7.4.1708 (Core) | Nginx             |
| Node10   | 172.16.17.10 | CentOS Linux release 7.4.1708 (Core) | etcd, docker, k8s |
| Node11   | 172.16.17.11 | CentOS Linux release 7.4.1708 (Core) | etcd, docker, k8s |
| Node12   | 172.16.17.12 | CentOS Linux release 7.4.1708 (Core) | etcd, docker, k8s |

### 一、环境设置（node10\node11\node12每一台主机都需要操作）

#### 操作系统文件限制

vi /etc/security/limits.conf
在文件末尾添加以下内容：

```
root soft nofile 655350
root hard nofile 655350
* soft nofile 655350
* hard nofile 655350
```

#### 关闭防火墙

```
systemctl stop firewalld
systemctl disable firewalld
```

#### 关闭setlinx

将`SELINUX`值设置为disabled：

```
vim /etc/selinux/config
SELINUX=disabled
```

#### 关闭swap

注释或删除swap交换分区：vi /etc/fstab

```
#
# /etc/fstab
# Created by anaconda on Fri Jun  2 14:11:50 2017
#
# Accessible filesystems, by reference, are maintained under '/dev/disk'
# See man pages fstab(5), findfs(8), mount(8) and/or blkid(8) for more info
#
/dev/mapper/centos-root /                       xfs     defaults        0 0
UUID=f5b4435a-77bc-48f4-8d22-6fa55e9e04a2 /boot                   xfs     defaults        0 0
/dev/mapper/centos-grid0 /grid0                  xfs     defaults        0 0
#/dev/mapper/centos-swap swap                    swap    defaults        0 0
```

#### kernel调优

添加如下内容，vi /etc/sysctl.conf：

```
net.ipv4.ip_forward=1
net.bridge.bridge-nf-call-iptables=1
net.bridge.bridge-nf-call-ip6tables=1
vm.swappiness=0
vm.max_map_count=655360
```

#### 创建用户

创建用户并且添加到docker组：

```
useradd rancher -G docker
passwd rancher
（生产密码 QEw2pldqPnPOkUsj）
```

#### ssh免密登录（node10\node11\node12）

每台主机上面执行下面命令，包括本机对本机

```
su - rancher
ssh-keygen -t rsa
ssh-copy-id -i .ssh/id_rsa.pub rancher@172.16.17.10
ssh-copy-id -i .ssh/id_rsa.pub rancher@172.16.17.11
ssh-copy-id -i .ssh/id_rsa.pub rancher@172.16.17.12
```

root用户也需要做免密登录

```
su - root
ssh-keygen -t rsa
ssh-copy-id -i .ssh/id_rsa.pub root@172.16.17.10
ssh-copy-id -i .ssh/id_rsa.pub root@172.16.17.11
ssh-copy-id -i .ssh/id_rsa.pub root@172.16.17.12
```



#### docker安装

安装最新版本docker 

```
yum install yum-utils device-mapper-persistent-data lvm2 curl -y
wget -O /etc/yum.repos.d/docker-ce.repo https://download.docker.com/linux/centos/docker-ce.repo
yum clean all && yum repolist && yum install docker-ce -y
systemctl start docker
systemctl enable docker
docker info
```

添加国内加速代理，设置storage-driver；设置默认内网网段；限制docker日志大小避免日志撑爆硬盘！！！！！

```
[root@node10 ~]# cat /etc/docker/daemon.json 
{"bip": "192.168.100.1/24"}
{
  "registry-mirrors": ["https://39r65dar.mirror.aliyuncs.com"],
    "storage-driver": "overlay2",
    "storage-opts": [
    "overlay2.override_kernel_check=true"
    ]
}
{
"log-driver": "json-file",
"log-opts": {
    "max-size": "100m",
    "max-file": "3"
    }
}
```

重启docker，如果起不来请检查/etc/docker/daemon.json配置文件

```
systemctl restart docker
```

### 二、nginx安装（node72节点部署nginx负载均衡）

```
[root@node9 ~]# wget -O /etc/yum.repos.d/CentOS-Base.repo http://mirrors.aliyun.com/repo/Centos-7.repo
[root@node9 ~]# wget -O /etc/yum.repos.d/epel.repo http://mirrors.aliyun.com/repo/epel-7.repo
[root@node9 ~]# yum clean all
[root@node9 ~]# yum install nginx -y
```

修改配置文件：vi /etc/nginx/nginx.conf

```
user nginx;
worker_processes 4;
worker_rlimit_nofile 40000;

events {
    worker_connections 8192;
}

http {
    # Gzip Settings
    gzip on;
    gzip_disable "msie6";
    gzip_disable "MSIE [1-6]\.(?!.*SV1)";
    gzip_vary on;
    gzip_static on;
    gzip_proxied any;
    gzip_min_length 0;
    gzip_comp_level 8;
    gzip_buffers 16 8k;
    gzip_http_version 1.1;
    gzip_types text/xml application/xml application/atom+xml application/rss+xml application/xhtml+xml image/svg+xml application/font-woff text/javascript application/javascript application/x-javascript text/x-json application/json application/x-web-app-manifest+json text/css text/plain text/x-component font/opentype application/x-font-ttf application/vnd.ms-fontobject font/woff2 image/x-icon image/png image/jpeg;

    server {
        listen         80;
        return 301 https://$host$request_uri;
    }
}

stream {
    upstream rancher_servers {
        least_conn;
        server 172.16.17.10:443 max_fails=3 fail_timeout=5s;
        server 172.16.17.11:443 max_fails=3 fail_timeout=5s;
        server 172.16.17.12:443 max_fails=3 fail_timeout=5s;
    }
    server {
        listen     443;
        proxy_pass rancher_servers;
    }
}
```

启动nginx：

```
sudo systemctl restart nginx.service
```

### 三、Rancher集群部署（以下操作全部在node10操作直至集群完成）

#### 安装必要工具

安装rke：

```
网上找下资源下载rke_linux-amd64并上传到服务器
[root@node10 ~]# chmod +x rke_linux-amd64
[root@node10 ~]# mv rke_linux-amd64 /usr/bin/rke
验证：
[root@node10 ~]# rke -v
rke version v0.2.4
```

安装kubectl：

```
网上找下资源下载kubectl_amd64-linux并上传到服务器
[root@node10 ~]# chmod +x kubectl_amd64-linux
[root@node10 ~]# mv kubectl_amd64-linux /usr/bin/kubectl
验证：
[root@node10 ~]# kubectl version
Client Version: version.Info{Major:"1", Minor:"15", GitVersion:"v1.15.0", GitCommit:"e8462b5b5dc2584fdcd18e6bcfe9f1e4d970a529", GitTreeState:"clean", BuildDate:"2019-06-19T16:40:16Z", GoVersion:"go1.12.5", Compiler:"gc", Platform:"linux/amd64"}
The connection to the server localhost:8080 was refused - did you specify the right host or port?
```

安装helm：

```
网上找下资源下载helm-v2.14.1-linux-amd64.tar.gz并上传到服务器
[root@node10 ~]# tar -zxvf helm-v2.14.1-linux-amd64.tar.gz 
[root@node10 ~]# mv linux-amd64/helm /usr/bin/helm
[root@node10 ~]# mv linux-amd64/tiller /usr/bin/tiller
[root@node10 ~]# rm -rf helm-v2.14.1-linux-amd64.tar.gz linux-amd64/
验证：
[root@node10 ~]# helm version
Client: &version.Version{SemVer:"v2.14.1", GitCommit:"5270352a09c7e8b6e8c9593002a73535276507c0", GitTreeState:"clean"}
Error: Get http://localhost:8080/api/v1/namespaces/kube-system/pods?labelSelector=app%3Dhelm%2Cname%3Dtiller: dial tcp [::1]:8080: connect: connection refused
[root@node10 ~]# tiller version
[main] 2019/06/28 19:34:21 Starting Tiller v2.14.1 (tls=false)
[main] 2019/06/28 19:34:21 GRPC listening on :44134
[main] 2019/06/28 19:34:21 Probes listening on :44135
[main] 2019/06/28 19:34:21 Storage driver is ConfigMap
[main] 2019/06/28 19:34:21 Max history per release is 0
```

### 四、安装k8s

1、切换到rancher用户

```
su - rancher
```

2、创建rancher集群配置文件：

vi rancher-cluster.yml

```
nodes:
  - address: 172.16.17.10
    user: rancher
    role: [controlplane,worker,etcd]
  - address: 172.16.17.11
    user: rancher
    role: [controlplane,worker,etcd]
  - address: 172.16.17.12
    user: rancher
    role: [controlplane,worker,etcd]

services:
  etcd:
    snapshot: true
    creation: 6h
    retention: 24h
```

3、启动集群

```
[rancher@node10 ~]$ rke up --config ./rancher-cluster.yml
INFO[0000] Initiating Kubernetes cluster                
INFO[0000] [dialer] Setup tunnel for host [172.16.17.11] 
INFO[0000] [dialer] Setup tunnel for host [172.16.17.12] 
INFO[0000] [dialer] Setup tunnel for host [172.16.17.10] 
INFO[0000] [state] Successfully started [cluster-state-deployer] container on host [172.16.17.10] 
INFO[0001] [state] Successfully started [cluster-state-deployer] container on host [172.16.17.11] 
INFO[0001] [state] Successfully started [cluster-state-deployer] container on host [172.16.17.12] 
INFO[0001] [certificates] Generating CA kubernetes certificates 
INFO[0002] [certificates] Generating Kubernetes API server aggregation layer requestheader client CA certificates 
INFO[0002] [certificates] Generating Node certificate   
INFO[0002] [certificates] Generating admin certificates and kubeconfig 
INFO[0002] [certificates] Generating Kubernetes API server proxy client certificates 
INFO[0002] [certificates] Generating etcd-172.16.17.10 certificate and key 
INFO[0002] [certificates] Generating etcd-172.16.17.11 certificate and key 
INFO[0003] [certificates] Generating etcd-172.16.17.12 certificate and key 
INFO[0003] [certificates] Generating Kube Controller certificates 
INFO[0003] [certificates] Generating Kube Scheduler certificates 
INFO[0004] [certificates] Generating Kube Proxy certificates 
INFO[0004] [certificates] Generating Kubernetes API server certificates 
INFO[0004] Successfully Deployed state file at [./rancher-cluster.rkestate] 
INFO[0004] Building Kubernetes cluster                  
INFO[0004] [dialer] Setup tunnel for host [172.16.17.12] 
INFO[0004] [dialer] Setup tunnel for host [172.16.17.10] 
INFO[0004] [dialer] Setup tunnel for host [172.16.17.11] 
INFO[0004] [network] Deploying port listener containers 
INFO[0005] [network] Successfully started [rke-etcd-port-listener] container on host [172.16.17.10] 
INFO[0005] [network] Successfully started [rke-etcd-port-listener] container on host [172.16.17.11] 
INFO[0005] [network] Successfully started [rke-etcd-port-listener] container on host [172.16.17.12] 
INFO[0005] [network] Successfully started [rke-cp-port-listener] container on host [172.16.17.10] 
INFO[0005] [network] Successfully started [rke-cp-port-listener] container on host [172.16.17.12] 
INFO[0005] [network] Successfully started [rke-cp-port-listener] container on host [172.16.17.11] 
INFO[0006] [network] Successfully started [rke-worker-port-listener] container on host [172.16.17.11] 
INFO[0006] [network] Successfully started [rke-worker-port-listener] container on host [172.16.17.10] 
INFO[0006] [network] Successfully started [rke-worker-port-listener] container on host [172.16.17.12] 
INFO[0006] [network] Port listener containers deployed successfully 
INFO[0006] [network] Running etcd <-> etcd port checks  
INFO[0006] [network] Successfully started [rke-port-checker] container on host [172.16.17.10] 
INFO[0006] [network] Successfully started [rke-port-checker] container on host [172.16.17.11] 
INFO[0006] [network] Successfully started [rke-port-checker] container on host [172.16.17.12] 
INFO[0006] [network] Running control plane -> etcd port checks 
INFO[0007] [network] Successfully started [rke-port-checker] container on host [172.16.17.11] 
INFO[0007] [network] Successfully started [rke-port-checker] container on host [172.16.17.10] 
INFO[0007] [network] Successfully started [rke-port-checker] container on host [172.16.17.12] 
INFO[0007] [network] Running control plane -> worker port checks 
INFO[0007] [network] Successfully started [rke-port-checker] container on host [172.16.17.11] 
INFO[0007] [network] Successfully started [rke-port-checker] container on host [172.16.17.10] 
INFO[0007] [network] Successfully started [rke-port-checker] container on host [172.16.17.12] 
INFO[0007] [network] Running workers -> control plane port checks 
INFO[0008] [network] Successfully started [rke-port-checker] container on host [172.16.17.11] 
INFO[0008] [network] Successfully started [rke-port-checker] container on host [172.16.17.10] 
INFO[0008] [network] Successfully started [rke-port-checker] container on host [172.16.17.12] 
INFO[0008] [network] Checking KubeAPI port Control Plane hosts 
INFO[0008] [network] Removing port listener containers  
INFO[0008] [remove/rke-etcd-port-listener] Successfully removed container on host [172.16.17.11] 
INFO[0008] [remove/rke-etcd-port-listener] Successfully removed container on host [172.16.17.10] 
INFO[0008] [remove/rke-etcd-port-listener] Successfully removed container on host [172.16.17.12] 
INFO[0008] [remove/rke-cp-port-listener] Successfully removed container on host [172.16.17.10] 
INFO[0008] [remove/rke-cp-port-listener] Successfully removed container on host [172.16.17.11] 
INFO[0008] [remove/rke-cp-port-listener] Successfully removed container on host [172.16.17.12] 
INFO[0009] [remove/rke-worker-port-listener] Successfully removed container on host [172.16.17.10] 
INFO[0009] [remove/rke-worker-port-listener] Successfully removed container on host [172.16.17.11] 
INFO[0009] [remove/rke-worker-port-listener] Successfully removed container on host [172.16.17.12] 
INFO[0009] [network] Port listener containers removed successfully 
INFO[0009] [certificates] Deploying kubernetes certificates to Cluster nodes 
INFO[0014] [reconcile] Rebuilding and updating local kube config 
INFO[0014] Successfully Deployed local admin kubeconfig at [./kube_config_rancher-cluster.yml] 
INFO[0014] Successfully Deployed local admin kubeconfig at [./kube_config_rancher-cluster.yml] 
INFO[0014] Successfully Deployed local admin kubeconfig at [./kube_config_rancher-cluster.yml] 
INFO[0014] [certificates] Successfully deployed kubernetes certificates to Cluster nodes 
INFO[0014] [reconcile] Reconciling cluster state        
INFO[0014] [reconcile] This is newly generated cluster  
INFO[0014] Pre-pulling kubernetes images                
INFO[0014] [pre-deploy] Pulling image [rancher/hyperkube:v1.13.5-rancher1] on host [172.16.17.10] 
INFO[0014] [pre-deploy] Pulling image [rancher/hyperkube:v1.13.5-rancher1] on host [172.16.17.11] 
INFO[0014] [pre-deploy] Pulling image [rancher/hyperkube:v1.13.5-rancher1] on host [172.16.17.12] 
INFO[0120] [pre-deploy] Successfully pulled image [rancher/hyperkube:v1.13.5-rancher1] on host [172.16.17.10] 
INFO[0159] [pre-deploy] Successfully pulled image [rancher/hyperkube:v1.13.5-rancher1] on host [172.16.17.11] 
INFO[0177] [pre-deploy] Successfully pulled image [rancher/hyperkube:v1.13.5-rancher1] on host [172.16.17.12] 
INFO[0177] Kubernetes images pulled successfully        
INFO[0177] [etcd] Building up etcd plane..              
INFO[0177] [etcd] Pulling image [rancher/coreos-etcd:v3.2.24-rancher1] on host [172.16.17.10] 
INFO[0201] [etcd] Successfully pulled image [rancher/coreos-etcd:v3.2.24-rancher1] on host [172.16.17.10] 
INFO[0201] [etcd] Successfully started [etcd] container on host [172.16.17.10] 
INFO[0201] [etcd] Saving snapshot [etcd-rolling-snapshots] on host [172.16.17.10] 
INFO[0202] [etcd] Successfully started [etcd-rolling-snapshots] container on host [172.16.17.10] 
INFO[0207] [certificates] Successfully started [rke-bundle-cert] container on host [172.16.17.10] 
INFO[0207] Waiting for [rke-bundle-cert] container to exit on host [172.16.17.10] 
INFO[0207] Container [rke-bundle-cert] is still running on host [172.16.17.10] 
INFO[0208] Waiting for [rke-bundle-cert] container to exit on host [172.16.17.10] 
INFO[0208] [certificates] successfully saved certificate bundle [/opt/rke/etcd-snapshots//pki.bundle.tar.gz] on host [172.16.17.10] 
INFO[0209] [etcd] Successfully started [rke-log-linker] container on host [172.16.17.10] 
INFO[0209] [remove/rke-log-linker] Successfully removed container on host [172.16.17.10] 
INFO[0209] [etcd] Pulling image [rancher/coreos-etcd:v3.2.24-rancher1] on host [172.16.17.11] 
INFO[0226] [etcd] Successfully pulled image [rancher/coreos-etcd:v3.2.24-rancher1] on host [172.16.17.11] 
INFO[0226] [etcd] Successfully started [etcd] container on host [172.16.17.11] 
INFO[0226] [etcd] Saving snapshot [etcd-rolling-snapshots] on host [172.16.17.11] 
INFO[0227] [etcd] Successfully started [etcd-rolling-snapshots] container on host [172.16.17.11] 
INFO[0232] [certificates] Successfully started [rke-bundle-cert] container on host [172.16.17.11] 
INFO[0232] Waiting for [rke-bundle-cert] container to exit on host [172.16.17.11] 
INFO[0232] Container [rke-bundle-cert] is still running on host [172.16.17.11] 
INFO[0233] Waiting for [rke-bundle-cert] container to exit on host [172.16.17.11] 
INFO[0233] [certificates] successfully saved certificate bundle [/opt/rke/etcd-snapshots//pki.bundle.tar.gz] on host [172.16.17.11] 
INFO[0234] [etcd] Successfully started [rke-log-linker] container on host [172.16.17.11] 
INFO[0234] [remove/rke-log-linker] Successfully removed container on host [172.16.17.11] 
INFO[0234] [etcd] Pulling image [rancher/coreos-etcd:v3.2.24-rancher1] on host [172.16.17.12] 
INFO[0253] [etcd] Successfully pulled image [rancher/coreos-etcd:v3.2.24-rancher1] on host [172.16.17.12] 
INFO[0253] [etcd] Successfully started [etcd] container on host [172.16.17.12] 
INFO[0253] [etcd] Saving snapshot [etcd-rolling-snapshots] on host [172.16.17.12] 
INFO[0254] [etcd] Successfully started [etcd-rolling-snapshots] container on host [172.16.17.12] 
INFO[0259] [certificates] Successfully started [rke-bundle-cert] container on host [172.16.17.12] 
INFO[0259] Waiting for [rke-bundle-cert] container to exit on host [172.16.17.12] 
INFO[0259] Container [rke-bundle-cert] is still running on host [172.16.17.12] 
INFO[0260] Waiting for [rke-bundle-cert] container to exit on host [172.16.17.12] 
INFO[0260] [certificates] successfully saved certificate bundle [/opt/rke/etcd-snapshots//pki.bundle.tar.gz] on host [172.16.17.12] 
INFO[0261] [etcd] Successfully started [rke-log-linker] container on host [172.16.17.12] 
INFO[0261] [remove/rke-log-linker] Successfully removed container on host [172.16.17.12] 
INFO[0261] [etcd] Successfully started etcd plane.. Checking etcd cluster health 
INFO[0261] [controlplane] Building up Controller Plane.. 
INFO[0261] [controlplane] Successfully started [kube-apiserver] container on host [172.16.17.12] 
INFO[0261] [healthcheck] Start Healthcheck on service [kube-apiserver] on host [172.16.17.12] 
INFO[0261] [controlplane] Successfully started [kube-apiserver] container on host [172.16.17.11] 
INFO[0261] [healthcheck] Start Healthcheck on service [kube-apiserver] on host [172.16.17.11] 
INFO[0261] [controlplane] Successfully started [kube-apiserver] container on host [172.16.17.10] 
INFO[0261] [healthcheck] Start Healthcheck on service [kube-apiserver] on host [172.16.17.10] 
INFO[0273] [healthcheck] service [kube-apiserver] on host [172.16.17.11] is healthy 
INFO[0273] [healthcheck] service [kube-apiserver] on host [172.16.17.10] is healthy 
INFO[0274] [controlplane] Successfully started [rke-log-linker] container on host [172.16.17.10] 
INFO[0274] [healthcheck] service [kube-apiserver] on host [172.16.17.12] is healthy 
INFO[0274] [remove/rke-log-linker] Successfully removed container on host [172.16.17.10] 
INFO[0274] [controlplane] Successfully started [rke-log-linker] container on host [172.16.17.11] 
INFO[0274] [controlplane] Successfully started [kube-controller-manager] container on host [172.16.17.10] 
INFO[0274] [healthcheck] Start Healthcheck on service [kube-controller-manager] on host [172.16.17.10] 
INFO[0274] [controlplane] Successfully started [rke-log-linker] container on host [172.16.17.12] 
INFO[0274] [remove/rke-log-linker] Successfully removed container on host [172.16.17.11] 
INFO[0274] [remove/rke-log-linker] Successfully removed container on host [172.16.17.12] 
INFO[0274] [controlplane] Successfully started [kube-controller-manager] container on host [172.16.17.12] 
INFO[0274] [healthcheck] Start Healthcheck on service [kube-controller-manager] on host [172.16.17.12] 
INFO[0274] [controlplane] Successfully started [kube-controller-manager] container on host [172.16.17.11] 
INFO[0274] [healthcheck] Start Healthcheck on service [kube-controller-manager] on host [172.16.17.11] 
INFO[0279] [healthcheck] service [kube-controller-manager] on host [172.16.17.10] is healthy 
INFO[0280] [controlplane] Successfully started [rke-log-linker] container on host [172.16.17.10] 
INFO[0280] [healthcheck] service [kube-controller-manager] on host [172.16.17.12] is healthy 
INFO[0280] [remove/rke-log-linker] Successfully removed container on host [172.16.17.10] 
INFO[0280] [healthcheck] service [kube-controller-manager] on host [172.16.17.11] is healthy 
INFO[0280] [controlplane] Successfully started [kube-scheduler] container on host [172.16.17.10] 
INFO[0280] [healthcheck] Start Healthcheck on service [kube-scheduler] on host [172.16.17.10] 
INFO[0280] [controlplane] Successfully started [rke-log-linker] container on host [172.16.17.12] 
INFO[0280] [remove/rke-log-linker] Successfully removed container on host [172.16.17.12] 
INFO[0280] [controlplane] Successfully started [rke-log-linker] container on host [172.16.17.11] 
INFO[0280] [remove/rke-log-linker] Successfully removed container on host [172.16.17.11] 
INFO[0280] [controlplane] Successfully started [kube-scheduler] container on host [172.16.17.12] 
INFO[0280] [healthcheck] Start Healthcheck on service [kube-scheduler] on host [172.16.17.12] 
INFO[0281] [controlplane] Successfully started [kube-scheduler] container on host [172.16.17.11] 
INFO[0281] [healthcheck] Start Healthcheck on service [kube-scheduler] on host [172.16.17.11] 
INFO[0285] [healthcheck] service [kube-scheduler] on host [172.16.17.10] is healthy 
INFO[0285] [controlplane] Successfully started [rke-log-linker] container on host [172.16.17.10] 
INFO[0286] [remove/rke-log-linker] Successfully removed container on host [172.16.17.10] 
INFO[0286] [healthcheck] service [kube-scheduler] on host [172.16.17.12] is healthy 
INFO[0286] [healthcheck] service [kube-scheduler] on host [172.16.17.11] is healthy 
INFO[0286] [controlplane] Successfully started [rke-log-linker] container on host [172.16.17.12] 
INFO[0286] [remove/rke-log-linker] Successfully removed container on host [172.16.17.12] 
INFO[0286] [controlplane] Successfully started [rke-log-linker] container on host [172.16.17.11] 
INFO[0287] [remove/rke-log-linker] Successfully removed container on host [172.16.17.11] 
INFO[0287] [controlplane] Successfully started Controller Plane.. 
INFO[0287] [authz] Creating rke-job-deployer ServiceAccount 
INFO[0287] [authz] rke-job-deployer ServiceAccount created successfully 
INFO[0287] [authz] Creating system:node ClusterRoleBinding 
INFO[0287] [authz] system:node ClusterRoleBinding created successfully 
INFO[0287] Successfully Deployed state file at [./rancher-cluster.rkestate] 
INFO[0287] [state] Saving full cluster state to Kubernetes 
INFO[0287] [state] Successfully Saved full cluster state to Kubernetes ConfigMap: cluster-state 
INFO[0287] [worker] Building up Worker Plane..          
INFO[0287] [sidekick] Sidekick container already created on host [172.16.17.10] 
INFO[0287] [sidekick] Sidekick container already created on host [172.16.17.12] 
INFO[0287] [sidekick] Sidekick container already created on host [172.16.17.11] 
INFO[0287] [worker] Successfully started [kubelet] container on host [172.16.17.10] 
INFO[0287] [healthcheck] Start Healthcheck on service [kubelet] on host [172.16.17.10] 
INFO[0287] [worker] Successfully started [kubelet] container on host [172.16.17.11] 
INFO[0287] [healthcheck] Start Healthcheck on service [kubelet] on host [172.16.17.11] 
INFO[0287] [worker] Successfully started [kubelet] container on host [172.16.17.12] 
INFO[0287] [healthcheck] Start Healthcheck on service [kubelet] on host [172.16.17.12] 
INFO[0292] [healthcheck] service [kubelet] on host [172.16.17.10] is healthy 
INFO[0292] [healthcheck] service [kubelet] on host [172.16.17.12] is healthy 
INFO[0292] [healthcheck] service [kubelet] on host [172.16.17.11] is healthy 
INFO[0293] [worker] Successfully started [rke-log-linker] container on host [172.16.17.10] 
INFO[0293] [worker] Successfully started [rke-log-linker] container on host [172.16.17.12] 
INFO[0293] [remove/rke-log-linker] Successfully removed container on host [172.16.17.10] 
INFO[0293] [worker] Successfully started [rke-log-linker] container on host [172.16.17.11] 
INFO[0293] [remove/rke-log-linker] Successfully removed container on host [172.16.17.12] 
INFO[0293] [worker] Successfully started [kube-proxy] container on host [172.16.17.10] 
INFO[0293] [healthcheck] Start Healthcheck on service [kube-proxy] on host [172.16.17.10] 
INFO[0293] [remove/rke-log-linker] Successfully removed container on host [172.16.17.11] 
INFO[0293] [worker] Successfully started [kube-proxy] container on host [172.16.17.12] 
INFO[0293] [healthcheck] Start Healthcheck on service [kube-proxy] on host [172.16.17.12] 
INFO[0293] [worker] Successfully started [kube-proxy] container on host [172.16.17.11] 
INFO[0293] [healthcheck] Start Healthcheck on service [kube-proxy] on host [172.16.17.11] 
INFO[0298] [healthcheck] service [kube-proxy] on host [172.16.17.10] is healthy 
INFO[0298] [healthcheck] service [kube-proxy] on host [172.16.17.12] is healthy 
INFO[0299] [healthcheck] service [kube-proxy] on host [172.16.17.11] is healthy 
INFO[0299] [worker] Successfully started [rke-log-linker] container on host [172.16.17.10] 
INFO[0299] [worker] Successfully started [rke-log-linker] container on host [172.16.17.12] 
INFO[0299] [remove/rke-log-linker] Successfully removed container on host [172.16.17.10] 
INFO[0299] [remove/rke-log-linker] Successfully removed container on host [172.16.17.12] 
INFO[0299] [worker] Successfully started [rke-log-linker] container on host [172.16.17.11] 
INFO[0299] [remove/rke-log-linker] Successfully removed container on host [172.16.17.11] 
INFO[0299] [worker] Successfully started Worker Plane.. 
INFO[0300] [cleanup] Successfully started [rke-log-cleaner] container on host [172.16.17.10] 
INFO[0300] [cleanup] Successfully started [rke-log-cleaner] container on host [172.16.17.11] 
INFO[0300] [remove/rke-log-cleaner] Successfully removed container on host [172.16.17.10] 
INFO[0300] [remove/rke-log-cleaner] Successfully removed container on host [172.16.17.11] 
INFO[0300] [cleanup] Successfully started [rke-log-cleaner] container on host [172.16.17.12] 
INFO[0300] [remove/rke-log-cleaner] Successfully removed container on host [172.16.17.12] 
INFO[0300] [sync] Syncing nodes Labels and Taints       
INFO[0300] [sync] Successfully synced nodes Labels and Taints 
INFO[0300] [network] Setting up network plugin: canal   
INFO[0300] [addons] Saving ConfigMap for addon rke-network-plugin to Kubernetes 
INFO[0300] [addons] Successfully saved ConfigMap for addon rke-network-plugin to Kubernetes 
INFO[0300] [addons] Executing deploy job rke-network-plugin 
INFO[0316] [addons] Setting up kube-dns                 
INFO[0316] [addons] Saving ConfigMap for addon rke-kube-dns-addon to Kubernetes 
INFO[0316] [addons] Successfully saved ConfigMap for addon rke-kube-dns-addon to Kubernetes 
INFO[0316] [addons] Executing deploy job rke-kube-dns-addon 
INFO[0321] [addons] kube-dns deployed successfully      
INFO[0321] [dns] DNS provider kube-dns deployed successfully 
INFO[0321] [addons] Setting up Metrics Server           
INFO[0321] [addons] Saving ConfigMap for addon rke-metrics-addon to Kubernetes 
INFO[0321] [addons] Successfully saved ConfigMap for addon rke-metrics-addon to Kubernetes 
INFO[0321] [addons] Executing deploy job rke-metrics-addon 
INFO[0326] [addons] Metrics Server deployed successfully 
INFO[0326] [ingress] Setting up nginx ingress controller 
INFO[0326] [addons] Saving ConfigMap for addon rke-ingress-controller to Kubernetes 
INFO[0326] [addons] Successfully saved ConfigMap for addon rke-ingress-controller to Kubernetes 
INFO[0326] [addons] Executing deploy job rke-ingress-controller 
INFO[0331] [ingress] ingress controller nginx deployed successfully 
INFO[0331] [addons] Setting up user addons              
INFO[0331] [addons] no user addons defined              
INFO[0331] Finished building Kubernetes cluster successfully 
```

4、如果操作失败，重新安装需要清理数据：

```
每个节点
su - root
rm -rf /var/lib/rancher/etcd/*
rm -rf /etc/kubernetes/*
docker rm -f `docker ps -aq`
node10
su - rancher
rke remove --config ./rancher-cluster.yml
```

等待30分钟左右，完成后它应显示：Finished building Kubernetes cluster successfully。

5、配置环境变量：
切换到root用户su - root

vi /etc/profile

```
export KUBECONFIG=/home/rancher/kube_config_rancher-cluster.yml
```

保存，并执行：

```
source /etc/profile
```

6、通过kubectl测试您的连接，并查看您的所有节点是否处于Ready状态

```
[root@node10 ~]# kubectl get nodes
NAME           STATUS   ROLES                      AGE    VERSION
172.16.17.10   Ready    controlplane,etcd,worker   4m7s   v1.13.5
172.16.17.11   Ready    controlplane,etcd,worker   4m7s   v1.13.5
172.16.17.12   Ready    controlplane,etcd,worker   4m7s   v1.13.5
```

7、检查集群Pod的运行状况

```
[root@node10 ~]# kubectl get pods --all-namespaces
NAMESPACE       NAME                                      READY   STATUS      RESTARTS   AGE
ingress-nginx   default-http-backend-78fccfc5d9-fb2hn     1/1     Running     0          7m6s
ingress-nginx   nginx-ingress-controller-bzfl2            1/1     Running     0          6m35s
ingress-nginx   nginx-ingress-controller-wsgz2            1/1     Running     0          6m45s
ingress-nginx   nginx-ingress-controller-z7vfr            1/1     Running     0          6m24s
kube-system     canal-hb5wm                               2/2     Running     0          7m19s
kube-system     canal-j79kp                               2/2     Running     0          7m19s
kube-system     canal-nk8hm                               2/2     Running     0          7m19s
kube-system     kube-dns-58bd5b8dd7-j4t7h                 3/3     Running     0          7m16s
kube-system     kube-dns-autoscaler-77bc5fd84-lwnpr       1/1     Running     0          7m15s
kube-system     metrics-server-58bd5dd8d7-7r97s           1/1     Running     0          7m11s
kube-system     rke-ingress-controller-deploy-job-s2nhp   0/1     Completed   0          7m7s
kube-system     rke-kube-dns-addon-deploy-job-dslj9       0/1     Completed   0          7m18s
kube-system     rke-metrics-addon-deploy-job-ghgh7        0/1     Completed   0          7m13s
kube-system     rke-network-plugin-deploy-job-rxwl4       0/1     Completed   0          7m33s
```

保存kube_config_rancher-cluster.yml和rancher-cluster.yml文件的副本,您将需要这些文件来维护和升级Rancher实例。

### Helm

使用Helm在集群上安装tiller服务以管理charts，由于RKE默认启用RBAC, 因此我们需要使用kubectl来创建一个serviceaccount，clusterrolebinding才能让tiller具有部署到集群的权限。

1、在kube-system命名空间中创建ServiceAccount：

```
[rancher@node10 ~]# kubectl -n kube-system create serviceaccount tiller
serviceaccount/tiller created
```

2、创建ClusterRoleBinding以授予tiller帐户对集群的访问权限：

```
[rancher@node10 ~]# kubectl create clusterrolebinding tiller --clusterrole cluster-admin --serviceaccount=kube-system:tiller
clusterrolebinding.rbac.authorization.k8s.io/tiller created
```

3、安装Helm Server(Tiller)

```
[rancher@node10 ~]# helm version  #先查询客户端版本 v2.14.1
Client: &version.Version{SemVer:"v2.14.1", GitCommit:"5270352a09c7e8b6e8c9593002a73535276507c0", GitTreeState:"clean"}
Error: could not find tiller

[rancher@node10 ~]# helm init --service-account tiller   --tiller-image registry.cn-hangzhou.aliyuncs.com/google_containers/tiller:v2.14.1 --stable-repo-url https://kubernetes.oss-cn-hangzhou.aliyuncs.com/charts #安装对应的服务端版本 v2.14.1

验证：
[rancher@node10 ~]# helm version
Client: &version.Version{SemVer:"v2.14.1", GitCommit:"5270352a09c7e8b6e8c9593002a73535276507c0", GitTreeState:"clean"}
Server: &version.Version{SemVer:"v2.14.1", GitCommit:"5270352a09c7e8b6e8c9593002a73535276507c0", GitTreeState:"clean"}
```

# 利用Helm部署高可用rancher集群

# 一、背景

Rancher HA有多种部署方式：

1. Helm HA安装，将Rancher部署在已有的Kubernetes集群中，Rancher将使用集群的etcd存储数据，并利用Kubernetes调度实现高可用性。
2. RKE HA安装，使用RKE工具安装独立的Kubernetes集群，专门用于Rancher HA部署运行，RKE HA安装仅支持Rancher v2.0.8以及之前的版本，Rancher v2.0.8之后的版本使用helm安装Rancher。
   本方案将基于已有的Kubernetes集群，利用Helm安装Rancher HA，并采用四层负载均衡方式。

  

# 二、添加Chart仓库地址

使用helm repo add命令添加Rancher chart仓库地址
Rancher tag和Chart版本选择参考：<https://www.cnrancher.com/docs/rancher/v2.x/cn/installation/server-tags/>

```
[rancher@node10 ~]# helm repo add rancher-stable https://releases.rancher.com/server-charts/stable
"rancher-stable" has been added to your repositories
```

# 三、使用自签名证书安装Rancher server

Rancher server设计默认需要开启SSL/TLS配置来保证安全，将ssl证书以Kubernetes Secret卷的形式传递给rancher server或Ingress Controller。首先创建证书密文，以便Rancher和Ingress Controller可以使用。

## 1、 生成自签名证书

\#脚本

```
#!/bin/bash -e

help ()
{
    echo  ' ================================================================ '
    echo  ' --ssl-domain: 生成ssl证书需要的主域名，如不指定则默认为localhost，如果是ip访问服务，则可忽略；'
    echo  ' --ssl-trusted-ip: 一般ssl证书只信任域名的访问请求，有时候需要使用ip去访问server，那么需要给ssl证书添加扩展IP，多个IP用逗号隔开；'
    echo  ' --ssl-trusted-domain: 如果想多个域名访问，则添加扩展域名（SSL_TRUSTED_DOMAIN）,多个扩展域名用逗号隔开；'
    echo  ' --ssl-size: ssl加密位数，默认2048；'
    echo  ' --ssl-date: ssl有效期，默认10年；'
    echo  ' --ca-date: ca有效期，默认10年；'
    echo  ' --ssl-cn: 国家代码(2个字母的代号),默认CN;'
    echo  ' 使用示例:'
    echo  ' ./create_self-signed-cert.sh --ssl-domain=www.test.com --ssl-trusted-domain=www.test2.com \ '
    echo  ' --ssl-trusted-ip=1.1.1.1,2.2.2.2,3.3.3.3 --ssl-size=2048 --ssl-date=3650'
    echo  ' ================================================================'
}

case "$1" in
    -h|--help) help; exit;;
esac

if [[ $1 == '' ]];then
    help;
    exit;
fi

CMDOPTS="$*"
for OPTS in $CMDOPTS;
do
    key=$(echo ${OPTS} | awk -F"=" '{print $1}' )
    value=$(echo ${OPTS} | awk -F"=" '{print $2}' )
    case "$key" in
        --ssl-domain) SSL_DOMAIN=$value ;;
        --ssl-trusted-ip) SSL_TRUSTED_IP=$value ;;
        --ssl-trusted-domain) SSL_TRUSTED_DOMAIN=$value ;;
        --ssl-size) SSL_SIZE=$value ;;
        --ssl-date) SSL_DATE=$value ;;
        --ca-date) CA_DATE=$value ;;
        --ssl-cn) CN=$value ;;
    esac
done

# CA相关配置
CA_DATE=${CA_DATE:-3650}
CA_KEY=${CA_KEY:-cakey.pem}
CA_CERT=${CA_CERT:-cacerts.pem}
CA_DOMAIN=localhost

# ssl相关配置
SSL_CONFIG=${SSL_CONFIG:-$PWD/openssl.cnf}
SSL_DOMAIN=${SSL_DOMAIN:-localhost}
SSL_DATE=${SSL_DATE:-3650}
SSL_SIZE=${SSL_SIZE:-2048}

## 国家代码(2个字母的代号),默认CN;
CN=${CN:-CN}

SSL_KEY=$SSL_DOMAIN.key
SSL_CSR=$SSL_DOMAIN.csr
SSL_CERT=$SSL_DOMAIN.crt

echo -e "\033[32m ---------------------------- \033[0m"
echo -e "\033[32m       | 生成 SSL Cert |       \033[0m"
echo -e "\033[32m ---------------------------- \033[0m"

if [[ -e ./${CA_KEY} ]]; then
    echo -e "\033[32m ====> 1. 发现已存在CA私钥，备份"${CA_KEY}"为"${CA_KEY}"-bak，然后重新创建 \033[0m"
    mv ${CA_KEY} "${CA_KEY}"-bak
    openssl genrsa -out ${CA_KEY} ${SSL_SIZE}
else
    echo -e "\033[32m ====> 1. 生成新的CA私钥 ${CA_KEY} \033[0m"
    openssl genrsa -out ${CA_KEY} ${SSL_SIZE}
fi

if [[ -e ./${CA_CERT} ]]; then
    echo -e "\033[32m ====> 2. 发现已存在CA证书，先备份"${CA_CERT}"为"${CA_CERT}"-bak，然后重新创建 \033[0m"
    mv ${CA_CERT} "${CA_CERT}"-bak
    openssl req -x509 -sha256 -new -nodes -key ${CA_KEY} -days ${CA_DATE} -out ${CA_CERT} -subj "/C=${CN}/CN=${CA_DOMAIN}"
else
    echo -e "\033[32m ====> 2. 生成新的CA证书 ${CA_CERT} \033[0m"
    openssl req -x509 -sha256 -new -nodes -key ${CA_KEY} -days ${CA_DATE} -out ${CA_CERT} -subj "/C=${CN}/CN=${CA_DOMAIN}"
fi

echo -e "\033[32m ====> 3. 生成Openssl配置文件 ${SSL_CONFIG} \033[0m"
cat > ${SSL_CONFIG} <<EOM
[req]
req_extensions = v3_req
distinguished_name = req_distinguished_name
[req_distinguished_name]
[ v3_req ]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
extendedKeyUsage = clientAuth, serverAuth
EOM

if [[ -n ${SSL_TRUSTED_IP} || -n ${SSL_TRUSTED_DOMAIN} ]]; then
    cat >> ${SSL_CONFIG} <<EOM
subjectAltName = @alt_names
[alt_names]
EOM
    IFS=","
    dns=(${SSL_TRUSTED_DOMAIN})
    dns+=(${SSL_DOMAIN})
    for i in "${!dns[@]}"; do
      echo DNS.$((i+1)) = ${dns[$i]} >> ${SSL_CONFIG}
    done

    if [[ -n ${SSL_TRUSTED_IP} ]]; then
        ip=(${SSL_TRUSTED_IP})
        for i in "${!ip[@]}"; do
          echo IP.$((i+1)) = ${ip[$i]} >> ${SSL_CONFIG}
        done
    fi
fi

echo -e "\033[32m ====> 4. 生成服务SSL KEY ${SSL_KEY} \033[0m"
openssl genrsa -out ${SSL_KEY} ${SSL_SIZE}

echo -e "\033[32m ====> 5. 生成服务SSL CSR ${SSL_CSR} \033[0m"
openssl req -sha256 -new -key ${SSL_KEY} -out ${SSL_CSR} -subj "/C=${CN}/CN=${SSL_DOMAIN}" -config ${SSL_CONFIG}

echo -e "\033[32m ====> 6. 生成服务SSL CERT ${SSL_CERT} \033[0m"
openssl x509 -sha256 -req -in ${SSL_CSR} -CA ${CA_CERT} \
    -CAkey ${CA_KEY} -CAcreateserial -out ${SSL_CERT} \
    -days ${SSL_DATE} -extensions v3_req \
    -extfile ${SSL_CONFIG}

echo -e "\033[32m ====> 7. 证书制作完成 \033[0m"
echo
echo -e "\033[32m ====> 8. 以YAML格式输出结果 \033[0m"
echo "----------------------------------------------------------"
echo "ca_key: |"
cat $CA_KEY | sed 's/^/  /'
echo
echo "ca_cert: |"
cat $CA_CERT | sed 's/^/  /'
echo
echo "ssl_key: |"
cat $SSL_KEY | sed 's/^/  /'
echo
echo "ssl_csr: |"
cat $SSL_CSR | sed 's/^/  /'
echo
echo "ssl_cert: |"
cat $SSL_CERT | sed 's/^/  /'
echo

echo -e "\033[32m ====> 9. 附加CA证书到Cert文件 \033[0m"
cat ${CA_CERT} >> ${SSL_CERT}
echo "ssl_cert: |"
cat $SSL_CERT | sed 's/^/  /'
echo

echo -e "\033[32m ====> 10. 重命名服务证书 \033[0m"
echo "cp ${SSL_DOMAIN}.key tls.key"
cp ${SSL_DOMAIN}.key tls.key
echo "cp ${SSL_DOMAIN}.crt tls.crt"
cp ${SSL_DOMAIN}.crt tls.crt
```

对应官网地址：

<https://www.cnrancher.com/docs/rancher/v2.x/cn/install-prepare/self-signed-ssl/#%E5%9B%9B-%E7%94%9F%E6%88%90%E8%87%AA%E7%AD%BE%E5%90%8D%E8%AF%81%E4%B9%A6>

#执行脚本生成证书

```
[rancher@node10 cert]# sh create_self-signed-cert.sh --ssl-domain=saas.rancher.com --ssl-trusted-ip=172.16.17.10,172.16.17.11,172.16.17.12 --ssl-size=2048 --ssl-date=3650
#生成证书
[rancher@node10 cert]# ll
总用量 44
-rw-r--r-- 1 root root 1131 6月  28 20:12 cacerts.pem
-rw-r--r-- 1 root root   17 6月  28 20:12 cacerts.srl
-rw-r--r-- 1 root root 1675 6月  28 20:12 cakey.pem
-rw-r--r-- 1 root root 5309 6月  28 20:11 create_self-signed-cert.sh
-rw-r--r-- 1 root root  366 6月  28 20:12 openssl.cnf
-rw-r--r-- 1 root root 2303 6月  28 20:12 saas.rancher.com.crt
-rw-r--r-- 1 root root 1078 6月  28 20:12 saas.rancher.com.csr
-rw-r--r-- 1 root root 1679 6月  28 20:12 saas.rancher.com.key
-rw-r--r-- 1 root root 2303 6月  28 20:12 tls.crt
-rw-r--r-- 1 root root 1679 6月  28 20:12 tls.key
```

## 2、使用kubectl创建tls类型的secrets

#创建命名空间

```
[rancher@node10 cert]# kubectl create namespace cattle-system
namespace/cattle-system created
```

#服务证书和私钥密文

```
[rancher@node10 cert]# kubectl -n cattle-system create secret tls tls-rancher-ingress --cert=./tls.crt --key=./tls.key
secret/tls-rancher-ingress created
```

#ca证书密文

```
[rancher@node10 cert]# kubectl -n cattle-system create secret generic tls-ca --from-file=cacerts.pem
secret/tls-ca created
```

## 3、安装rancher server

#使用helm安装rancher HA

```
[root@node10 cert]# helm install rancher-stable/rancher --name rancher2 --namespace cattle-system --set hostname=saas.rancher.com --set ingress.tls.source=secret --set privateCA=true
NAME:   rancher2
LAST DEPLOYED: Fri Jun 28 20:14:53 2019
NAMESPACE: cattle-system
STATUS: DEPLOYED

RESOURCES:
==> v1/ClusterRoleBinding
NAME      AGE
rancher2  0s

==> v1/Deployment
NAME      READY  UP-TO-DATE  AVAILABLE  AGE
rancher2  0/3    3           0          0s

==> v1/Pod(related)
NAME                       READY  STATUS             RESTARTS  AGE
rancher2-57c84cfc98-db5r9  0/1    ContainerCreating  0         0s
rancher2-57c84cfc98-f257c  0/1    ContainerCreating  0         0s
rancher2-57c84cfc98-hxcwn  0/1    ContainerCreating  0         0s

==> v1/Service
NAME      TYPE       CLUSTER-IP  EXTERNAL-IP  PORT(S)  AGE
rancher2  ClusterIP  10.43.12.8  <none>       80/TCP   0s

==> v1/ServiceAccount
NAME      SECRETS  AGE
rancher2  1        0s

==> v1beta1/Ingress
NAME      HOSTS             ADDRESS  PORTS  AGE
rancher2  saas.rancher.com  80, 443  0s


NOTES:
Rancher Server has been installed.

NOTE: Rancher may take several minutes to fully initialize. Please standby while Certificates are being issued and Ingress comes up.

Check out our docs at https://rancher.com/docs/rancher/v2.x/en/

Browse to https://saas.rancher.com

Happy Containering!
```

#查看创建

```
[root@k8s-master03 ~]# kubectl get ns
NAME                         STATUS   AGE
cattle-global-data           Active   2d5h
cattle-system                Active   2d5h

[root@k8s-master03 ~]# kubectl get ingress -n cattle-system           
NAME       HOSTS                 ADDRESS   PORTS     AGE
rancher2   rancher.sumapay.com             80, 443   57m

[root@k8s-master03 ~]# kubectl get service -n cattle-system        
NAME       TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)   AGE
rancher2   ClusterIP   10.111.16.80   <none>        80/TCP    54m

[root@k8s-master03 ~]# kubectl get serviceaccount -n cattle-system           
NAME       TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)   AGE
rancher2   ClusterIP   10.111.16.80   <none>        80/TCP    51m

[root@k8s-master03 ~]# kubectl get ClusterRoleBinding -n cattle-system -l app=rancher2 -o wide
NAME       AGE   ROLE                        USERS   GROUPS   SERVICEACCOUNTS
rancher2   58m   ClusterRole/cluster-admin                    cattle-system/rancher2

[root@k8s-master03 ~]# kubectl get pods -n cattle-system 
NAME                                    READY   STATUS    RESTARTS   AGE
cattle-cluster-agent-594b8f79bb-pgmdt   1/1     Running   5          2d2h
cattle-node-agent-lg44f                 1/1     Running   0          2d2h
cattle-node-agent-zgdms                 1/1     Running   5          2d2h
rancher2-9774897c-622sc                 1/1     Running   0          50m
rancher2-9774897c-czxxx                 1/1     Running   0          50m
rancher2-9774897c-sm2n5                 1/1     Running   0          50m

[root@k8s-master03 ~]# kubectl get deployment -n cattle-system 
NAME                   READY   UP-TO-DATE   AVAILABLE   AGE
cattle-cluster-agent   1/1     1            1           2d4h
rancher2               3/3     3            3           55m
```

## 4、为Agent Pod添加主机别名(/etc/hosts)

如果你没有内部DNS服务器而是通过添加/etc/hosts主机别名的方式指定的Rancher server域名，那么不管通过哪种方式(自定义、导入、Host驱动等)创建K8S集群，K8S集群运行起来之后，因为cattle-cluster-agent Pod和cattle-node-agent无法通过DNS记录找到Rancher server,最终导致无法通信。

解决方法

可以通过给cattle-cluster-agent Pod和cattle-node-agent添加主机别名(/etc/hosts)，让其可以正常通信(前提是IP地址可以互通)。

```
#cattle-cluster-agent pod
kubectl -n cattle-system \
patch deployments cattle-cluster-agent --patch '{
    "spec": {
        "template": {
            "spec": {
                "hostAliases": [
                    {
                        "hostnames":
                        [
                            "saas.rancher.com"
                        ],
                            "ip": "172.16.17.72"
                    }
                ]
            }
        }
    }
}'

#cattle-node-agent pod
kubectl -n cattle-system \
patch  daemonsets cattle-node-agent --patch '{
    "spec": {
        "template": {
            "spec": {
                "hostAliases": [
                    {
                        "hostnames":
                        [
                            "saas.rancher.com"
                        ],
                            "ip": "172.16.17.72"
                    }
                ]
            }
        }
    }
}'
```

至此，rancher HA已部署完毕，由于不是NodePort形式，在没有部署ingress-controller情况下，我们还不能直接去访问rancher服务。
ingress-controller部署请参考[traefik部署与使用](https://blog.51cto.com/fengjicheng/2391250)。