import socket
import keyboard






def main():
    keyboard_client = Keyboard_Client()
    keyboard_client.connect("192.168.1.131",576)
    









class Keyboard_Client:
    def __init__(self) -> None:
        try: 
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print ("client successfully created")
        except socket.error as err: 
            print ("client creation failed with error %s" %(err))
    def connect(self,port,ip):
        try:
            self.client.connect(ip,port)
            print("connection succed")
        except:
            print("failed to connect")

    


if __name__ == "__main__":
    main()