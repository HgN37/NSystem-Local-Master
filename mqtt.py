import paho.mqtt.client as mqtt
from rasp_info import rasp_get_id
import json
import ast

class MQTT():
	''' Communication with server via WiFi or Ethernet '''
	payload_queue = []
	def __init__(self, broker, port, topicin, topicout):
		self.topicin = topicin
		self.topicout = topicout
		def on_connect(client, userdata, flags, rc):
			print('Connected with code ' + str(rc))
			client.subscribe(self.topicin)
			print('Connected to ' + broker)
			print('Subscribed to ' + self.topicin)

		def on_message(client, userdata, msg):
			# print(msg.topic + ': ' + msg.payload.decode('utf-8'))
			# print('Get msg')
			self.payload_queue.append(msg.payload.decode('utf-8'))

		def on_disconnect(client, userdata, rc):
			print('Disconnect from ' + broker)
			print('Try to reconnect')
			client.reconnect()

		self.client = mqtt.Client()
		self.client.on_connect = on_connect
		self.client.on_message = on_message
		self.client.on_disconnect = on_disconnect

		self.client.connect(broker, port, 60)

	def send(self, payload):
		self.client.publish(self.topicout, payload)

	def get(self):
		next_msg = ''
		if len(self.payload_queue):
			next_msg = self.payload_queue[0]
			del self.payload_queue[0]
		return next_msg

	def run(self):
		self.client.loop()

	def send_frame(self, addr, func, dev1, dev2, *data):
		tx = {}
		tx['ADDR'] = addr
		tx['FUNC'] = func
		tx['DEV1'] = dev1
		tx['DEV2'] = dev2
		tx['DATA'] = {}
		for i in range(len(data)):
			tx['DATA'][str(i+1)] = data[i]
		self.send(json.dumps(tx))

def main():
	tpin = rasp_get_id() + '/m2s'
	tpout = rasp_get_id() + '/s2m'
	mqtt = MQTT('iot.eclipse.org', 1883, tpin, tpout)
	msg = ''
	while True:
		msg = mqtt.get()
		if (msg != ''):
			print(msg)
			mqtt.send_frame('USER1', 'CONTROL', 'LED', 'NONE', 'ON')
			msg = ''
		mqtt.run()

if __name__ == '__main__':
	main()
