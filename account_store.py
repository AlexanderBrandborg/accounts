""" This module defines the abstract AccountStore class"""
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class Account:
    """ Representation of account as stored """
    id: str
    user_id: str
    balance: int

class AccountStoreError(Exception):
    """ Base exception for account stores """
    def __init__(self, original_exception: Exception, message: str):
        self.message = message
        self.original_exception = original_exception
        super().__init__(message)
    def __str__(self):
        return f"{self.message} (originalException: {self.original_exception})"


class AccountStoreGetError(AccountStoreError):
    """Exception raised when get operation failed """
    def __init__(self, original_exception, message = "Get operation failed unexpectedly, when attempting to look up account."):
        super().__init__(original_exception, message)

class AccountStoreCreateError(AccountStoreError):
    """Exception raised when create operation failed """
    def __init__(self, original_exception, message = "Operation failed unexpectedly, when attempting to create account."):
        super().__init__(original_exception, message)

class AccountStoreUpdateError(AccountStoreError):
    """Exception raised when create operation failed """
    def __init__(self, original_exception, message = "Operation failed unexpectedly, when attempting to update account."):
        super().__init__(original_exception, message)

class AccountStore(ABC):
    """ Abstract class, which all account stores will inherit from """

    @abstractmethod
    def create_account(self, user_id: str, initial_balance: int):
        """ Abstract method for creating account in store"""

    @abstractmethod
    def update_account(self, account: Account):
        """ Abstract method for updating an account in store"""

    @abstractmethod
    def get_account(self, account_id: str, user_id: str = None):
        """ Abstract method for getting account from store"""

    @abstractmethod
    def get_accounts(self, user_id: str):
        """ Abstract method for getting all accounts belonging to a user"""
