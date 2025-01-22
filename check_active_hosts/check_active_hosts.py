import pyodbc
from dotenv import load_dotenv
import json
import os
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email import encoders

try:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dotenv_path = os.path.join(base_dir, '.env')
    
    load_dotenv(dotenv_path)
    
    sba_db_db = os.environ['sba_db_db']
    db_server = os.environ['db_server']
    ignored_hosts = os.environ['ignored_hosts']
    db_driver = os.environ['db_driver']
    
except Exception as e:
    with open ('logfile.log', 'a') as file:
        file.write(f"""Problem z wczytywaniem zmiennych środowiskowych - {str(e)}\n""")

now = subtracted_formatted_date = formatDateTime = subtracted_date = formatted_date = None
try:
    now = datetime.now()
    formatted_date = now.strftime("%Y-%m-%d")
    formatDateTime = now.strftime("%d/%m/%Y %H:%M")
    subtracted_date = now - timedelta(days=7)
    subtracted_formatted_date = subtracted_date.strftime("%Y-%m-%d")
except Exception as e:
    with open ('logfile.log', 'a') as file:
        file.write(f"""Problem z wczytyaniem daty - {str(e)}\n""")

try:
    ignored_hosts = json.loads(ignored_hosts)
except Exception as e:
    with open ('logfile.log', 'a') as file:
        file.write(f"""Aktwyne salony check problem z ładowaniem ignorowanych salonów - {str(e)}\n""")

try:
    cnxn = pyodbc.connect(f"Driver={{ODBC Driver 17 for SQL Server}};Server={db_server};Database={sba_db_db};Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes;")
    cursor = cnxn.cursor()

    cursor.execute("SELECT ST_NAZWA, AKTYWNE, CFG_DATA from dbo.STANOWISKA WHERE len(ST_NAZWA) = 4 ORDER BY 3 DESC ")
    hosts = cursor.fetchall()
    
except Exception as e:
    with open ('logfile.log', 'a') as file:
        file.write(f"""Problem z wczytaniem danych z bazy danych - {str(e)}\n""")
    
try:  
    activeList = []
    inactiveList = []
    inactiveWithT = [] #salony nieaktywne z flaga T (aktywne) w db
    activeWithN = [] #salony aktywne z flaga N (niekatywne) w db
    for host in hosts:
        # Ignore ignored hosts from .env 
        if host[0] in ignored_hosts:
            continue 
        if host[2] >= subtracted_formatted_date:
            activeList.append(host[0])
            if host[1] == 'N':
                activeWithN.append(host[0])
        else:
            inactiveList.append(host[0])
            if host[1] == 'T':
                inactiveWithT.append(host[0])

    activeList.sort()
    inactiveList.sort()
    inactiveWithT.sort()
    activeWithN.sort()
except Exception as e:
    with open ('logfile.log', 'a') as file:
        file.write(f"""Problem z filtrowaniem hostów - {str(e)}\n""")

try:
    with open ("aktywne_salony.txt", 'w') as file:
        activelist_to_file = '\n'.join(activeList)
        file.write(activelist_to_file)
        
except Exception as e:
    with open ('logfile.log', 'a') as file:
        file.write(f"""Problem z tworzeniem pliku wyjściowego z aktywnymi salonami - {str(e)}\n""")


try:
    with open ("różnice_sbait.txt", 'w') as file:
        content = ''
        if activeWithN:
            content += f'Salony akytwne, które są w archiwum IT mann:\n'
            for host in activeWithN:
                content += f'{host}\n'
                
        if inactiveWithT:
            content+=f'Salony nieaktywne, które są aktywne w IT mann:\n'
            for host in inactiveWithT:
                content += f'{host}\n'
        if content:
            file.write(content)
        else:
            file.write("Brak różnic SbaIt.")
        
except Exception as e:
    with open ('logfile.log', 'a') as file:
        file.write(f"""Problem z tworzeniem pliku wyjściowego z róznicami sbait - {str(e)}\n""")







