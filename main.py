import digitalio,analogio
import board
import busio
import time
import adafruit_sdcard
import adafruit_dht
import storage
import adafruit_pcf8523
import gc
from adafruit_seesaw . seesaw import Seesaw

gc.enable()

# initialize and mount the SD card
def mount_SD():
    spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
    cs = digitalio.DigitalInOut(board.D10)
    sdcard = adafruit_sdcard.SDCard(spi, cs)
    vfs = storage.VfsFat(sdcard)
    storage.mount(vfs, "/sd")

#initialize moisture & temperature sensor
def get_DHT(dht_pin):
    return adafruit_dht.DHT22(dht_pin)

#get photocell
def get_photocell(photocell_pin):
    return analogio.AnalogIn(photocell_pin)

#calibrates all sensors
def calibrate_sensors():
    #TODO: implement

#get analogue voltage
def analog_voltage (adc):
    return adc.value / 65535 * adc.reference_voltage

#returns list of current values
def log_values(t,dht,photocell):
    date = str (t.tm_mday) + '/' + str(t.tm_mon) + '/' + str(t.tm_year)
    times = str(t.tm_hour) + ':' + str(t.tm_min) + ':' + str(t.tm_sec)

    air_temp = dht.temperature
    humidity = dht.humidity
    photo_val = photocell.values
    volts = analog_voltage(photocell)
    moisture = 1 #TODO: implement soil sensor

    return [date,times,air_temp,humidity,photo_val,volts,moisture]

returns the past moisture reading where r is how many readings back is returned
def get_past_moisture(logs, r = 1):
    try:
        return logs[-1*(1+r)][-1]
    except Exception as e:
        print('error in get_past_moisture():\n' + str(e))

dht = get_DHT(board.D5)
photocell = get_photocell(board.A1)
logs = []
max_len = 50
count = 0

with open('/sd/ DHT22_photocell_results . txt ', "rw") as f:
        while count < 50:
            count += 1
            t = rtc.datetime
            current_log = log_values(t,dht,photocell)
            if len(logs) < max_len:
            logs.append(current_log)
            else:
                logs[log].pop(0)
                logs[log].append(current_log)
