import busio
import adafruit_pcf8523
import time
import board
i2c = busio .I2C( board .SCL , board .SDA)
rtc = adafruit_pcf8523 . PCF8523 ( i2c )
days = (" Sunday ", " Monday ", " Tuesday ", " Wednesday ", " Thursday ", " Friday ", "Saturday ")
year = 2020 # Calendar Year
month = 5 # Month (1= January , 12= December )
date = 12 # Date
hour = 13 # Hour (0 -23)
minute = 39 # Minute (0 -59)
sec = 0 # Second (0 -59)
wday = 0 # (0= Sunday , 6= Saturday )
# This physically sets the clock
t = time . struct_time ((year , month , date , hour , minute , sec , wday , -1 , -1))
print (" Setting time to:",t)
rtc. datetime = t