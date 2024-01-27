import socket
import keyboard
import PIL
import threading
from PIL import ImageGrab, Image
import os
import struct
import time 

keyboard_port = 576 #24 * 24
screen_port = 626 # its funnier
ser_ip = "192.168.1.110"


def main():
    if is_connection_possible(ser_ip, keyboard_port): #it is only checking for the tcp because udp cant be checked
        start_threads()
    else:
        print("server is not reachable. fuck you:)")
        exit()


def start_threads():
    # Create threads for each function
    keyboard_thread = threading.Thread(target=keyboard_control)
    screen_thread = threading.Thread(target=share_screen)

    # Start the threads
    keyboard_thread.start()
    screen_thread.start()

    # Wait for both threads to finish
    keyboard_thread.join()
    screen_thread.join()
 

def share_screen():
    sender = Picture_Message_Sender(ser_ip, screen_port)
    while True:
        sender.send_picture_messages()


class Picture_Message_Sender:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send_packet(self, packet):
        self.socket.sendto(packet, (self.host, self.port))

    def send_picture_messages(self):
        picture_maker = picture_message_maker()
        packets = picture_maker.make_picture_packets()
        for packet in packets:
            self.send_packet(packet)
        time.sleep(0.001)

class picture_message_maker:
    # protocol: first 4 bytes is the size of the image
    def __init__(self, chunk_size=4096, start_of_image_marker=b'IMAG') -> None:  #b for bytes
        self.image = None
        self.name = "temp.jpg"
        self.seq_num = 0
        self.size = 0 # can be to 2 ** 32 bytes
        self.chunk_size = chunk_size
        self.start_of_image_marker = start_of_image_marker

    def take_screenshot(self):
        self.image = ImageGrab.grab()
        self.image.save(self.name)

    def calculate_picture_size(self):
        self.size = os.path.getsize(self.name) # in bytes

    def make_picture_packets(self):
        self.take_screenshot()
        self.calculate_picture_size()
        

        # Open the file in binary read mode
        with open(self.name, "rb") as file:
            # Read the content of the file
            image_bytes = file.read()

        total_packets = (len(image_bytes) + self.chunk_size - 1) // self.chunk_size

        packets = []
        for seq_num in range(total_packets):
            start_idx = seq_num * self.chunk_size
            end_idx = min((seq_num + 1) * self.chunk_size, len(image_bytes)) # min function in case will be packet with lower chunk(last chunk)
            chunk = image_bytes[start_idx:end_idx]
        
        # Pack the size, sequence number, and total number of packets
            header = struct.pack('H', seq_num)
            
        # Add the start of image marker to the first packet
            if seq_num == 0:
                header = struct.pack('IHH', self.size, seq_num, total_packets)
                header = self.start_of_image_marker + header

            # Create the packet by concatenating header and image data
            packet = header + chunk
            packets.append(packet)

        return packets



def keyboard_control():
    keyboard_client = Keyboard_Client()
    keyboard_client.connect(ser_ip,keyboard_port)
    keyboard_client.recive_and_press_keys()


class Keyboard_Client:
    def __init__(self) -> None:
        try: 
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print ("keyboard client successfully created")
        except socket.error as err: 
            print ("keyboard client creation failed with error %s" %(err))
            exit()

    def connect(self,ip,port):
        try:
            self.client.connect((ip,port))
            print("keyboard connection succed")
        except:
            print("keyboard failed to connect")


    def recive_and_press_keys(self):
        key = self.client.recv(1024).decode() #reciving key name
        while key != "esc":
            Keyboard_engine.press_and_release(key)
            key = self.client.recv(1024) #reciving key name
            key = key.decode()


class Keyboard_engine:

    def press_and_release(key: keyboard):
        try:
            keyboard.press_and_release(key)
        except:
            print("there was a key that dont exist(probably hebrew letters)")



def is_connection_possible(host, port):
    try:
        # Create a socket and attempt to connect to the specified host and port
        with socket.create_connection((host, port), timeout=5) as s:
            return True  # Connection successful
    except (socket.timeout, ConnectionRefusedError):
        return False  # Connection failed
    


if __name__ == "__main__":
    main()