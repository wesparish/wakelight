from machine import RTC
from machine import Pin
from machine import Timer
from neopixel import NeoPixel
import network
import ntptime
import ujson

connect_status_pin = Pin(16, Pin.OUT)

def read_config():
    # Load config file
    with open("config/config.json", "r") as config_file:
        return ujson.load(config_file)

def read_wifi_config():
    # Load config file
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
        print("Setting np[%s]: to %s" % (i, (r, g, b)))
        np[i] = (r, g, b)
    np.write()

def check_times(junk):
    print("In check_times()")
    ntptime.settime() # set the rtc datetime from the remote server
    curr_time = rtc.datetime()
    print(curr_time)    # get the date and time in UTC
    print("Time: %s/%s/%s %s:%s:%s" % (curr_time[1],
                                       curr_time[2],
                                       curr_time[0],
                                       curr_time[4]-6, # no TZ support
                                       curr_time[5],
                                       curr_time[6]))
    configuration = read_config()
    print("configuration: %s" % configuration)

    for item in configuration['wakelight']:
        print("Checking %s >= %s" % (curr_time[4] - 6, int(item['start_time']['hour'])))
        print("Checking %s <= %s" % (curr_time[4] - 6, int(item['end_time']['hour'])))
        print("Checking %s >= %s" % (curr_time[5], int(item['start_time']['minute'])))
        print("Checking %s <= %s" % (curr_time[4] - 6, int(item['end_time']['minute'])))
        if (curr_time[4] - 6) >= int(item['start_time']['hour']) and \
           (curr_time[4] - 6) <= int(item['end_time']['hour']) and \
            curr_time[5] >= int(item['start_time']['minute']) and \
            curr_time[5] <= int(item['end_time']['minute']):
            print("Turning on LED!")
            set_led(item['color']['red'],
                    item['color']['green'],
                    item['color']['blue'])
        else:
            print("Turning off LED!")
            # Turn off LED
            set_led(0, 0, 0)

timer2 = Timer(-1)
timer2.init(period=10000, mode=Timer.PERIODIC, callback=check_times)

print("End of main.py!")
