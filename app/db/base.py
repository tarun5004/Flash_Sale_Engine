# app/db/base.py
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
"""base.py should never import models
✅ migration / create_tables script imports models"""