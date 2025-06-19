"""This module implements the UserCollection class"""
from dataclasses import dataclass
import secrets
import base64
import logging
import bcrypt
from user_store import UserStore, UserStoreGetError, UserStoreCreateError, StoredUser
from errors import APIError

@dataclass
class User:
    """ User class that is safe to pass up to API level"""
    id: str
    username: str

class InvalidUsernameError(APIError):
    def __init__(self, username: str):
        super().__init__("Invalid username submitted. Must be an alphanumeric string under 20 char.", 400, username=username)

class UserAlreadyExistsError(APIError):
    def __init__(self, username: str):
        super().__init__("User with same username already exists.", 400, username=username)

class UserNotFoundError(APIError):
    def __init__(self, username: str):
        super().__init__("User not found.", 404, username=username)

class AuthenticationError(APIError):
    def __init__(self, username: str):
        super().__init__("Unauthenticated.", 401, username=username)

class UserLookupError(APIError):
    def __init__(self, username: str):
        super().__init__("Unexpected error. Unable to look up user.", 500, username=username)

class UserCreateError(APIError):
    def __init__(self, username: str):
        super().__init__("Unexpected error. Unable to create user", 500, username=username)


class UserCollection():
    """ Collection containing all the logic for working with users and access to the user store """
    def __init__(self, user_store: UserStore):
        self.__user_store = user_store
        self.root_logger = logging.getLogger("root")
        self.audit_logger = logging.getLogger("audit")

    def __obscure_user(self, stored_user: StoredUser)  -> User:
        return User(stored_user.id, stored_user.username)

    def __is_valid_username(self, username: str) -> bool:
        return username.isalnum() and len(username) <= 20
    
    def __internal_get_user(self, username: str) -> StoredUser | None:
        if(not self.__is_valid_username(username)): 
            raise InvalidUsernameError(username)
        
        try: 
            user = self.__user_store.get_user(username)
        except UserStoreGetError as e:
            self.root_logger.warning("Fetching user from store failed. username='%s' e='%s'", username, e)
            raise UserLookupError(username) from e
        
        return user

    def create_user(self, username: str) -> tuple[User, str]:
        """ Create a new user with username and generate a password for them """
        if(not self.__is_valid_username(username)):
            raise InvalidUsernameError(username)
        
        existing_user = self.__internal_get_user(username)
        if existing_user:
            raise UserAlreadyExistsError(username)

        # Using bcrypt to generate a salted hash of the password.
        # Both the password and hash are transported and stored as base64 strings, just to make sure they stay intact.
        # bcrypt is a bit outdated now according to https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html. But using it here as an example of password hashing.
        pwd_bytes = secrets.token_bytes(16) # Generating password for the user to make sure that it is strong. :^ )
        pwd_base64 = base64.urlsafe_b64encode(pwd_bytes).decode("ascii")

        salt = bcrypt.gensalt()
        hashed_pwd = bcrypt.hashpw(pwd_bytes, salt)

        try:
            new_user = self.__user_store.create_user(username,  base64.urlsafe_b64encode(hashed_pwd).decode('ascii'))
            self.audit_logger.info("New User created. username=%s, user_id=%s", new_user.username, new_user.id)
        except UserStoreCreateError as e:
            self.root_logger.warning("Creating user in store failed. username='%s' e='%s'", username, e)
            raise UserCreateError(username) from e
        
        return (self.__obscure_user(new_user), pwd_base64)
    
    def get_user(self, username: str) -> User:
        """ Gets user by username """
        user = self.__internal_get_user(username)
        if not user:
            self.root_logger.info("User with given name not found. username=%s", username)
            raise UserNotFoundError(username)

        return self.__obscure_user(user)
    
    def authenticate(self, username: str, pwd: str) -> User:
        """ Check if user can authenticate with password. Throws an error if user cannot be authenticated """
        user = self.__internal_get_user(username)
        if not user:
            self.root_logger.info("User with given name not found. username=%s", username)
            raise UserNotFoundError(username)
    
        if not bcrypt.checkpw(base64.urlsafe_b64decode(pwd.encode('ascii')),  base64.urlsafe_b64decode(user.hashed_pwd)):
            self.root_logger.info("User failed to authenticate. username=%s", username)
            raise AuthenticationError(username)
        
        return self.__obscure_user(user)