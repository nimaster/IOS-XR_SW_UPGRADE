#!/usr/bin/env python3

### IOS-XR install script to automate install add, activate and commit
###
### run script using the syntax:
### python3 auto-install.py <ip_address> <username> <password> <image_filename>
### for example:
### python3 auto-install.py 10.58.245.158 test Test123! NCS1001-iosxr-px-k9-7.8.1.tar
### it is assumed the image has already been copied to the harddisk: of the device

__author__ = "Niall Masterson"
__email__ = "nimaster@cisco.com"


from ncclient import manager
from ncclient.xml_ import to_ele
import time
import xmltodict
import sys

#import logging

#logging.basicConfig(
#       level=logging.DEBUG,
#   )


### FUNCTIONS TO CONVERT XML RESPONSE TO PYTHON DICTIONARIES ###

def get_op_state(rep):
    global op_state
    dict = xmltodict.parse(rep)
    op_state = dict['rpc-reply']['data']['install']['request']['state']

def get_op_error(rep):
    global op_error
    dict = xmltodict.parse(rep)
    op_error = dict['rpc-reply']['data']['install']['request']['error']

def get_op_id(rep):
    global op_id
    dict = xmltodict.parse(rep)
    op_id = dict['rpc-reply']['op-id']['#text']

### IP ADDRESS, USERNAME, PASSWORD AND SW IMAGE CAN BE PASSED AS ARGUMENTS BY THE USER

device_ip = sys.argv[1]
device_username = sys.argv[2]
device_password = sys.argv[3]
device_image = sys.argv[4]


### INSTALL ADD VIA NETCONF ###

nc = manager.connect_ssh(host=device_ip, username=device_username, password=device_password, device_params={"name": "iosxr"}, manager_params={"timeout": 3000})

addrpc = f"""
 <install-add xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-spirit-install-act">
  <packagepath>/misc/disk1/</packagepath>
  <packagename>{device_image}</packagename>
 </install-add>
"""

reply = nc.dispatch(to_ele(addrpc))

#print(reply.xml)

### PARSE NETCONF RPC REPLY FOR INSTALL OPERATION ID ###

#dict = xmltodict.parse(reply.xml)
#op_id = dict['rpc-reply']['op-id']['#text']

get_op_id(reply.xml)

print("adding",device_image,"to repository. Operation ID is:",op_id)

time.sleep(30)

### CHECK INSTALL LOG FOR STATUS OF OPERATION ID ###

statusrpc = """
<get>
 <filter type="subtree">
  <install xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-install-oper">
    <request>
      <state/>
      <error/>
    </request>
  </install>
 </filter>
</get>
"""

reply = nc.dispatch(to_ele(statusrpc))

#print(reply.xml)
get_op_state(reply.xml)

print("Operation ID",op_id,"status:",op_state)


while op_state == 'in-progress':
    time.sleep(30)
    reply = nc.dispatch(to_ele(statusrpc))
    get_op_state(reply.xml)
    print(op_state)

if op_state == "failure":
    print("install failed for operation",op_id,"see error log below")
    get_op_error(reply.xml)
    print(op_error)
    sys.exit()
elif op_state == "success":
    print("moving to install activate stage")
else:
    print("something went wrong")
    get_op_error(reply.xml)
    print(op_error)
    sys.exit()


### INSTALL ACTIVATE USING OPERATION ID ###

activaterpc = """
<install-activate xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-spirit-install-act"> 
  <ids>
    <id-no>%s</id-no>
  </ids>
</install-activate>
""" %(op_id)

reply = nc.dispatch(to_ele(activaterpc))
#print(reply.xml)
get_op_id(reply.xml)


time.sleep(30)

reply = nc.dispatch(to_ele(statusrpc))
#print(reply.xml)
get_op_state(reply.xml)

print("activating image",device_image,"Operation ID is:",op_id)
print("Operation ID",op_id,"status:",op_state)

time.sleep(30)

while op_state == 'in-progress':
    time.sleep(30)
    reply = nc.dispatch(to_ele(statusrpc))
    get_op_state(reply.xml)
    print(op_state)

if op_state == "failure":
    print("install failed for operation",op_id,"see error log below")
    get_op_error(reply.xml)
    print(op_error)
    sys.exit()
elif op_state == "success":
    print("system will now reboot which will take some time and then move to install commit stage")
else:
    print("something went wrong")
    get_op_error(reply.xml)
    print(op_error)
    sys.exit()


### INSTALL COMMIT AFTER RELOAD ###

time.sleep(180)

commitrpc = """
<install-commit xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-spirit-install-act">
</install-commit>
"""

r = 0

while r < 20:
    try:
        nc = manager.connect_ssh(host=device_ip, username=device_username, password=device_password, device_params={"name": "iosxr"}, manager_params={"timeout": 3000})
        reply = nc.dispatch(to_ele(commitrpc))
        #print(reply.xml)
        r = 20
        get_op_id(reply.xml)
        print("install commit started, operation ID:",op_id)
    except Exception:
        print("system still rebooting, will retry install commit in 2 minutes")
        time.sleep(120)
        r += 1
        if r == 20:
            print("system not responding, exiting install script")
