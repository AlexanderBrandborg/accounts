""" This module implements AccountStore with a simple list """
import uuid
from account_store import AccountStore, Account, AccountStoreGetError, AccountStoreCreateError, AccountStoreUpdateError

class InMemoryAccountStore(AccountStore):
    """ An in memory store used during debugging and testing. It's just based around a list really, don't get too excited."""
    __accounts: list[Account]

    def __init__(self):
        super().__init__()
        self.__accounts: list[Account] = []

    def create_account(self, user_id: str, initial_balance: int):
        account_id = str(uuid.uuid4())
        account = Account(user_id = user_id, id=account_id, balance=initial_balance)

        try:
            self.__accounts.append(account)
        except Exception as e:
            raise AccountStoreCreateError(e) from e
        return account


    def update_account(self, account: Account):
        try:
            index = next(i for i, x in enumerate(self.__accounts) if x.id == account.id)
            self.__accounts[index] = account
        except Exception as e:
            raise AccountStoreUpdateError(e) from e

    def get_account(self, account_id: str, user_id: str = None):
        user_check = lambda id: id == user_id if user_id else lambda _: True
        account_check = lambda id: id == account_id if account_id else lambda _: True    
        try:
            return next(x for x in self.__accounts if user_check(x.user_id) and account_check(x.id))
        except StopIteration:
            return None
        except Exception as e:
            raise AccountStoreGetError(e) from e
        
    def get_accounts(self, user_id: str):
        try:
            return [x for x in self.__accounts if x.user_id == user_id]
        except Exception as e:
            raise AccountStoreGetError(e) from e