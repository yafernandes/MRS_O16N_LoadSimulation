import re
import requests
import json
import time
import threading
import pandas as pd

WEB_NODE_HOST = 'WEB_NODE_HOST'
WEB_NODE_PORT = 'WEB_NODE_PORT'
SERVICE_NAME = 'SERVICE_NAME'
SERVICE_VERSION = 'SERVICE_VERSION'
USERNAME = 'USERNAME'
PASSWORD = 'PASSWORD'
PARALLEL_THREADS = 'PARALLEL_THREADS'
RUNS_PER_THREAD = 'RUNS_PER_THREAD'

config = {}

with open('LoadSimulation.config') as in_file:
    for line in in_file:
        m = re.match("\s*([^=\s]+)\s*=\s*(.*)\s*", line)
        if m:
            config[m.group(1).upper()] = m.group(2)

loginURL = 'http://{0}:{1}/login'.format(config[WEB_NODE_HOST], config[WEB_NODE_PORT])
wsURL = 'http://{0}:{1}/api/{2}/{3}'.format(config[WEB_NODE_HOST], config[WEB_NODE_PORT], config[SERVICE_NAME], config[SERVICE_VERSION])

headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
    }

payload = {
    'username': config[USERNAME],
    'password': config[PASSWORD]
    }

response = requests.post(loginURL, data = json.dumps(payload),  headers = headers)

if (response.status_code != 200):
    print(response.text)
    exit(1)

headers['Authorization'] = 'Bearer ' + response.json()['access_token']

with open(config[SERVICE_NAME] + '.' + config[SERVICE_VERSION] + '.json') as in_file:
    payload = in_file.read()

print("Testing if configuration works...")
response = requests.post(wsURL, data = payload,  headers = headers)
if (response.status_code != 200):
    print("There might be an issue with the payload.")
    print(response.text)
    exit(1)

print("Configuration works!")

results = list()

def mrs_load():
    for i in range(int(config[RUNS_PER_THREAD])):
        start = time.time()
        try:
            response = requests.post(wsURL, data = payload,  headers = headers)
        except RuntimeError as error:
            print(error.getMessage())
            pass
        end = time.time()
        results.append((end - start) * 1000)

print("Starting threads...")
runs = config[PARALLEL_THREADS].split(',')
for run in runs:
    nruns = int(run)
    for n in range(nruns):
        threading.Thread(target = mrs_load).start()
    
    for thread in threading.enumerate():
        if(thread != threading.main_thread()):
            thread.join()
    print()
    print("Run with {nruns} threads.  Times in ms.".format(nruns = nruns))
    print(pd.Series(results).describe())
    