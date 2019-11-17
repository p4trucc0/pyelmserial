import pandas as pd
import numpy as np
import math
import serial
import time
import datetime

# Andrea Patrucco, 16/11/2019
# Library to access the ELM327 usb - serial "dongle"

DEFAULT_BAUDRATE = 38400
DEFAULT_PORT = "COM33"
DEFAULT_TERMINATOR = b"\r"
DEFAULT_TIMEOUT = 2 # seconds?

#datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
DATETIME_LOG_FORMAT = r"%Y-%m-%d %H:%M:%S.%f"
DATETIME_FILES_FORMAT = r"%Y_%m_%d_%H_%M_%S"

class Elm327:
	def __init__(self, comport = DEFAULT_PORT, baudrate = DEFAULT_BAUDRATE, \
		terminator = DEFAULT_TERMINATOR, timeout = DEFAULT_TIMEOUT, log_file = None, \
		auto_open_serial = False, poll_list = list()):
		self.comport = comport
		self.baudrate = baudrate
		self.terminator = terminator
		self.timeout = timeout
		if log_file is None:
			self.log_file = datetime.datetime.now().strftime(DATETIME_FILES_FORMAT) + '_elm.txt'
		else:
			self.log_file = log_file
		self.auto_open_serial = auto_open_serial
		self.add_log("INIT", "Object created.")
		self.add_log("INIT", "Serial port set to " + self.comport)
		self.add_log("INIT", "Baudrate set to " + str(self.baudrate))
		self.poll_list = poll_list
		self.serial = None
		if self.auto_open_serial:
			self.open()
		pass

	# Logging function:
	#	- logtype: brief string describing type of log
	#	- data: string describing event.
	def add_log(self, logtype, data):
		log = open(self.log_file, 'a')
		log.write(datetime.datetime.now().strftime(DATETIME_LOG_FORMAT) + "\t" + logtype + "\t" + data + "\n")
		log.close()
		pass

	def open(self):
		self.serial = serial.Serial(self.comport, self.baudrate, \
			timeout = self.timeout)
		self.add_log("OPEN", "Serial port object created.")
		pass

	def write(self, data):
		if not self.serial is None:
			data_full = data.encode('utf-8') + self.terminator # Check this!
			self.add_log("TX", data)
			self.serial.write(data_full)
		else:
			self.add_log("TX", "Error: Serial Port is undefined.")
		pass

	def read_until_char(self, endchar = b">"):
		if not self.serial is None:
			last_char = b'.' # any, try with null
			bstr = ''
			while (last_char != endchar): # add some basic timeout here!
				last_char = self.serial.read(1)
				bstr = bstr + last_char.decode('utf-8')
			bstr_log = bstr.replace(self.terminator.decode('utf-8'), '_')
			self.add_log("RX", bstr_log)
		else:
			bstr = None
			self.add_log("RX", "Error: Serial Port is Undefined.")
		return bstr

	def add_to_poll_list(self, idn):
		if not idn in self.poll_list:
			self.poll_list.append(idn)
			self.add_log("POLL_MNG", "Added id " + str(idn) + " to Poll List")
		else:
			self.add_log("POLL_MNG", "Could not add id " + str(idn) + "to Poll List: already there...")
		pass

	def remove_from_poll_list(self, idn):
		if not idn in self.poll_list:
			self.add_log("POLL_MNG", "Could not remove id " + str(idn) + " from Poll List: not there...")
		else:
			self.poll_list.remove(idn)
			self.add_log("POLL_MNG", "Removed id " + str(idn) + "from Poll List")		
		pass

	# Pass to the ELM327 initial commands.
	# TODO: add formatting options (correct parsing depends upon them)
	# TODO: add checks to determine whether initialization failed.
	def initialize(self):
		if not self.serial is None:
			self.write("ATZ")
			msgo = self.read_until_char()
			self.write("ATSP0")
			msgo = self.read_until_char()
			self.add_log("ELM_INIT", "Device initialized with ATZ - ATSP0 sequence.")
		else:
			self.add_log("ELM_INIT", "Error: could not initialize ELM327: serial does not exist.")
		pass

	def poll_signal(self, idn, parse_out = False):
		hex_id = hex(idn)[2:].upper()
		if len(hex_id) < 2:
			hex_id = '0' + hex_id
		str2send = "01" + hex_id
		self.add_log("POLL_MNG", "Polling id " + str(idn) + ".")
		self.write(str2send)
		out = self.read_until_char()
		if parse_out:
			# self.add_log("PARSER", "Sorry, still not implemented.")
			self.parse_out(out, idn)
		pass

	def parse_out(self, msg, idn):
		try:
			dct_prs = ob2_parser_v0(msg, idn)
			str2log = "Msg Id: " + str(dct_prs['IdR']) + " (" + \
				dct_prs['Descr'] + ") - Value = " + str(dct_prs['Val'])
			self.add_log("PARSER", str2log)
		except:
			self.add_log("PARSER", "Error in parsing message.")
		pass

	def poll(self, parse_out = False, timeout = 30):
		t0 = datetime.datetime.now()
		if parse_out:
			addstr = " parsing output."
		else:
			addstr = " without parsing output"
		self.add_log("POLL_MNG", "POLLSTART with timeout " + str(timeout) + addstr)
		t1 = t0
		while ((t1 - t0).seconds < timeout):
			t1 = datetime.datetime.now()
			for idx in self.poll_list:
				self.poll_signal(idx, parse_out = parse_out)
		self.add_log("POLL_MNG", "POLLEND after timeout.")
		pass


