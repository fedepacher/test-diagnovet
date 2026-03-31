import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from peewee import OperationalError, fn

from api.app.model.user_model import Users as UserModel
from api.app.schema.token_schema import TokenData
from api.app.schema.user_schema import User as UserSchema
from api.app.utils.settings import Settings


SECRET_KEY = Settings.secret_key
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = int(Settings.token_expire)
DEFAULT_EXPIRATION_TIME = 15

if SECRET_KEY is None:
    raise ValueError("SECRET_KEY env var not set")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def verify_password(plain_password, password):
    """Validate password.

    Args:
        plain_password (str): Password stored in DB.
        password (str): Password.

    Returns:
        Bool: Password validation status.
    """
    logging.info("Verifying password")
    password_verified = pwd_context.verify(plain_password, password)
    return password_verified


def get_password_hash(password) -> str:
    """Generate hash.

    Args:
        password (str): Password.

    Returns:
        str: Password hashed.
    """
    logging.info("Getting hash")
    password_hash = pwd_context.hash(password)
    return password_hash


def get_user(username: str) -> UserModel:
    """Get user or email depends on if logging was with email or username.

    Args:
        username (str): Username or email.

    Returns:
        Any: User if exists.
    """
    logging.info(f"Getting user {username}")
    try:
        username_lower = username.lower()
        user = UserModel.filter(
            (fn.LOWER(UserModel.email) == username_lower) |
            (fn.LOWER(UserModel.username) == username_lower)
        ).first()
        return user
    except OperationalError as e:
        logging.error(f"Database error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database connection failed")


def authenticate_user(username: str, password: str) -> UserSchema:
    """Check if username and password exists.

    Args:
        username (str): Username.
        password (str): Password

    Returns:
        UserSchema: user
    """
    logging.info(f"Authenticating user {username}")
    user = get_user(username)
    if not user:
        logging.debug(f"User {username} does not exist")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    if not verify_password(password, user.password):
        logging.debug(f"Password for user {username} does not exist")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    logging.debug(f"User {username} Authenticated")
    user_ret = UserSchema(
        id=user.id,
        email=user.email,
        username=user.username,
    )
    return user_ret


def create_token(data: dict, expires_delta: Optional[timedelta] = None, secret_key: str = SECRET_KEY):
    """Create an access token.

    Args:
        data (dict): Data to store in token.
        expires_delta (Optional[timedelta], optional): Token expiration time. Defaults to None.
        secret_key (str): Secret key.

    Returns:
        str: Token.
    """
    logging.info("Creating access token")
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
        logging.debug(f"Token expiration time: {expire}")
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=DEFAULT_EXPIRATION_TIME)
        logging.debug(f"Token expiration time: {expire}")
    to_encode.update({"exp": expire})
    encode_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
    return encode_jwt


def decode_token(token: str) -> dict | None:
    """Decode a JWT token

    Args:
        token (str): JWT token

    Returns:
        str | None: extracted data from the token or None if token is invalid.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logging.error(e)
        return None


def get_token_data(user: UserSchema, token_expiration: timedelta, secret_key: str) -> str:
    """Create the token data.

    Args:
       user (UserSchema): User.
       token_expiration (str): Token.
       secret_key (str): Secret key.

    Returns:
        str: Token.
    """
    token = create_token(
        data={"sub": user.username,
              "user_id": user.id,
              "email": user.email
              },
        expires_delta=token_expiration,
        secret_key=secret_key
    )
    return token


def generate_access_token(user: UserSchema) -> str:
    """Generate access token.

    Args:
        user (UserSchema): User.

    Returns:
        str: Token.
    """
    logging.info(f"Generating token for user {user.username}")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = get_token_data(user, access_token_expires, SECRET_KEY)
    logging.debug(f"Token for user {user.username}: {token}")
    return token


def get_current_user(token: str = Depends(oauth2_scheme)) -> UserModel:
    """Get the user information based on the token information. 

    Args:
        token (str, optional): Token. Defaults to Depends(oauth2_scheme).

    Raises:
        credentials_exception: Credential fail.

    Returns:
        _type_: _description_
    """
    logging.info("Retrieving user")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token)
        if payload is None:
            logging.warning("Could not validate credentials")
            raise credentials_exception
        username: str = payload.get('sub')
        email: str = payload.get('email')
        if username is None:
            logging.warning("Username was not found in token payload")
            raise credentials_exception
        token_data = TokenData(username=email)

    except JWTError:
        logging.warning("Token cannot be decoded")
        raise credentials_exception

    user = get_user(username=token_data.username)
    if user is None:
        logging.warning("Username was not found in database")
        raise credentials_exception
    logging.debug(f"Username {user} exist")
    return user
