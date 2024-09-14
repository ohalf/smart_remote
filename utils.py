import inspect
import pickle
import os

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

def get_fr_command(device):
    device.sweep_frequency()
    input("When the LED blinks, point the remote at the Broadlink device for the first time and long press the button you want to learn.")
    ok = device.check_frequency()
    if ok:
        print('Frequency found!')
    device.find_rf_packet()
    input("When the LED blinks, point the remote at the Broadlink device for the second time and short press the button you want to learn.")
    return device.check_data()