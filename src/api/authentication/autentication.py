from passlib.context import CryptContext

SECRET_KEY = "26f3bad8b23608b165b1f57694bd3a775bf41107d8d2f8be5637c6da3bc68dc1"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)
