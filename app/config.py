import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev_key_for_development')
    DEBUG = os.getenv('FLASK_ENV') == 'development'
       
  # Configuration PostgreSQL
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'alla')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'passer123')
    POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', 5432))
    DBNAME = os.getenv('DBNAME', 'gestion_prompt')

    DATABASE_URL = f"dbname={DBNAME} user={POSTGRES_USER} password={POSTGRES_PASSWORD} host={POSTGRES_HOST}"

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev_secret")