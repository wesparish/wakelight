from machine import RTC
from machine import Pin
from machine import Timer
from neopixel import NeoPixel
import network
import ntptime
import ujson
import utime

connect_status_pin = Pin(16, Pin.OUT)

def read_config():
    with open("config/config.json", "r") as config_file:
        return ujson.load(config_file)

def read_wifi_config():
    with open("config/wifi_credentials.json", "r") as config_file:
        return ujson.load(config_file)

def do_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        connect_status_pin.off() # turn on LED while connecting
        wifi_config = read_wifi_config()
        wlan.connect(wifi_config['wifi_credentials']['ssid'],
                     wifi_config['wifi_credentials']['password'])
        while not wlan.isconnected():
            pass
        connect_status_pin.on() # turn off LED once connected
    print('network config:', wlan.ifconfig())

do_connect()
ntptime.settime() # set the rtc datetime from the remote server

rtc = RTC()

np_pin = Pin(0, Pin.OUT)
num_pixels_global = 12
np = NeoPixel(np_pin, num_pixels_global)

def set_led(r, g, b, num_pixels=num_pixels_global):
    for i in range(num_pixels):
        np[i] = (r, g, b)
    np.write()

def check_times(junk):
    print("In check_times()")
    do_connect()
    ntptime.settime() # set the rtc datetime from the remote server

    configuration = read_config()
    print("configuration: %s" % configuration)

    curr_time = utime.localtime()
    print(curr_time)    # get the date and time in UTC
    print("Time: %s/%s/%s %s:%s:%s" % (curr_time[1],
                                       curr_time[2],
                                       curr_time[0],
                                       curr_time[3]-configuration['tz_offset'], # no TZ support
                                       curr_time[4],
                                       curr_time[5]))

    led_on = False
    for item in configuration['wakelight']:
        start_time = utime.mktime((curr_time[0], curr_time[1], curr_time[2],
                                   int(item['start_time']['hour'])+configuration['tz_offset'],
                                   int(item['start_time']['minute']),
                                   0,
                                   0, 55))
        end_time = utime.mktime((curr_time[0], curr_time[1], curr_time[2],
                                 int(item['end_time']['hour'])+configuration['tz_offset'],
                                 int(item['end_time']['minute']),
                                 0,
                                 0, 55))
        print("start_time: %s, end_time: %s, time(): %s" % (start_time, end_time, utime.time()))
        if utime.time() >= start_time and utime.time() <= end_time:
            print("Turning on LED! with color (%s, %s, %s)" % (item['color']['red'],
                                                               item['color']['green'],
                                                               item['color']['blue']))
            set_led(item['color']['red'],
                    item['color']['green'],
                    item['color']['blue'])
            led_on = True
    if not led_on:
        print("Turning off LED!")
        set_led(0, 0, 0)

timer2 = Timer(-1)
timer2.init(period=10000, mode=Timer.PERIODIC, callback=check_times)

print("End of main.py!")
