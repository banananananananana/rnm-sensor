#!/usr/bin/env bash

#trap those background proces id's
trap "exit" INT TERM ERR
trap "kill 0" EXIT

#check for local or remote config file
while true; do
  echo "$(date -u) - checking for config file changes"
    if [ $(jq -r '.[] | .config_file_source[] | .use_remote_config' /opt/rnm-sensor/rnm-sensor-config.json) == true ]
      then
      echo "$(date -u) - remote config file option is set, downloading file..."
      curl -m 5 -s -o /opt/rnm-sensor/rnm-sensor-config.json $(jq -r '.[] | .config_file_source[] | .source' /opt/rnm-sensor/rnm-sensor-config.json)
      fi
  sleep 10
done &

#sleeping 1 so the config file will have time to be written before proceeding
sleep 1

#set input file variables
echo "$(date -u) - setting ping destinations"
ping_hosts=$(cat /opt/rnm-sensor/rnm-sensor-config.json |  jq -r '.[] | .ping_destinations[] | .destination')
echo "$(date -u) - setting curl destinations"
curl_hosts=$(cat /opt/rnm-sensor/rnm-sensor-config.json |  jq -r '.[] | .curl_destinations[] | .destination')

#start ping loop
while true; do
    for line in $(echo "$ping_hosts"); do
      ping -D -O -c 1 "$line" | jc --ping >>/var/log/rnm-sensor/ping_output-rnm-sensor.log &
    done
  sleep 10
done &

#start curl loop
while true; do
    for line in $(cat /opt/rnm-sensor/rnm-sensor-config.json |  jq -r '.[] | .curl_destinations[] | .destination'); do
        curl -I -s --write-out '%{json}' "$line" -o /dev/null | jq --arg now "$(date +%s%3N)" '. += {"curl_timestamp":$now}' |  jq -c . >>/var/log/rnm-sensor/curl_output-rnm-sensor.log
    done
    sleep 10
done &

echo "$(date -u) - rnm-sensor startup complete"
wait
