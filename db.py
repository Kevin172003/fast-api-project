from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

from urllib.parse import quote_plus

# for mysql

# SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:root@127.0.0.1:3306/TodoApplicationDatabase"


#for sqlite3
SQLALCHEMY_DATABASE_URL = "sqlite:///./todosapp.db"

# For postgresql
# password = "Kevin@2003"
# encoded_password = quote_plus(password)
# SQLALCHEMY_DATABASE_URL = f"postgresql://postgres:{encoded_password}@localhost/TodoApplicationDatabase"




# used to establish a connection with a database.
# It creates a database engine that allows interaction with the database.
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

 
# A session is used to interact with the database in an isolated transaction.
# It allows you to add, delete, and modify database records.

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


#  function that returns a base class for creating ORM models.
Base = declarative_base()



