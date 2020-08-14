#!/usr/bin/env bash
hostnamectl set-hostname $(/usr/bin/cat /sys/class/net/eth0/address | sudo sed s/:/-/g)
