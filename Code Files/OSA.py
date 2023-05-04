import socket
from time import sleep, time

class OSA:
    # Class to operate the OSA
    def __init__(self, IP):
        # Create a TCP/IP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect the socket to the port where the server is listening
        server_address = (IP, 10001)
        print('connecting to {} port {}'.format(*server_address))
        self.sock.connect(server_address)
        self.sock.settimeout(120)
        self.Auth()
        self._pts = None


    def sendToOSA(self, string: str, print_flag = True):
        # Add a newline character to the end of the string
        string = string + "\r\n"
        if print_flag:
            print('sending {}'.format(string))
        # Convert the string to a binary representation
        binary_data = string.encode("utf-8")
        # Sending the correct format to OSA
        self.sock.sendall(binary_data)

    def receiveFromOSA(self, MSGLEN = 1024) -> str:
        # Add a newline character to the end of the string
        binary_data = self.sock.recv(1024)
        string = binary_data.decode("utf-8")
        # Remove the newline character from the end of the string
        string = string.rstrip("\r\n")
        return string

    def Auth(self):
        self.sendToOSA('open \"anonymous\"') # This is open \"Username"
        if self.receiveFromOSA() != 'AUTHENTICATE CRAM-MD5.':
            print("Connection failed\n")
            self.sock.close()
            return False
        else:
            self.sendToOSA(' ') # Here is the password. If there is no password send '_' (a 'space').
            if self.receiveFromOSA() != 'ready':
                print("Connection failed\n")
                self.sock.close()
                return False
            else:
                print("Auth succeed\n")
                return True

    def setCenterFreq(self, cf):
        # Set the centeer frequency in nm.
        try:
            cf = float(cf)
            if cf < 600 or cf > 1700:
                print("Failed to change Center Frequency, Input must be in range [600,1700]")
                return False
        except:
                print("Failed to change Center Frequency, Input must be number")
                return False
        self.sendToOSA(':sens:wav:cent {}nm'.format(cf))
        return True

    def setSpan(self, span):
        # Set the span. The range will be: [(cf-span/2, cf+span/2)]
        self.sendToOSA(':sens:wav:span {}nm'.format(span))
        return True

    def setPoints(self, points):
        # The number of points per sweep.
        if points == 'auto on':
            self.sendToOSA(':sens:sweep:points:{}'.format(points))
        else:
            self.sendToOSA(':sens:sweep:points:auto off')
            self.sendToOSA(':sens:sweep:points {}'.format(points))
            
        
        self.sendToOSA(':sens:sweep:points?')

        self._pts = int(self.receiveFromOSA())
        return True
    
    def getPoints(self):
        return self._pts
    
    def setAveraging(self, times):
        # from documantation :SENSE:AVERAGE:COUNT 100
        self.sendToOSA(':SENSE:AVERAGE:COUNT {}'.format(times))

    def setSpeed(self, speed):
        # Changing the speed of the sweep
        self.sendToOSA(':sens:sweep:speed {}'.format(speed))
        return True

    def setSens(self, sens):
        # Changing the sensetivity of the device measurment
        self.sendToOSA(':sens:sens {}'.format(sens))
        return True

    ############################################################################## Page 68 on OSA Control Manuall
    def setRes(self, res):
    # Changing the resolution of the device measurment
        # self.sendToOSA(':SENSe:BANDwidth|:BWIDth[:RESolution]<wsp><NRf>[M|Hz]'.format(res))
        self.sendToOSA(':SENSE:BANDWIDTH:RESOLUTION {:.3f}NM'.format(float(res)))
        #self.sendToOSA(''.format(res))
        return True

    def saveBMPFile(self, name='temp'):
        # Saving a picture from the OSA device.
        self.sendToOSA(':mmem:stor:grap color,bmp,"{}",int'.format(name))
        self.sendToOSA(':mmem:data? \"{}.bmp\",int'.format(name))
        return self.sock.recv(1024*1024)

    def getCSVFile(self, name="temp"):
        # Getting an Excel file - the data for the measurment to work with.
        self.sendToOSA(':MMEMORY:CDIRECTORY?')
        print(self.receiveFromOSA())
        self.sendToOSA(':MMEMORY:STORE:TRACE TRA,CSV,"{}",INTERNAL'.format(name))
        completeFile = False
        while not completeFile:
            # self.sendToOSA(':MMEMORY:DATA "{}.csv", internal'.format(name))
            self.sendToOSA(':MMEMORY:DATA? "{}.csv", internal'.format(name))
            data = self.sock.recv(1024*1024)
            sleep(0.5)
            if self.__checkNumberOfPoints(data=data):
                completeFile = True
        self.sendToOSA(':MMEMORY:DELETE "{}.csv", internal'.format(name))
        return data

#--------------------------------------here we must start changing.
    def sweep(self, mode=1):
        # number of sweeps
        while mode != 0:
            # mode: number of sweeps


            self.sendToOSA(':init:smode 1')
            self.sendToOSA('*CLS')
            sweep_completed = False
            while not sweep_completed:
                self.sendToOSA(':init')
                start = time()
                # Wating for sweep to complete
                while True:
                    self.sendToOSA(':stat:oper:even?', print_flag=False)                
                    ans = self.receiveFromOSA()
                    if ans == '1':
                        sweep_completed = True
                        break
                    if time() - start > 30:
                        break             
                
            mode = mode - 1
    
    def sweepLive(self, mode=1):
        # number of sweeps
        sleepTime = 0.1
        index = 0
        while mode != 0:
            # mode: number of sweeps
            sleep(0.05)
            self.sendToOSA(':init:smode 1')
            sleep(0.05)
            self.sendToOSA('*CLS')
            sleep(0.05)
            self.sendToOSA(':init')
            sleep(0.05)

            # Wating for sweep to complete
            N = 200 * sleepTime
            i = 0
            ans = '0'
            index = index + 1
            while(ans != '1'):
                self.sendToOSA(':stat:oper:even?', print_flag=False)
                print("Before: ")
                print(index)
                ans = self.receiveFromOSA()
                print("After: ")
                print(index)
                sleep(sleepTime)
                i = i+1
                if (i >= N):
                    ans = '1'

            print(index)
            print(i)    
            mode = mode - 1

    def __checkNumberOfPoints(self, data):
        data_decoded = data.decode("utf-8")
        data_decoded = data_decoded.split("\r\n")
        len_smpls = len(data_decoded[39:-2])
        if len_smpls == self._pts:
            return True
        return False


if __name__ == '__main__':
    osa = OSA(IP = '10.0.0.101')
    osa.setAveraging('2')
