import time
from flask import Flask, request, jsonify, current_app, render_template
from MyThread import ThreadManager
from broadlink import Device
import broadlink
from tasks import stop_all_task, front_end_target_task, sam_mode_task

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

@app.route('/stop_all', endpoint='stop_all', methods=['GET'])
def stop_all():
    dev = current_app.dev
    manager.add_thread(name= "StopAll", target=stop_all_task, args=(dev, manager,))
    return jsonify({"status": f"Stopping everything"}), 200

@app.route('/front_end_target', endpoint='front_end_target', methods=['POST'])
def front_end_target():
    data = request.get_json()

    # Check if a specific field is present
    if data is None:
        return jsonify({"error": "No JSON data provided"}), 400
    
    if 'ac_setting' not in data:
        return jsonify({"error": "Missing 'ac_setting'"}), 400

    if 'ac_time' not in data:
        return jsonify({"error": "Missing 'ac_time'"}), 400

    if 'fan_speed_requested' not in data:
        return jsonify({"error": "Missing 'fan_speed_requested'"}), 400
    
    dev = current_app.dev
    ac_setting = int(data['ac_setting'])
    ac_time = int(data['ac_time'])
    fan_speed_requested = int(data['fan_speed_requested'])
    manager.add_thread(name= "FrontEndTarget", target=front_end_target_task, args=(dev, ac_setting, ac_time, fan_speed_requested))

    # Return a JSON response
    return jsonify({"status": f"{ac_time} minutes ac then fan {fan_speed_requested}"}), 200

@app.route('/hello', methods=['GET'])
def hello():
    return jsonify({"status": "Hello World"}), 200

@app.route('/sam_mode', endpoint='sam_mode', methods=['GET'])
def sam_mode():
    dev = current_app.dev
    manager.add_thread(name="SamMode", target=sam_mode_task, args=(dev,))
    return jsonify({"status": "Sam mode started: 30 min AC, 2 hours off, cycling."}), 200

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
