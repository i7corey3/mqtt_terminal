from MQTT import MQTT
import time

mqtt = MQTT("localhost")

cmd_topic = "mqtt_terminal/command"
listen_topic = "mqtt_terminal/output"

# create a listener
mqtt.createListener("cmd_out", listen_topic)

# create a client
mqtt.createSender("cmd_in", cmd_topic)
timeout = 2
start_time = time.time()
current_time = time.time()

# check the message buffer
while True:
   
    command = input("$ ")
    mqtt.send("cmd_in", cmd_topic, command, qos=2)
    start_time = time.time()
    while True:
        current_time = time.time()
        if current_time - start_time >= timeout:
            mqtt.send("cmd_in", cmd_topic, "Command Timeout", qos=2)
            print("Command Timeout")
            
            break
       
        output = mqtt.MQTT_Message[listen_topic]
        if output != []:
            print(output)
            mqtt.MQTT_Message[listen_topic] = []
            break
           