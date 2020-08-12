## Remote Network Monitor Sensor aka RNM-SENSOR
Determining the health of your network is often based on a central [NMS](https://github.com/librenms/librenms/blob/master/README.md) hosted on your virtualization platform of your, be it on-prem or in the cloud, doing snmp and/or icmp based polling of your network devices. 

To some extent, this may be fine. But in a scenario where you virtualization platform is experiencing problems, the metrics on your NMS may be affected, which will make it hard to track down the problem if you solely rely on these data. 

This project aims to provide a method for doing real time performance analytics of a given network - **as seen from the user**.

It utilizes the raspberry pi as a "sensor" that you can deploy to any part of your network, where it will collect ping and/or curl metrics from defined in the config. 

The config file can be hot-loaded from a URL into your fleet of sensors by setting the config variable `use_remote_config":"true"`. This means you will be able to do on the fly troubleshooting to any given host in just a couple of minutes - using real time data provided by your sensor network.

Installation - requires ubuntu 20.04 64bit for raspberry pi https://ubuntu.com/download/raspberry-pi

```
#start by updating ubuntu  to the latest and greatest
sudo apt update && apt dist-upgrade
sudo reboot

#add the following lines in order to use RAM as local logging - this will minimize SD card IO
sudo vi /etc/fstab
tmpfs           /tmp            tmpfs   nosuid,nodev         0       0
tmpfs           /var/log        tmpfs   nosuid,nodev         0       0
tmpfs           /var/tmp        tmpfs   nosuid,nodev         0       0

#Create logging directory and set permissions
sudo mkdir /var/log/rnm-sensor
sudo chown ubuntu:ubuntu -R /var/log/rnm-sensor/

#install package dependencies
sudo apt install -y libssl-dev autoconf libtool make unzip python3-pip jq

#install JC which is a tool for parsing cli output in json
#github.com/kellyjonbrazil/jc/blob/master/README.md
sudo pip3 install jc

#remove pre-packaged curl, and install newest version that has a json write-out option
sudo apt remove curl
sudo apt purge curl
sudo apt-get update
cd /usr/local/src
sudo wget https://curl.haxx.se/download/curl-7.71.1.zip
sudo unzip curl-7.71.1.zip
cd curl-7.71.1
sudo ./buildconf
sudo ./configure --with-ssl 
sudo make
sudo make install
sudo cp /usr/local/bin/curl /usr/bin/curl
curl -V

#move to /opt, git clone rnm-sensor, set the default "ubuntu" user permissions and make rnm-sensor.sh executeable
cd /opt
sudo git clone https://github.com/banananananananana/rnm-sensor.git
sudo chown ubuntu:ubuntu -R rnm-sensor/
sudo chmod +x rnm-sensor/rnm-sensor.sh

#install filebeat
#https://www.elastic.co/guide/en/beats/filebeat/current/setup-repositories.html

wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
sudo apt-get install apt-transport-https
echo "deb https://artifacts.elastic.co/packages/7.x/apt stable main" | sudo tee -a /etc/apt/sources.list.d/elastic-7.x.list
sudo apt-get update && sudo apt-get install filebeat
sudo systemctl enable filebeat


```
