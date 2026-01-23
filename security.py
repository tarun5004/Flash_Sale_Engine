from passlib.context import CryptContext
from datetime import datetime, timedelta   #current time nikalne ke liye , token expire calculate karne ke liye # time add karne ke liye Ex- datetime.utcnow() + timedelta(minutes=30)
from app.core.config import settings      #load secret key from config and algorithm hs256 , access token expire minutes
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
    
def create_access_token(data: dict) -> str: #ye payload hota hai , isme hum user info rakhte hai EX- data = {"sub": user.id} Sub = sunject(JWT standard keyword)
    """Create JWT token with expiration time"""
    
    # Copy data to avoid modifying the original and safe handling
    to_encode = data.copy() # why copy ? to avoid modifying the original data dictionary ,clean handling and practice
    # Calculate expiration time
    expire = datetime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    ) #utcnow() = UTC time use hota hai (timezone safe) JWT STANTARD
    
    to_encode.update({"exp": expire}) # "exp" JWT standart reserved key , token kab expire hoga(payload mai expiry add karte hai)
    # token encode karte hai
    encoded_jwt = jwt.encode(
        to_encode,              # encode dict - string token , secret key se sign hota hai
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

#========================================
# Decode JWT token and verify
#========================================

def verify_access_token(token: str) -> dict:
    """Iska kaam
    token asli hai, expire to nahi?, data nikal ke do"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        raise ValueError("Could not validate credentials")