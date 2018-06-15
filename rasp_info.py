def rasp_get_id():
	serial = ""
	try:
		f = open('/proc/cpuinfo', 'r')
		for line in f:
			if line[0:6] == 'Serial':
				serial = line[10:26]
		f.close()
	except:
		serial = 'ERROR'
	return serial

def main():
	print(rasp_get_id())

if __name__ == '__main__':
	main()