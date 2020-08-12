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
You can either download our pre-build image and write it to your SD card, or you can go through the manual steps below.

#### Manual install steps

start by updating ubuntu  to the latest and greatest
```
sudo apt update && apt dist-upgrade
sudo reboot
```

Edit your `sudo vi /etc/fstab` file, and add the lines below to the file. 
It will ensure the logging directories are stored in memory - minimizing the writes to your SD card.
```
tmpfs           /tmp            tmpfs   nosuid,nodev         0       0
tmpfs           /var/log        tmpfs   nosuid,nodev         0       0
tmpfs           /var/tmp        tmpfs   nosuid,nodev         0       0
```

install package dependencies
```
sudo apt install -y libssl-dev autoconf libtool make unzip python3-pip jq
```

install [JC](https://github.com/kellyjonbrazil/jc/blob/master/README.md) which is a tool for parsing cli output in json
```
sudo pip3 install jc
```

remove pre-packaged curl, and install newest version that has a [json write-out option](https://daniel.haxx.se/blog/2020/03/17/curl-write-out-json/)
```
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
```

Change dir to /opt, install rnm-sensor from git
```
cd /opt
sudo git clone https://github.com/banananananananana/rnm-sensor.git
```

Set the default "ubuntu" user permissions and make rnm-sensor.sh executeable
```
sudo chown ubuntu:ubuntu -R rnm-sensor/
sudo chmod +x rnm-sensor/rnm-sensor.sh
```

install [filebeat](https://www.elastic.co/guide/en/beats/filebeat/current/setup-repositories.html) for log shipping to your ELK stack 
```
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
sudo apt-get install apt-transport-https
echo "deb https://artifacts.elastic.co/packages/7.x/apt stable main" | sudo tee -a /etc/apt/sources.list.d/elastic-7.x.list
sudo apt-get update && sudo apt-get install filebeat
sudo systemctl enable filebeat
```

### Configuration

Install and enable rnm-sensor as a systemd service

Add the service file to systemd `sudo vi /etc/systemd/system/rnm-sensor.service` and paste the command below into the file.
```
[Unit]
Description=RNM sensor
After=network.service

[Service]
ExecStartPre=+/usr/bin/mkdir -p /var/log/rnm-sensor
ExecStartPre=+/usr/bin/chown ubuntu:ubuntu -R /var/log/rnm-sensor/
Type=simple
Restart=always
RestartSec=1
User=ubuntu
ExecStart=/opt/rnm-sensor/rnm-sensor.sh

[Install]
WantedBy=multi-user.target
```

Enable and start the service by typing
```
sudo systemctl enable rnm-sensor
sudo systemctl start rnm-sensor.service
```

The service will now collect performance data, and log to the files `curl_output-rnm-sensor.log and` `ping_output-rnm-sensor.log` in the directory `/var/log/rnm-sensor`
