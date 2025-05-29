import mysql.connector
import pandas as pd
import csv
class dbHandler:
  def __init__ (self):
    db_connection = mysql.connector.connect(
                      host="localhost",
                      user="root",
                      passwd="<your-database-password>", # Change only this 
                      auth_plugin='mysql_native_password'
       
               )
    db_cursor = db_connection.cursor(buffered=True)
  
  # Create and connect to the database
  def createDatabase(self, databaseName):
    query1 = "CREATE DATABASE " + databaseName 
    query2 = "USE " + databaseName 
    self.db_cursor.execute(query1)
    self.db_cursor.execute(query2)
  
  #Delete Database
  def deleteDatabase(self, databaseName):
    query = "DROP DATABASE "+databaseName
    self.db_cursor.execute(query)
  
  #Delete Table
  def deleteTable(self, tableName):
    query = "DROP TABLE "+ tableName
    self.db_cursor.execute(query)