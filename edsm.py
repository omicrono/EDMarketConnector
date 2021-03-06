import requests
import threading
from sys import platform
import time
import urllib

import Tkinter as tk

from config import applongname, appversion, config

if __debug__:
    from traceback import print_exc

class EDSM:

    _TIMEOUT = 10
    FAKE = ['CQC', 'Training', 'Destination']	# Fake systems that shouldn't be sent to EDSM

    def __init__(self):
        self.result = { 'img': None, 'url': None, 'done': True }
        self.syscache = set()

        EDSM._IMG_KNOWN    = tk.PhotoImage(data = 'R0lGODlhDgAOAMIEAFWjVVWkVWS/ZGfFZwAAAAAAAAAAAAAAACH5BAEKAAQALAAAAAAOAA4AAAMsSLrcHEIEp8C4GDSLu15dOCyB2E2EYGKCoq5DS5QwSsDjwomfzlOziA0ITAAAOw==')	# green circle
        EDSM._IMG_UNKNOWN  = tk.PhotoImage(data = 'R0lGODlhDgAOAKECAGVLJ+ddWO5fW+5fWyH5BAEKAAMALAAAAAAOAA4AAAImnI+JEAFqgJj0LYqFNTkf2VVGEFLBWE7nAJZbKlzhFnX00twQVAAAOw==')	# red circle
        EDSM._IMG_NEW      = tk.PhotoImage(data = 'R0lGODlhEAAQAMZwANKVHtWcIteiHuiqLPCuHOS1MN22ZeW7ROG6Zuu9MOy+K/i8Kf/DAuvCVf/FAP3BNf/JCf/KAPHHSv7ESObHdv/MBv/GRv/LGP/QBPXOPvjPQfjQSvbRSP/UGPLSae7Sfv/YNvLXgPbZhP7dU//iI//mAP/jH//kFv7fU//fV//ebv/iTf/iUv/kTf/iZ/vgiP/hc/vgjv/jbfriiPriiv7ka//if//jd//sJP/oT//tHv/mZv/sLf/rRP/oYv/rUv/paP/mhv/sS//oc//lkf/mif/sUf/uPv/qcv/uTv/uUv/vUP/qhP/xP//pm//ua//sf//ubf/wXv/thv/tif/slv/tjf/smf/yYP/ulf/2R//2Sv/xkP/2av/0gP/ylf/2df/0i//0j//0lP/5cP/7a//1p//5gf/7ev/3o//2sf/5mP/6kv/2vP/3y//+jP///////////////////////////////////////////////////////////////yH5BAEKAH8ALAAAAAAQABAAAAePgH+Cg4SFhoJKPIeHYT+LhVppUTiPg2hrUkKPXWdlb2xHJk9jXoNJQDk9TVtkYCUkOy4wNjdGfy1UXGJYOksnPiwgFwwYg0NubWpmX1ArHREOFYUyWVNIVkxXQSoQhyMoNVUpRU5EixkcMzQaGy8xhwsKHiEfBQkSIg+GBAcUCIIBBDSYYGiAAUMALFR6FAgAOw==')
        EDSM._IMG_ERROR    = tk.PhotoImage(data = 'R0lGODlhDgAOAIABAAAAAP///yH5BAEKAAEALAAAAAAOAA4AAAIcjIGJxqHaIJPypBYvzms77X1dWHlliKYmuI5GAQA7')	  # BBC Mode 5 '?'

    # Just set link without doing a lookup
    def link(self, system_name):
        self.cancel_lookup()
        if system_name in self.FAKE:
            self.result = { 'img': '', 'url': None, 'done': True, 'uncharted': False }
        else:
            self.result = { 'img': '', 'url': 'https://www.edsm.net/show-system?systemName=%s' % urllib.quote(system_name), 'done': True, 'uncharted': False }

    def lookup(self, system_name, known=0):
        self.cancel_lookup()

        if system_name in self.FAKE:
            self.result = { 'img': '', 'url': None, 'done': True, 'uncharted': False }
        elif known or system_name in self.syscache:
            self.result = { 'img': EDSM._IMG_KNOWN, 'url': 'https://www.edsm.net/show-system?systemName=%s' % urllib.quote(system_name), 'done': True, 'uncharted': False }
        else:
            self.result = { 'img': EDSM._IMG_ERROR, 'url': 'https://www.edsm.net/show-system?systemName=%s' % urllib.quote(system_name), 'done': True, 'uncharted': False }
            r = requests.get('https://www.edsm.net/api-v1/system?sysname=%s&coords=1&fromSoftware=%s&fromSoftwareVersion=%s' % (urllib.quote(system_name), urllib.quote(applongname), urllib.quote(appversion)), timeout=EDSM._TIMEOUT)
            r.raise_for_status()
            data = r.json()

            if data == -1 or not data:
                # System not present - but don't create it on the assumption that the caller will
                self.result['img'] = EDSM._IMG_NEW
                self.result['uncharted'] = True
            elif data.get('coords'):
                self.result['img'] = EDSM._IMG_KNOWN
                self.syscache.add(system_name)
            else:
                self.result['img'] = EDSM._IMG_UNKNOWN
                self.result['uncharted'] = True

    # Asynchronous version of the above
    def start_lookup(self, system_name, known=0):
        self.cancel_lookup()

        if system_name in self.FAKE:
            self.result = { 'img': '', 'url': None, 'done': True, 'uncharted': False }
        elif known or system_name in self.syscache:	# Cache URLs of systems with known coordinates
            self.result = { 'img': EDSM._IMG_KNOWN, 'url': 'https://www.edsm.net/show-system?systemName=%s' % urllib.quote(system_name), 'done': True, 'uncharted': False }
        else:
            self.result = { 'img': '', 'url': 'https://www.edsm.net/show-system?systemName=%s' % urllib.quote(system_name), 'done': False, 'uncharted': False }
            self.thread = threading.Thread(target = self.worker, name = 'EDSM worker', args = (system_name, self.result))
            self.thread.daemon = True
            self.thread.start()

    def cancel_lookup(self):
        self.thread = None	# orphan any existing thread
        self.result = { 'img': '', 'url': None, 'done': True }	# orphan existing thread's results

    def worker(self, system_name, result):
        try:
            r = requests.get('https://www.edsm.net/api-v1/system?sysname=%s&coords=1&fromSoftware=%s&fromSoftwareVersion=%s' % (urllib.quote(system_name), urllib.quote(applongname), urllib.quote(appversion)), timeout=EDSM._TIMEOUT)
            r.raise_for_status()
            data = r.json()

            if data == -1 or not data:
                # System not present - create it
                result['img'] = EDSM._IMG_NEW
                result['uncharted'] = True
                result['done'] = True	# give feedback immediately
                requests.get('https://www.edsm.net/api-v1/url?sysname=%s&fromSoftware=%s&fromSoftwareVersion=%s' % (urllib.quote(system_name), urllib.quote(applongname), urllib.quote(appversion)), timeout=EDSM._TIMEOUT)	# creates system
            elif data.get('coords'):
                result['img'] = EDSM._IMG_KNOWN
                result['done'] = True
                self.syscache.add(system_name)
            else:
                result['img'] = EDSM._IMG_UNKNOWN
                result['uncharted'] = True
        except:
            if __debug__: print_exc()
            result['img'] = EDSM._IMG_ERROR
        result['done'] = True


