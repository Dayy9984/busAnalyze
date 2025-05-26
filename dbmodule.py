import os
from sqlalchemy import create_engine

class dbmodule:
    
    def __init__(self):
        self.HOST = "127.0.0.1"
        self.PORT = 3306
        self.USER = "root"
        self.PASSWORD = "600900"
      
    
    def get_db(self,db_name):
        DB_NAME = db_name
        db_connection = create_engine(f"mysql+pymysql://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{DB_NAME}")
        conn = db_connection.connect()
        return conn
    
    def get_db_con(self,db_name):
        DB_NAME = db_name
        db_connection = create_engine(f"mysql+pymysql://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{DB_NAME}")
        return db_connection