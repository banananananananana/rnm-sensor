#check if script is run as root
if [ $(id -u) != 0 ] ; then
    echo "Please run as root"
    exit
fi

#start by updating ubuntu to the latest and greatest
apt update -y
apt dist-upgrade -y

#add logging directories to tmpfs to minimize sd card io
echo "tmpfs           /tmp            tmpfs   nosuid,nodev         0       0">>/etc/fstab
echo "tmpfs           /var/log        tmpfs   nosuid,nodev         0       0">>/etc/fstab
echo "tmpfs           /var/tmp        tmpfs   nosuid,nodev         0       0">>/etc/fstab

#install package dependencies
sudo apt install -y libssl-dev autoconf libtool make unzip python3-pip jq net-tools
sudo pip3 install jc

#upgrade curl to json out version
apt remove curl -y
apt purge curl -y
apt-get update
cd /usr/local/src
sudo wget https://curl.haxx.se/download/curl-7.71.1.zip
sudo unzip curl-7.71.1.zip
cd curl-7.71.1
./buildconf
./configure --with-ssl
make
make install
cp /usr/local/bin/curl /usr/bin/curl

#set permissions
chown ubuntu:ubuntu -R /opt/rnm-sensor/
chmod +x /opt/rnm-sensor/rnm-sensor.sh

#add systemd service
mv /opt/rnm-sensor/rnm-sensor.service /etc/systemd/system/rnm-sensor.service

#enable service
systemctl enable rnm-sensor

#echo ending
echo ""
echo "ALL DONE - please reboot"
