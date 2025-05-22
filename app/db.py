import mysql.connector
import pandas as pd
import csv

db_connection = mysql.connector.connect(
  host="localhost",
  user="root",
  passwd="<your-database-password>", # Change only this 
  auth_plugin='mysql_native_password'
)
print(db_connection)
