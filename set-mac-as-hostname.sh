#!/usr/bin/env bash
hostnamectl set-hostname "$(sed s/:/-/g </sys/class/net/eth0/address)"
