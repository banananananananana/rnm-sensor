#!/usr/bin/env bash

# Check if script is run as root
if [ "$(id -u)" != 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Start by updating ubuntu to the latest and greatest
apt update -y
apt dist-upgrade -y

# Add logging directories to tmpfs to minimize sd card io
{
  echo "tmpfs /tmp      tmpfs nosuid,nodev  0 0"
  echo "tmpfs /var/log  tmpfs nosuid,nodev  0 0"
  echo "tmpfs /var/tmp  tmpfs nosuid,nodev  0 0"
} >>/etc/fstab

# Install package dependencies
apt install -y libssl-dev autoconf libtool make unzip python3-pip jq net-tools apt-transport-https
pip3 install jc

# Upgrade curl to a version that supports "json" write-out
apt purge curl -y
apt update
cd /usr/local/src || exit 2

wget https://curl.haxx.se/download/curl-7.71.1.zip
unzip curl-7.71.1.zip

cd curl-7.71.1 || exit 2

./buildconf && ./configure --with-ssl
make && make install
ln -s /usr/local/bin/curl /usr/bin/curl

# Install filebeat and copy template config
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | apt-key add -
echo "deb https://artifacts.elastic.co/packages/7.x/apt stable main" | tee -a /etc/apt/sources.list.d/elastic-7.x.list
apt update && apt install -y filebeat
cp /opt/rnm-sensor/filebeat/filebeat-template.yml /etc/filebeat/filebeat.yml
systemctl enable filebeat

# Set permissions
chown ubuntu:ubuntu -R /opt/rnm-sensor/
chmod +x /opt/rnm-sensor/rnm-sensor.sh

# Add systemd service
cp /opt/rnm-sensor/rnm-sensor.service /etc/systemd/system/rnm-sensor.service

# Enable RNM-sensor service
systemctl enable rnm-sensor
systemctl start rnm-sensor

# Echo ending
echo ""
echo "ALL DONE - please reboot"
