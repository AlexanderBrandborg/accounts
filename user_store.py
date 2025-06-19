"""This module defines the abstract UserStore class"""
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class StoredUser:
    """ Representation of user as stored"""
    id: str
    username: str
    hashed_pwd: str

class UserStoreError(Exception):
    """ Base exception for user stores """
    def __init__(self, original_exception: Exception, message: str):
        self.message = message
        self.original_exception = original_exception
        super().__init__(message)
    def __str__(self):
        return f"{self.message} (originalException: {self.original_exception})"


class UserStoreGetError(UserStoreError):
    """Exception raised when get operation failed """
    def __init__(self, original_exception, message = "Get operation failed unexpectedly, when attempting to look up user."):
        super().__init__(original_exception, message)

class UserStoreCreateError(UserStoreError):
    """Exception raised when create operation failed """
    def __init__(self, original_exception, message = "Fetch operation failed unexpectedly, when attempting to create user."):
        super().__init__(original_exception, message)

class UserStore(ABC):
    """ Abstract class, which all user stores will inherit from """

    @abstractmethod
    def create_user(self, username: str, hashed_pwd: bytes):
        """ Abstract method for creating user in store"""

    @abstractmethod
    def get_user(self, username: str):
        """ Abstract method for getting user from store"""