from MQTT import MQTT
import subprocess
import threading
import os
import numpy as np


class MqttTerminalHost:
    def __init__(self, broker, port=1883):
        self.mqtt = MQTT(broker, port)
        
        self.user = os.popen("whoami").read().replace("\n", '')
        self.cmd_topic = "mqtt_terminal/command"
        self.listen_topic = "mqtt_terminal/output"
        self.error = None
        self.out = None
        self.command = []
        self.timeout = False
        self.pwd = os.getcwd()
        # create a listener
        self.mqtt.createListener("cmd_in_L", self.cmd_topic)

        # create a client
        self.mqtt.createSender("cmd_out_L", self.listen_topic)

        self.thread = threading.Thread(target=self.send_command, args=()).start()

    def send_command(self):
        
        while True:
            self.command = self.mqtt.MQTT_Message[self.cmd_topic]
            if self.command != []:
                if self.command.split(' ')[0] == 'cd':
                    try:
                        if len(self.command.split(' ')) == 1:
                            os.chdir(f"/home/{self.user}/")
                            self.pwd = f"/home/{self.user}/"
                        else:
                            if self.command.split(' ')[1] != '':
                                if self.command.split(" ")[1] == '~/':
                                    os.chdir(f"/home/{self.user}/")
                                    self.pwd = f"/home/{self.user}/"
                                else:
                                    os.chdir(self.command.split(' ')[1])
                                    self.pwd = self.command.split(' ')[1]
                            else:
                                os.chdir(f"/home/{self.user}/")
                                self.pwd = f"/home/{self.user}/"
                            
                        self.mqtt.send("cmd_out_L", self.listen_topic, "", qos=2)
                    except Exception as e:
                        #print(e)
                        self.mqtt.send("cmd_out_L", self.listen_topic, str(e), qos=2)
                else:
                    self.p = subprocess.Popen('exec ' + self.command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    self.out, self.error = self.p.communicate()
                    # if self.command.split(' ')[0:2] == 'ls':
                    #     folder = np.array(os.listdir(self.pwd))
                    #     allItems = np.array(self.out)
                        
                         
                    if self.error is not None and len(self.error) > 0:  
                        self.mqtt.send("cmd_out_L", self.listen_topic, self.error, qos=2)
                    else:
                        self.mqtt.send("cmd_out_L", self.listen_topic, self.out, qos=2)
                        

                self.mqtt.MQTT_Message[self.cmd_topic] = []     

    def main(self):
        try:
            while True:
            
                if self.mqtt.MQTT_Message[self.cmd_topic] == "Command Timeout":
                    
                    self.p.kill()
                    self.mqtt.MQTT_Message[self.cmd_topic] = []
        except Exception as e:
            pass
            #print(e)
                
                

if __name__ == "__main__":
    m = MqttTerminalHost("localhost")
    m.main()
        
