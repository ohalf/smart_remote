import pickle
import broadlink
import time
from flask import Flask, request, jsonify, current_app
from MyThread import ThreadManager
from threading import Event
from broadlink import Device

manager = ThreadManager()

def get_dev() -> Device:
    devices = broadlink.discover()
    return devices[0]

def auth_dev(dev:Device) -> Device:
    dev.auth()
    return dev

def create_app() -> Flask:
    app = Flask(__name__)

    with app.app_context():
        # Initialize the device once and store it in the app context
        dev = get_dev()
        app.dev = auth_dev(dev)

    return app

app = create_app()

def stop_all_task(dev, terminate_flag: Event):
    manager.terminate_all_threads() # marks all threads for termination, this specific task does not check termination flag so it will continue
    with open("./saved_commands.pkl", 'rb') as f:
        data = pickle.load(f)
    dev.send_data(data["fan_off"])
    time.sleep(5)
    dev.send_data(data["ac_off"])
    terminate_flag.set() # This is just for logical sense, in reality the thread will be set as terminated by the manager


@app.route('/stop_all', endpoint='stop_all', methods=['GET'])
def stop_all():
    dev = current_app.dev
    manager.add_thread(name= "StopAll", target=stop_all_task, args=(dev,))
    return jsonify({"status": f"Stopping everything"}), 200

def ac_then_sleep_task(dev, waiting_period_minutes, terminate_flag: Event):
    with open("./saved_commands.pkl", 'rb') as f:
        data = pickle.load(f)
    
    dev.send_data(data["ac_on_25"])

    timer = 0
    should_continue = True
    while not terminate_flag.is_set() and should_continue:
        if timer == waiting_period_minutes * 60:
            should_continue = False
        time.sleep(1)
        timer += 1

    dev.send_data(data["ac_off"])
    terminate_flag.set()

def ac_then_fan_task(dev, waiting_period_minutes, terminate_flag: Event):
    with open("./saved_commands.pkl", 'rb') as f:
        data = pickle.load(f)

    timer = 0
    should_continue = True
    while not terminate_flag.is_set() and should_continue:
        if timer == 0:
            print("Turning off fan")
            dev.send_data(data["fan_off"])
        if timer == 5:
            print("Turning on ac")
            dev.send_data(data["ac_on_25"])
            should_continue = False
        time.sleep(1)
        timer += 1

    timer = 0
    should_continue = True
    while not terminate_flag.is_set() and should_continue:
        if timer == waiting_period_minutes * 60:
            should_continue = False
        time.sleep(1)
        timer += 1
        

    timer = 0
    should_continue = True
    while not terminate_flag.is_set() and should_continue:
        if timer == 0:
            print("Turning on fan")
            dev.send_data(data["fan_3"])
        if timer == 5:
            print("Turning off ac")
            dev.send_data(data["ac_off"])
            should_continue = False
        time.sleep(1)
        timer += 1
    terminate_flag.set()

@app.route('/ac_then_fan', endpoint='ac_then_fan', methods=['GET'])
def ac_then_fan():
    dev = current_app.dev
    time_in_minutes_between = 15
    manager.add_thread(name= "Ac_then_fan", target=ac_then_fan_task, args=(dev, time_in_minutes_between,))
    return jsonify({"status": f"{time_in_minutes_between} minutes ac then fan3"}), 200

@app.route('/post_ac_then_fan', endpoint='post_ac_then_fan', methods=['POST'])
def post_ac_then_fan():
    data = request.get_json()

    # Check if a specific field is present
    if data is None:
        return jsonify({"error": "No JSON data provided"}), 400
    
    if 'time_in_minutes_between' not in data:
        return jsonify({"error": "Missing 'time_in_minutes_between'"}), 400
    
    dev = current_app.dev
    time_in_minutes_between = int(data['time_in_minutes_between'])
    manager.add_thread(name= "Ac_then_fan", target=ac_then_fan_task, args=(dev, time_in_minutes_between,))
    
    # Return a JSON response
    return jsonify({"status": f"{time_in_minutes_between} minutes ac then fan3"}), 200

@app.route('/post_ac_then_off', endpoint='post_ac_then_off', methods=['POST'])
def post_ac_then_off():
    data = request.get_json()

    # Check if a specific field is present
    if data is None:
        return jsonify({"error": "No JSON data provided"}), 400
    
    if 'time_in_minutes' not in data:
        return jsonify({"error": "Missing 'time_in_minutes'"}), 400
    
    dev = current_app.dev
    time_in_minutes = int(data['time_in_minutes'])
    manager.add_thread(name= "Ac_then_sleep", target=ac_then_sleep_task, args=(dev, time_in_minutes,))
    
    # Return a JSON response
    return jsonify({"status": f"{time_in_minutes} minutes ac then off"}), 200

@app.route('/hello', methods=['GET'])
def hello():
    return jsonify({"status": "Hello World"}), 200

if __name__ == '__main__':
    app.run(host='10.100.102.2', port=5000, debug=False)
