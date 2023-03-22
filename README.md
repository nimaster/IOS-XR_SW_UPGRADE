# IOS-XR_SW_UPGRADE
Script automates IOS-XR software upgrades/downgraded using netconf

Automates install add, activate and commit
run script using the syntax:
python3 auto-install.py <ip_address> <username> <password> <image_filename>
for example:
python3 auto-install.py 10.58.245.158 test Test123! NCS1001-iosxr-px-k9-7.8.1.tar
it is assumed the image has already been copied to the harddisk: of the device
