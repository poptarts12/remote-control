import socket
import keyboard
import threading
import tkinter
from PIL import Image, ImageTk
import struct
import io
import time

keyboard_port = 576 #24 * 24
screen_port = 626 # 25 * 25 its funnier

def main():
    # Create threads for each function
    keyboard_thread = threading.Thread(target=keyboard_control)
    screen_thread = threading.Thread(target=screen_control)
    escape_thread = threading.Thread(target=listen_for_escape,args=(keyboard_thread,screen_thread))

    # Start the threads
    keyboard_thread.start()
    screen_thread.start()
    escape_thread.start()

    # Wait for all threads to finish
    keyboard_thread.join()
    screen_thread.join()
    escape_thread.join()

    # Add an input prompt to keep the command prompt open
    input("Press Enter to exit...")

def listen_for_escape(keyboard_thread, screen_thread):
    print("Press 'esc' to exit...")
    keyboard.wait("esc")
    exit()
    # You can perform cleanup or additional actions here if needed


def screen_control():
    screen_viewer_ser =  screen_share_server(screen_port)
    screen_viewer_ser.receive_and_show()

def keyboard_control():
    keyboard_ser = Keyboard_server(keyboard_port)
    keyboard_ser.listen_and_accept()
    keyboard_engine = Keybord_conection(keyboard_ser)
    keyboard_engine.listen_and_send() # listening to the keyboard

class screen_share_server:
    def __init__(self,port) -> None:
        try: 
            self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.server.bind(('', port)) # '' makes the server listen to request coming from other computers on the network 
            gui_thread = threading.Thread(target=self.little_gui)
            gui_thread.start()
            print("screen share server successfully created")
            self.pilImageTk = None
            self.screenshot_name = "last screenshot.jpg"
        except socket.error as err: 
            print("screen share server creation failed with error %s" %(err))
    
    def little_gui(self):
        self.root = tkinter.Tk()
        self.w, self.h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.overrideredirect(1)
        self.root.geometry("%dx%d+0+0" % (self.w, self.h))
        self.root.focus_set()    
        self.root.bind("<Escape>", lambda e: (e.widget.withdraw(), e.widget.quit(), exit())) # if esc button is pressed it will stop
        self.canvas = tkinter.Canvas(self.root,width=self.w,height=self.h)
        self.canvas.pack()
        self.canvas.configure(background='black')
        pil_image = Image.open("temp.jpg")
        pil_image = self.resize_image_to_fit_dimensions(pil_image)
        pil_image = ImageTk.PhotoImage(pil_image)
        self.imagesprite = self.canvas.create_image(self.w/2, self.h/2,image=pil_image)
        
        self.root.mainloop()


    # buff size = 8 bytes header +  4096 bytes image data 
    # first header:  4 bytes image start marker, 4 bytes start size, 2 bytes seq_num, 2 bytes total_packets
    # all the rest packets header: 2 bytes seq_num
    # 'I' represents an unsigned integer, typically 4 bytes.
    # 'HH' represents two unsigned short integers, each typically 2 bytes.
    
    def receive_and_show(self):
        while True:
            # Receive the header (dynamic buffer size based on expected header size)
            header_data, addr = self.server.recvfrom(4108) # more 4 bytes for beggining 
            if not header_data:
                continue

            # Check for the presence of the start of image marker
            if header_data.startswith(b'IMAG'):
                received_data = b""  # b for bytes

                size, seq_num, total_packets = struct.unpack('IHH', header_data[4:12])  # Skip the start of image marker
                print(f"Received header: Size={size}, Sequence Number={seq_num}, Total Packets={total_packets}")
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
                    except OSError as packet_problem:
                        in_order = False
                        print("packet raise error \n ignoring rest of packets")
                        break # check for the start to the next image


                    seq_num = struct.unpack('H', packet[:2])[0]

                    
                    if seq_num != packet_num and in_order:
                        print(seq_num)
                        print(packet_num)
                        print("Packets out of order. Ignoring the image.")
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
                    self.update_image(image)
            else:
                continue     # If the start of image marker is not present, discard the data
    
    
    def update_image(self, pilImage):
        pilImage = self.resize_image_to_fit_dimensions(pilImage)
        # Create a new PhotoImage object and store it as an instance variable
        self.pilImageTk = ImageTk.PhotoImage(pilImage)
        self.canvas.itemconfig(self.imagesprite, image=self.pilImageTk)
        
        self.root.update()

    def resize_image_to_fit_dimensions(self,pilImage):
        imgWidth, imgHeight = pilImage.size
        if imgWidth > self.w or imgHeight > self.h:
            ratio = min(self.w/imgWidth, self.h/imgHeight)
            imgWidth = int(imgWidth*ratio)
            imgHeight = int(imgHeight*ratio)
            pilImage = pilImage.resize((imgWidth,imgHeight), Image.ANTIALIAS)
        return pilImage
    





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