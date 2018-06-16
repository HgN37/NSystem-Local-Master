import serial
import sys
from gpiozero import LED
# import time

class RS485():
	''' Communication with slave via RS485 '''
	def __init__(self, port):
		self.ser = serial.Serial()
		self.ser.baudrate = 9600
		self.ser.parity = serial.PARITY_EVEN
		self.ser.port = port
		self.fix = 0
		try:
			self.ser.open()
		except:
			print("ERROR: Can't open port " + port)
	def send(self, array):
		self.ser.write(bytearray(array))
		self.ser.flush()
	def available(self):
		return self.ser.in_waiting
	def get(self):
		if self.available():
			byte = ord(self.ser.read())
			#print("0x{:02x}".format(byte))
			return byte

class Modbus(RS485):
	''' Modbus protocol '''

	def crc_generate(self, current_crc, new_byte):
		next_crc = current_crc ^ new_byte
		for loop in range(8):
			if (next_crc & 0x0001) != 0:
				next_crc = next_crc >> 1
				next_crc = next_crc ^ 0xA001
			else:
				next_crc = next_crc >> 1
		return next_crc
	def send_frame(self, addr, func, reg, num, *data):
		frame = []
		crc = 0xFFFF
		frame.append(addr)
		crc = self.crc_generate(crc, addr)
		frame.append(func)
		crc = self.crc_generate(crc, func)
		frame.append(reg)
		crc = self.crc_generate(crc, reg)
		frame.append(num)
		crc = self.crc_generate(crc, num)
		for byte in range(len(data)):
			frame.append(data[byte])
			crc = self.crc_generate(crc, data[byte])
		frame.append((crc & 0xFF00) >> 8)
		frame.append((crc & 0x00FF))
		#print(frame)
		self.send(frame)
	def get_frame(self, num):
		frame = {'ADDR':0, 'FUNC':0, 'REG':0, 'NUM':0, 'DATA':[], 'CRC1':0, 'CRC2':0}
		if self.available():
			crc = 0xFFFF
			time_out = 0xFFFF
			while(self.available() == 0 and time_out != 0 ):
				time_out = time_out - 1
			if time_out == 0:
				print('Timeout1')
				return 'ERROR'
			frame['ADDR'] = self.get()
			#print(frame['ADDR'])
			crc = self.crc_generate(crc, frame['ADDR'])
			time_out = 0xFFFF
			while(self.available() == 0 and time_out != 0 ):
				time_out = time_out - 1
			if time_out == 0:
				print('Timeout2')
				return 'ERROR'
			frame['FUNC'] = self.get()
			#print(frame['FUNC'])
			crc = self.crc_generate(crc, frame['FUNC'])
			'''
			time_out = 0xFFFF
			while(self.available() == 0 and time_out != 0 ):
				time_out = time_out - 1
			if time_out == 0:
				print('Timeout3')
				return 'ERROR'
			frame['REG'] = self.get()
			#print(frame['REG'])
			crc = self.crc_generate(crc, frame['REG'])
			time_out = 0xFFFF
			while(self.available() == 0 and time_out != 0 ):
				time_out = time_out - 1
			if time_out == 0:
				print('Timeout4')
				return 'ERROR'
			frame['NUM'] = self.get()
			crc = self.crc_generate(crc, frame['NUM'])
			'''
			for i in range(num):
				time_out = 0xFFFF
				while(self.available() == 0 and time_out != 0 ):
					time_out = time_out - 1
				if time_out == 0:
					print('Timeout5')
					return 'ERROR'
				frame['DATA'].append(self.get())
				crc = self.crc_generate(crc, frame['DATA'][i])
			time_out = 0xFFFF
			while(self.available() == 0 and time_out != 0 ):
				time_out = time_out - 1
			if time_out == 0:
				print('Timeout6')
				#print(frame)
				return 'ERROR'
			frame['CRC1'] = self.get()
			time_out = 0xFFFF
			while(self.available() == 0 and time_out != 0 ):
				time_out = time_out - 1
			if time_out == 0:
				print('Timeout7')
				return 'ERROR'
			frame['CRC2'] = self.get()
			if(crc != ((frame['CRC1'] << 8) | frame['CRC2'])):
				#print(frame)
				print(crc)
				print('crc')
				return 'ERROR'
			#self.ser.reset_input_buffer()
			return frame
		else:
			return 'ERROR'


def main():
	print('Master - Slave Connection')
	slave = Modbus('/dev/ttyUSB0')
	while True:
		slave.send_frame(0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF)


if __name__ == '__main__':
	main()
