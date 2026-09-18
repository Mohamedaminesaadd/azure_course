import pyodbc

server = "databaseaminesaad.database.windows.net"
database = "free-sql-db-6706668"
username = "sql-lab-amine-2026"
password = "4495678925@A"

connection_string = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    f"SERVER={server},1433;"
    f"DATABASE={database};"
    f"UID={username};"
    f"PWD={password};"
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
    "Connection Timeout=30;"
)

try:
    connection = pyodbc.connect(connection_string)

    print("Connected to Azure SQL successfully!")

    cursor = connection.cursor()

    cursor.execute("SELECT @@VERSION")

    row = cursor.fetchone()

    print(row[0])

    cursor.close()
    connection.close()

except pyodbc.Error as e:
    print("Connection failed:")
    print(e)