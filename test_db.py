import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

print("--- Database Connection Diagnosis ---")
print(f"Host: {os.getenv('MYSQL_HOST')}")
print(f"User: {os.getenv('MYSQL_USER')}")
print(f"Port: {os.getenv('MYSQL_PORT')}")
# Don't print password for security, just length
pwd = os.getenv('MYSQL_PASSWORD')
print(f"Password length: {len(pwd) if pwd else 0}")

try:
    # 1. Try connecting without database first (to check login)
    print("\n1. Testing Login...")
    conn = mysql.connector.connect(
        host=os.getenv('MYSQL_HOST'),
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASSWORD'),
        port=int(os.getenv('MYSQL_PORT'))
    )
    if conn.is_connected():
        print("[SUCCESS] Login SUCCESS!")
        conn.close()
    
    # 2. Try connecting WITH database
    print("\n2. Testing Database Selection...")
    conn = mysql.connector.connect(
        host=os.getenv('MYSQL_HOST'),
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASSWORD'),
        database=os.getenv('MYSQL_DATABASE'),
        port=int(os.getenv('MYSQL_PORT'))
    )
    if conn.is_connected():
        print("[SUCCESS] Database Connection SUCCESS!")
        conn.close()

except Error as e:
    print(f"\n[ERROR]: {e}")
    if e.errno == 1045:
        print("   -> Wrong username or password")
    elif e.errno == 1049:
        print(f"   -> Database '{os.getenv('MYSQL_DATABASE')}' does not exist!")
    elif e.errno == 2003:
        print("   -> Can't connect to MySQL server (Is it running?)")
