import mqtt
import socket
import ast
import os
import threading

server = socket.socket()
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(('', 33333))
server.listen(5)

class threadSystem(threading.Thread):
	systemList = []
	def __init__(self, raspid):
		threading.Thread.__init__(self)
		self.raspid = raspid
		self.devlistdir = './RASP/' + self.raspid + '/' + 'DEVLIST' + '.txt'
		self.devlist = {'FILE':'DEVLIST', 'RASPID':str(self.raspid)}
		self.rulelistdir = './RASP/' + self.raspid + '/' + 'RULELIST' + '.txt'
		self.rulelist = {'FILE':'RULELIST', 'RASPID':str(self.raspid)}
		self.devdatadir = './RASP/' + self.raspid + '/' + 'DEVDATA' + '.txt'
		self.devdata = {'FILE':'DEVDATA', 'RASPID':str(self.raspid)}
		systemList.append(self.raspid)
		tpin = self.raspid + '/s2m'
		tpout = self.raspid + '/m2s'
		self.mqtt = MQTT('iot.eclipse.org', 1883, tpin, tpout)
	def run(self):
		start_time = datetime.datetime.now()
		while True:
			delta = (datetime.datetime.now() - start_time).seconds
			if delta > 60:
				print('System {} disconnected'.format(self.raspid))
				systemList.pop(self.raspid, None)
				return
			self.mqtt.run()
			msg = ''
			msg = self.mqtt.get()
			if msg != '':
				cmd = ast.literal_eval(msg)
				if cmd['FUNC'] == 'UPDATE':
					if cmd['DEV1'] in self.devdata:
						if len(devdata[cmd['DEV1']]) > 100:
							del self.devdata[cmd['DEV1']][0]
						self.devdata[cmd['DEV1']].append(cmd['DATA']['1'])
					else:
						self.devdata[cmd['DEV1']] = []
						self.devdata[cmd['DEV1']].append(cmd['DATA']['1'])
					f = open(devdatadir, 'w')
					f.write(str(self.devdata))
					f.close()
		

def raspHandler(data):
	jsondata = ast.literal_eval(data)
   # print(jsondata)
	raspid = jsondata['RASPID']
	filename = jsondata['FILE']
	if not os.path.isdir('./RASP/' + raspid):
		os.makedirs('./RASP/' + raspid)
   # print('Done mkdir')
	if not os.path.exists('./RASP/' + raspid + '/' + filename + '.txt'):
		f = open('./RASP/' + raspid + '/' + filename + '.txt', 'w')
		f.close()
	f = open('./RASP/' + raspid + '/' + filename + '.txt', 'r')
	current_data = f.read()
	f.close()
	if data != current_data:
		f = open('./RASP/' + raspid + '/' + filename + '.txt', 'w')
		f.write(data)
		f.close()
	if raspid not in threadSystem.systemList:
		threadSystem(raspid)

while True:
    client, addr = server.accept()
    print('Connect from addr {}: {}'.format(addr[0],addr[1]))
    data = client.recv(1024).decode('utf-8')
    raspHandler(data)
