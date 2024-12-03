from MQTT import MQTT
import time
import readline
from functions import bcolors, MyCompleter
from fileHandler import FileHandler
import sys


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

        self.file = FileHandler("opened_file.txt", self.mqtt, self.cmd_topic, self.listen_topic, self.timeout)

        self.mqtt.send("cmd_in", self.cmd_topic, "whoami", qos=2)
        time.sleep(self.timeout)
        try: 
            self.name = self.mqtt.MQTT_Message[self.listen_topic].replace('\n', '')
        except:
            print("Failed to connect to device, make sure the mqtt_host.py script is running on remote computer")
            sys.exit()
        self.mqtt.send("cmd_in", self.cmd_topic, "hostname", qos=2)
        time.sleep(self.timeout)
        self.hostname = self.mqtt.MQTT_Message[self.listen_topic].replace('\n', '')
        self.mqtt.send("cmd_in", self.cmd_topic, "pwd", qos=2)
        time.sleep(self.timeout)
        self.pwd = self.mqtt.MQTT_Message[self.listen_topic].replace('\n', '')
        self.mqtt.send("cmd_in", self.cmd_topic, "ls -a", qos=2)
        time.sleep(self.timeout)
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

            command = input(f"{bcolors.BOLD}{bcolors.FAIL}{self.name}@{self.hostname}{bcolors.ENDC}:{bcolors.BOLD}{bcolors.OKBLUE}{self.pwd}{bcolors.ENDC}$ ")

            if command[0:2] == "cd":
                self.pwd_update = True

            if command[0:4] == "nano" or command[0:3] == "vim":
                self.file.open_file(command.split(" ")[1])
            elif command[0:4] == "save":
                self.file.save_file(f"{self.pwd}/{command.split(' ')[1]}")
            else:
                self.mqtt.send("cmd_in", self.cmd_topic, command, qos=2)
                start_time = time.time()
                while True:
                    output = self.mqtt.MQTT_Message[self.listen_topic]
                    current_time = time.time()
                    if current_time - start_time >= self.timeout:
                        self.mqtt.send("cmd_in", self.cmd_topic, "Command Timeout", qos=2)
                        time.sleep(self.timeout)
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
                        
                            time.sleep(self.timeout)
                            self.pwd = self.mqtt.MQTT_Message[self.listen_topic].replace('\n', '')
                            self.mqtt.send("cmd_in", self.cmd_topic, "ls -a", qos=2)
                            time.sleep(self.timeout)
                            self.completer.options = self.mqtt.MQTT_Message[self.listen_topic].replace('\n', ' ').split(" ")
                            readline.set_completer(self.completer.complete)
                            readline.parse_and_bind('tab: complete')
                            self.pwd_update = False
                        self.mqtt.MQTT_Message[self.listen_topic] = []
                        break

if __name__ == "__main__":
    m = MqttTerminal('3.tcp.ngrok.io', 27178)
    # m = MqttTerminal('localhost',1883)
    m.main()

                
                
