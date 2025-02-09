from database import engine, Base

# Create tables in the MySQL database
Base.metadata.create_all(bind=engine)
