from broadlink import Device
import pickle
import time
from MyThread import ThreadManager
from threading import Event
from flask import jsonify, request
from datetime import datetime, timedelta, UTC
import requests
from zoneinfo import ZoneInfo

def stop_all_task(dev: Device, manager:ThreadManager, terminate_flag: Event):
    manager.terminate_all_threads() # marks all threads for termination, this specific task does not check termination flag so it will continue
    with open("./saved_commands.pkl", 'rb') as f:
        data = pickle.load(f)
    dev.send_data(data["fan_off"])
    time.sleep(5)
    dev.send_data(data["ac_off"])
    terminate_flag.set() # This is just for logical sense, in reality the thread will be set as terminated by the manager

def front_end_target_task(dev: Device, ac_setting:int, ac_time:int, fan_speed_requested:int, terminate_flag: Event):
    if fan_speed_requested not in [0, 1, 2, 3]:
        return jsonify({"error": "Invalid fan speed requested"}), 400
    
    if ac_setting not in [25]:
        return jsonify({"error": "Invalid AC setting"}), 400

    with open("./saved_commands.pkl", 'rb') as f:
        data = pickle.load(f)

    # Send the initial command to turn off the fan and turn on the AC
    timer = 0
    should_continue = True
    while not terminate_flag.is_set() and should_continue:
        if timer == 0:
            print("Turning off fan")
            dev.send_data(data["fan_off"])
        if timer == 5:
            print(f"Turning on ac at {ac_setting}")
            dev.send_data(data[f"ac_on_{ac_setting}"])
            should_continue = False
        time.sleep(1)
        timer += 1

    # Wait for the specified time
    timer = 0
    should_continue = True
    print(f"Waiting for {ac_time} minutes")
    while not terminate_flag.is_set() and should_continue:
        if timer == ac_time * 60:
            should_continue = False
        time.sleep(1)
        timer += 1
        

    # Send the command to turn on the fan at the requested speed and turn off the AC
    timer = 0
    should_continue = True
    while not terminate_flag.is_set() and should_continue:
        if timer == 0:
            if fan_speed_requested == 0:
                print("Turning off fan")
                dev.send_data(data["fan_off"])
            else:
                print(f"Turning on fan {fan_speed_requested}")
                dev.send_data(data[f"fan_{fan_speed_requested}"])
        if timer == 5:
            print("Turning off ac")
            dev.send_data(data["ac_off"])
            should_continue = False
        time.sleep(1)
        timer += 1
    terminate_flag.set()

def get_worldtimeapi_utc_unix_time(max_attempts=3, delay=2):
    """
    Try to fetch UTC unixtime from WorldTimeAPI up to max_attempts times.
    Waits 'delay' seconds between attempts on failure.
    Returns the unixtime on success, or None on repeated failure.
    """
    url = "https://worldtimeapi.org/api/ip"
    headers = {"User-Agent": "Mozilla/5.0"}
    for attempt in range(0, max_attempts):
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data['unixtime']
            else:
                print(f"WorldTimeAPI attempt {attempt + 1}: HTTP {response.status_code}")
        except Exception as e:
            print(f"WorldTimeAPI attempt {attempt + 1} failed: {e}")
        if attempt < max_attempts - 1:
            time.sleep(delay)
    print(f"WorldTimeAPI failed after {max_attempts} attempts.")
    return None

def sam_mode_task(dev, terminate_flag: Event):
    """
    Cycles: 30 min AC on, 2 hours off, repeat until stopped.
    Checks terminate_flag to stop the cycle.
    Exits before starting a new cycle if current time is past 6pm (Tel Aviv local time).
    On first run, checks system time against worldtimeapi.org time and warns if off by >5 min.
    If a delta is detected, applies it to all subsequent time checks (no further API calls).
    """
    with open("./saved_commands.pkl", 'rb') as f:
        data = pickle.load(f)
    # Check system time accuracy at start
    api_utc_unixtime = get_worldtimeapi_utc_unix_time()
    delta = 0
    if api_utc_unixtime:
        delta = api_utc_unixtime - int(time.time())
        if abs(delta) > 300:
            print(f"Warning: System UTC time differs from WorldTimeAPI by {abs(delta)} seconds! Adjusting checks by this delta.")
    while not terminate_flag.is_set():
        utc_now = datetime.now(UTC) + timedelta(seconds=delta)
        tel_aviv_now = utc_now.replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo("Asia/Tel_Aviv"))
        if tel_aviv_now.hour >= 18:
            print("It's past 6pm (Tel Aviv, system/delta), exiting cycle.")
            return
        # AC ON for 30 minutes
        dev.send_data(data['ac_on_25'])
        for _ in range(30 * 60):
            if terminate_flag.is_set():
                return
            time.sleep(1)
        # AC OFF for 2 hours
        dev.send_data(data['ac_off'])
        for _ in range(2 * 60 * 60):
            if terminate_flag.is_set():
                return
            time.sleep(1)