#!/bin/bash

tcp_ports=(6379 44205 9999 46448 26257 8050 53 822 8055 631 8088 8761 16379 10050 9092 44519 7880 3881 80 443 8999 5000 22)
udp_ports=(53 67 323 5353 50947)

for i in ${tcp_ports[@]}
do
  firewall-cmd --zone=public --add-port=${i}/tcp --permanent
  echo "add ${i} success"
done

for i in ${udp_ports[@]}
do
  firewall-cmd --zone=public --add-port=${i}/udp --permanent
  echo "add ${i} success"
done

firewall-cmd --reload
echo "reload firewalld success"