def ob2_parser_v0(msg, idx, sp = "\r", long_format = True):
	out = dict()
	# Split message removing returns.
	msgs = msg.split(sp)
	ms = msgs[1]
	print(ms)
	msi = hexstr2list(ms)
	if long_format:
		msi = msi[3:-1]
	# TODO: implement this as sort of switch-dict
	idr = msi[1]
	out['Ack'] = msi[0] == 65
	out['IdR'] = msi[1]
	if idx == 0:
		out['Descr'] = "PIDs supported (bits)"
		out["Val"] = (256 ** 3) * msi[2] + (256 ** 2) * msi[3] + (256 ** 1) * msi[4] + msi[5]
	elif idx == 1:
		out['Descr'] = "Status since DTCC (bits)"
		out["Val"] = (256 ** 3) * msi[2] + (256 ** 2) * msi[3] + (256 ** 1) * msi[4] + msi[5]
	elif idx == 2:
		out['Descr'] = "Freeze DTC (bits)"
		out["Val"] = 256 * msi[2] + msi[3]
	elif idx == 3:
		out['Descr'] = "Fuel System Status (bits)"
		out["Val"] = 256 * msi[2] + msi[3]
	elif idx == 4:
		out['Descr'] = "Engine Load"
		out["Val"] = msi[2] * (100 / 255)
	elif idx == 5:
		out['Descr'] = "Coolant Temp"
		out["Val"] = msi[2] - 40
	elif idx == 6:
		out['Descr'] = "Short Term Fuel Trim Bk 1"
		out["Val"] = msi[2] * (100/128) - 100
	elif idx == 7:
		out['Descr'] = "Long Term Fuel Trim Bk 1"
		out["Val"] = msi[2] * (100/128) - 100
	elif idx == 8:
		out['Descr'] = "Short Term Fuel Trim Bk 2"
		out["Val"] = msi[2] * (100/128) - 100
	elif idx == 9:
		out['Descr'] = "Long Term Fuel Trim Bk 2"
		out["Val"] = msi[2] * (100/128) - 100
	elif idx == 10:
		out['Descr'] = "Fuel Pressure kPa"
		out["Val"] = msi[2] * 3
	elif idx == 11:
		out['Descr'] = "Intake Manifold Absolute Pressure kPa"
		out["Val"] = msi[2]
	elif idx == 12: 
		out['Descr'] = "Engine RPM"
		out['Val'] = (256 * msi[2] + msi[3]) / 4
	elif idx == 13:
		out['Descr'] = 'Speed km/h'
		out['Val'] = msi[2]
	elif idx == 14:
		out['Descr'] = 'Timing Advance ° before TDC'
		out['Val'] = msi[2]/2 - 64
	elif idx == 15:
		out['Descr'] = 'Intake Air Temp.'
		out['Val'] = msi[2] - 40
	elif idx == 16:
		out['Descr'] = 'Mass airflow g/s'
		out['Val'] = (256 * msi[2] + msi[3]) / 100 
	elif idx == 17:
		out['Descr'] = 'Throttle pos'
		out['Val'] = msi[2] * 100 / 255
	return out

def hexstr2list(hexstr):
	hs = hexstr.split(' ')
	out = list()
	for h in hs:
		if len(h) > 1:
			out.append(int(h, 16))
	return out

def bv2int(bv):
	N = len(bv)
	out = 0
	for i in range(N):
		out = out + bv[i] * (2 ** (N - i - 1))
	return out
































