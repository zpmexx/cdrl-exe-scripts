from pyzabbix import ZabbixAPI
from dotenv import load_dotenv
import json
import os
import csv
from datetime import datetime
from collections import Counter
import pyodbc


base_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(base_dir, '.env')

load_dotenv(dotenv_path)


# Replace these with your actual Zabbix server details
zabbix_server = os.environ['zabbix_server']
zabbix_username = os.environ['zabbix_username']
zabbix_password = os.environ['zabbix_password']

db_server = os.environ['db_server']
db_driver = os.environ['db_driver']
db_sba = os.environ['db_sba']



now = formatDateTime = formatted_date = None
try:
    now = datetime.now()
    formatDateTime = now.strftime("%d/%m/%Y %H:%M")
    formatted_date = now.strftime("%Y-%m-%d")
except Exception as e:
    pass

#Connect to Zabbix API, data in .env file
try:
    zapi = ZabbixAPI(zabbix_server)
    zapi.login(zabbix_username, zabbix_password)
    print(f"Connected to Zabbix API Version {zapi.api_version()}")

    # Example: Get a list of all hosts
    hosts = zapi.host.get(output="extend")
    print(f"Number of hosts in Zabbix: {len(hosts)}")
except Exception as e:
    with open ('logfile.log', 'a') as file:
        file.write(f"""{formatDateTime} Problem z połączeniem z zabixem - {str(e)}\n""")

# Example: Check if a specific host has any items

#Hosts\clients list
salonList = []
try:
    conn = pyodbc.connect(f"Driver={db_driver};Server={db_server};Database={db_sba};Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes;")
    cursor = conn.cursor()

    query = """
        SELECT ST_NAZWA
        FROM dbo.STANOWISKA
        WHERE AKTUALNE_IP LIKE '172.38%'
        AND AKTYWNE LIKE 'T'
        AND LEN(ST_NAZWA) < 5
        OR ST_NAZWA = 'A010-1'
    """

    cursor.execute(query)

    for row in cursor.fetchall():
        salonList.append(row.ST_NAZWA)

    # Close the cursor and connection
    cursor.close()
    conn.close()
except Exception as e:
    with open ('logfile.log', 'a') as file:
        file.write(f"""{formatDateTime} Problem z połaczeniem z baza danych - {str(e)}\n""")


#hosts dict to keep connection status value 0 - not connected, 1 - connected, 11 - no host found, 12 - no hisotrical data, 13 - no item zabbix[host,agent,available]
hostsDict = {}

try:
    for host_name in salonList:
        host = zapi.host.get(filter={"host": host_name})

        if host:
            host_id = host[0]["hostid"]
            items = zapi.item.get(hostids=host_id, output="extend")
            # interfaces = zapi.hostinterface.get(hostids=host_id, output=["ip"])
            # ip_address = interfaces[0]["ip"]
            #print(f"Number of items for host '{host_name}': {len(items)}")
        else:
            #11
            hostsDict[host_name] = 11
            #print(f"No host found with name '{host_name}'")

        # Example: Get latest data for a specific item
        if items:
            item_key = "zabbix[host,agent,available]"  # Replace with your specific item key
            item = zapi.item.get(hostids=host_id, filter={"key_": item_key}, output="extend")
            
            if item:
                item_id = item[0]["itemid"]
                history = zapi.history.get(itemids=item_id, limit=10, output="extend", sortfield="clock", sortorder="DESC")
                #0/1
                if history:
                    #print(f"{host_name} - {history[0]['value']}")
                    hostsDict[host_name] = history[0]['value']
                else:
                    #12
                    print(f"No historical data found for item '{host_name}'")
                    hostsDict[host_name] = 12
                    
            else:
                #13
                print(f"No item found with key '{item_key}' for host '{host_name}'")
                hostsDict[host_name] = 13

    # Logout from the API
    zapi.user.logout()
except Exception as e:
    with open ('logfile.log', 'a') as file:
        file.write(f"""{formatDateTime} Problem z odczytwaniem danych z zabixa - {str(e)}\n""")


# #count values in dict
count_dict = Counter(hostsDict.values())

#connected/disconected summary
summary_count_txt = f"{formatDateTime}\nLiczba połaczonych klientów: {count_dict['1']}, liczba rozłączonych: {count_dict['0']}\n"

connected_hosts = []
disconnected_hosts = []
error_dict = {}

#hosts status to lists/dict
for k,v in hostsDict.items():
    if v == '0':
        disconnected_hosts.append(k)
    elif v == '1':
        connected_hosts.append(k)
    else:
        error_dict[k] = v


try:
    content = f"{summary_count_txt}\n"
    content += '\n'.join(disconnected_hosts)
    with open('sprawdzenie_vpn.txt', 'w') as file:
        file.write(content)
        
except Exception as e:
    with open ('logfile.log', 'a') as file:
        file.write(f"""{formatDateTime} Problem z zapisem wyniku do pliku - {str(e)}\n""")











