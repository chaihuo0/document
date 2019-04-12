#### nginx编译安装

拷贝文件nginx_runtime文件夹到/omipay/

```
yum -y install gcc pcre pcre-devel zlib zlib-devel openssl openssl-devel
```

先安装LuaJIT-2.0.2

```
cd /omipay/nginx_runtime
tar -zxvf LuaJIT-2.0.2.tar.gz
cd LuaJIT-2.0.2
make PREFIX=/usr/local/nginx/lua
make install PREFIX=/usr/local/nginx/lua
```

`vi /etc/profile`，在最后添加2行

```
export LUAJIT_LIB=/usr/local/nginx/lua/lib
export LUAJIT_INC=/usr/local/nginx/lua/include/luajit-2.0
```

进入nginx_runtime

```
cd /omipay/nginx_runtime
./Install_nginx1.13.10.sh install
chown -R nobody:root /usr/local/nginx
ln -s /usr/local/nginx/sbin/nginx /usr/bin/nginx
```

`Install_nginx1.13.10.sh`内容

```shell
function Install_nginx()
{

    echo "============================Install Nginx================================="
    #groupadd www
    #useradd -s /sbin/nologin -g www www

    #tar -zxvf LuaJIT-2.0.2.tar.gz
    #cd LuaJIT-2.0.2
    #sed -i -r "s#(\export PREFIX=).*#\1${install_dir}nginx/lua#g" Makefile
    #make && make install
    #cd ..
    #
    #sed -i '/^export LUAJIT_LIB=.*/d' /etc/profile
    #echo -e export LUAJIT_LIB=${install_dir}nginx/lua/lib >>/etc/profile    
    #
    #sed -i '/^export LUAJIT_INC=.*/d' /etc/profile
    #echo -e export LUAJIT_INC=${install_dir}nginx/lua/include/luajit-2.0 >> /etc/profile 

    . /etc/profile

    #tar -zxvf echo-nginx-module-0.56.tar.gz
    unzip echo-nginx-module
    tar -zxvf lua-nginx-module-0.10.11.tar.gz
    tar -zxvf ngx_devel_kit-v0.2.19.tar.gz


    tar  -zxvf nginx-1.13.10.tar.gz 
    cd nginx-1.13.10
    ./configure --prefix=${install_dir}nginx \
    --user=www  \
    --group=www \
    --with-http_stub_status_module \
    --with-http_ssl_module \
    --with-ld-opt="-Wl,-rpath,/usr/local/nginx/lua/lib" \
    --http-client-body-temp-path=cache/client_body_temp \
    --http-proxy-temp-path=cache/proxy_temp \
    --http-fastcgi-temp-path=cache/fastcgi_temp \
    --http-uwsgi-temp-path=cache/uwsgi_temp \
    --http-scgi-temp-path=cache/scgi_temp \
    --add-module=$cur_dir/echo-nginx-module-master  \
    --add-module=$cur_dir/lua-nginx-module-0.10.11 \
    --add-module=$cur_dir/headers-more-nginx-module-master \
    --add-module=$cur_dir/ngx_devel_kit-0.2.19 

    make -j 10

    make install
    exit

    sed  -i "#^${install_dir}nginx/lua/lib$#d" /etc/ld.so.conf
    echo "${install_dir}nginx/lua/lib" >>/etc/ld.so.conf
    ldconfig

}

if [[ $1 == 'install' ]];then
   cur_dir=`pwd`
   install_dir='/usr/local/'
   export PATH=$PATH:/bin:/sbin:/usr/bin:/usr/sbin:${install_dir}bin:${install_dir}sbin:~/bin

   Install_nginx
fi
```



