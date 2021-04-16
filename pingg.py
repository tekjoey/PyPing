#import neccesary packages
import subprocess
import datetime
import json
import time

#get list of ip addressses to ping and asign to variable
with open("ip.json", "r") as ip:
	ipaddress = json.loads(ip.read())

#set date variables so we dont have to do it again
date_now = datetime.datetime.now().date()
time_now = datetime.datetime.now().time()

#define some global variables
max_single_expired = 5 #max attempts to reach an unresponsive host
expired_dict = {} #place to store number of times a host has been unreachable
total_expired_dict = {}
unreachable_skips = {}
critical_expired = [] #place to store hosts that have surpased max_single_expired. these will not be tried to reach again.
for i in ipaddress: #setup the expired_dict with all the ip addresses being queried
	expired_dict[i] = 0
	total_expired_dict[i] = 0
	unreachable_skips[i] = 5 #number of loops an unreachable host will be skipped before they are tried again.

all_reachable = True #set to false when all hosts have surpassed max_single_expired (line 56)

#function to write to both log files
def write_files(json_input, txt_input):
	with open ("ping_log.json", "a") as plj:
		plj.write("\n")
		plj.write(json.dumps(json_input, indent=2))

	with open("ping_log.txt", "a") as plt:
		plt.write(txt_input)

#function to redefine system messages and write to log files
def write_system_files(script_event_type, script_status, script_message):
	json_script_status = {
	"Event Type": script_event_type, 
	"Status": script_status, 
	"Details": script_message, 
	"Date": str(date_now), 
	"Time": str(time_now)
	}
	txt_script_status = f"\n---{script_status} - {script_message}--- \n\n"
	write_files(json_script_status, txt_script_status)

#write restart message to log files
write_system_files("System Event", "Restart", "The program has been restarted")

#loop to ping all the hosts. will be stoped if all become unreachable more than max_single_expired times
while all_reachable:

	for address in ipaddress:

		if len(critical_expired) == len(ipaddress): #this means all addresses have failed
			print(f"{critical_expired}, - critical expired list")
			print("All critical expired")
			write_system_files("Ping Error", "//- All Ping Fail", "All addresses are unreachable. Check connections and restart program. -//")
			all_reachable = False
			break

		if address in critical_expired: #if this particular address has been deamed unreachable
			if unreachable_skips[address] == 1: #if the next loop is gonna be the time to try to reach it again.
				critical_expired.remove(address) #remove the address from the critical expired list
			print(f"{address} in critial expired. {unreachable_skips[address]} tries left")
			write_system_files("Ping Error", "Single Ping Fail", f"{address} has critically failed. Will try again in {unreachable_skips[address]} loops.")
			unreachable_skips[address] -= 1
			continue

		try:

			pingg = subprocess.run(["ping", "-c", "1", ipaddress[address]], capture_output = True, text = True, timeout = 2)
			details = pingg.stdout

			if pingg.returncode == 0:
				result = "Success!"
				ping_status = "Online"
			else:
				result = "Failure?"
				ping_status = "Unknown Error Code"

		except subprocess.TimeoutExpired:
			result = f"Failure #{expired_dict[address] + 1}!"
			ping_status = "Unreachable"
			details = "Unreachable"
			expired_dict[address] += 1
			total_expired_dict[address] += 1
			print(f"{address} is {ping_status.lower()}. Will try {max_single_expired - expired_dict[address]} more times")
			
		if expired_dict[address] == max_single_expired: #this means that the addresses has failed 10 or more times
			write_system_files("Ping Error", "Single Ping Fail", f"{address} has failed {max_single_expired} pings")
			print(f"{expired_dict}, - expired dictionary")
			print(f"{address} has failed {expired_dict[address]} times")
			critical_expired.append(address)
			expired_dict[address] = 0
			continue

		txt_ping_result = f"{result} As of {date_now}, at {time_now.isoformat('minutes')} {address} is {ping_status}.\n"

		json_ping_result = {
			"Event Type": "Ping", 
			"Name": address, 
			"IP address" : ipaddress[address], 
			"Status": ping_status, 
			"Date": str(date_now), 
			"Time": str(time_now.isoformat("seconds")),
			"Details": details,
			"Total / Temp Expired Pings Since Restart": str(total_expired_dict[address]) + "/" + str(expired_dict[address])
		}

		write_files(json_ping_result, txt_ping_result)

	time.sleep(100)


