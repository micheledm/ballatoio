import time
import board
import digitalio
import adafruit_dht
from picamera import PiCamera,Color
from time import gmtime, strftime

connRelay = digitalio.DigitalInOut(board.D17)
connRelay.direction = digitalio.Direction.OUTPUT
connRelay.value = True

connDht = adafruit_dht.DHT22(board.D4)

camera = PiCamera()

def deviceCamera(cmd):
    if cmd == "snap":
        dir = "/home/pi"
        name = "image"
        ext = "jpg"
        filename = "{}/{}.{}".format(dir,name,ext)
        timestamp = str(strftime("%Y-%m-%d %H:%M:%S", gmtime()))
        pictureText = timestamp + ": T" + str(getTemperature()) + "C, H" + str(getHumidity())
        camera.start_preview()
        camera.annotate_background = Color('blue')
        camera.annotate_foreground = Color('yellow')
        camera.annotate_text = pictureText
        camera.rotation = 180
        time.sleep(5)
        camera.capture(filename)
        camera.stop_preview()
        print("Saving picture to " + filename)

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
            print("Current temperature is {}C".format(temp))
            return temp
        else:
            print("Failed to retrieve temperature")

def getHumidity():
    hum = connDht.humidity
    if hum is not None:
        print("Current humidity level is {}%".format(hum))
        return hum
    else:
        print("Failed to retrieve temperature")


while True:
    try:
        time.sleep(3)
#       getTemperature()
#       getHumidity()
        deviceCamera("snap")
        time.sleep(2)
        deviceRelay("toggle")
        time.sleep(3)
        deviceRelay("toggle")
    except RuntimeError as error:
        print(error.args[0])
    except KeyboardInterrupt:
         print('Kill by keyboard')
         quit()
