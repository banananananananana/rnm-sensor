#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Remote Network Monitor Sensor."""


import json
import logging
import multiprocessing as mp
import re
import signal
import subprocess
import time
from typing import List

import requests
import multiprocessing_logging

import jc.parsers.dig
import jc.parsers.ping
import jc.parsers.traceroute


BASEDIR = "/opt/rnm-sensor/"
CONFIG_FILENAME = BASEDIR + "rnm-sensor-config.json"
TEST_INTERVAL = 60.0
REMOTE_CHECK_INTERVAL = 300
PROBE_TIMEOUT = 5


def load_config():
    """Load in the local config."""
    global CONFIG
    try:
        with open(CONFIG_FILENAME, "r") as config_file:
            CONFIG = json.loads(config_file.read())
            config_file.close()
    except IOError as error:
        print("ERROR: Cannot open configfile '{}', {}".format(CONFIG_FILENAME, error))
    global PROBES
    for target in CONFIG["targets"]:
        for probe in target["probes"]:
            PROBES[probe].append(target)


def check_remote_config():
    """Load remote config if required."""
    global CONFIG
    while True:
        if CONFIG["config_file_source"][0]["use_remote_config"]:
            if "source" in CONFIG["config_file_source"][0]:
                SENSOR_LOG.info("Remote config required, fetching configuration ..")
                req = requests.get(
                    CONFIG["config_file_source"][0]["source"], stream=True
                )
                if req.status_code == 200:
                    remote_conf = req.json()
                    if CONFIG == remote_conf:
                        SENSOR_LOG.info("Remote config matches local config.")
                    else:
                        SENSOR_LOG.info(
                            "Remote config differs from local, updating local .."
                        )
                        CONFIG = remote_conf
                        try:
                            with open(CONFIG_FILENAME, "w") as local_config_file:
                                json.dump(
                                    remote_conf,
                                    local_config_file,
                                    indent=4,
                                    sort_keys=True,
                                )
                                local_config_file.close()
                                SENSOR_LOG.info(
                                    "New local config has been written to disk."
                                )
                        except IOError as error:
                            SENSOR_LOG.error(
                                "ERROR: Cannot write to configfile '%s', %s",
                                CONFIG_FILENAME,
                                error,
                            )

                else:
                    print(
                        "Loading remote config failed with status code:",
                        req.status_code,
                    )
        else:
            break

        time.sleep(
            REMOTE_CHECK_INTERVAL - ((time.time() - STARTTIME) % REMOTE_CHECK_INTERVAL)
        )


def dig(dest: str) -> None:
    """Perform ns lookup and print output."""
    try:
        output = subprocess.run(
            ["/usr/bin/dig", dest],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            timeout=PROBE_TIMEOUT,
        )
        dig_result = jc.parsers.dig.parse(output.stdout.decode())[0]
        dig_result["dig_timestamp"] = time.time()
        DIG_LOG.info(json.dumps(dig_result))
    except subprocess.CalledProcessError as error:
        SENSOR_LOG.info("ERROR: %s", error)
    except subprocess.TimeoutExpired as error:
        SENSOR_LOG.info("ERROR: %s", error)


def curl(dest: str) -> None:
    """Curl destination and print output."""
    try:
        output = subprocess.run(
            ["/usr/bin/curl", "-I", "-w '%{json}'", dest],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            timeout=PROBE_TIMEOUT,
        )
        curl_result = json.loads(
            re.match(r"^ '(.*)'$", output.stdout.decode().split("\n")[-1]).groups()[0]
        )
        curl_result["curl_timestamp"] = time.time()
        CURL_LOG.info(json.dumps(curl_result))
    except subprocess.CalledProcessError as error:
        SENSOR_LOG.info("ERROR: %s", error)
    except subprocess.TimeoutExpired as error:
        SENSOR_LOG.info("ERROR: %s", error)


def ping(dest: str) -> None:
    """Ping host and print output."""
    try:
        output = subprocess.run(
            ["/usr/bin/ping", "-DO", "-c1", "-W3", dest],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            timeout=PROBE_TIMEOUT,
        )
        ping_result = jc.parsers.ping.linux_parse(output.stdout.decode())
        ping_result["ping_timestamp"] = time.time()
        PING_LOG.info(json.dumps(ping_result))
    except subprocess.CalledProcessError as error:
        SENSOR_LOG.info("ERROR: %s", error)
    except subprocess.TimeoutExpired as error:
        SENSOR_LOG.info("ERROR: %s", error)


def traceroute(dest: str) -> None:
    """Perform traceroute and print output."""
    try:
        output = subprocess.run(
            ["/usr/sbin/traceroute", "-w1", "--mtu", dest],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            timeout=PROBE_TIMEOUT,
        )
        traceroute_output = jc.parsers.traceroute.parse(output.stdout.decode())
        traceroute_output["traceroute_timestamp"] = time.time()
        TRACEROUTE_LOG.info(json.dumps(traceroute_output))
    except subprocess.CalledProcessError as error:
        SENSOR_LOG.info("ERROR: %s", error)
    except subprocess.TimeoutExpired as error:
        SENSOR_LOG.info("ERROR: %s", error)


