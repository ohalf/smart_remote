import inspect
import pickle
import os
from broadlink import Device
import broadlink

def print_args(*args, **kwargs):
    frame = inspect.currentframe()
    args_info = inspect.getargvalues(frame)
    arguments = args_info.locals
    print("Arguments passed to the function:")
    for arg, value in arguments.items():
        print(f"{arg}: {value}")

def print_entire_pickle_file_for_debug():
    with open("./saved_commands.pkl", 'rb') as f:
        data = pickle.load(f) 
    print(data.keys())
    print(data)

def add_to_pickle(file_path, key, value):
    print(f"Adding:\n{key} : {value}")
    # Initialize an empty dictionary
    data = {}
    
    # If the file exists, read the existing data
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            data = pickle.load(f)
    
    # Add the new key-value pair
    data[key] = value
    
    # Write the updated dictionary back to the file
    with open(file_path, 'wb') as f:
        pickle.dump(data, f)

def get_ir_command(device):
    device.enter_learning()
    input("When the LED blinks, point the remote at the Broadlink device and press the button you want to learn.")
    return device.check_data()

def get_rf_command(device):
    try:
        device.cancel_sweep_frequency()
    except:
        pass  # in case it's not sweeping yet
    input("Sweeping frequencies. Press enter to continue...")
    device.sweep_frequency()
    input("When the LED blinks, point the remote at the Broadlink device for the first time and long press the button you want to learn.")
    ok = device.check_frequency()
    if ok:
        print('Frequency found!')
    else:
        print('Frequency not found, Exiting...')
        return None
    device.find_rf_packet()
    input("When the LED blinks, point the remote at the Broadlink device for the second time and short press the button you want to learn.")
    return device.check_data()

def get_dev() -> Device:
    devices = broadlink.discover()
    return devices[0]

def auth_dev(dev:Device) -> Device:
    dev.auth()
    return dev

def init() -> Device:
    dev = get_dev()
    dev = auth_dev(dev)
    return dev

def some_debug(dev:Device):
    print("Debugging function called")
    dev.cancel_sweep_frequency()

if __name__ == "__main__":
    # dev = init()

    # # some_debug(dev)

    # # Testing the functions
    # fan_2 = get_rf_command(dev)
    # print(f"fan_2: {fan_2}")
    # # add_to_pickle("./saved_commands.pkl", "fan_2", fan_2)

    from WorldTimeAPI import services as serv
    myclient = serv.client('timezone')
    regions = myclient.regions()
    print(regions.data)