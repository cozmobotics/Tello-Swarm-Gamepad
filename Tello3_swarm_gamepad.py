#! /usr/bin/python3
# tello demo by Ryze Robotics, modified by Martin Piehslinger

import threading 
import socket
import sys
import time
import pygame

#-----------------------------------------------------------------------------------
def recv1():
	global TimeSent
	global Ready
	global Running
	global DataDecoded
	
	print ("Tello recv task 1 started")
	count = 0
	while Running: 
		RecvError = False
		try:
			data, server = sock1.recvfrom(1518)
		except Exception as e:
			RecvError = True
			if (str(e) == 'timed out'):
				# print (".", end = "") # python2 users, please remove this line
				pass
			else:
				log ('\n------------------- Exception: ' + str(e) + '\n')
				break
		if (not RecvError):
			try:
				DataDecoded = data.decode(encoding="utf-8")
				print('-1-:' + DataDecoded)
				Ready = True
			except Exception as e:
				print (str(e))

	sock1.close()
	print ("recv 1 ended")
#-----------------------------------------------------------------------------------
def recv2():
	global TimeSent
	global Ready
	global Running
	global DataDecoded
	
	print ("Tello recv task 2 started")
	count = 0
	while Running: 
		RecvError = False
		try:
			data, server = sock2.recvfrom(1518)
		except Exception as e:
			RecvError = True
			if (str(e) == 'timed out'):
				# print (".", end = "") # python2 users, please remove this line
				pass
			else:
				log ('\n------------------- Exception: ' + str(e) + '\n')
				break
		if (not RecvError):
			try:
				DataDecoded = data.decode(encoding="utf-8")
				print('-2-:' + DataDecoded)
				Ready = True
			except Exception as e:
				print (str(e))
				
	sock2.close()
	print ("recv 2 ended")
#--------------------------------------------------------------
def rcCommand (RcArray):
	'''create a command like rc 100 100 100 100 from an array of 4 integers'''
	RcCommand = 'rc'
	for Count in range (0,4):
		if (RcArray[Count] > 100):
			RcArray[Count] = 100
		if (RcArray[Count] < -100):
			RcArray[Count] = -100
		RcCommand = RcCommand + ' ' + str(RcArray[Count])
	
	print (RcCommand)
	return (RcCommand)


#-----------------------------------------------------------------------------------
def timeout():
	global Running
	global sock1
	global sock2
	global timeout1
	global timeout2
	global timeoutSeconds
	
	print ("Tello keepalive task started")
	keepaliveCommand = "command"
	keepaliveCommand = keepaliveCommand.encode(encoding="utf-8") 
	
	while Running: 
		time.sleep(1)
		
		timeout1 = timeout1 - 1
		if timeout1 <= 0:
			sock1.sendto(keepaliveCommand, tello_address_1)
			timeout1 = timeoutSeconds
			
		timeout2 = timeout2 - 1
		if timeout2 <= 0:
			sock2.sendto(keepaliveCommand, tello_address_2)
			timeout2 = timeoutSeconds
			
	print ("keepalive task ends")
			
#-----------------------------------------------------------------------------------
def pad():
	global Running
	global Rc
	global sock1
	global sock2
	global Ready
	global enable1
	global enable2
	global timeout1
	global timeout2
	global timeoutSeconds
	global multYaw
	global multPitch		# same as multYaw,but reverse Forward/Back
	global multRoll		# same as multYaw,but reverse Left/Right


	timeEnd = 0
	vals = []
	
	pygame.init()	# to avoid: pygame.error: video system not initialized
	pygame.joystick.init()

	numJoysticks = pygame.joystick.get_count()
	print ("%i gamepad(s) found" % numJoysticks)

	if (numJoysticks > 0):

		_joystick = pygame.joystick.Joystick(0)
		_joystick.init()
		print ("Joystick name: ", _joystick.get_name())
		num_axes = _joystick.get_numaxes()
		print ("joystick has ", num_axes, " axes")
		if (num_axes < 4):
			print ("WARNING: This joystick is not suitable for steering a quadrocopter!")
		
		while (Running):
			now = time.time()
			msg = "" # preset
			for event in pygame.event.get(): 				# User did something.
				if event.type == pygame.JOYBUTTONDOWN:
					print ("button down ", event.button)
					if (event.button == 0):		# B
						msg = "land"
						timeEnd = now
					elif (event.button == 1):	# A
						enable1 = False
						enable2 = True
						print ("enabling Tello 2")
					elif (event.button == 2):	# Y
						enable1 = True
						enable2 = False
						print ("enabling Tello 1")
					elif (event.button == 3):	# X
						enable1 = True
						enable2 = True
						print ("enabling Tello 1 and 2")
					elif (event.button == 4):	# left shoulder button
						multYaw = 1
					elif (event.button == 5):	# right shoulder button
						multYaw = -1
					elif (event.button == 6):	# back
						msg = "takeoff"
					elif (event.button == 7):	# start
						#Running = False
						msg  = "rc -100 -100 -100 100"		# start motors
						msg2 = "rc -100 -100 -100 100"		# start motors
					elif (event.button == 9):	# left stick
						enable1 = True
						enable2 = True
						msg = "emergency"
					elif (event.button == 10):	# right stick
						enable1 = True
						enable2 = True
						msg = "emergency"
				elif event.type == pygame.JOYBUTTONUP:
					if (event.button == 0):		# B
						timeEnd = 0
						msg  = "rc 0 0 0 0"		
						msg2 = "rc 0 0 0 0"		
				elif event.type == pygame.JOYHATMOTION:
					print ("hat event ", event.type)
					(hor,vert) = event.value
					if (hor != 0):
						multRoll = -hor
					if (vert != 0):
						multPitch = vert
					print ("LR:", multRoll, " FB:", multPitch)
				elif event.type == pygame.JOYAXISMOTION: 
					old_vals = vals
					vals = []
					for axis in range (num_axes):
						vals.append (int(100 *_joystick.get_axis(axis)))
					if old_vals != vals:
						if (len(vals) >= 5):
							msg = "rc " + str(vals[3]) + " " + str(-vals[4]) + " " + str(-vals[1]) + " " + str(vals[0])
							msg2 = "rc " + str(vals[3] * multRoll) + " " + str(-vals[4] * multPitch) + " " + str(-vals[1]) + " " + str(multYaw * vals[0])
	
					
			if (msg != ""):
				if not msg.startswith("rc"):
					print (msg)
					msg2 = msg
				if enable1:
					msg = msg.encode(encoding="utf-8") 
					sent = sock1.sendto(msg, tello_address_1)
					timeout1 = timeoutSeconds
				if enable2:
					msg2 = msg2.encode(encoding="utf-8") 
					sent = sock2.sendto(msg2, tello_address_2)
					timeout2 = timeoutSeconds
					
			if (timeEnd > 0) and (now > timeEnd + 3.0):
				Running = False
				print ("ending program, please press Return to quit")

		# loop has ended
		_joystick.quit()
	else:
		print ("WARNING: No gamepad found")
		
	print ("pad task ended")
