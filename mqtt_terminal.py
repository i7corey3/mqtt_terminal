from MQTT import MQTT
import time

class MqttTerminal:
    def __init__(self, broker, port=1883):
        self.mqtt = MQTT(broker, port)

        self.cmd_topic = "mqtt_terminal/command"
        self.listen_topic = "mqtt_terminal/output"

        # create a listener
        self.mqtt.createListener("cmd_out", self.listen_topic)

        # create a client
        self.mqtt.createSender("cmd_in", self.cmd_topic)
        self.timeout = 1
        self.start_time = time.time()
        self.current_time = time.time()
        self.pwd_update = False

        self.mqtt.send("cmd_in", self.cmd_topic, "whoami", qos=2)
        time.sleep(0.2)
        self.name = self.mqtt.MQTT_Message[self.listen_topic].replace('\n', '')
        self.mqtt.send("cmd_in", self.cmd_topic, "hostname", qos=2)
        time.sleep(0.2)
        self.hostname = self.mqtt.MQTT_Message[self.listen_topic].replace('\n', '')
        self.mqtt.send("cmd_in", self.cmd_topic, "pwd", qos=2)
        time.sleep(0.2)
        self.pwd = self.mqtt.MQTT_Message[self.listen_topic].replace('\n', '')

    def main(self):

        while True:
        
            command = input(f"{self.name}@{self.hostname}:{self.pwd}$ ")
            if command == "cd":
                self.pwd_update = True
            self.mqtt.send("cmd_in", self.cmd_topic, command, qos=2)
            start_time = time.time()
            while True:
                output = self.mqtt.MQTT_Message[self.listen_topic]
                current_time = time.time()
                if current_time - start_time >= self.timeout:
                    self.mqtt.send("cmd_in", self.cmd_topic, "Command Timeout", qos=2)
                    time.sleep(1)
                    print("Command Timeout")
                    self.mqtt.MQTT_Message[self.listen_topic] = []
                    break
            
                if output != []:
                    print(output)
                    self.mqtt.MQTT_Message[self.listen_topic] = []
                    if self.pwd_update:
                        self.mqtt.send("cmd_in", self.cmd_topic, "pwd", qos=2)
                        time.sleep(0.2)
                        self.pwd = self.mqtt.MQTT_Message[self.listen_topic].replace('\n', '')
                        self.pwd_update = False
                    break

if __name__ == "__main__":
    m = MqttTerminal('localhost')
    m.main()

                
                