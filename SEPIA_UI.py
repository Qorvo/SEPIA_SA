import os
import sys
import re
import tempfile
import argparse
import subprocess
import math
import random, string
from quantiphy import Quantity


strerr = '''\
#######################################################################
## ERROR:  The first parameter should be either one of "od" or "ud". ##
#######################################################################
'''
strod = f'''\
Usage #1::  You have an over-dump response:
>> {sys.argv[0]} od --d0="0 0" --d1="33ns 20.366mV" --d2="0.375us 26.316mV" --d3="2.015us 4.2168mV" --Istep="500uA" --Sim
'''

strud = f'''\
Usage #2::  You have an under-dump response:
>> {sys.argv[0]} ud --d0="0 0" --p1="1 3.077us -38.81mV" --p2="1.5 10.43us 29.3mV" --Istep="-2A" --Sim

'''
struse = strod + "\n  or\n\n" + strud


if len(sys.argv) > 1:
	if sys.argv[1] == 'od':		mode = "od"
	elif  sys.argv[1] == 'ud':	mode = "ud"
	else:						mode = "error"
else:							mode = "error"

for arg in sys.argv:
	if arg == '-h' or arg == '--help':
		if mode == 'od':	print(strod);
		elif mode == 'ud':	print(strud);
		else:				print(struse);
		exit(1)

if mode == 'error':
	print(strerr)
	print(struse);
	exit(1)

def Step_Current_Check(string):
	val = re.match(r'^\s*([^,\s]+),*\s*,*\s*$',string).groups()
	if len(val) != 1:
		msg = 'one (1) value "current"" expected'
		raise argparse.ArgumentTypeError(msg)
	for v in val:
		i = Quantity(val[0]).real
	return (i)

def Time_Voltage_Check(string):
	val = re.match(r'^\s*([^,\s]+),*\s*,*\s*([^,\s]+),*\s*,*\s*$',string).groups()
	if len(val) != 2:
		msg = 'two (2) values "time" & "voltage" expected'
		raise argparse.ArgumentTypeError(msg)
	for v in val:
		t = Quantity(val[0]).real
		v = Quantity(val[1]).real
	return (t, v)

def Npeak_Time_Voltage_Check(string):
	val = re.match(r'^\s*([^,\s]+),*\s*,*\s*([^,\s]+),*\s*,*\s*([^,\s]+),*\s*,*\s*$',string).groups()
	if len(val) != 3:
		msg = 'three (3) values "nPeak", "time" & "voltage" expected'
		raise argparse.ArgumentTypeError(msg)
	for v in val:
		n = Quantity(val[0]).real
		t = Quantity(val[1]).real
		v = Quantity(val[2]).real
	if (n % 0.5) != 0:
		msg = '"nPeak" should be 0.5 × N; N = 2, 3, 4, ...'
		raise argparse.ArgumentTypeError(msg)
	return (n, t, v)

parser = argparse.ArgumentParser()
parser.add_argument("DumpMode", help='Specify "od" (overdump) or "ud" (underdump)', choices=['od', 'ud'])
parser.add_argument('--Istep', help='Load Step Current: "current (A)"', type=Step_Current_Check, required=True, metavar='"+999mA" or "-999mA"')
parser.add_argument('--d0', help=' Pre-Sample: "time (s)" and "voltage (V)"; "JUST BEFORE" Load-Step', type=Time_Voltage_Check, required=True, metavar='"<Step Start Time (s)> <Start Voltage (V)>"')

if mode == 'ud':
	parser.add_argument('--p1', help=' 1st Peak:   "nPeak", "time (s)" and "voltage (V)"; nPeak=1,1.5,2,2.5,...', type=Npeak_Time_Voltage_Check, required=True, metavar='"<Peak #> <Time (s)> <Voltage (V)>"')
	parser.add_argument('--p2', help=' 2nd Peak:   "nPeak", "time (s)" and "voltage (V)"; nPeak=1,1.5,2,2.5,...', type=Npeak_Time_Voltage_Check, required=True, metavar='"<Peak #> <Time (s)> <Voltage (V)>"')
	parser.add_argument('--d9', help='Post-Sample: "time (s)" and "voltage (V)"', type=Time_Voltage_Check, required=False, metavar='"<End Time (s)> <Final Voltage (V)>"')
