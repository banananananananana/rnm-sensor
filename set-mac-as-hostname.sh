#!/usr/bin/env bash
HOSTNAME=$(cat /sys/class/net/`ip route|grep default|sed -E 's/.*dev (\S*).*/\1/'`/address|sed 's/:/-/g')
perl -pi -e "s/127.0.0.1.*/127.0.0.1 localhost $HOSTNAME/" /etc/hosts
hostnamectl set-hostname $HOSTNAME
