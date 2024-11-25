import os
import time

class FileHandler:

    def __init__(self, file, mqtt, cmd_topic, listen_topic, timeout):
        self.mqtt = mqtt
        self.listen_topic = listen_topic
        self.timeout = timeout
        self.cmd_topic = cmd_topic
        self.file = file
        self.file_path_to_store = f"{os.path.dirname(__file__)}/{self.file}"
        self.opened_file = ""

    def open_file(self, file):
        self.mqtt.send("cmd_in", self.cmd_topic, f"cat {file}", qos=2)
        start_time = time.time()
        while True:
            output = self.mqtt.MQTT_Message[self.listen_topic]
            current_time = time.time()
            if current_time - start_time >= self.timeout:
                self.mqtt.send("cmd_in", self.cmd_topic, "Command Timeout", qos=2)
                time.sleep(2)
                print("Command Timeout")
                self.mqtt.MQTT_Message[self.listen_topic] = []
                break
            if output != []:
                print(f"File Contents are stored in {self.file}")

                with open(self.file_path_to_store, "w") as f:
                    f.write(output)
                    self.mqtt.MQTT_Message[self.listen_topic] = []
                break
    
    def save_file(self, file_to_save):
        with open(self.file_path_to_store, "r") as f:
            self.opened_file = "".join(f.readlines())

        self.mqtt.send("cmd_in", self.cmd_topic, f"printf '{self.opened_file}' > {file_to_save}", qos=2)
        start_time = time.time()
        while True:
            output = self.mqtt.MQTT_Message[self.listen_topic]
            current_time = time.time()
            if current_time - start_time >= self.timeout:
                self.mqtt.send("cmd_in", self.cmd_topic, "Command Timeout", qos=2)
                time.sleep(2)
                print("Command Timeout")
                self.mqtt.MQTT_Message[self.listen_topic] = []
                break
            if output != []:
                print(f"File Contents are stored in {self.file}")
                self.mqtt.MQTT_Message[self.listen_topic] = []
                break
    


if "__main__" == __name__:
    f = FileHandler("opened_file.txt")

    print(f.save_file())