elif mode == 'od':
	parser.add_argument('--d1', help=' Pre-Peak Sample:    "time (s)" and "voltage (V)"', type=Time_Voltage_Check, required=True, metavar='"<Time, around middle of "start" and "peak" (s)> <Voltage (V)>"')
	parser.add_argument('--d2', help=' Post-Peak Sample 1: "time (s)" and "voltage (V)"', type=Time_Voltage_Check, required=True, metavar='"<Time, around middle of tail, after "peak" (s)> <Voltage (V)>"')
	parser.add_argument('--d3', help=' Post-Peak Sample 2: "time (s)" and "voltage (V)"', type=Time_Voltage_Check, required=True, metavar='"<Time, almost tail but can see meaningful voltage" (s)> <Voltage (V)>"')

parser.add_argument('--Simulation', help='Execute QSPICE on SEPIA Extracted Model', action='store_true', required=False)
parser.add_argument('--Netlist', help='Output QSPICE Netlist of SEPIA Extracted Model', action='store_true', required=False)

try:
	args = parser.parse_args()
except SystemExit:
	print(f"\nError!  See HELP:  {sys.argv[0]} --help\n")
	if mode == 'od':	print(strod);
	elif mode == 'ud':	print(strud);
	else:				print(struse);
	exit(1)
except argparse.ArgumentError:
	print(f"\nError!  See HELP:  {sys.argv[0]} -h\n")
	if mode == 'od':	print(strod);
	elif mode == 'ud':	print(strud);
	else:				print(struse);
	exit(1)

if mode == 'ud':
	if args.d9:
		post_v = args.d9[1]
	else:
		post_v = args.d0[1]
	out = f'''\
ud
{args.d0[0]},{args.d0[1]},{post_v}
{args.p1[0]},{args.p1[1]},{args.p1[2]}
{args.p2[0]},{args.p2[1]},{args.p2[2]}
{args.Istep}
'''
elif mode == 'od':
	out = f'''\
od
{args.d0[0]},{args.d0[1]}
{args.d1[0]},{args.d1[1]}
{args.d2[0]},{args.d2[1]}
{args.d3[0]},{args.d3[1]}
{args.Istep}
'''

#######################################

score = "SEPIA.exe"

sc = subprocess.Popen(score, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
scout, scerr = sc.communicate(input=out.encode())

scerr1 = scerr.decode().replace("\\xa9", "\u00a9")


#print(scerr.decode())
#print(unicode(scerr, encoding='utf-8'))
#print(scerr.decode("utf-8"))
print(scerr1)

if args.Netlist == True:
	print(scout.decode())

if args.Simulation == True:

	qhome = os.path.expanduser("~") + r"\QSPICE\QSPICE80.exe"
	uhome = os.path.expanduser("~") + r"\QSPICE\QUX.exe"
	qsys = r'c:\Program Files\QSPICE\QSPICE80.exe'
	usys = r'c:\Program Files\QSPICE\QUX.exe'

	if os.path.isfile(qhome):
		scmd = qhome
		ucmd = uhome
	elif os.path.isfile(qsys):
		scmd = qsys
		ucmd = usys
	else:
		print('Please install QSPICE from qspice.com, before using "--Simulation" option')
		wb = subprocess.Popen('explorer.exe "https://qspice.com"', stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
		exit(1)

	tfile = "tmpSEPIA_" + "".join(random.choices(string.ascii_letters + string.digits, k=16)) + ".qraw"
	qs = subprocess.Popen('"' + scmd + '" -p " <= Netlist from STDIN" -r ' + tfile, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	qsout, qserr = qs.communicate(input=scout)

#print(qsout.decode())
#print(qserr.decode())

	qux = subprocess.Popen('"' + ucmd + '" ' + tfile, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

