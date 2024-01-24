import socket
import keyboard




def main():
    ser = Server(576)
    ser.listen_and_accept()










class Server:
    def __init__(self,port) -> None:
        try: 
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind(('', port)) # '' makes the server listen to request coming from other computers on the network 
            print ("server successfully created")
        except socket.error as err: 
            print ("server creation failed with error %s" %(err))
    def listen_and_accept(self):
        self.server.listen(1)
        print("server is listening...")
        self.client_sock, self.adrr = self.server.accept()
        print("connected to client!")

    
        
class Keybordconection:
    pass
 




if __name__ == "__main__":
    main()