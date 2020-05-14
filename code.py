import digitalio, analogio
import board
import busio
import time
import adafruit_sdcard
import adafruit_dht
import storage
import adafruit_pcf8523
import gc
import sys
from adafruit_seesaw.seesaw import Seesaw
from clock import rtc,i2c

gc.enable()

# initialize and mount the SD card
def mount_SD():
    spi= busio .SPI ( board .SCK , board .MOSI , board . MISO )
    cs= digitalio . DigitalInOut ( board . D10)
    sdcard = adafruit_sdcard . SDCard (spi , cs)
    vfs= storage . VfsFat ( sdcard )
    storage . mount (vfs , "/sd")

#initialize humidity & temperature sensor
def get_DHT(dht_pin):
    return adafruit_dht.DHT22(dht_pin)

def get_soil_sensor(i2c):
    return Seesaw(i2c, addr = 0x36)

#get photocell
def get_photocell(photocell_pin):
    return analogio.AnalogIn(photocell_pin)

def init_leds():

    yellow = digitalio.DigitalInOut(board.D6)
    blue = digitalio.DigitalInOut(board.D9)
    green = digitalio.DigitalInOut(board.D11)
    red = digitalio.DigitalInOut(board.D12)
    yellow.direction = digitalio.Direction.OUTPUT
    blue.direction = digitalio.Direction.OUTPUT
    green.direction = digitalio.Direction.OUTPUT
    red.direction = digitalio.Direction.OUTPUT

    return yellow, blue, green, red

#calibrates all sensors
#def calibrate_sensors():
    #TODO: implement

#get analogue voltage
def analog_voltage (adc):
    return (adc.value / 65535 * adc.reference_voltage)

#returns list of current values
def log_values(t,dht,photocell,soil):
    date = str (t.tm_mday) + '/' + str(t.tm_mon) + '/' + str(t.tm_year)
    times = str(t.tm_hour) + ':' + str(t.tm_min) + ':' + str(t.tm_sec)

    air_temp = dht.temperature
    humidity = dht.humidity
    photo_val = photocell.value
    volts = analog_voltage(photocell)
    moisture = soil.moisture_read()
    soil_temp = 1   # soil.get_temp()

    return (date,times,humidity,moisture,air_temp,soil_temp,photo_val,volts)

# checks latest reading for values out of tolerance regions
def check_log(log,POS):
    bounds = [(300,350),(300,350),(25,28.5)] # tolerance region for humidity, moisture, and air temp
    flags = [False for _ in range(3)]
    for pos in range(len(flags)):
        if log[pos+2]<bounds[pos][0] or log[pos+2]>bounds[pos][1]:
            flags[pos] = True
            print('out of tolerance region at pos =', (str(pos)+'!') )
    return tuple(flags)

def cross_check(flags_log):
    print('flags:',flags_log[-1],flags_log[-2])
    try:
        match = [(c and l) for c,l in zip(flags_log[-1],flags_log[-2])]
    except Exception as e:
        print('could not get two previous flag logs')
    print('match data:',match)

    if match[0]:
        print('\nhumidity is off\n')
        for blink in range(2):
            yellow.value = True
            time.sleep(.05)
            yellow.value = False
            time.sleep(.05)
    if match[1]:
        print('soil moisture is off\n')
        for blink in range(2):
            blue.value = True
            time.sleep(.05)
            blue.value = False
            time.sleep(.05)
    if match[2]:
        print('air temp is off\n')
        for blink in range(2):
            green.value = True
            time.sleep(.05)
            green.value = False
            time.sleep(.05)

#returns the past moisture reading where r is how many readings back is returned
def get_past_moisture(logs,POS, r = 1):
    try:
        return logs[-1*(1+r)][POS['moisture']]
    except Exception as e:
        print('error in get_past_moisture():\n' + str(e))

mount_SD()
dht = get_DHT(board.D5)
soil = get_soil_sensor(i2c)
photocell = get_photocell(board.A1)
POS = {'date': 0, 'times': 1, 'humidity' : 2, 'moisture' : 3, 'air temp' : 4,
        'soil temp' : 5, 'photo val' : 6, 'volts' : 7} #position of various data in logs
logs = []
flags_log = [] #record of past flag logs
max_len = 50 #maximum length for logs until older entries are overwritten
count = 0

yellow,blue,green,red = init_leds()

with open("/sd/results.txt", "a") as f:
    while count < 50:
        count += 1
        t = rtc.datetime

        current_log = log_values(t,dht,photocell,soil)
        if len(logs) < max_len:
            logs.append(current_log)
        else:
            logs.pop(0)
            logs.append(current_log)

        current_flags = check_log(current_log,POS)
        if len(flags_log) >= max_len:
            flags_log.pop(0)
        flags_log.append(current_flags)
        if len(flags_log)>1:
            cross_check(flags_log)

        print(current_log)
        print(len(logs))
        time.sleep(0.15)
        f.write(str(current_log) + '\n')

[print(str(log[3])+'\n') for log in logs]