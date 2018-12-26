#/bin/bash
UNISON=`ps -ef |grep -v grep|grep -c inotifywait`
if [ ${UNISON} -lt 1 ]
then
ip2="172.17.14.219"
src2="/var/tgw/"
dst2="/var/tgw/ "
/usr/local/bin/inotifywait -mrq -e create,delete,modify,move $src2 | while read line
do
/usr/local/bin/unison -batch $src2 ssh://$ip2/$dst2
echo -n "$line " >> /var/log/inotify/inotify$(date +%u).log
echo ` date +%F\ %T " " -f1-4` >> /var/log/inotify/inotify$(date +%u).log
done
fi

