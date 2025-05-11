import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev_key_for_development')
    DEBUG = os.getenv('FLASK_ENV') == 'development'
       
  # Configuration PostgreSQL
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'alla')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'passer123')
    DB_PORT = int(os.getenv('DB_PORT', 5432))
    DB_NAME = os.getenv('DB_NAME', 'gestion_prompt')

    DATABASE_URL = f"dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD} host={DB_HOST}"

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev_secret")