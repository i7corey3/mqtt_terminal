from MQTT import MQTT
import time
import readline
from functions import bcolors, MyCompleter


class MqttTerminal:
    def __init__(self, broker, port=1883):
        self.mqtt = MQTT(broker, port)

        self.cmd_topic = "mqtt_terminal/command"
        self.listen_topic = "mqtt_terminal/output"

        # create a listener
        self.mqtt.createListener("cmd_out", self.listen_topic)

        # create a client
        self.mqtt.createSender("cmd_in", self.cmd_topic)
        self.timeout = 2
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
        self.mqtt.send("cmd_in", self.cmd_topic, "ls -a", qos=2)
        time.sleep(0.2)
        self.fileList = self.mqtt.MQTT_Message[self.listen_topic].replace('\n', ' ').split(" ")
        self.mqtt.MQTT_Message[self.listen_topic] = []

        self.completer = MyCompleter(self.fileList)
        readline.set_completer(self.completer.complete)
        readline.parse_and_bind('tab: complete')


    def checkHomeDir(self):
        home = len(f'/home/{self.name}')
        
        if len(self.pwd) > home:
            self.pwd = self.pwd.replace(f'/home/{self.name}/', '~/')
        elif len(self.pwd) == home:
            self.pwd = self.pwd.replace(f'/home/{self.name}', '~/')
        
    
    def main(self):

        
        while True:
            self.checkHomeDir()

            command = input(f"{bcolors.BOLD}{bcolors.OKGREEN}{self.name}@{self.hostname}{bcolors.ENDC}:{bcolors.BOLD}{bcolors.OKBLUE}{self.pwd}{bcolors.ENDC}$ ")

            if command[0:2] == "cd":
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
                    if command[0:2] == 'ls':
                        print(output.replace("\n", '\t'))

                            
                    else:
                        print(output)
                    
                    if self.pwd_update:
                        self.mqtt.send("cmd_in", self.cmd_topic, "pwd", qos=2)
                       
                        time.sleep(0.2)
                        self.pwd = self.mqtt.MQTT_Message[self.listen_topic].replace('\n', '')
                        self.mqtt.send("cmd_in", self.cmd_topic, "ls -a", qos=2)
                        time.sleep(0.2)
                        self.completer.options = self.mqtt.MQTT_Message[self.listen_topic].replace('\n', ' ').split(" ")
                        readline.set_completer(self.completer.complete)
                        readline.parse_and_bind('tab: complete')
                        self.pwd_update = False
                    self.mqtt.MQTT_Message[self.listen_topic] = []
                    break

if __name__ == "__main__":
    m = MqttTerminal('localhost')
    m.main()

                
                