def signal_handler(sig, frame):
    """Exit gracefully."""
    print("Signal handler called with signal", sig)
    exit(0)


def init_logs() -> List[str]:
    """Initialize the required logfiles."""
    log_path = CONFIG["logging"]["path"]
    logs_started = []

    if CONFIG["logging"]["sensor"]:
        filename = log_path + CONFIG["logging"]["sensor"]
        sensor_log_formatter = (
            "%(asctime)s [%(levelname)s]: %(message)s in %(pathname)s:%(lineno)d"
        )
        global SENSOR_LOG
        # SENSOR_LOG = logging.getLogger('sensor')
        SENSOR_LOG.setLevel(logging.INFO)
        sensor_log_filehandler = logging.FileHandler(filename)
        sensor_log_filehandler.setLevel(logging.INFO)
        sensor_log_filehandler.setFormatter(logging.Formatter(sensor_log_formatter))
        SENSOR_LOG.addHandler(sensor_log_filehandler)
        logs_started.append("sensor")

    if PROBES["curl"] or PROBES["all"]:
        filename = log_path + CONFIG["logging"]["probes"]["curl"]
        global CURL_LOG
        CURL_LOG = logging.getLogger("curl")
        CURL_LOG.setLevel(logging.INFO)
        curl_log_filehandler = logging.FileHandler(filename)
        curl_log_filehandler.setLevel(logging.INFO)
        curl_log_filehandler.setFormatter(logging.Formatter())
        CURL_LOG.addHandler(curl_log_filehandler)
        logs_started.append("curl")

    if PROBES["dig"] or PROBES["all"]:
        filename = log_path + CONFIG["logging"]["probes"]["dig"]
        global DIG_LOG
        DIG_LOG = logging.getLogger("dig")
        DIG_LOG.setLevel(logging.INFO)
        dig_log_filehandler = logging.FileHandler(filename)
        dig_log_filehandler.setLevel(logging.INFO)
        dig_log_filehandler.setFormatter(logging.Formatter())
        DIG_LOG.addHandler(dig_log_filehandler)
        logs_started.append("dig")

    if PROBES["ping"] or PROBES["all"]:
        filename = log_path + CONFIG["logging"]["probes"]["ping"]
        global PING_LOG
        PING_LOG = logging.getLogger("ping")
        PING_LOG.setLevel(logging.INFO)
        ping_log_filehandler = logging.FileHandler(filename)
        ping_log_filehandler.setLevel(logging.INFO)
        ping_log_filehandler.setFormatter(logging.Formatter())
        PING_LOG.addHandler(ping_log_filehandler)
        logs_started.append("ping")

    if PROBES["traceroute"] or PROBES["all"]:
        filename = log_path + CONFIG["logging"]["probes"]["traceroute"]
        global TRACEROUTE_LOG
        TRACEROUTE_LOG = logging.getLogger("traceroute")
        TRACEROUTE_LOG.setLevel(logging.INFO)
        traceroute_log_filehandler = logging.FileHandler(filename)
        traceroute_log_filehandler.setLevel(logging.INFO)
        traceroute_log_filehandler.setFormatter(logging.Formatter())
        TRACEROUTE_LOG.addHandler(traceroute_log_filehandler)
        logs_started.append("traceroute")

    return logs_started


CONFIG = {}
SENSOR_LOG = logging.getLogger("sensor")
CURL_LOG = logging.getLogger("curl")
DIG_LOG = logging.getLogger("dig")
PING_LOG = logging.getLogger("ping")
TRACEROUTE_LOG = logging.getLogger("traceroute")


signal.signal(signal.SIGINT, signal_handler)


if __name__ == "__main__":

    STARTTIME = time.time()

    PROBES = {
        "all": [],
        "curl": [],
        "dig": [],
        "ping": [],
        "traceroute": [],
    }

    load_config()

    LOGS = init_logs()
    SENSOR_LOG.info("initiated the following logs: '%s'", ", ".join(LOGS))
    multiprocessing_logging.install_mp_handler()

    P = mp.Process(target=check_remote_config)
    P.start()

    while True:

        for dig_dest in [*PROBES["dig"], *PROBES["all"]]:
            p = mp.Process(target=dig, args=(dig_dest["nameserver"],))
            p.start()
        for curl_dest in [*PROBES["curl"], *PROBES["all"]]:
            p = mp.Process(target=curl, args=(curl_dest["url"],))
            p.start()
        for ping_dest in [*PROBES["ping"], *PROBES["all"]]:
            p = mp.Process(target=ping, args=(ping_dest["ip"],))
            p.start()
        for traceroute_dest in [*PROBES["traceroute"], *PROBES["all"]]:
            p = mp.Process(target=traceroute, args=(traceroute_dest["ip"],))
            p.start()

        time.sleep(TEST_INTERVAL - ((time.time() - STARTTIME) % TEST_INTERVAL))
