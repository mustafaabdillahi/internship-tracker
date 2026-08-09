from fastapi import FastAPI
from dotenv import load_dotenv
import os
import sqlalchemy

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

app = FastAPI()
engine = sqlalchemy.create_engine(DATABASE_URL)

# For now, just pings the database
@app.get("/health")
def get_health():
    with engine.connect() as conn:
        query = sqlalchemy.text("SELECT 1;")
        conn.execute(query)
        conn.commit()
    return {"Database": "pinged"}


@app.get("/")
def root():
    return {"Hello": "World"}