import time
import json
import paho.mqtt.client as mqtt
import RPI.GPIO as GPIO

buzzer=16

GPIO.setmode(GPIO.BOARD)
GPIO.setup(buzzer,GPIO.OUT)

# Function to read sensor values
def read_from_sensor():
    humidity, temperature = Adafruit_DHT.read_retry(11, 4)
    if humidity > 10 or temperature>5:
        GPIO.output(buzzer,GPIO.HIGH)
    return  humidity,temperature

# Thingsboard platform credentials
THINGSBOARD_HOST = 'demo.thingsboard.io'
ACCESS_TOKEN = 'kQh0Z3AlTArMOyvciyKK'

INTERVAL = 5
sensor_data = {'temperature' :0,'humidity':0}
next_reading = time.time()
client = mqtt.Client()
client.username_pw_set(ACCESS_TOKEN)
client.connect(THINGSBOARD_HOST,1883,60)

client.loop_start()

try:
    while True:
        temp,hum = read_from_sensor()
        print("Temperature:",temperature, chr(176) + "C")
        print("Humidity:", humidity,"%rH")
       
        sensor_data['temperature'] = temperature
        sensor_data['humidity'] = humidity
       
        client.publish('v1/devices/me/telemetry',json.dumps(sensor_data),1)
        next_reading += INTERVAL
        sleep_time = next_reading-time.time()
        if sleep_time >0:
            time.sleep(sleep_time)

except KeyboardInterrupt:
    pass

client.loop_stop()
client.disconnect()