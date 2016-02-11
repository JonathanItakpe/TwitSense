import os
import json


def parse_config():
    config = {}
    # from file args
    if os.path.exists('config.json'):
        with open('config.json') as fc:
            config.update(json.load(fc))
    return config
