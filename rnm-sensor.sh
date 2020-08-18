#!/usr/bin/env bash

# Trap those background proces id's
trap "exit" INT TERM ERR
trap "kill 0" EXIT

CONFIG_FILE="/opt/rnm-sensor/rnm-sensor-config.json"
PING_LOG_FILE="/var/log/rnm-sensor/ping_output-rnm-sensor.log"
CURL_LOG_FILE="/var/log/rnm-sensor/curl_output-rnm-sensor.log"

# Check for local or remote config file
while true; do
  echo "$(date -u) - checking for config file changes"

  if [[ $(jq -r '.[] | .config_file_source[] | .use_remote_config' <$CONFIG_FILE) == true ]]; then
    echo "$(date -u) - remote config file option is set, downloading file..."
    curl -m 5 -s -o $CONFIG_FILE "$(jq -r '.[] | .config_file_source[] | .source' <$CONFIG_FILE)"
  fi

  sleep 10
done &

# Sleeping 1 second so the config file will have time to be written before proceeding
sleep 1

# Set input file variables
echo "$(date -u) - setting ping destinations"
ping_hosts=$(jq -r '.[] | .ping_destinations[] | .destination' <$CONFIG_FILE)

echo "$(date -u) - setting curl destinations"
curl_hosts=$(jq -r '.[] | .curl_destinations[] | .destination' <$CONFIG_FILE)

# Start ping loop
while true; do
  for host in $ping_hosts; do
    ping -DOc 10 "$host" | jc --ping >>$PING_LOG_FILE &
  done

  sleep 10

done &

# Start curl loop
while true; do
  for host in $curl_hosts; do
    curl -Isw '%{json}' "$host" -o /dev/null | jq --arg now "$(date +%s%3N)" '. += { "curl_timestamp": $now }' | jq -c . >>$CURL_LOG_FILE
  done

  sleep 10

done &

echo "$(date -u) - rnm-sensor startup complete"
wait
