from pyzabbix import ZabbixAPI
from dotenv import load_dotenv
import os
from datetime import datetime
import pyodbc

now = formatDateTime = formatted_date = None
try:
    now = datetime.now()
    formatDateTime = now.strftime("%d/%m/%Y %H:%M")
    formatted_date = now.strftime("%Y-%m-%d")
except Exception as e:
    pass

try:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dotenv_path = os.path.join(base_dir, '.env')
    load_dotenv(dotenv_path)

    zabbix_server = os.environ['zabbix_server']
    zabbix_username = os.environ['zabbix_username']
    zabbix_password = os.environ['zabbix_password']

    db_server = os.environ['db_server']
    db_driver = os.environ['db_driver']
    db_sba = os.environ['db_sba']
except Exception as e:
    with open ('logfile.log', 'a') as file:
        file.write(f"""{formatDateTime} Problem z wczytaniem zmiennych środowiskowych - {str(e)}\n""")


#Connect to Zabbix API, data in .env file
try:
    zapi = ZabbixAPI(zabbix_server)
    zapi.login(zabbix_username, zabbix_password)
    print(f"Connected to Zabbix API Version {zapi.api_version()}")

    # Example: Get a list of all hosts
    hosts = zapi.host.get(output="extend")
    print(f"Number of hosts in Zabbix: {len(hosts)}")

    #Hosts\clients list
    salonList = [host['name'] for host in hosts if len(host['name']) < 8]
except Exception as e:
    with open ('logfile.log', 'a') as file:
        file.write(f"""{formatDateTime} Problem z wczytaniem danych z Zabix - {str(e)}\n""")

zabix_dict = {}
sba_db_dict = {}

try:
    for host_name in salonList:
        host = zapi.host.get(filter={"host": host_name})
        
        if host:
            host_id = host[0]["hostid"]
            #get host ip address
            interfaces = zapi.hostinterface.get(hostids=host_id, output=["ip"])
            ip_address = interfaces[0]["ip"]
            zabix_dict[host_name] = ip_address
            #print(host_name,ip_address)
except Exception as e:
    with open ('logfile.log', 'a') as file:
        file.write(f"""{formatDateTime} Problem z obróbka danych - {str(e)}\n""")


try:
    cnxn = pyodbc.connect(f"Driver={db_driver};Server={db_server};Database={db_sba};Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes;")
    cursor = cnxn.cursor()

    cursor.execute("SELECT ST_NAZWA, AKTUALNE_IP from dbo.STANOWISKA where len(ST_NAZWA) < 8 and CFG_DATA >= DATEADD(DAY, -30, GETDATE()) and AKTYWNE = 'T'")
    db_hosts = cursor.fetchall()

    for host in db_hosts:
        sba_db_dict[host[0]] = host[1]
    print(len(sba_db_dict))
    print(len(zabix_dict))
    # pierwsza jest w bazie (aktualna w teorii, druga zabix nieakutalna w teorii)
    different_values = {k: (sba_db_dict[k], zabix_dict[k]) for k in sba_db_dict if k in zabix_dict and sba_db_dict[k] != zabix_dict[k]}
except Exception as e:
    with open ('logfile.log', 'a') as file:
        file.write(f"""{formatDateTime} Problem z połączeniem z baza danych - {str(e)}\n""")

try:
    with open ("różnice_ip_salony_zabix_db.txt", 'w', encoding='utf-8') as file:
        if different_values:
            for db, zab in different_values.items():
                file.write(f"Poprawne SBA-IT (w teorii): {db}   Błędne ZABIX (w teorii): {zab}\n")
        else:
            file.write("Brak różnic w adresach IP.")
except Exception as e:
    with open ('logfile.log', 'a') as file:
        file.write(f"""{formatDateTime} Problem z tworzeniem pliku wyjściowego - {str(e)}\n""")