#-----------------------------------------------------------------------------------

# customize the following 4 lines to reflect your setup 
tello_address_1 = ('192.168.10.1', 8889)
tello_address_2 = ('192.168.10.1', 8889)
wlan0 = 'wlan0'
wlan1 = 'wlan1'

host = ''
port = 9000
locaddr = (host,port) 


# Create a UDP socket
sock1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock1.setsockopt(socket.SOL_SOCKET, 25, wlan0.encode()) # Linux only 
sock1.settimeout (1)

sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock2.setsockopt(socket.SOL_SOCKET, 25, wlan1.encode()) # Linux only 
sock2.settimeout (1)

sock1.bind(locaddr)
sock2.bind(locaddr)
TimeSend = 0
Ready = True
enable1 = True
enable2 = True
timeout1 = 0
timeout2 = 0
timeoutSeconds = 10
multYaw = 1 	# set to -1 to let the Tellos turn in different directions
multPitch  = 1		# same as multYaw,but reverse Forward/Back
multRoll  = 1		# same as multYaw,but reverse Left/Right

print ('\r\n\r\nTello Python3 Demo.\r\n')

print ('Tello: command takeoff land flip forward back left right \r\n       up down cw ccw speed speed? battery?\r\n')

print ('end -- quit demo.\r\n')

Running = True
DataDecoded = ""

#recvThread create
recvThread1 = threading.Thread(target=recv1)
recvThread1.start()

#recvThread create
recvThread2 = threading.Thread(target=recv2)
recvThread2.start()

#padThread create
padThread = threading.Thread(target=pad)
padThread.start()

#timeoutThread create
timeoutThread = threading.Thread(target=timeout)
timeoutThread.start()

while Running: 
	# if (Ready):
		try:
			msg = input(">");

			if not msg:
				break  

			msg = msg.strip()
			
			if 'end' == msg:
				print ('End requested')
				Running = False
				# break

			elif (msg == "1"):
				enable1 = True
				enable2 = False
				print ("enabling Tello 1")
			elif (msg == "2"):
				enable2 = True
				enable1 = False
				print ("enabling Tello 2")
			elif (msg == "3"):
				enable1 = True
				enable2 = True
				print ("enabling Tello 1 and 2")
			elif (msg == "rr"):
				multRoll = multRoll * (-1)
				print ("Roll:", multRoll)
			elif (msg == "pp"):
				multPitch = multPitch * (-1)
				print ("Pitch:", multPitch)
			elif (msg == "yy"):
				multYaw = multYaw * (-1)
				print ("Yaw:", multYaw)
				
			# Send data
			else:
				Ready = False
				msg2 = msg
				if enable1:
					# print ("sending " + msg)
					msg = msg.encode(encoding="utf-8") 
					sent = sock1.sendto(msg, tello_address_1)
					timeout1 = timeoutSeconds
				if enable2:
					#reverse cw/ccw etc.
					if (multYaw == -1): 
						if (msg2.startswith ("ccw")):
							msg2 = msg2.replace ("ccw", "cw")
						elif (msg2.startswith ("cw")):
							msg2 = msg2.replace ("cw", "ccw")
					if (multPitch == -1): 
						if (msg2.startswith ("forward")):
							msg2 = msg2.replace ("forward", "back")
						elif (msg2.startswith ("back")):
							msg2 = msg2.replace ("back", "forward")
					if (multRoll == -1): 
						if (msg2.startswith ("left")):
							msg2 = msg2.replace ("left", "right")
						elif (msg2.startswith ("right")):
							msg2 = msg2.replace ("right", "left")
					print ("sending " + msg2)
					msg2 = msg2.encode(encoding="utf-8") 
					sent = sock2.sendto(msg2, tello_address_2)
					timeout2 = timeoutSeconds
					TimeSent = time.time()
				# print (str(sent) + ' bytes sent')
		except KeyboardInterrupt:
			print ("Ctrl-C received, exit")
			Running = False

TimeShutdown = 2
print ("Will shut down in " + str(TimeShutdown) + " seconds")
time.sleep (TimeShutdown) # give recv tasks some time to end 
print ("Thank you for using Tello")



