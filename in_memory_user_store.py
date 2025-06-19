""" This module implements UserStore with a simple list """
import uuid
from user_store import UserStore, StoredUser, UserStoreGetError, UserStoreCreateError

class InMemoryUserStore(UserStore):
    """ An in memory store used during debugging and testing. It's just based around a list really, don't get too excited."""
    __users: list[StoredUser]

    def __init__(self):
        super().__init__()
        self.__users = []
    
    def create_user(self, username: str, hashed_pwd: bytes):
        try:
            user_id = str(uuid.uuid4())
            user = StoredUser(user_id, username, hashed_pwd)
            self.__users.append(user)
            return user
        except Exception as e:
            raise UserStoreCreateError(e) from e

    def get_user(self, username: str):
        try:
            return next(x for x in self.__users if x.username == username)
        except StopIteration:
            return None
        except Exception as e:
            raise UserStoreGetError(e) from e
            