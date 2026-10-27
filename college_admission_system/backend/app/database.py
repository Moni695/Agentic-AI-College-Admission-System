from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from .config import get_settings

settings = get_settings()
db_url = settings.database_url

# Normalize PostgreSQL prefix for SQLAlchemy 1.4+ compatibility
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# Ensure PyMySQL driver is used for generic mysql:// URIs
if db_url.startswith("mysql://"):
    db_url = db_url.replace("mysql://", "mysql+pymysql://", 1)

engine_kwargs = {}
if "sqlite" in db_url:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_pre_ping"] = True

try:
    engine = create_engine(db_url, **engine_kwargs)
    # If using local MySQL, quickly verify if MySQL server is listening
    if "localhost" in db_url or "127.0.0.1" in db_url:
        with engine.connect() as conn:
            pass
except Exception as exc:
    # Gracefully fall back to SQLite so local developers without MySQL or Docker can run immediately
    if "localhost" in db_url or "127.0.0.1" in db_url:
        print("\n[NOTE] Local MySQL is not running. Using built-in SQLite database (college_admission.db) automatically.\n")
        db_url = "sqlite:///college_admission.db"
        engine = create_engine(db_url, connect_args={"check_same_thread": False})
    else:
        raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
