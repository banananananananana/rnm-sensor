# Remote Network Monitor Sensor aka RNM-SENSOR
Determining the health of your network is often based on a central [NMS](https://github.com/librenms/librenms/blob/master/README.md) hosted on your virtualization platform of your, be it on-prem or in the cloud, doing snmp and/or icmp based polling of your network devices. 

To some extent, this may be fine. But in a scenario where you virtualization platform is experiencing problems, the metrics on your NMS may be affected, which will make it hard to track down the problem if you solely rely on these data. 

This project aims to provide a method for doing real time performance analytics of a given network - **as seen from the user**.

It utilizes the raspberry pi as a "sensor" that you can deploy to any part of your network, where it will collect ping and/or curl metrics from defined in the config. 

The config file can be hot-loaded from a URL into your fleet of sensors by setting the config variable `use_remote_config":"true"`. 
This means you will be able to do on the fly troubleshooting, to any given host, in just a couple of minutes - using real time data provided by your sensor network.

### Prerequisites
* Raspberry PI 3/4
* Ubuntu 20.04 64bit for raspberry pi - https://ubuntu.com/download/raspberry-pi 
* ELK stack for visualization

### Install
You can either download our pre-build image and write it to your SD card, or you can go through the manual steps below.

#### Manual install steps

start by updating ubuntu  to the latest and greatest
```
sudo apt update && apt dist-upgrade
sudo reboot
```
