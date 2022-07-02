import subprocess
import shlex
import time
import logging
from pathlib import Path

VERSION = '1.33'
# ping every sleep_sec seconds
sleep_sec = 10
# after offline_limit seconds, we do something
offline_limit = 60

ping_host = '8.8.8.8'
ifaces = ['wlan0', 'wwan0', 'eth0']


class Pinger:
    def __init__(self):
        # 0 - offline, 1 - online
        self.current_status = self.old_status = 0
        self.status_time = 0
        self.current_msg = self.old_msg = ''
        current_dir = str(Path.cwd())
        logging.basicConfig(filename=current_dir + '/ping.log', filemode='a',
                            format='%(asctime)s - %(message)s', level=logging.INFO)

    def ping(self, iface, host):
        # -4: IPv4 query
        # -c 1: 1 ping only
        # -I <iface>: use <iface> as communicating interface
        # -n: numeric lookup
        # -q: quiet (minimal reporting)
        cmd = 'ping -4 -c 1 -I {} -n -q {}'.format(iface, host)
        p = subprocess.run(shlex.split(cmd), capture_output=True)
        return p

    def test_iface(self, interfaces):
        logging.info("pinging for active interfaces")
        active_ifaces = []
        for iface in interfaces:
            p = self.ping(iface, ping_host)
            if(p.returncode == 0):
                logging.info('{} - active'.format(iface))
                active_ifaces.append(iface)
            else:
                logging.info('{} - inactive'.format(iface))
        return active_ifaces

    def action(self):
        # rigorous action!
        print("we have been offline TOO LONG")
        logging.error("we have been offline for {} seconds! We DEMAND to be reconnected!".format(
            int(time.time()) - self.status_time))
        # e.g. restart _a_ service, or the device etc
        # subprocess.run(shlex.split('reboot'))

    def start(self):
        logging.info("===STARTING UP===")
        self.active_ifaces = self.test_iface(ifaces)
        if len(self.active_ifaces):
            while True:
                for iface in self.active_ifaces:
                    p = self.ping(iface, ping_host)
                    if p.returncode == 1:
                        self.current_status = 0
                        self.current_msg = 'offline'
                    if p.returncode == 0:
                        self.current_status = 1
                        self.current_msg = 'online'
                    if self.current_status != self.old_status:
                        if self.status_time == 0:
                            logging.info('+++ {} online'.format(iface))
                        else:
                            print('{}: {} -> {}'.format(iface,
                                  self.old_msg, self.current_msg))
                            logging.info('{} for {} seconds, now {}'.format(
                                self.old_msg, int(time.time()) - self.status_time, self.current_msg))
                        self.status_time = int(time.time())
                        self.old_msg = self.current_msg
                        self.old_status = self.current_status
                    if self.current_status == 0 and time.time() - self.status_time > offline_limit:
                        self.action()
                    time.sleep(sleep_sec)
        else:
            logging.error('no active interfaces found, exiting')


pinger = Pinger()
pinger.start()
