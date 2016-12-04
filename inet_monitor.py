#! /usr/bin/env python

import os
import platform
import time
import sys
import atexit
from ConfigParser import SafeConfigParser


class INetMonitor():

    def __init__(self, export_csv=True, notify=True, longest_time_online=0, longest_time_offline=0, overall_offline=0, overall_online=0, csv_file=str(time.time()) + ".csv"):
        self._ts_last_change = time.time()
        self._ts_last_check = time.time()
        self.currently_online = ping()
        self._longest_time_online = longest_time_online
        self._longest_time_offline = longest_time_offline
        self._overall_offline = overall_offline
        self._overall_online = overall_online
        self._export_csv = export_csv
        self._notify = notify

        if export_csv:
            self.csv_file = open(csv_file, "a")

    def check(self):
        res = ping()
        time.sleep(1)
        now = time.time()

        if not res:
            self._overall_offline += now - self._ts_last_check
        else:
            self._overall_online += now - self._ts_last_check

        if res != self.currently_online:
            self._ts_last_change = now

            if self._notify:
                notify(res)

        if self.currently_online:
            self._longest_time_online = max(
                now - self._ts_last_change, self._longest_time_online)
        else:
            self._longest_time_offline = max(
                now - self._ts_last_change, self._longest_time_offline)

        self.currently_online = res
        self._ts_last_check = now

        if self._export_csv:
            self.csv_file.write(str(round(now)) + "," +
                                ("1" if res else "0") + "\n")

    def refresh_output(self):
        seconds = time.time() - self._ts_last_change
        duration_current_state = INetMonitor._split_time(seconds)
        longest_online = INetMonitor._split_time(self._longest_time_online)
        longest_offline = INetMonitor._split_time(self._longest_time_offline)
        overall_duration = INetMonitor._split_time(
            self._overall_offline + self._overall_online)

        output = "Online" if self.currently_online else "Offline"
        output += " for " + str(duration_current_state["hours"]) + "h " + str(
            duration_current_state["minutes"]) + "m " + str(duration_current_state["seconds"]) + "s. "
        output += "Longest time online: " + str(longest_online["hours"]) + "h " + str(
            longest_online["minutes"]) + "m " + str(longest_online["seconds"]) + "s. "
        output += "Longest time offline: " + str(longest_offline["hours"]) + "h " + str(
            longest_offline["minutes"]) + "m " + str(longest_offline["seconds"]) + "s. Overall ratio: " + str(round(self._overall_offline / (self._overall_online + self._overall_offline), 2) * 100) + r"% offline."
        output += " Running for " + str(overall_duration["hours"]) + "h " + str(
            overall_duration["minutes"]) + "m " + str(overall_duration["seconds"]) + "s."
        sys.stdout.write("\r" + output)
        sys.stdout.flush()

    @staticmethod
    def _split_time(seconds):
        seconds = round(seconds, 1)

        hours = seconds // 3600
        seconds = seconds % 3600
        minutes = seconds // 60
        seconds = seconds % 60

        return {"hours": hours, "minutes": minutes, "seconds": seconds}

    @staticmethod
    def monitor_connection():
        monitor = None

        if os.path.isfile("config.ini"):
            print "Resuming from previous state..."
            config = SafeConfigParser()
            config.read('config.ini')

            monitor = INetMonitor(longest_time_offline=config.getfloat("main", "longest_time_offline"), longest_time_online=config.getfloat(
                "main", "longest_time_online"), overall_offline=config.getfloat("main", "overall_offline"), overall_online=config.getfloat("main", "overall_online"), csv_file=config.get("main", "csv_file"))
        else:
            print "Starting new measurements..."
            monitor = INetMonitor()

        def save_state():
            config = SafeConfigParser()
            config.add_section('main')
            config.set('main', "longest_time_online",
                       str(monitor._longest_time_online))
            config.set('main', "longest_time_offline",
                       str(monitor._longest_time_offline))
            config.set('main', "overall_offline", str(monitor._overall_offline))
            config.set('main', "overall_online", str(monitor._overall_online))
            config.set('main', "csv_file", monitor.csv_file.name)

            with open('config.ini', 'w') as f:
                config.write(f)

        atexit.register(save_state)

        try:
            while True:
                monitor.check()
                monitor.refresh_output()
        except KeyboardInterrupt:
            pass

# Taken from
# http://stackoverflow.com/questions/2953462/pinging-servers-in-python
def ping():
    """
    Returns True if host responds to a ping request
    """
    host = "8.8.8.8"

    os_name = platform.system().lower()

    # Ping parameters as function of OS
    ping_str = ("-n" if os_name == "windows" else "-c") + \
        " 1 -" + ("t" if os_name == "darwin" else "W") + " 5"

    # Ping
    return os.system("ping " + ping_str + " " + host + " > /dev/null 2> /dev/null") == 0


def notify(now_online):
    os_name = platform.system().lower()

    if os == "windows":
        import winsound

        if now_online:
            winsound.Beep(500, 500)
        else:
            winsound.Beep(100, 500)
    elif os_name == "darwin":
        if now_online:
            os.system('say "Yeah!"')
        else:
            os.system('say "Nope!"')
    elif os_name == "linux":
        if now_online:
            # os.system("beep -f 500 -l 500")
            sys.stdout.write("\a")
        else:
            # os.system("beep -f 100 -l 500")
            sys.stdout.write("\a\a")


INetMonitor.monitor_connection()
