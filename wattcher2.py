#!/usr/bin/env python
import datetime
import eeml
import optparse
import serial
import sys
import time 

import sensorhistory

from xbee import xbee

from Adafruit_I2C import Adafruit_I2C
from Adafruit_MCP230xx import Adafruit_MCP230XX
from Adafruit_CharLCDPlate import Adafruit_CharLCDPlate

LOGFILENAME = 'xbee.log'

ENERGY_PRICE = 0.09160 # Batavia Electric
SERIALPORT = "/dev/ttyUSB0"    # the com/serial port the XBee is connected to
BAUDRATE = 9600      # the baud rate we talk to the xbee
CURRENTSENSE = 4       # which XBee ADC has current draw data
VOLTSENSE = 0          # which XBee ADC has mains voltage data
MAINSVPP = 170 * 2     # +-170V is what 120Vrms ends up being (= 120*2sqrt(2))
vrefcalibration = [492,  # Calibration for sensor #0
                   505,  # Calibration for sensor #1
                   489,  # Calibration for sensor #2
                   492,  # Calibration for sensor #3
                   501,  # Calibration for sensor #4
                   493]  # etc... approx ((2.4v * (10Ko/14.7Ko)) / 3
CURRENTNORM = 15.5  # conversion to amperes from ADC
NUMWATTDATASAMPLES = 1800 # how many samples to watch in the plot window, 1 hr @ 2s samples
MAXWATTLISTLEN = 200

def add_wattvalue(value, watts):
    """Append a watt sample reading to a list of watts, limiting
    to a maximum length (this was for graphing
    """
    if len(watts) < MAXWATTLISTLEN:
        watts.append(value)
    else:
        watts.pop(0)
        watts.append(value)
    return watts

def avgvalue(data):
    """Average from a list of samples values over one 1/60Hz cycle"""
    avg = 0
    # 16.6 samples per second, one cycle = ~17 samples
    # close enough for govt work :(
    for i in range(17):
        avg += abs(data[i])
    avg /= 17.0
    return avg

def logfile_init(filename):
    try:
        logfile = open(LOGFILENAME, 'r+')
    except IOError:
        # didn't exist yet
        logfile = open(LOGFILENAME, 'w+')
        logfile.write("#Date, time, sensornum, avgWatts\n");
        logfile.flush()
    return logfile

def get_voltagedata(xb):
    """A list of voltages"""
    # we'll only store n-1 samples since the first one is usually messed up
    voltagedata = [-1] * (len(xb.analog_samples) - 1)
    # grab 1 thru n of the ADC readings, referencing the ADC constants
    # and store them in nice little arrays
    for i in range(len(voltagedata)):
        voltagedata[i] = xb.analog_samples[i+1][voltsense]
    
    min_v = 1024 # XBee ADC is 10 bits, so max value is 1023
    max_v = 0
    for i in range(len(voltagedata)):
        if (min_v > voltagedata[i]):
            min_v = voltagedata[i]
        if (max_v < voltagedata[i]):
            max_v = voltagedata[i]

    # figure out the 'average' of the max and min readings
    avgv = (max_v + min_v) / 2
    # also calculate the peak to peak measurements
    vpp = max_v-min_v

    for i in range(len(voltagedata)):
        #remove 'dc bias', which we call the average read
        voltagedata[i] -= avgv
        # We know that the mains voltage is 120Vrms = +-170Vpp
        voltagedata[i] = (voltagedata[i] * MAINSVPP) / vpp
    return voltagedata

def get_ampdata(xb):
    """A list of Amps"""
    ampdata = [-1] * (len(self.xb.analog_samples ) -1)
    for i in range(len(ampdata)):
        ampdata[i] = xb.analog_samples[i+1][currentsense]
    # normalize current readings to amperes
    for i in range(len(ampdata)):
        # VREF is the hardcoded 'DC bias' value, its
        # about 492 but would be nice if we could somehow
        # get this data once in a while maybe using xbeeAPI
        if vrefcalibration[self.xb.address_16]:
            ampdata[i] -= vrefcalibration[self.xb.address_16]
        else:
            ampdata[i] -= vrefcalibration[0]
        # the CURRENTNORM is our normalizing constant
        # that converts the ADC reading to Amperes
        ampdata[i] /= CURRENTNORM
    return ampdata

def get_wattdata(voltagedata, ampdata):
    """A list of Watt values"""
    # calculate instant. watts, by multiplying V*I for each sample point
    wattdata = [0] * len(voltagedata)
    for i in range(len(wattdata)):
        wattdata[i] = voltagedata[i] * ampdata[i]
    avgwatt = avgvalue(wattdata)
    return avgwatt

def get_whdata(avgwatt, sensorhistories, sensorhistory, save_log=False):
    '''return deltawatthours'''
    currminute = (int(time.time())/60) % 10
    if (((time.time() - sensorhistory.fiveminutetimer) >= 60.0)
        and (currminute % 5 == 0)
        ):
        sensorhistory.reset5mintimer()
    for history in sensorhistories.sensorhistories:
        wattsused += history.avgwattover5min()
        whused += history.dayswatthr
    # add up the delta-watthr used since last reading
    # Figure out how many watt hours were used since last reading
    elapsedseconds = time.time() - sensorhistory.lasttime
    dwatthr = (avgwatt * elapsedseconds) / (60.0 * 60.0)  # 60 seconds in 60 minutes = 1 hr
    sensorhistory.addwatthr(dwatthr)
    sensorhistory.lasttime = time.time()
    logfile.seek(0, 2) # 2 == SEEK_END. ie, go to the end of the file
    logfile.write(time.strftime("%Y %m %d, %H:%M")+", "+
                                                 str(sensorhistory.sensornum)+", "+
                                                 str(sensorhistory.avgwattover5min())+"\n")
    logfile.flush()
    print wattsused
    return dwatthr

if __name__ == "__main__":

    # set up the log
    logfile = logfile_init(LOGFILENAME)

    # set up the sensorhistories
    sensorhistories = sensorhistory.SensorHistories(logfile)

    # set up the LCD
    lcd = Adafruit_CharLCDPlate(busnum = 1)

    # set up serial connection
    ser = serial.Serial(SERIALPORT, BAUDRATE)

    while True:

        # grab one packet from the xbee, or timeout
        packet = xbee.find_packet(ser)
        if not packet:
            continue
        else:
            voltsense = VOLTSENSE
            currentsense = CURRENTSENSE
            xb = xbee(packet)             # parse the packet
            ampdata = get_ampdata(xb)
            voltagedata = get_voltagedata(xb)
            avgwatt = get_wattdata(voltagedata, ampdata)
            deltawatthours = get_whdata(avgwatt)
            lcd_message = "Cur: %.2f" % avgwatt 
            lcd.clear()
            lcd.backlight(lcd.OFF)
            lcd.message(lcd_message)
         
