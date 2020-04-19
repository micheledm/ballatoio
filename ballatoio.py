import time
import board
import digitalio
import adafruit_dht
from picamera import PiCamera,Color
from time import gmtime, strftime, sleep
import os
from pathlib import Path
import paho.mqtt.client as mqtt
import secrets_file
import log

#IMPOSTAZINI PIN BOARD
connRelay = digitalio.DigitalInOut(board.D17)
connRelay.direction = digitalio.Direction.OUTPUT
connRelay.value = True
connDht = adafruit_dht.DHT22(board.D4)

#IMPOSTAZIONI CAMERA
camera = PiCamera()

#IMPOSTAZIONI MQTT
mqtt_host = secrets_file.mqtt_host()
mqtt_port = 1883
mqtt_un = secrets_file.mqtt_un()
mqtt_pw = secrets_file.mqtt_pw()

#MQTT TOPICS
mqtt_device = "/homeassistant/ballato.io/"
topic_temp = mqtt_device + "temperature"
topic_hum = mqtt_device + "humidity"

def dirExists(dir):
    Path(dir).mkdir(parents=True, exist_ok=True)

def deviceCamera(cmd):
    if cmd == "snap":
        tm = str(strftime("%H%M%S", gmtime()))
        dt = str(strftime("%Y%m%d", gmtime()))
        ts = str(strftime("%Y%m%d-%H%M%S-ballatoio", gmtime()))
        name = ts
        ext = "jpg"
        dir = "/home/pi/storage/storage-3/picamera/" + dt
        dirExists(dir)
        filename = "{}/{}.{}".format(dir,name,ext)
        timestamp = str(strftime("%Y-%m-%d %H:%M:%S", gmtime()))
        pictureText = timestamp + ": T" + str(getTemperature()) + "C, H" + str(getHumidity())
        try:
            camera.start_preview()
            camera.annotate_background = Color('blue')
            camera.annotate_foreground = Color('yellow')
            camera.annotate_text = pictureText
            camera.rotation = 180
            time.sleep(5)
            camera.capture(filename)
            camera.stop_preview()
            print("Saving picture to " + filename)
        except:
            print(error.args[0])

def deviceRelay(cmd):
    if cmd == "on":
        connRelay.value = False
        print("Turning on relay")
    elif cmd == "off":
        connRelay.value = True
        print("Turning off relay")
    elif cmd == "status":
        value = connRelay.value
        if value == True:
            status = "off"
        elif value == False:
            status = "on"
        else:
            status = "error"
        print("Relay status: {}".format(status))
        return status
    elif cmd == "toggle":
        if deviceRelay("status") == "on":
            deviceRelay("off")
        elif deviceRelay("status") == "off":
            deviceRelay("on")
        else:
            print("Something went wrong, relay value not recognized ({})".format(deviceRelay("status")))
    else:
        print("Command not recognized")

def getTemperature():
    temp = connDht.temperature
    if temp is not None:
#       print("Current temperature is {}C".format(temp))
        return temp
    else:
        print("Failed to retrieve temperature")
        return "error"

def getHumidity():
    hum = connDht.humidity
    if hum is not None:
#       print("Current humidity level is {}%".format(hum))
        return hum
    else:
        print("Failed to retrieve temperature")
        return "error"

#COSE MQTT

def mqttConnect():
    global client
    client = mqtt.Client()
    client.username_pw_set(mqtt_un, password=mqtt_pw)
    client.connect(mqtt_host, mqtt_port)
    client.on_message=on_message
    client.loop_start()
    #client.on_log=on_log

def mqttDisconnect():
    client.loop_stop()
    client.disconnect()

def mqttPublish(tp, pl, rt):
    if pl is not None or pl != "error":
        client.publish(tp, payload=pl, qos=0, retain=rt)
    else:
        print("Skipping publishing with payload " + pl)
#   print("Published on: %s with message %s and retain %s" % (tp, pl, rt))

def on_message(client, userdata, message):
    print("message received |",str(message.payload.decode("utf-8")).strip())
    print("message topic=",message.topic)
    print("message qos=",message.qos)
    print("message retain flag=",message.retain)

def on_log(client, userdata, level, buf):
    print("log: ",buf)

#INIZIALIZZAZIONE MQTT
mqttConnect()
client.subscribe(topic_temp)
client.subscribe(topic_hum)

while True:
    try:
        curr_temp = getTemperature()
        curr_hum = getHumidity()
        mqttPublish(topic_temp,curr_temp, False)
        mqttPublish(topic_hum,curr_hum,False)
        time.sleep(5)
    except RuntimeError as error:
        print(error.args[0])
    except KeyboardInterrupt:
        print('Kill by keyboard')
        mqttDisconnect()
        quit()
