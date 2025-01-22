import pyodbc
from dotenv import load_dotenv
import json
import os
from datetime import datetime, timedelta

now = subtracted_formatted_date = formatDateTime = subtracted_date = formatted_date = None
try:
    now = datetime.now()
    formatted_date = now.strftime("%Y-%m-%d")
    formatted_date_obj = datetime.strptime(formatted_date, '%Y-%m-%d')
    formatDateTime = now.strftime("%d/%m/%Y %H:%M")
    subtracted_date = now - timedelta(days=14)
    subtracted_formatted_date = subtracted_date.strftime("%Y-%m-%d")
except Exception as e:
    pass

try:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dotenv_path = os.path.join(base_dir, '.env')
    load_dotenv(dotenv_path)
    
    db_server = os.environ['db_server']
    db_driver = os.environ['db_driver']
    sba_db_db = os.environ['sba_db_db']
    ignored_users_str = os.environ['ignored_users']
    ignored_users = ignored_users_str.split(',')
    ignored_users = [user.strip() for user in ignored_users]
    
except Exception as e:
    with open ('logfile.log', 'a') as file:
        file.write(f"""{formatDateTime} Problem z wczytaniem zmiennych środowiskowych - {str(e)}\n""")

try:
    #data from db
    cnxn = pyodbc.connect(f"Driver={db_driver};Server={db_server};Database={sba_db_db};Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes;")
    cursor = cnxn.cursor()

    cursor.execute("select ST_Nazwa, CFG_data from dbo.STANOWISKA where CFG_DATA < ? and AKTYWNE = 'T'  order by CFG_DATA desc", subtracted_formatted_date)
    hosts = cursor.fetchall()
except Exception as e:
    with open ('logfile.log', 'a') as file:
        file.write(f"""{formatDateTime} Problem z odpytaniem bazy danych - {str(e)}\n""")

with open('nieaktywni_użytkownicy.txt', 'w', encoding='utf-8') as file:
    # Write non-ignored users
    for host in hosts:
        if host[0] not in ignored_users:
            last_activity_date = datetime.strptime(host[1], '%Y-%m-%d')
            days_inactive = (formatted_date_obj - last_activity_date).days
            file.write(f"Użytkownik {host[0]} nieaktywny od {host[1]} liczba niekaktywnych dni: {days_inactive}\n")

    # If there are ignored users, write them as well
    if ignored_users:
        file.write("\nNieaktywni ignorowani\n")
        for user in ignored_users:
            file.write(f"{user}\n")