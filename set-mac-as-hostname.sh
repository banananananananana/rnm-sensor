#!/usr/bin/env bash
hostnamectl set-hostname "$(cat /sys/class/net/`ip route|grep default|sed -E 's/.*dev (\S*).*/\1/'`/address|sed 's/:/-/g')"
