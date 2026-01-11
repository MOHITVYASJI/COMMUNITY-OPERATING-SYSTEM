"""Database connection managers for PostgreSQL, MongoDB, and Redis"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from motor.motor_asyncio import AsyncIOMotorClient
import redis
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# PostgreSQL Setup
POSTGRES_URL = os.getenv('POSTGRES_URL')
engine = create_engine(POSTGRES_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# MongoDB Setup
MONGO_URL = os.getenv('MONGO_URL')
DB_NAME = os.getenv('DB_NAME')
mongo_client = AsyncIOMotorClient(MONGO_URL)
mongo_db = mongo_client[DB_NAME]

# Redis Setup
REDIS_URL = os.getenv('REDIS_URL')
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

def get_db():
    """Dependency for PostgreSQL session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_mongo_db():
    """Get MongoDB database instance"""
    return mongo_db

def get_redis_client():
    """Get Redis client instance"""
    return redis_client
