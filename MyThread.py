import threading
import time
from typing import List

class MyThread(threading.Thread):
    def __init__(self, name, terminate_flag:threading.Event, target=None, args=()):
        super().__init__(target=target, args=args)
        self.name = name
        self.terminate_flag = terminate_flag

    def run(self):
        if self._target:
            self._target(*self._args)  # Execute the target function
        self.terminate_flag.set()

    def terminate(self):
        print(f"Thread {self.name} termination requested")
        self.terminate_flag.set()  # Signal the thread to stop

    def is_terminated(self):
        return self.terminate_flag.is_set()

class ThreadManager:
    def __init__(self):
        self.threads:List[MyThread] = []  # List to hold active threads

    def add_thread(self, name, target, args):
        terminate_flag = threading.Event()
        new_thread = MyThread(name, terminate_flag, target=target, args=(*args, terminate_flag))
        new_thread.start()
        self.threads.append(new_thread)
        print(f"Added thread: {name}")

    def remove_terminated_threads(self):
        before_count = len(self.threads)
        self.threads = [t for t in self.threads if not t.is_terminated()]
        after_count = len(self.threads)
        print(f"Removed {before_count - after_count} terminated threads")

    def terminate_thread(self, name):
        for thread in self.threads:
            if thread.name == name:
                thread.terminate()
                break
        else:
            print(f"No thread found with name: {name}")
        self.remove_terminated_threads()
    
    def terminate_all_threads(self):
        for thread in self.threads:
            thread.terminate()
        self.remove_terminated_threads()

    def list_active_threads(self):
        active = [t.name for t in self.threads if not t.is_terminated()]
        print(f"Active threads: {active}")
        return active

    def monitor_threads(self):
        while self.threads:
            time.sleep(2)
            self.remove_terminated_threads()
