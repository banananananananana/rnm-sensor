# Remote Network Monitor Sensor aka RNM-SENSOR
Determining the health of your network is often based on a central [NMS](https://github.com/librenms/librenms/blob/master/README.md) hosted on your virtualization platform of your, be it on-prem or in the cloud, doing snmp and/or icmp based polling of your network devices. 

To some extent, this may be fine. But in a scenario where you virtualization platform is experiencing problems, the metrics on your [NMS](https://github.com/librenms/librenms/blob/master/README.md) may be affected. Or say you have a switch or router that is silently discarding packets, yet it reports no problems to you NMS. Tracking down the problem will be difficult if these data are all you have to go by. 

This project aims to provide an inexpensive method for doing real time network performance analytics - **as seen from the user**.

It utilizes the raspberry pi as a "sensor" that you can deploy to any part of your network, where it will collect ping and/or curl metrics towards hosts defined in the config. 

The config file can be hot-loaded from a URL into your fleet of sensors by setting the config variable `use_remote_config":"true"`. 
This means you will be able to do on the fly troubleshooting, to any given host, in just a couple of minutes - using real time data provided by your sensor network.

### Prerequisites
* Raspberry PI 3/4
* Ubuntu 20.04 64bit for raspberry pi - https://ubuntu.com/download/raspberry-pi 
* ELK stack for visualization

### Install
You can either download our pre-build image and write it to your SD card, or you can run the included installer.

```
cd /opt
sudo git clone https://github.com/banananananananana/rnm-sensor.git 
cd rnm-sensor
sudo ./install.sh
```

The install script does the following
* Installs required packages in order to run rnm-sensor (libssl-dev autoconf libtool make unzip python3-pip jq net-tools jc)
* Updates curl to the latest version (which supports json write-out logging)
* Creates tmpfs for /tmp/ /var/log/ /var/tmp/ in order to minimize SD wear
* Adds a systemd service called rnm-sensor
* Sets the MAC address of the PI as hostname. This makes it possible to clone the SD card for mass deployments, while being able to track each PI within the network
