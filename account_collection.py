""" This module implements the AccountCollection class """
from dataclasses import dataclass
import logging

from account_store import AccountStore, AccountStoreCreateError, AccountStoreGetError, AccountStoreUpdateError
from errors import APIError

@dataclass
class Account:
    id: str
    user_id: str
    balance: int

class AccountLookupError(APIError):
    def __init__(self, account_id: str):
        super().__init__("Unexpected error. Unable to look up account.", 500, account_id=account_id)

class AccountListLookupError(APIError):
    def __init__(self, user_id: str):
        super().__init__("Unexpected error. Unable to look up accounts.", 500, user_id=user_id)

class AccountCreateError(APIError):
    def __init__(self):
        super().__init__("Unexpected error. Unable to create account", 500)

class AccountUpdateError(APIError):
    def __init__(self, account_id: str):
        super().__init__("Unexpected error. Unable to create account", 500, account_id=account_id)

class InvalidInitialBalanceError(APIError):
    def __init__(self, balance):
        super().__init__("Submitted balance must be an integer above 0", 400, balance=balance)

class AccountNotFoundError(APIError):
    def __init__(self, account_id: str):
        super().__init__("Account not found.", 404, account_id=account_id)

class SelfTransferError(APIError):
    def __init__(self, account_id: str):
        super().__init__("Account not allowed to transfer to itself.", 400, account_id=account_id)

class IllegalTransferAmountError(APIError):
    def __init__(self, amount: int, balance: int):
        super().__init__("Transfer amount must be an integer above zero, and not leave the account negative.", 400, amount=amount, balance=balance)

class TransferError(APIError):
    def __init__(self, from_account_id: str, to_account_id: str):
        super().__init__("Unexpected error. Transfer failed", 500, from_account_id=from_account_id, to_account_id=to_account_id)

class AccountCollection():
    """
    Collection for interacting with accounts.
    """
    def __init__(self, account_store: AccountStore):
        self.__account_store = account_store
        self.root_logger = logging.getLogger("root")
        self.audit_logger = logging.getLogger("audit")

    def __internal_get_account(self, account_id, user_id = None) -> Account | None:
        try:
            return self.__account_store.get_account(account_id, user_id)
        except AccountStoreGetError as e:
            user_id_str = "" if not user_id else user_id
            self.root_logger.warning("Unexpected error occurred when trying to perform an account lookup. account_id='%s', user_id='%s", account_id, user_id_str)
            raise(AccountLookupError(account_id)) from e

    def create_account(self, user_id: str, initial_balance: int) -> str:
        """ Creates a new account for a user """
        if(not isinstance(initial_balance, int) or initial_balance < 0):
            raise InvalidInitialBalanceError(initial_balance)
        try:
            account = self.__account_store.create_account(user_id, initial_balance)
            self.audit_logger.info("Account created. account_id=%s, user_id=%s", account.id, user_id)
        except AccountStoreCreateError as e:
            self.root_logger.warning("Unexpected error occurred when trying to create account. e='%s'", e)
            raise AccountCreateError() from e
        return account

    def get_user_account(self, user_id: str, account_id: str) -> Account:
        """Gets a user's account by id """
        account = self.__internal_get_account(account_id, user_id)
        if (not account):
            self.root_logger.info("Account not found for user. user_id='%s'", user_id)
            raise AccountNotFoundError(account_id)
        return account
        
    def get_user_accounts(self, user_id: str) -> list[Account]:
        """Lists all of a user's accounts"""
        try:
            return self.__account_store.get_accounts(user_id)
        except AccountStoreGetError as e:
            self.root_logger.warning("Failed to list accounts for user. user_id='%s', e='%s'", user_id, e)
            raise AccountListLookupError(user_id) from e

    def transfer(self, user_id: str, from_account_id: str, to_account_id: str, amount: int) -> Account:
        """Transfers an amount betweeen two accounts"""
        # Validate that transfer is possible and allowed
        if(from_account_id == to_account_id):
            raise SelfTransferError(from_account_id)

        from_account = self.get_user_account(user_id, from_account_id)

        if(not isinstance(amount, int) or amount <= 0 or from_account.balance < amount):
            raise IllegalTransferAmountError(amount, from_account.balance)

        to_account = self.__internal_get_account(account_id=to_account_id)
        if(not to_account):
            raise AccountNotFoundError(to_account_id)

        # Start the transfer
        original_from_account = from_account
        from_account.balance = from_account.balance - amount
        to_account.balance = to_account.balance + amount

        try:
            self.__account_store.update_account(from_account)
        except AccountStoreUpdateError as e:
            self.root_logger.warning("Unexpected error occurred when attempting to update the from-account during a transfer. from_account_id='%s', to_account_id='%s',  e='%s'", from_account_id, to_account_id, e)
            raise TransferError(from_account_id, to_account_id) from e
        try:
            self.__account_store.update_account(to_account)
        except AccountUpdateError as e:
            self.root_logger.warning("Unexpected error when attempting to update to-account during transfer. Attempting a roll-back. from_account_id='%s', to_account_id='%s',  e='%s'", from_account_id, to_account_id, e)
            self.__rollback(original_from_account, to_account_id)

        self.audit_logger.info("Transfered an amount between two accounts. from_account_id=%s, to_account_id=%s, user_id=%s, amount=%s", from_account_id, to_account_id, user_id, amount)
        return from_account
    
    def __rollback(self, original_from_account: Account, to_account_id: str):
        try:
            self.__account_store.update_account(original_from_account)
            self.root_logger.info("Successfully rolled back the transfer. from_account_id='%s', to_account_id='%s'", original_from_account.id, to_account_id) 
            raise TransferError(to_account_id, original_from_account.id)
        except Exception as e:
            self.root_logger.error("Unsuccessfully rolled back the transfer. Store is in a corrupted state. from_account_id='%s', to_account_id='%s' e='%s'", original_from_account.id, to_account_id, e) 
            raise TransferError(to_account_id, original_from_account.id) from e