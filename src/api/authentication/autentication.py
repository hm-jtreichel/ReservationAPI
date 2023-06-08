from passlib.context import CryptContext

from ...db.manager import SessionFacade
from sqlalchemy import select

from datetime import timedelta, datetime

from jose import jwt

from ..owners.ownerModels import OwnerModel

SECRET_KEY = "26f3bad8b23608b165b1f57694bd3a775bf41107d8d2f8be5637c6da3bc68dc1"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

session = SessionFacade()


def verify_password(plain_password, hashed_password) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def authenticate_owner(email: str, password: str):
    qry = select(OwnerModel).where(OwnerModel.email == email)
    owner = session.scalars(qry).first()

    if not owner:
        return False
    if not verify_password(password, owner.hashed_password):
        return False

    return owner
