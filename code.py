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

#get analogue voltage
def analog_voltage (adc):
    return (adc.value / 65535 * adc.reference_voltage)

#calibrates all sensors
def calibrate_sensors():
    print('\n\nsensors calibrated\n\n')

def correct_humidity():
    print('\nmisting air with water to correct humidity\n')
    for blink in range(2):
            yellow.value = True
            time.sleep(.05)
            yellow.value = False
            time.sleep(.05)
def correct_moisture():
    print('\nwatering plants to increase soil moisture\n')
    for blink in range(2):
            blue.value = True
            time.sleep(.05)
            blue.value = False
            time.sleep(.05)
def correct_temperature():
    print('\nTemperature is off; adjust climate control\n')
    for blink in range(2):
            green.value = True
            time.sleep(.05)
            green.value = False
            time.sleep(.05)

#returns list of current values
def log_values(t,dht,photocell,soil):
    t_abs = rtc.datetime
    date = str (t_abs.tm_mday) + '/' + str(t_abs.tm_mon) + '/' + str(t_abs.tm_year)
    times = str(t_abs.tm_hour) + ':' + str(t_abs.tm_min) + ':' + str(t)

    air_temp = dht.temperature
    humidity = dht.humidity
    photo_val = photocell.value
    volts = analog_voltage(photocell)
    moisture = moisture_to_percent(soil.moisture_read())
    soil_temp = 1   # soil.get_temp()

    return (date,times,humidity,moisture,air_temp,soil_temp,photo_val,volts)

# checks latest reading for values out of tolerance regions
def check_log(log,POS,flowering):
    bounds = [(65,85),(.2,.3),(21.1,26.8)] # tolerance region for humidity, moisture, and air temp
    if flowering:
        bounds[0] = (50,65)
    flags = [False for _ in range(3)]
    for pos in range(len(flags)):
        if pos == 1:
            if log[pos+2]<bounds[pos][0]:
                flags[pos] = True
        else:
            if log[pos+2]<bounds[pos][0] or log[pos+2]>bounds[pos][1]:
                flags[pos] = True
    return tuple(flags)

def print_log(log, POS):
    print_str = ''
    for data,label in zip(log,POS):
        if label is 'humidity':
            print_str += label + ': ' + str(data) + '% ; '
        elif label is 'moisture':
            print_str += label + ': {:.1f}% ; '.format(data*100)
        else:
            print_str += label + ': ' + str(data) + ' ; '
    return print_str


def cross_check(flags_log):
    try:
        match = [(c and l) for c,l in zip(flags_log[-1],flags_log[-2])]
    except Exception as e:
        print('could not get two previous flag logs')

    if match[0] and not match[1]:
        correct_humidity()
    if match[1]:
        correct_moisture()
    if match[2]:
        correct_temperature()

#returns the past moisture reading where r is how many readings back is returned
def get_past_moisture(logs,POS, r = 1):
    try:
        return logs[-1*(1+r)][POS['moisture']]
    except Exception as e:
        print('error in get_past_moisture():\n' + str(e))
#returns the percent moisture
def moisture_to_percent(moisture):
    percent = ((moisture - 200)/1800)
    print('{:.1f}% moisture'.format(percent*100))
    return percent

mount_SD()
dht = get_DHT(board.D5)
soil = get_soil_sensor(i2c)
photocell = get_photocell(board.A1)
POS = ('date', 'time', 'humidity', 'moisture', 'air temp',
        'soil temp', 'photo val', 'volts') #position of various data in logs
logs = []
flags_log = [] #record of past flag logs
max_len = 50 #maximum length for logs until older entries are overwritten
yellow,blue,green,red = init_leds()
popped = False
time_not_up = True
flowering = False
run_time = 30 #runtime in seconds
ti = rtc.datetime[5]

with open("/sd/results.txt", "w") as f:
    while time_not_up:
        t = rtc.datetime[5]-ti
        if t % 5 == 0:                               #setting the interval for sensor calibration
            calibrate_sensors()

        if t % 2 == 0:                               #setting the interval for logging data
            current_log = log_values(t,dht,photocell,soil)
            if len(logs) < max_len:
                logs.append(current_log)
            else:
                logs.pop(0)
                logs.append(current_log)

            current_flags = check_log(current_log, POS, flowering)

            if len(flags_log) >= max_len:
                if not popped:
                    f.write('\n\npopping oldest reading\n\n')
                flags_log.pop(0)
                popped = True

            flags_log.append(current_flags)
            if len(flags_log)>1:
                cross_check(flags_log)

            print_log(current_log,POS)
            f.write('run time is ' + str(t) + ' seconds:\n     ' + print_log(current_log,POS) + '\n')

        if t >= run_time:
            time_not_up = False
            print('\n\nruntime is complete\n\n')
        else:
            time.sleep(1)