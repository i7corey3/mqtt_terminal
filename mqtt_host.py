from MQTT import MQTT
import subprocess
import threading


class MqttTerminalHost:
    def __init__(self, broker, port=1883):
        self.mqtt = MQTT(broker, port)

        self.cmd_topic = "mqtt_terminal/command"
        self.listen_topic = "mqtt_terminal/output"
        self.error = None
        self.out = None
        self.command = []
        self.timeout = False
        # create a listener
        self.mqtt.createListener("cmd_in_L", self.cmd_topic)

        # create a client
        self.mqtt.createSender("cmd_out_L", self.listen_topic)

        self.thread = threading.Thread(target=self.send_command, args=()).start()

    def send_command(self):
        while True:
            
            if self.command != []:
                self.p = subprocess.Popen(self.command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                self.out, self.error = self.p.communicate()
                if self.error is not None and len(self.error) > 0:  
                    self.mqtt.send("cmd_out_L", self.listen_topic, self.error, qos=2)
                else:
                    self.mqtt.send("cmd_out_L", self.listen_topic, self.out, qos=2)

                self.mqtt.MQTT_Message[self.cmd_topic] = []
                

    def main(self):
        while True:
            self.command = self.mqtt.MQTT_Message[self.cmd_topic]
            if self.command == "Command Timeout":
                print("kill")
                self.p.kill()
                self.mqtt.MQTT_Message[self.cmd_topic] = []
                
                

if __name__ == "__main__":
    m = MqttTerminalHost("localhost")
    m.main()
        