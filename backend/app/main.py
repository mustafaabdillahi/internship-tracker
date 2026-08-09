from fastapi import FastAPI
from config import Config
import sqlalchemy

config = Config()
app = FastAPI()
engine = sqlalchemy.create_engine(config.database_url)

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