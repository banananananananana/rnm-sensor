#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pythonification of rnm-sensor.sh
"""

__author__ = "You made this?  I made this!"

import json
import logging
import multiprocessing as mp
import re
import signal
import subprocess
import time

import multiprocessing_logging
import requests

import jc.parsers.dig
import jc.parsers.ping
import jc.parsers.tracepath
import jc.parsers.traceroute


BASEDIR = "/opt/rnm-sensor/"
CONFIG_FILENAME = BASEDIR + "rnm-sensor-config.json"
TEST_INTERVAL = 10.0
REMOTE_CHECK_INTERVAL = 5
PROBE_TIMEOUT = 5


def load_config():
    """
    Loads in the local config.
    """
    global CONFIG
    try:
        with open(CONFIG_FILENAME, "r") as config_file:
            CONFIG = json.loads(config_file.read())
            config_file.close()
    except IOError as error:
        print("ERROR: Cannot open configfile '{}', {}".format(
            CONFIG_FILENAME, error))
    global PROBES
    for target in CONFIG['targets']:
        for probe in target['probes']:
            PROBES[probe].append(target)


def check_remote_config():
    """
    Load remote config if required.
    """
    global CONFIG
    while True:
        if CONFIG['config_file_source'][0]['use_remote_config']:
            if 'source' in CONFIG['config_file_source'][0]:
                SENSOR_LOG.info(
                    "Remote config required, fetching configuration ..")
                req = requests.get(CONFIG['config_file_source']
                                   [0]['source'], stream=True)
                if req.status_code == 200:
                    remote_conf = req.json()
                    if CONFIG == remote_conf:
                        SENSOR_LOG.info("Remote config matches local config.")
                    else:
                        SENSOR_LOG.info(
                            "Remote config differs from local, updating local ..")
                        CONFIG = remote_conf
                        try:
                            with open(CONFIG_FILENAME, "w") as local_config_file:
                                json.dump(remote_conf, local_config_file,
                                          indent=4, sort_keys=True)
                                local_config_file.close()
                                SENSOR_LOG.info(
                                    "New local config has been written to disk.")
                        except IOError as error:
                            SENSOR_LOG.error("ERROR: Cannot write to configfile '%s', %s",
                                CONFIG_FILENAME, error))

                else:
                    print("Loading remote config failed with status code:",
                          req.status_code)
        else:
            break

        time.sleep(REMOTE_CHECK_INTERVAL -
                   ((time.time() - STARTTIME) % REMOTE_CHECK_INTERVAL))


def dig(dest):
    """
    Perform ns lookup and print output.
    """

    try:
        output = subprocess.run(
            ["dig", dest['nameserver']],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            timeout=PROBE_TIMEOUT
        )
        DIG_LOG.info(jc.parsers.dig.parse(output.stdout.decode())[0])
    except subprocess.CalledProcessError as error:
        SENSOR_LOG.info("ERROR: %s", error)
    except subprocess.TimeoutExpired as error:
        SENSOR_LOG.info("ERROR: %s", error)


def curl(dest):
    """
    Curl destination and print output.
    """

    try:
        output = subprocess.run(
            [
                "/home/tk/code/rnm_sensor/curl-7.71.1/src/curl",
                "-I",
                "-w '%{json}'",
                dest['url']
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            timeout=PROBE_TIMEOUT
        )
        CURL_LOG.info(
            re.match(
                "^ '(.*)'$",
                output.stdout.decode().split('\n')[-1]
            ).groups()[0])
    except subprocess.CalledProcessError as error:
        SENSOR_LOG.info("ERROR: %s", error)
    except subprocess.TimeoutExpired as error:
        SENSOR_LOG.info("ERROR: %s", error)


def ping(dest):
    """
    Ping host and print output.
    """
    try:
        output = subprocess.run(
            ["ping", "-DO", "-c1", "-W3", dest['ip']],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            timeout=PROBE_TIMEOUT
        )
        PING_LOG.info(jc.parsers.ping.linux_parse(output.stdout.decode()))
    except subprocess.CalledProcessError as error:
        SENSOR_LOG.info("ERROR: %s", error)
    except subprocess.TimeoutExpired as error:
        SENSOR_LOG.info("ERROR: %s", error)


def tracepath(dest):
    """
    Perform traceroute and print output.
    """

    try:
        output = subprocess.run(
            ["tracepath", dest['ip']],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            timeout=PROBE_TIMEOUT
        )
        TRACEPATH_LOG.info(jc.parsers.tracepath.parse(output.stdout.decode()))
        print(output)
    except subprocess.CalledProcessError as error:
        SENSOR_LOG.info("ERROR: %s", error)
    except subprocess.TimeoutExpired as error:
        SENSOR_LOG.info("ERROR: %s", error)


def traceroute(dest):
    """
    Perform traceroute and print output.
    """

    try:
        output = subprocess.run(
            ["traceroute", "-w1", "--mtu", dest['ip']],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            timeout=PROBE_TIMEOUT
        )
        TRACEROUTE_LOG.info(
            jc.parsers.traceroute.parse(output.stdout.decode()))
    except subprocess.CalledProcessError as error:
        SENSOR_LOG.info("ERROR: %s", error)
    except subprocess.TimeoutExpired as error:
        SENSOR_LOG.info("ERROR: %s", error)


def signal_handler(sig, frame):
    """
    Exit gracefully.
    """
    print("Signal handler called with signal", sig)
    exit(0)


def init_logs():
    """
    Initialize the required logfiles.
    """

    log_path = CONFIG['logging']['path']
    logs_started = []

    if CONFIG['logging']['sensor']:
        filename = log_path + CONFIG['logging']['sensor']
        sensor_log_formatter = "%(asctime)s [%(levelname)s]: %(message)s in %(pathname)s:%(lineno)d"
        global SENSOR_LOG
        SENSOR_LOG = logging.getLogger('sensor')
        SENSOR_LOG.setLevel(logging.INFO)
        sensor_log_filehandler = logging.FileHandler(filename)
        sensor_log_filehandler.setLevel(logging.INFO)
        sensor_log_filehandler.setFormatter(
            logging.Formatter(sensor_log_formatter))
        SENSOR_LOG.addHandler(sensor_log_filehandler)
        logs_started.append('sensor')

    if PROBES['curl'] or PROBES['all']:
        filename = log_path + CONFIG['logging']['probes']['curl']
        global CURL_LOG
        CURL_LOG = logging.getLogger('curl')
        CURL_LOG.setLevel(logging.INFO)
        curl_log_filehandler = logging.FileHandler(filename)
        curl_log_filehandler.setLevel(logging.INFO)
        curl_log_filehandler.setFormatter(logging.Formatter())
        CURL_LOG.addHandler(curl_log_filehandler)
        logs_started.append('curl')

    if PROBES['dig'] or PROBES['all']:
        filename = log_path + CONFIG['logging']['probes']['dig']
        global DIG_LOG
        DIG_LOG = logging.getLogger('dig')
        DIG_LOG.setLevel(logging.INFO)
        dig_log_filehandler = logging.FileHandler(filename)
        dig_log_filehandler.setLevel(logging.INFO)
        dig_log_filehandler.setFormatter(logging.Formatter())
        DIG_LOG.addHandler(dig_log_filehandler)
        logs_started.append('dig')

    if PROBES['ping'] or PROBES['all']:
        filename = log_path + CONFIG['logging']['probes']['ping']
        global PING_LOG
        PING_LOG = logging.getLogger('ping')
        PING_LOG.setLevel(logging.INFO)
        ping_log_filehandler = logging.FileHandler(filename)
        ping_log_filehandler.setLevel(logging.INFO)
        ping_log_filehandler.setFormatter(logging.Formatter())
        PING_LOG.addHandler(ping_log_filehandler)
        logs_started.append('ping')

    if PROBES['tracepath'] or PROBES['all']:
        filename = log_path + CONFIG['logging']['probes']['tracepath']
        global TRACEPATH_LOG
        TRACEPATH_LOG = logging.getLogger('tracepath')
        TRACEPATH_LOG.setLevel(logging.INFO)
        tracepath_log_filehandler = logging.FileHandler(filename)
        tracepath_log_filehandler.setLevel(logging.INFO)
        tracepath_log_filehandler.setFormatter(logging.Formatter())
        TRACEPATH_LOG.addHandler(tracepath_log_filehandler)
        logs_started.append('tracepath')

    if PROBES['traceroute'] or PROBES['all']:
        filename = log_path + CONFIG['logging']['probes']['traceroute']
        global TRACEROUTE_LOG
        TRACEROUTE_LOG = logging.getLogger('traceroute')
        TRACEROUTE_LOG.setLevel(logging.INFO)
        traceroute_log_filehandler = logging.FileHandler(filename)
        traceroute_log_filehandler.setLevel(logging.INFO)
        traceroute_log_filehandler.setFormatter(logging.Formatter())
        TRACEROUTE_LOG.addHandler(traceroute_log_filehandler)
        logs_started.append('traceroute')

    return logs_started


CONFIG = None
SENSOR_LOG = None
CURL_LOG = None
DIG_LOG = None
PING_LOG = None
TRACEPATH_LOG = None
TRACEROUTE_LOG = None


signal.signal(signal.SIGINT, signal_handler)


if __name__ == '__main__':

    global STARTTIME
    STARTTIME = time.time()

    PROBES = {
        'all': [],
        'curl': [],
        'dig': [],
        'ping': [],
        'tracepath': [],
        'traceroute': []
    }

    load_config()

    logs = init_logs()
    SENSOR_LOG.info("initiated the following logs: '{%s}'", ", ".join(logs))
    multiprocessing_logging.install_mp_handler()

    p = mp.Process(target=check_remote_config)
    p.start()

    while True:

        for dig_dest in [*PROBES['dig'], *PROBES['all']]:
            p = mp.Process(target=dig, args=(dig_dest,))
            p.start()
        for curl_dest in [*PROBES['curl'], *PROBES['all']]:
            p = mp.Process(target=curl, args=(curl_dest,))
            p.start()
        for ping_dest in [*PROBES['ping'], *PROBES['all']]:
            p = mp.Process(target=ping, args=(ping_dest,))
            p.start()
        for tracepath_dest in [*PROBES['tracepath'], *PROBES['all']]:
            p = mp.Process(target=tracepath, args=(tracepath_dest,))
            p.start()
        for traceroute_dest in [*PROBES['traceroute'], *PROBES['all']]:
            p = mp.Process(target=traceroute, args=(traceroute_dest,))
            p.start()

        time.sleep(TEST_INTERVAL - ((time.time() - STARTTIME) % TEST_INTERVAL))
