环境 主节点 172.181.53.18 







### 关闭防火墙

systemctl stop firewalld.service
systemctl disable firewalld.service
sed -i 's/SELINUX=enforcing/SELINUX=disabled/g' /etc/selinux/config



### 安装docker

#安装这个软件是为了使用yum-config-manager
yum -y install yum-utils  


#卸载已安装的docker（如果以前安装过docker）


yum remove docker docker-common docker-selinux docker-engine -y

yum install -y yum-utils device-mapper-persistent-data lvm2

 yum-config-manager --add-repo http://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo

yum list docker-ce --showduplicates | sort -r


yum makecache fast

 yum install docker-ce -y



### 关闭交换内存

swapoff -a

sed -i 's/.*swap.*/#&/' /etc/fstab

```
# vi /etc/fstab
//将其中交换分区一行使用注释符屏蔽起来，比如：
# /etc/fstab: static file system information.
#
# Use 'blkid' to print the universally unique identifier for a
# device; this may be used with UUID= as a more robust way to name devices
# that works even if disks are added and removed. See fstab(5).
#
# <file system> <mount point>   <type>  <options>       <dump>  <pass>
/dev/mapper/userver--vg-root /               ext4    errors=remount-ro 0       1
#/dev/mapper/userver--vg-swap_1 none            swap    sw              0       0
/dev/fd0        /media/floppy0  auto    rw,user,noauto,exec,utf8 0       0
```

### 设置hostanme和hosts文件

 sed -i 's/localhost.localdomain/node16/g' /etc/hostname
 hostname node16

 echo '172.181.53.18      node18'>>/etc/hosts
 echo '172.181.53.17      node17'>>/etc/hosts
 echo '172.181.53.16      node16'>>/etc/hosts



## 脚本关闭防护墙和安装docker-ce 、关闭交换内存

```
#！/bin/bash
#关闭防火墙
systemctl stop firewalld.service
systemctl disable firewalld.service
#关闭selinux
sed -i 's/SELINUX=enforcing/SELINUX=disabled/g' /etc/selinux/config

#卸载已安装的docker（如果以前安装过docker）
#yum remove docker docker-common docker-selinux docker-engine -y
#安装这个软件是为了使用yum-config-manager
yum install -y yum-utils device-mapper-persistent-data lvm2
yum-config-manager --add-repo http://mirrors.aliyun.com/docker-ce/linux/centos/dockerce.repo
yum list docker-ce --showduplicates | sort -r
yum makecache fast
yum install docker-ce -y
systemctl start docker
systemctl enable docker

#关闭交换内存
swapoff -a
sed -i 's/.*swap.*/#&/' /etc/fstab


 cat <<EOF >  /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
EOF

sysctl --system
 
cat <<EOF > /etc/yum.repos.d/kubernetes.repo
[kubernetes]
name=Kubernetes
baseurl=https://mirrors.aliyun.com/kubernetes/yum/repos/kubernetes-el7-x86_64/
enabled=1
gpgcheck=1
repo_gpgcheck=1
gpgkey=https://mirrors.aliyun.com/kubernetes/yum/doc/yum-key.gpg https://mirrors.aliyun.com/kubernetes/yum/doc/rpm-package-key.gpg
EOF
#安装kubeadm
yum install -y epel-release  && yum install -y net-tools wget vim  ntpdate
yum install -y kubelet kubeadm kubectl kubernetes-cni
systemctl enable kubelet && systemctl start kubelet


```



### 脚本拉取k8s v1.14.1 相关镜像

```

echo ""
echo "=========================================================="
echo "Pull Kubernetes v1.14.1 Images from aliyuncs.com ......"
echo "=========================================================="
echo ""

MY_REGISTRY=registry.cn-hangzhou.aliyuncs.com/openthings

## 拉取镜像
docker pull ${MY_REGISTRY}/k8s-gcr-io-kube-apiserver:v1.14.1
docker pull ${MY_REGISTRY}/k8s-gcr-io-kube-controller-manager:v1.14.1
docker pull ${MY_REGISTRY}/k8s-gcr-io-kube-scheduler:v1.14.1
docker pull ${MY_REGISTRY}/k8s-gcr-io-kube-proxy:v1.14.1
docker pull ${MY_REGISTRY}/k8s-gcr-io-etcd:3.3.10
docker pull ${MY_REGISTRY}/k8s-gcr-io-pause:3.1
docker pull ${MY_REGISTRY}/k8s-gcr-io-coredns:1.3.1

## 添加Tag
docker tag ${MY_REGISTRY}/k8s-gcr-io-kube-apiserver:v1.14.1 k8s.gcr.io/kube-apiserver:v1.14.1
docker tag ${MY_REGISTRY}/k8s-gcr-io-kube-scheduler:v1.14.1 k8s.gcr.io/kube-scheduler:v1.14.1
docker tag ${MY_REGISTRY}/k8s-gcr-io-kube-controller-manager:v1.14.1 k8s.gcr.io/kube-controller-manager:v1.14.1
docker tag ${MY_REGISTRY}/k8s-gcr-io-kube-proxy:v1.14.1 k8s.gcr.io/kube-proxy:v1.14.1
docker tag ${MY_REGISTRY}/k8s-gcr-io-etcd:3.3.10 k8s.gcr.io/etcd:3.3.10
docker tag ${MY_REGISTRY}/k8s-gcr-io-pause:3.1 k8s.gcr.io/pause:3.1
docker tag ${MY_REGISTRY}/k8s-gcr-io-coredns:1.3.1 k8s.gcr.io/coredns:1.3.1

echo ""
echo "=========================================================="
echo "Pull Kubernetes v1.14.1 Images FINISHED."
echo "into registry.cn-hangzhou.aliyuncs.com/openthings, "
echo "           by openthings@https://my.oschina.net/u/2306127."
echo "=========================================================="

echo ""

```



### 用`kubeadm`安装`k8s   `

 172.181.53.18 是网卡`IP`地址、10.244.0.0/16是用于容器的`IP`地段

```
kubeadm init --kubernetes-version=v1.14.1 --apiserver-advertise-address=172.181.53.18 --pod-network-cidr=10.244.0.0/16
```

按照提示

```
mkdir -p $HOME/.kube
cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
chown $(id -u):$(id -g) $HOME/.kube/config

```



需要在k8s 里面安装  配置文件可以网上找

 kubectl apply -f kube-flannel.yml



安装rancher

docker pull rancher/rancher 
docker run -d --restart=unless-stopped -p 80:80 -p 443:443 rancher/rancher:latest