from passlib.context import CryptContext
from datetime import datetime, timedelta   #current time nikalne ke liye , token expire calculate karne ke liye # time add karne ke liye Ex- datetime.utcnow() + timedelta(minutes=30)

from jose import jwt, JWTError   # time add karne ke liye Ex- datetime.utcnow() + timedelta(minutes=30)

#bcrypt context for hashing passwords
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

def hash_password(password: str) -> str:
    # Plain password to hashed password
    return pwd_context.hash(password)

def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    """Login ke time check:
    user ka password == db wala hash? 
    """
    
    return pwd_context.verify(
        plain_password,
        hashed_password
    )
    
    
    
"""
JWT LOGIC Utility File


"""