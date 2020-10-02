#import multiprocess as multiprocess
import paho.mqtt.client as mqttClient
import json
from multiprocessing import Process,Queue
#current thread
#client.sub
from decada_python_client import decada_client
def on_connect(client, userdata, flags, rc):

    if rc == 0:

        print("Connected to broker")

        global Connected                #Use global variable
        Connected = True                #Signal connection

    else:

        print("Connection failed")

def on_message(client, userdata, message):
    print ("Message received: "  + message.payload.decode("utf-8"))
    #with open('D:\Intern Sem\AIOT\daata.csv','a+') as f:
        #f.write("Message received: "  + message.payload + "\n")
    payload = json.loads(message.payload)
    #print (payload)
    payload_dict = {}
    for data_entry in payload["DATA"]:
        payload_dict[data_entry["ID"]] = float(data_entry["V"])
    print(payload_dict)
    decada_client.postMeasurePoints(payload_dict)

    #print(decada_client.queryAttributes(["id"]))

    #decada_client.updateAttributes({"id": 100})

    #print(decada_client.queryAttributes(["id"]))
    #print(values)
Connected = False   #global variable for the state of the connection

broker_address= "10.3.1.50" #Broker address
port = 1883                         #Broker port
user = ""                    #Connection username
password = ""            #Connection password

client = mqttClient.Client("Python")               #create new instance
client.username_pw_set(user, password=password)    #set username and password
client.on_connect= on_connect                      #attach function to callback
client.on_message= on_message                      #attach function to callback
client.connect(broker_address,port,60) #connect
client.subscribe("THE TOPIC WHICH YOU WANT TO SUB") #subscribe
client.loop_forever() #then keep listening forever

