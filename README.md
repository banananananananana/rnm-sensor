Short intro
-Work in progress

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

#install dependencies

#install python 3 pip
sudo apt install python3-pip

#install jc
sudo pip3 install jc

#install filebeat
#https://www.elastic.co/guide/en/beats/filebeat/current/setup-repositories.html

wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
sudo apt-get install apt-transport-https
echo "deb https://artifacts.elastic.co/packages/7.x/apt stable main" | sudo tee -a /etc/apt/sources.list.d/elastic-7.x.list
sudo apt-get update && sudo apt-get install filebeat
sudo systemctl enable filebeat

#update curl with json write-out option
sudo apt remove curl
sudo apt purge curl
sudo apt-get update
sudo apt-get install -y libssl-dev autoconf libtool make unzip
cd /usr/local/src
wget https://curl.haxx.se/download/curl-7.71.1.zip
unzip curl-7.71.1.zip
cd curl-7.71.1
sudo ./buildconf
sudo ./configure --with-ssl 
sudo make
sudo make install
sudo cp /usr/local/bin/curl /usr/bin/curl
curl -V

#Create logging directory and set permissions
sudo mkdir /var/log/rnm-sensor
sudo chown ubuntu:ubuntu -R /var/log/rnm-sensor/



```
