import socket
import keyboard






def main():
    cli = Client()
    cli.connect("192.168.1.110",576)
    









class Client:
    def __init__(self) -> None:
        try: 
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print ("client successfully created")
        except socket.error as err: 
            print ("client creation failed with error %s" %(err))
    def connect(self,port,ip):
        try:
            self.client.connect(ip,port)
        except:
            print("failed to connect")
    
    