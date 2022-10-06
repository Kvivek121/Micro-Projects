from gpiozero import PWMLED, MCP3008
import RPi.GPIO as GPIO
import Adafruit_DHT
import time
from bmp280 import BMP280
import xlsxwriter
try:
    from smbus2 import SMBus
except ImportError:
    from smbus import SMBus
import sys
import json
import paho.mqtt.client as mqtt


def DHT11_sensor_humidity():
    sum1=[]
    sum2=0
    for i in range(10):
        humidity, temperature = Adafruit_DHT.read_retry(11, 4)
        sum1.append(humidity)
        sum2+=temperature
    return(sum1)


def temperature():
    bus = SMBus(1)
    bmp280 = BMP280(i2c_dev=bus)
    temperature = bmp280.get_temperature()
    temp='{:05.2f} '.format(temperature)
    return temp


def pressure():
    bus = SMBus(1)
    bmp280 = BMP280(i2c_dev=bus)
    pressure = bmp280.get_pressure()
    return('{:05.2f}hPa'.format( pressure))

    
def relative_altitude():
    bus = SMBus(1)
    bmp280 = BMP280(i2c_dev=bus)

    baseline_values = []
    baseline_size = 100

    print("Collecting baseline values for {:d} seconds. Do not move the sensor!\n".format(baseline_size))

    for i in range(baseline_size):
        pressure = bmp280.get_pressure()
        baseline_values.append(pressure)
        time.sleep(1)

    baseline = sum(baseline_values[:-25]) / len(baseline_values[:-25])
    temp=0
    avg_list=[]
    while temp!=10:
        altitude = bmp280.get_altitude(qnh=baseline)
        avg_list.append(altitude)
        #print('Relative altitude: {:05.2f} metres'.format(altitude))
        time.sleep(1)
        temp+=1
    return (avg_list)


def rain_detect():
    pot = MCP3008(0)
    temp=[]
    sum=0
    
    for i in range(20):
        temp.append((40)*(1-(pot.value)))
    for i in range(20):
        sum+=temp[i]
    return(sum/20)
        
#def file_update(A,B,C,D,E):
def file_update(A,B,C,E):
    #create file (workbook) and worksheet
    outWorkbook = xlsxwriter.Workbook("out.xlsx")
    outsheet= outWorkbook.add_worksheet()

    
    outsheet.write("A1","Humidity")
    outsheet.write("B1","temperature")
    outsheet.write("C1","pressure")
    #outsheet.write("D1","Relative altitude")
    outsheet.write("E1","Rain")
    

    for i in range(10):
        outsheet.write(i+1,0,A[i])
        outsheet.write(i+1,1,B[i])
        outsheet.write(i+1,2,C[i])
        #outsheet.write(i+1,3,D[i])
        outsheet.write(i+1,4,E[i])
    
    outWorkbook.close()


while True:
    GPIO.setmode(GPIO.BCM)

    THINGSBOARD_HOST = 'demo.thingsboard.io'
    ACCESS_TOKEN = 'mshIJIm70Ci948NFP9bp'

    #sensor_data = {'humidity':0,'temperature' :0,'pressure':0,'relative_altitude':0,'rain_detect':0}
    sensor_data = {'Humidity':0,'Temperature' :0,'Pressure':0,'Rain_detect':0}
    #next_reading = time.time()

    client = mqtt.Client()
    client.username_pw_set(ACCESS_TOKEN)
    client.connect(THINGSBOARD_HOST,1883,60)

    client.loop_start()

    A=[]
    B=[]
    C=[]
    #D=[]
    E=[]

    A=DHT11_sensor_humidity()
    #D=relative_altitude()

    for i in range(10):
        B.append(temperature())
        C.append(pressure())
        E.append('{:05.2f}'.format(rain_detect()))

    print(A)
    print(B)
    print(C)
    #print(D)
    print(E)

    file_update(A,B,C,E)

    def read_from_sensor(A,B,C,E,count):
        hum=A[count]
        temp=B[count]
        press=C[count]
        #rel=D[count]
        rain=E[count]
        return hum,temp,press,rain

    try:
        for i in range(10):
            count=1
            hum,temp,press,rain = read_from_sensor(A,B,C,E,count)
            print("Humidity:", hum,"%rH")
            print("Temperature:",temp, chr(176) + "C")
            print("Pressure:", press,"hPa")
           # print("Relative_altitude:",rel,"meters")
            print("Rain_detect:",rain,"mm")
            
            sensor_data['Humidity'] = hum
            sensor_data['Temperature'] = temp
            sensor_data['Pressure'] = press
            #sensor_data['Relative_altitude'] = rel
            sensor_data['Rain_detect'] = rain

            client.publish('v1/devices/me/telemetry',json.dumps(sensor_data),1)
            time.sleep(1.5)
            
            count+=1

    except KeyboardInterrupt:
        pass

    client.loop_stop()
    client.disconnect()
    