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
from Bluetin_Echo import Echo


#IMPOSTAZINI PIN BOARD
connRelay = digitalio.DigitalInOut(board.D17)
connRelay.direction = digitalio.Direction.OUTPUT
connRelay.value = True
connDht = adafruit_dht.DHT22(board.D4)

#IMPOSTAZIONI CAMERA
camera = PiCamera()

#IMPOSTAZIONI SENSORE PROSSIMITA'
prox_trigger_pin = 27
prox_echo_pin = 22
speed_of_sound = 315
prox_samples = 10
echo = Echo(prox_trigger_pin, prox_echo_pin, speed_of_sound)

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

def deviceCamera(cmd, n):
    dt = str(strftime("%Y%m%d", gmtime()))
    dir = "/home/pi/storage/storage-3/picamera/" + dt
    dirExists(dir)
    if cmd == "snap":
        ext = "jpg"
        for x in range (0, n):
            ts = str(strftime("%Y%m%d-%H%M%S-ballatoio", gmtime()))
            name = ts
            filename = "{}/{}.{}".format(dir,name,ext)
            timestamp = str(strftime("%Y-%m-%d %H:%M:%S", gmtime()))
#            pictureText = timestamp + ": T" + str(getTemperature()) + "C, H" + str(getHumidity())
            pictureText = "TEST"
            try:
                camera.start_preview()
                camera.annotate_background = Color('blue')
                camera.annotate_foreground = Color('yellow')
                camera.annotate_text = pictureText
                camera.rotation = 180
                camera.capture(filename)
                camera.stop_preview()
                print("Saving picture to " + filename)
            except:
                print(error.args[0])
    elif cmd == "video":
        ext = "h264"
        ts = str(strftime("%Y%m%d-%H%M%S-ballatoio", gmtime()))
        name = ts
        filename = "{}/{}.{}".format(dir,name,ext)
        try:
            print("Starting a new video")
            camera.start_preview()
            camera.start_recording(filename)
            sleep(n)
            camera.stop_recording()
            camera.stop_preview()
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

def deviceProximity():
    result = echo.read('cm', prox_samples)
    if result > 0:
        return result
    else:
        print("Proximity can't be 0, trying again")
        sleep(1)
        deviceProximity()

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
print("Initializing script")
mqttConnect()
#client.subscribe(topic_temp)
#client.subscribe(topic_hum)

while True:
    try:
#        curr_temp = getTemperature()
#        curr_hum = getHumidity()
#        mqttPublish(topic_temp,curr_temp, False)
#        mqttPublish(topic_hum,curr_hum,False)
#        deviceCamera("snap", 5)
        proximity = deviceProximity()
        print("Proximity sensor " + str(proximity))
        if proximity < 30:
            deviceCamera("video", 30)
        time.sleep(5)

    except RuntimeError as error:
        echo.stop()
        print(error.args[0])
    except KeyboardInterrupt:
        print('Kill by keyboard')
        echo.stop()
        mqttDisconnect()
        quit()
