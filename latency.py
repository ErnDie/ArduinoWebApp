import json
from datetime import datetime, timedelta
import string
import numpy as np

import ntplib


class Latency:

    def __init__(self):
        ntp_call = ntplib.NTPClient()
        response = ntp_call.request('de.pool.ntp.org', version=3)
        self.ntp_correction = (response.delay / 2) + response.offset
        self.rtt_list = []
        self.owd_list = []

    def start(self):
        self.start_time_rtt = datetime.now()
        self.start_time_owd = datetime.utcfromtimestamp(datetime.now().timestamp() + self.ntp_correction)

    def calculateLatency(self, response: string):
        self.end_time_rtt = datetime.now()
        responseParts = response.split(';')
        print(f"ResponseParts: {responseParts}")
        ntpDelayString = responseParts[0].split("NTP-Delay: ")[1]
        print(f"NTP Delay: {ntpDelayString}")
        arduinoNtpTimeString = responseParts[1].split("UTC-Time: ")[1]
        print(f"arduinoNtpTimeString: {arduinoNtpTimeString}")
        arduinoNtpTime = datetime.strptime(arduinoNtpTimeString, "%H:%M:%S.%f")

        owdTimeDelta = arduinoNtpTime - self.start_time_owd
        owMicroSeconds = str(owdTimeDelta).split('.')

        self.owd = round(float(str(owdTimeDelta.seconds) + "." + owMicroSeconds[1]), 6)
        self.rtt = self._calculateRTT(self.end_time_rtt - self.start_time_rtt, ntpDelayString)
        self.rtt_list.append(self.rtt)
        self.owd_list.append(self.owd)
        print(len(self.rtt_list))
        print(len(self.owd_list))

    def printLatency(self):
        print("TCP OWD: " + str(self.owd) + "s")
        print("TCP RTT: " + str(self.rtt) + "s")

    def _calculateRTT(self, timeDelta: timedelta, ntpDelayString: string):
        ntpDelay = int(ntpDelayString)
        timeDelta = timeDelta - timedelta(microseconds=ntpDelay * 1000)
        # If you use timedelta.microseconds the 0 at the beginning will be cut
        microSecondsString = str(timeDelta).split('.')[1]
        rtt = float(str(timeDelta.seconds) + "." + microSecondsString)
        return rtt

    def calculateRTTMetrics(self):
        rtt_sorted = self.rtt_list.copy()
        rtt_sorted.sort()
        self.rtt_max = rtt_sorted[-1]
        self.rtt_min = rtt_sorted[0]
        self.rtt_mean_interval = round(float(np.mean(self.rtt_list)), 6)
        self.rtt_std_deviation = round(float(np.std(self.rtt_list)), 6)
        self.rtt_25_quantil = np.quantile(self.rtt_list, .25)
        self.rtt_75_quantil = np.quantile(self.rtt_list, .75)
        self.rtt_average = round(float(np.average(self.rtt_list)), 6)

    def calculateOWDMetrics(self):
        owd_sorted = self.owd_list.copy()
        owd_sorted.sort()
        self.owd_max = owd_sorted[-1]
        self.owd_min = owd_sorted[0]
        self.owd_mean_interval = round(float(np.mean(self.owd_list)), 6)
        self.owd_std_deviation = round(float(np.std(self.owd_list)), 6)
        self.owd_25_quantil = np.quantile(self.owd_list, .25)
        self.owd_75_quantil = np.quantile(self.owd_list, .75)
        self.owd_average = round(float(np.average(self.owd_list)), 6)


    def calculateRTTJitter(self):
        self.jitter_intervals = [round(abs(self.rtt_list[i] - self.rtt_list[i - 1]), 6) for i in range(1, len(self.rtt_list))]
        self.jitter_mean_interval = round(float(np.mean(self.jitter_intervals)), 6)
        self.jitter_std_deviation = round(float(np.std(self.jitter_intervals)), 6)
        time_intervals_sorted = self.jitter_intervals.copy()
        time_intervals_sorted.sort()
        self.jitter_max = time_intervals_sorted[-1]
        self.jitter_min = time_intervals_sorted[0]
        self.jitter_25_quantil = np.quantile(self.jitter_intervals, .25)
        self.jitter_75_quantil = np.quantile(self.jitter_intervals, .75)
        self.jitter_average = round(float(np.average(self.jitter_intervals)), 6)


    def saveAsJSON(self):
        time = 3
        json_object = []
        for rtt in self.rtt_list:
            dic = {"seconds": time, "latency": rtt, "latency_type": "rtt"}
            json_object.append(dic)
            time = time + 3

        time = 3
        for owd in self.owd_list:
            dic = {"seconds": time, "latency": owd, "latency_type": "owd"}
            json_object.append(dic)
            time = time + 3

        time = 6
        for jitter in self.jitter_intervals:
            dic = {"seconds": time, "latency": jitter, "latency_type": "jitter"}
            json_object.append(dic)
            time = time + 3

        with open("sample.json", "w") as outfile:
            json.dump(json_object, outfile)

    def saveMetricsAsTxt(self):
        result = "RTT-Ergebnisse: " + ','.join(map(str, self.rtt_list)) + "\n"
        result += "RTT-Min: " + str(self.rtt_min) + "\n"
        result += "RTT-Max: " + str(self.rtt_max) + "\n"
        result += "RTT-25%-Quartil: " + str(self.rtt_25_quantil) + "\n"
        result += "Mean: " + str(self.rtt_mean_interval) + "\n"
        result += "RTT-75%-Quartil: " + str(self.rtt_75_quantil) + "\n"
        result += "RTT-Durchschnitt: " + str(self.rtt_average) + "\n"
        result += "RTT-Standardabweichung: " + str(self.rtt_std_deviation) + "\n\n"

        result += "OWD-Ergebnisse: " + ','.join(map(str, self.owd_list)) + "\n"
        result += "OWD-Min: " + str(self.owd_min) + "\n"
        result += "OWD-Max: " + str(self.owd_max) + "\n"
        result += "OWD-25%-Quartil: " + str(self.owd_25_quantil) + "\n"
        result += "OWD-Mean: " + str(self.owd_mean_interval) + "\n"
        result += "OWD-75%-Quartil: " + str(self.owd_75_quantil) + "\n"
        result += "OWD-Durchschnitt: " + str(self.owd_average) + "\n"
        result += "OWD-Standardabweichung: " + str(self.owd_std_deviation) + "\n\n"

        result += "Jitter-Ergebnisse: " + ','.join(map(str, self.jitter_intervals)) + "\n"
        result += "Jitter-Min: " + str(self.jitter_min) + "\n"
        result += "Jitter-Max: " + str(self.jitter_max) + "\n"
        result += "Jitter-25%-Quartil: " + str(self.jitter_25_quantil) + "\n"
        result += "Jitter-Mean: " + str(self.jitter_mean_interval) + "\n"
        result += "Jitter-75%-Quartil: " + str(self.jitter_75_quantil) + "\n"
        result += "Jitter-Durchschnitt: " + str(self.jitter_average) + "\n"
        result += "Jitter-Standardabweichung: " + str(self.jitter_std_deviation) + "\n\n"

        with open("metrics.txt", "w") as outfile:
            outfile.write(result)

    def cleanUpData(self):
        self.rtt_list = [val for val in self.rtt_list if val <= 0.3]
        self.owd_list = [val for val in self.owd_list if val <= 0.2]
