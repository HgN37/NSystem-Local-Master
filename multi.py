import threading
import time

class mythread(threading.Thread):
	def __init__(self, t):
		threading.Thread.__init__(self)
		self.t = t
	def run(self):
		count = 10
		while count:
			print(str(self.t))
			time.sleep(self.t)
			count = count - 1
		
thread1 = mythread(1)
thread2 = mythread(2)

thread1.start()
thread2.start()
