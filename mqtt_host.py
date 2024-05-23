from MQTT import MQTT
import os

mqtt = MQTT("localhost")

cmd_topic = "mqtt_terminal/command"
listen_topic = "mqtt_terminal/output"

# create a listener
mqtt.createListener("cmd_in_L", cmd_topic)

# create a client
mqtt.createSender("cmd_out_L", listen_topic)

while True:
 
    command = mqtt.MQTT_Message["cmd_in_L"]
    if command != []:
        out = os.popen(command.decode()).read()
        mqtt.send("cmd_out_L", listen_topic, out, qos=2)
        mqtt.MQTT_Message["cmd_out_L"] = []