import os, sys, io
import M5
from M5 import *
from umqtt import *
from utility import print_error_msg

#
# tailored for OPENDTU mqtt messages
#

## config START

# MQTT settings
MQTT_HOST='_mqtt_host_'

# set this to your inverter serial #
SERIAL_NUM='_serial_'

## config END

mqtt_client = None

# labels
w_strom2 = None
w_solar1 = None
w_yield_day = None
w_temp = None

def transform(sval : str, unit: str):
  try:
    # drop the decimals
    fval = float(sval)
    return str(f"{int(fval)} {unit}")
  except:
    return f"<noVal> {unit}"


def mqtt_event_strom2(data):
  global w_strom2
  try:
    w_strom2.setText(transform(data[1].decode('utf-8'), 'W'))
  except:
    pass


def mqtt_event_solar1(data):
  global w_solar1
  try:
    w_solar1.setText(transform(data[1].decode('utf-8'), 'W'))
  except:
    pass


def mqtt_event_yield_day(data):
  global w_yield_day
  try:
    w_yield_day.setText(transform(data[1].decode('utf-8'), 'W'))
  except:
    pass


def mqtt_event_temp(data):
  global w_temp
  try:
    w_temp.setText(transform(data[1].decode('utf-8'), 'C'))
  except:
    pass

def connectAndSubscribe():
  global mqtt_client
  try:
    if mqtt_client:
      mqtt_client.disconnect()
  except:
      pass

  # keepalive will lead to ping, if no messages are exchanged
  mqtt_client = MQTTClient('m5s3core', MQTT_HOST, port=1883, user='', password='', ssl=False, keepalive=20)
  mqtt_client.set_last_will('m5_exit_topic', 'good bye', retain=False, qos=0)
  mqtt_client.connect(clean_session=True)
  mqtt_client.subscribe('vzlogger/data/chn1/agg', mqtt_event_strom2, qos=0)
  mqtt_client.subscribe('solar/ac/power', mqtt_event_solar1, qos=0)
  mqtt_client.subscribe('solar/ac/yieldday', mqtt_event_yield_day, qos=0)
  mqtt_client.subscribe('solar/' + SERIAL_NUM + '/0/temperature', mqtt_event_temp, qos=0)


def setup():
  M5.begin()
  Widgets.setRotation(1)
  Widgets.fillScreen(0x000000)
   # 0-255
  Widgets.setBrightness(80)

  # labels
  global w_strom2, w_solar1, w_yield_day, w_temp
  w_strom2 = Widgets.Label("strom2", 0, 2, 1.0, 0xffffff, 0x000000, Widgets.FONTS.DejaVu24)
  w_solar1 = Widgets.Label("solar1", 0, 34, 1.0, 0xffffff, 0x000000, Widgets.FONTS.DejaVu24)
  w_yield_day = Widgets.Label("yield_day", 0, 66, 1.0, 0xffffff, 0x000000, Widgets.FONTS.DejaVu24)
  w_temp = Widgets.Label("temp", 0, 99, 1.0, 0xffffff, 0x000000, Widgets.FONTS.DejaVu24)

  connectAndSubscribe()


def loop():
  global mqtt_client

  counter = 1
  while True:
    M5.update()
    try:
      # blocking
      mqtt_client.wait_msg()
      counter = counter + 1
      # QOS 0 will not require ACKs or RESPs
      # so the client will timeout w/o pings
      if counter > 10:
        counter = 1
        mqtt_client.ping()
    except:
      connectAndSubscribe()


if __name__ == '__main__':
  try:
    setup()
    while True:
      try:
        loop()
      except Exception as ex:
        #print_error_msg(ex)
        pass
  except (Exception, KeyboardInterrupt) as e:
    try:
      print_error_msg(e)
    except ImportError:
      print("please update to latest firmware")
  