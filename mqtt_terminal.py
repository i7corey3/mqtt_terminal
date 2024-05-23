from mqtt_terminal.mqtt_terminal.MQTT import MQTT


mqtt = MQTT("localhost")

cmd_topic = "mqtt_terminal/command"
listen_topic = "mqtt_terminal/output"

# create a listener
mqtt.createListener("cmd_out", listen_topic)

# create a client
mqtt.createSender("cmd_in", cmd_topic)


# check the message buffer
while True:
   
    command = input("$ ")
    mqtt.send("cmd_in", cmd_topic, command, qos=2)
    while True:
        output = mqtt.MQTT_Message[listen_topic]
        if output != []:
            print(output.decode())
            break
           