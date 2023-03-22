import sys
from netmiko import ConnectHandler

device_username = sys.argv[1]
device_password = sys.argv[2]


with open('device_ip.txt') as devices:
    for ipaddr in devices:
        device = {
            'device_type': 'cisco_xr',
            'ip' : ipaddr,
            'username': device_username,
            'password': device_password,
            'port': '22',
        }
        net_connect = ConnectHandler(**device)

        print('configuring netconf on device:',ipaddr)

        output = net_connect.send_config_set(['ssh server v2','ssh server netconf vrf default','netconf-yang agent','ssh','commit'])
        print(output)

        print('\n###COMPLETE###\n')
