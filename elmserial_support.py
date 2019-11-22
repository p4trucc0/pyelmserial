# Andrea Patrucco, 17/11/2019
# Support functions to elmserial.
import re
import pandas as pd

PID_EXCEL = 'PIDs.xlsx'
PID = pd.read_excel(PID_EXCEL, index_col = 'Idx')

def obd_parser(msg, idx, sp = "\r", long_format = True):
	out = dict()
	#msgs = msg.split(sp)
	ms = msg.split(sp)[1]
	msi = hexstr2list(ms)
	if long_format:
		msi = msi[3:-1]
	out['Ack'] = msi[0] == 65
	out['IdR'] = msi[1]
	msb = msi[2:-1]
	out['Descr'], out['Val'] = parse_bytes(msb, idx)
	return out

def parse_bytes(msb, idx):
	if PID.loc[idx]['Bytes'] == 1:
		v = msb[0]
	elif PID.loc[idx]['Bytes'] == 2:
		v = 256 * msb[0] + msb[1]
	elif PID.loc[idx]['Bytes'] == 4:
		v = (256 ** 3) * msb[0] + (256 ** 2) * msb[1] + 256 * msb[2] + msb[3]
	value = v * PID.loc[idx]['Multiplier'] + PID.loc[idx]['Offset']
	description = PID.loc[idx]['Description']
	return description, value

def hexstr2list(hexstr):
	hs = hexstr.split(' ')
	out = list()
	for h in hs:
		if len(h) > 1:
			out.append(int(h, 16))
	return out

PARSER_STR = r"\d\d:\d\d:\d\d.\d\d\d\d\d\d\tPARSER\tMsg\sId:\s(\d+?)\s\((\D+?)\)\s-\sValue\s=\s(.+)"

def log_parser(txt_in):
	f = open(txt_in, 'r')
	tc = f.read()
	lines = tc.split('\n')
	out = pd.DataFrame()
	i = 0
	for line in lines:
		if "PARSER" in line:
			test = re.search(PARSER_STR, line)
			localtime_seconds = 3600*float(line[11:13]) + 60*float(line[14:16]) + float(line[17:21])
			if test:
				dct = {'Id': int(test.group(1)), \
					'LocalTime': localtime_seconds, \
					'Description': test.group(2), \
					'Value': float(test.group(3))}
				out = out.append(pd.DataFrame(dct, index = [i]))
				i = i + 1
	return out




