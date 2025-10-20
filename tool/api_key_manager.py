import threading
import requests
import os
from dotenv import load_dotenv

class APIKeyManager:
    def __init__(self, keys):
        self.keys = keys
        self.index = 0
        self.lock = threading.Lock()

    def get_current_key(self):
        with self.lock:
            return self.keys[self.index].strip()
            
    def get_next_key(self):
        with self.lock:
            try:
                self.index = self.index + 1
                key = self.keys[self.index]
                return key.strip()
            except IndexError:
                return None