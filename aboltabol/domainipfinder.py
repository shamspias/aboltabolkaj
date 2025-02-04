# This scripts find the ip adress of multiple domain names

import sys,socket

def getIP(site):
	
		site = i.strip()
		try:
			if 'http://' not in site:
				IP1 = socket.gethostbyname(site)
				print (site+" "+"IP: "+IP1)
				open('ips.txt', 'a').write(IP1+'\n')
			elif 'http://' in site:
				url = site.replace('http://', '').replace('https://', '').replace('/', '')
				IP2 = socket.gethostbyname(url)
				print (site+" "+"IP: "+IP2)
				open('ips.txt', 'a').write(IP2+'\n')
	
		except:
			pass

print("First create a .txt file with Domain names")
print("Domain no need to use http or https")
print("Then give the file name in domain list name section")

nam=input('Domain List name :')
with open(nam) as f:
    for i in f:
        getIP(i)

		
