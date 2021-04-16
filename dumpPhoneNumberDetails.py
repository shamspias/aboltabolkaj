import requests
import json
import csv

'''
Condition to set Carrier Name to SMS Getaway

'''


def find_carrier(phone, carrier):
    if 'AT&T' in carrier:
        return phone + '@txt.att.net'

    elif 'T-Mobile' in carrier:
        return phone + '@tmomail.net'

    elif 'Verizon' or 'Cellco Partnership' in carrier:
        return phone + '@vtext.com'

    elif 'Sprint' in carrier:
        return phone + '@pm.sprint.com'

    elif 'US cellular' in carrier:
        return phone + '@mms.uscc.net'

    elif 'USA mobility' in carrier:
        return phone + '@usamobility.net'

    elif 'Virgin mobile' in carrier:
        return phone + '@vmobl.com'

    elif 'Golden state cellular' in carrier:
        return phone + '@gscsms.com'

    elif 'Great call' in carrier:
        return phone + '@vtxt.com'

    elif 'MetroPCS' in carrier:
        return phone + '@mymetropcs.com'

    elif 'Boost mobile' in carrier:
        return phone + '@sms.myboostmobile.com'

    elif 'Cricket' in carrier:
        return phone + '@sms.cricketwireless.net'

    elif 'Other' in carrier:
        return phone + '@mmst5.tracfone.com'


'''
End Condition

'''

'''
Save in a Text File

'''


def save_to_text(midst, sms_gateway_address):
    with open("dict.txt", "a") as information:
        information.write(str(midst) + '\n')

    with open("new.txt", "a") as agd:
        agd.write(str(sms_gateway_address) + '\n')


'''
Save in a csv File

* Need to fixed Column

'''


def save_to_csv(midst):
    w = csv.writer(open("output.csv", "a"))
    for key, val in midst.items():
        w.writerow([key, val])


'''
Save in a json File

* Need to fix the format

'''


def save_to_json(midst):
    my_json = json.dumps(midst)
    information = open("dict.json", "a")
    information.write(my_json + ',\n')
    information.close()


'''
Send The API Request

'''


def send_request(api_key, phone, countryCode):
    request_url = 'http://apilayer.net/api/validate?access_key=' + api_key + '&number=' + phone + '&country_code=' + countryCode + '&format=1'
    info = requests.get(request_url)
    return info.json()


'''
Main Code Start

'''

apikey = 'Your API Key'  # Get From apilayer.net
# phoneNumber = ''
country = 'US'  # To Change Country Code
count = 0
with open('numbers.txt', 'r') as f:
    phoneNumbers = [line.strip() for line in f]

for number in phoneNumbers:

    myInfo = send_request(apikey, number, country)

    if not myInfo['valid']:
        if count == 0:
            country = ''
            myInfo = send_request(apikey, number, country)
            count += 1
        else:
            continue

    sms_gateway_address = find_carrier(number, myInfo['carrier'])

    myInfo['sms_gateway_address'] = sms_gateway_address

    save_to_text(myInfo, sms_gateway_address)