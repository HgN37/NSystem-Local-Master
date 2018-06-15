<<<<<<< HEAD
import serial

ser = serial.Serial()
ser.baudrate = 9600
ser.parity = serial.PARITY_EVEN
ser.port = '/dev/ttyUSB0'
ser.open()

while True:
	print('.')
	ser.write(0xFF)
	ser.flush()
=======
import socket

socketServer = socket.socket(
    socket.AF_INET, socket.SOCK_STREAM)
print(socket.gethostname())
socketServer.bind(('3.7.96.104', 37777))
socketServer.listen(5)

while True:
  print('Wait for connection')
  (client, address) = socketServer.accept()
  try:
    print('Connect from ', address)
  finally:
    client.close()
>>>>>>> 58c0732ccba179373605a6ae3085b5bd6a8fcfbd
