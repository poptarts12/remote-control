import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QTimer
from PIL import Image, ImageTk
import threading
import keyboard
import socket
import struct
import io

keyboard_port = 576 #24 * 24
screen_port = 626 # 25 * 25 its funnier

def main():
    # Create threads for each function
    keyboard_thread = threading.Thread(target=keyboard_control)
    screen_thread = threading.Thread(target=screen_control)

    # Start the threads
    keyboard_thread.start()
    screen_thread.start()

    # Wait for all threads to finish
    keyboard_thread.join()
    screen_thread.join()

    # Add an input prompt to keep the command prompt open
    input("Press Enter to exit...")



def keyboard_control():
    keyboard_ser = Keyboard_server(keyboard_port)
    keyboard_ser.listen_and_accept()
    keyboard_engine = Keybord_conection(keyboard_ser)
    keyboard_engine.listen_and_send() # listening to the keyboard

def screen_control():
    screen_viewer_ser =  screen_share_server(screen_port)
    screen_viewer_ser.receive_and_show()


class screen_share_server:
    def __init__(self,port) -> None:
        try: 
            self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.server.bind(('', port)) # '' makes the server listen to request coming from other computers on the network 
        except:
            print("server is not working")
            exit()

        self.screenshot_name = "last_screenshot.jpg"
        self.image = None
        self.continue_reciving = True

        # Create the Qt application and main window
        self.app = QApplication(sys.argv)
        self.main_window = QMainWindow()
        self.init_gui()

        # Start the GUI update timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_gui)
        self.timer.start(100)  # Set the update interval in milliseconds
       
        # Start the server thread
        server_thread = threading.Thread(target=self.receive_and_show)
        server_thread.start()

        # Connect the keyPressEvent event to the close_window function
        self.main_window.keyPressEvent = self.close_window

        # Run the application
        sys.exit(self.app.exec_())

    def init_gui(self):
        self.main_widget = QWidget()
        self.main_layout = QVBoxLayout(self.main_widget)

        self.main_widget.setWindowFlags(Qt.WindowType.FramelessWindowHint) 

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)

        # Set the QLabel to cover the full screen without any offset
        screen_rect = QApplication.desktop().screenGeometry()
        self.image_label.setGeometry(screen_rect)

        self.main_layout.addWidget(self.image_label)

        self.main_window.setCentralWidget(self.main_widget)
        self.main_window.showFullScreen()

    def update_gui(self):
        if self.image:
            pixmap = QPixmap.fromImage(self.image)
            self.image_label.setPixmap(pixmap)


    
    def close_window(self, event):
        if event.key() == Qt.Key_Escape:
            self.continue_reciving = False
            self.app.quit()

    

    # buff size = 8 bytes header +  4096 bytes image data 
    # first header:  4 bytes image start marker, 4 bytes start size, 2 bytes seq_num, 2 bytes total_packets
    # all the rest packets header: 2 bytes seq_num
    # 'I' represents an unsigned integer, typically 4 bytes.
    # 'HH' represents two unsigned short integers, each typically 2 bytes.
    
    def receive_and_show(self):
        while self.continue_reciving:
            # Receive the header (dynamic buffer size based on expected header size)
            header_data, addr = self.server.recvfrom(4108) # more 4 bytes for beggining 
            if not header_data:
                continue

            # Check for the presence of the start of image marker
            if header_data.startswith(b'IMAG'):
                received_data = b""  # b for bytes

                size, seq_num, total_packets = struct.unpack('IHH', header_data[4:12])  # Skip the start of image marker
                print(f"Received image header: Size={size}, Sequence Number={seq_num}, Total Packets={total_packets}")
                received_packets = set()
                received_data += header_data[12:] #take the first data
                received_packets.add(seq_num)

                in_order = True  # Flag to track whether packets are in order
                for packet_num in range(1, total_packets):
                    try:
                        if packet_num == total_packets - 1 and in_order:
                            print(str(size % 4096 + 2 ))
                            packet, addr = self.server.recvfrom((size % 4096) + 2)  # Assuming 2 bytes for header seq num and the rest bytes for data
                        else:
                            packet, addr = self.server.recvfrom(4098)  # Assuming 2 bytes for header seq num and 4096 bytes for data
                    except:
                        in_order = False
                        print("packet raise error \n ignoring rest of packets")
                        break # check for the start to the next image


                    seq_num = struct.unpack('H', packet[:2])[0]

                    
                    if seq_num != packet_num and in_order:
                        in_order = False  # Flag to track whether packets are in order
                        break # check for the start to the next image

                    # Process the packet if it's in order
                    if in_order:
                        received_data += packet[2:]
                        received_packets.add(seq_num)

                # If all packets were received in order, display the image
                if in_order and len(received_packets) == total_packets:
                    image = Image.open(io.BytesIO(received_data))
                    image.save(self.screenshot_name)
                    self.image = QImage(self.screenshot_name)

            else:
                continue     # If the start of image marker is not present, discard the data

class Keyboard_server:
    def __init__(self,port) -> None:
        try: 
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind(('', port)) # '' makes the server listen to request coming from other computers on the network 
            print ("keyboard server successfully created")
        except socket.error as err: 
            print ("keyboard server creation failed with error %s" %(err))

    def listen_and_accept(self):
        self.server.listen(1)
        print("keyboard server is listening...")
        self.client_sock, self.adrr = self.server.accept()
        print("keyboard connected to client!")

    def send_key(self, key_pressed):
        print("key pressed: " + key_pressed.name)
        self.client_sock.send(str(key_pressed.name).encode())
        print("key sented")



class Keybord_conection:
    def __init__(self, keyboard_sock: Keyboard_server) -> None:
        self.sock = keyboard_sock

    def listen_and_send(self):
        print("keyboard is in record. for stop press esc")
        keyboard.on_press(self.sock.send_key)
        try:
            keyboard.wait("esc")
        except KeyboardInterrupt:
            pass
        finally:
            keyboard.unhook_all()
            print("pc controlling stopped")
            


if __name__ == "__main__":
    main()