# Flight log - https://www.edsm.net/api-logs
def export(data, edsmlookupfn):

    querytime = config.getint('querytime') or int(time.time())

    writelog(querytime, data['lastSystem']['name'], edsmlookupfn)


def writelog(timestamp, system, edsmlookupfn, coordinates=None):

    try:
        # Look up the system before adding it to the log, since adding it to the log has the side-effect of creating it
        edsmlookupfn()

        if system in EDSM.FAKE:
            return

        url = 'https://www.edsm.net/api-logs-v1/set-log?commanderName=%s&apiKey=%s&systemName=%s&dateVisited=%s&fromSoftware=%s&fromSoftwareVersion=%s' % (
            urllib.quote(config.get('edsm_cmdrname').encode('utf-8')),
            urllib.quote(config.get('edsm_apikey')),
            urllib.quote(system),
            urllib.quote(time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(timestamp))),
            urllib.quote(applongname),
            urllib.quote(appversion)
        )
        if coordinates:
            url += '&x=%.3f&y=%.3f&z=%.3f' % coordinates
        r = requests.get(url, timeout=EDSM._TIMEOUT)
        r.raise_for_status()
        reply = r.json()
        (msgnum, msg) = reply['msgnum'], reply['msg']
    except:
        if __debug__: print_exc()
        raise Exception(_("Error: Can't connect to EDSM"))

    # Message numbers: 1xx = OK, 2xx = fatal error, 3xx = error (but not generated in practice), 4xx = ignorable errors
    if msgnum // 100 not in (1,4):
        raise Exception(_('Error: EDSM {MSG}').format(MSG=msg))
