from rs485 import Modbus
from mqtt import MQTT
import rasp_info
import time
import sys
import ast
import threading
import datetime
import socket

devlist = {'FILE':'DEVLIST','RASPID':str(rasp_info.rasp_get_id())}
devdata = {'FILE':'DEVDATA','RASPID':str(rasp_info.rasp_get_id())}
rulelist = {'FILE':'RULELIST','RASPID':str(rasp_info.rasp_get_id())}
rs485Lock = threading.Lock()
devlistLock = threading.Lock()
devdataLock = threading.Lock()
rulelistLock = threading.Lock()
mqttLock = threading.Lock()

tpin = rasp_info.rasp_get_id() + '/m2s'
tpout = rasp_info.rasp_get_id() + '/s2m'
modbus = Modbus('/dev/ttyUSB0')
mqtt = MQTT('iot.eclipse.org', 1883, tpin, tpout)


class threadDeviceManager(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
	def run(self):
		global devlist
		while True:
			rs485Lock.acquire(1)
			devlistLock.acquire(1)
			devdataLock.acquire(1)
			start_time = datetime.datetime.now()
			print('Start scanning for lost device...')
			dev2remove = []
			for key, _ in devlist.items():
				if key == 'FILE':
					continue
				if key == 'RASPID':
					continue
				modbus.send_frame(int(key), 0x01, 0xF1, 0x02)
				frame = modbus.get_frame(2)
				timeout_start = datetime.datetime.now()
				timeout = (datetime.datetime.now() - timeout_start).seconds
				while(frame == 'ERROR' and timeout < 1):
					frame = modbus.get_frame(2)
					timeout = (datetime.datetime.now() - timeout_start).seconds
				
				if frame == 'ERROR':
					print('  + Found a missing device at addr ', key)
					dev2remove.append(key)
			for dev in dev2remove:
				devlist.pop(dev, None)
				devdata.pop(dev, None)
			print('Done')
			print('Start scanning new device')
			addr = 1
			for rand in range(32):
				if addr == 32:
					addr = 0
				while str(addr) in devlist.keys():
					addr = addr + 1
				print('Scanning random num {} for addr {}'.format(rand, addr))
				modbus.send_frame(0x00, 0x00, 0x30, 0x02, rand, addr)
				time.sleep(0.01)
				frame = modbus.get_frame(2)
				if frame == 'ERROR':
					pass
				else:
					print('  + Found new device at addr ', addr)
					devlist[str(addr)] = {'HARDWARE':0,'ID':0}
					devlist[str(addr)]['HARDWARE'] = frame['DATA'][0]
					devlist[str(addr)]['ID'] = frame['DATA'][1]
					#devdataLock.acquire()
					devdata[str(addr)] = []
					#devdata[str(addr)].append(0)
					#devdataLock.release()
					#print(devlist)
					addr = addr + 1
			print('Done')
			end_time = datetime.datetime.now() - start_time
			print('Scanning done in ', str(end_time))
			rs485Lock.release()
			devlistLock.release()
			devdataLock.release()
			input()
			#time.sleep(10)

class threadMqttRun(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
	def run(self):
		while True:
			try:
				mqtt.run()
			except:
				time.sleep(2)
				pass

class threadMqttCommand(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
	def run(self):
		print('Try to connect to mqtt broker')
		while True:
			#mqtt.run()
			try:
				msg = ''
				msg = mqtt.get()
				if(msg != ''):
					rs485Lock.acquire(1)
					cmd = ast.literal_eval(msg)
					if(cmd['ADDR'] != rasp_info.rasp_get_id()):
						print('Wrong addr')
					else:
						if(cmd['FUNC'] == 'WRITE'):
							print('GET WRITE FUNC: \r\n' + str(cmd))
							modbus.send_frame(int(cmd['DEV1']), 0x02, 0x10, 0x02, (int(cmd['DATA']['1'])&0xFF00)>>8, int(cmd['DATA']['1'])&0x00FF)
						elif(cmd['FUNC'] == 'READ'):
							print('GET READ FUNC: \r\n' + str(cmd))
							modbus.send_frame(int(cmd['DEV1']), 0x01, 0x10, 0x02)
						elif(cmd['FUNC'] == 'RULE'):
							print('GET RULE FUNC: \r\n' + str(cmd))
							rulelistLock.acquire()
							rulelist[cmd['DATA']['4']] = {'DEV1':'', 'DEV2':'', 'DATA':{'1':'', '2':'', '3':''}}
							rulelist[cmd['DATA']['4']]['DEV1'] = cmd['DEV1']
							rulelist[cmd['DATA']['4']]['DEV2'] = cmd['DEV2']
							rulelist[cmd['DATA']['4']]['DATA']['1'] = cmd['DATA']['1']
							rulelist[cmd['DATA']['4']]['DATA']['2'] = cmd['DATA']['2']
							rulelist[cmd['DATA']['4']]['DATA']['3'] = cmd['DATA']['3']
							rulelistLock.release()
							#print(rulelist)
						elif(cmd['FUNC'] == 'DELRULE'):
							print('GET DELRULE FUNC: \r\n' + str(cmd))
							rulelistLock.acquire()
							rulelist.pop(cmd['DATA']['4'], None)
							rulelistLock.release()
					res = modbus.get_frame(2)
					timeout_start = datetime.datetime.now()
					timeout = (datetime.datetime.now() - timeout_start).seconds
					while(res == 'ERROR' and timeout < 1):
						res = modbus.get_frame(2)
						timeout = (datetime.datetime.now() - timeout_start).seconds
					if(res != 'ERROR'):
						print(res)
						res_data = str(res['DATA'][0] << 8 | res['DATA'][1])
						#.acquire()
						mqtt.send_frame(cmd['ADDR'], cmd['FUNC'], cmd['DEV1'], cmd['DEV2'], res_data, 'FF', 'FF', 'FF')
						#mqtt.run()
						#mqttLock.release()
					rs485Lock.release()
			except:
				pass
				
class threadUpdateData(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
	def run(self):
		while True:
			mqtt.send_frame(rasp_info.rasp_get_id(), 'UPDATE', '0', 'FF', 'FF', 'FF', 'FF', 'FF')
			devdataLock.acquire()
			print('Get data...')
			for addr, value in devdata.items():
				if addr == 'FILE':
					continue
				if addr == 'RASPID':
					continue
				rs485Lock.acquire(1)
				modbus.send_frame(int(addr), 0x01, 0x10, 0x02)
				res = modbus.get_frame(2)
				timeout_start = datetime.datetime.now()
				timeout = (datetime.datetime.now() - timeout_start).seconds
				while(res == 'ERROR' and timeout < 1):
					res = modbus.get_frame(2)
					timeout = (datetime.datetime.now() - timeout_start).seconds
				rs485Lock.release()
				if res != 'ERROR':
					print(res)
					data = res['DATA'][0] << 8 | res['DATA'][1]
					print(data)
					if(len(devdata) > 100):
						del dev[0]
					devdata[addr].append(data)
					#mqttLock.acquire()
					mqtt.send_frame(rasp_info.rasp_get_id(), 'UPDATE', addr, 'FF', str(data), 'FF', 'FF', 'FF')
					#mqtt.run()
					#mqttLock.release()
			devdataLock.release()
			time.sleep(2)	
			

class threadRule(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
	def run(self):
		global rulelist
		while True:
			condition = False
			rulelistLock.acquire()
			devdataLock.acquire()
			for key, rule in rulelist.items():
				if key == 'FILE':
					continue
				if key == 'RASPID':
					continue
				# Get current value
				try:
					if(int(rule['DEV2']) == 0x00):
						now = datetime.datetime.now()
						data = now.hour*60 + now.minute
					else:
						data = int(devdata[rule['DEV2']][-1])
				except:
					continue
				#print(data)
				# Read rule value
				if (rule['DATA']['2'] == rule['DATA']['3']):
					if data == int(rule['DATA']['2']):
						condition = True
				elif (rule['DATA']['3'] == 'FF'):
					if data > int(rule['DATA']['2']):
						condition = True
				elif (rule['DATA']['3'] == 'FF'):
					if data < int(rule['DATA']['3']):
						condition = True
				else:
					if data > int(rule['DATA']['2']) and data < int(rule['DATA']['3']):
						condition = True
				# Do rule if need
				#print(devlist[rule['DEV1']]['LASTDATA'])
				#print(rule['DATA']['1'])
				if condition == True and int(devdata[rule['DEV1']][-1]) != int(rule['DATA']['1']):
					rs485Lock.acquire()
					modbus.send_frame(int(rule['DEV1']), 0x02, 0x10, 0x02, (int(rule['DATA']['1'])&0xFF00)>>8, (int(rule['DATA']['1'])&0x00FF))		
					res = modbus.get_frame(2)
					timeout_start = datetime.datetime.now()
					timeout = (datetime.datetime.now() - timeout_start).seconds
					while(res == 'ERROR' and timeout < 1):
						res = modbus.get_frame(2)
						timeout = (datetime.datetime.now() - timeout_start).seconds
					if(res != 'ERROR'):
						res_data = res['DATA'][0] << 8 | res['DATA'][1]
						if len(devdata) > 100:
							del devdata[0]
						devdata[str(res['ADDR'])].append(res_data)
					rs485Lock.release()
					print('Task Done ', key)
			rulelistLock.release()
			devdataLock.release()
			#time.sleep(1)

class threadUpdateFile(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.tempdevlist = '{}'
		self.temprulelist = '{}'
		self.tempdevdata = '{}'
	def run(self):
		global devlist
		global rulelist
		need_update = False
		start_time = datetime.datetime.now()
		while True:
			#print('Check file')
			devlistLock.acquire(1)
			rulelistLock.acquire(1)
			devdataLock.acquire(1)
			if self.tempdevlist != str(devlist):
				print('Update dev data')
				self.tempdevlist = str(devlist)
				f = open('./devlist.txt', 'w')
				f.write(str(self.tempdevlist))
				f.close()
				need_update = True
			if self.temprulelist != str(rulelist):
				print('Update rule list')
				self.temprulelist = str(rulelist)
				f = open('./rulelist.txt', 'w')
				f.write(str(self.temprulelist))
				f.close()
				need_update = True
			if self.tempdevdata != str(devdata):
				self.tempdevdata = str(devdata)
				f = open('./devdata.txt', 'w')
				f.write(str(devdata))
				f.close()
			if (datetime.datetime.now() - start_time).seconds > 60:
				start_time = datetime.datetime.now()
				need_update = True
			devlistLock.release()
			rulelistLock.release()
			devdataLock.release()
			if need_update is True:
				print('UPDATE TO SOCKET SERVER')
				for i in range(3):
					try:
						sock = socket.socket()
						sock.connect(('cretatech.com', 33333))
						sock.send(self.tempdevlist.encode('utf-8'))
						sock.close()
						sock = socket.socket()
						sock.connect(('cretatech.com', 33333))
						sock.send(self.temprulelist.encode('utf-8'))
						sock.close()
						need_update = False
						print('UPDATE DONE')
						break
					except:
						time.sleep(1)
						pass
				if need_update is True:
					print('ERROR CONNECT TO SOCKET SERVER')
			time.sleep(1)

try:
	current_rule = open('./rulelist.txt', 'r')
	content = current_rule.read()
	print(content)
	rulelist = ast.literal_eval(content)
except:
	pass

thread1 = threadDeviceManager()
thread2 = threadMqttCommand()
thread3 = threadUpdateData()
thread4 = threadRule()
thread5 = threadUpdateFile()
thread7 = threadMqttRun()
thread_list = [thread1, thread2, thread3, thread4, thread5, thread7]
thread7.start()
thread1.start()
thread2.start()
thread3.start()
thread4.start()
thread5.start()
'''
while True:
	for thread in thread_list:
		if not thread.isAlive():
			print(thread.__class__)
'''
