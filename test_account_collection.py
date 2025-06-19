""" This module tests the AccountCollection class"""
import uuid
from dataclasses import dataclass
import pytest
from account_collection import AccountCollection, InvalidInitialBalanceError, AccountNotFoundError, SelfTransferError, IllegalTransferAmountError
from in_memory_account_store import InMemoryAccountStore, Account

@dataclass
class TestUser:
    id: str
    account: Account

@pytest.fixture
def empty_account_collection():    
    return AccountCollection(InMemoryAccountStore())

def test_listing_accounts_for_user_before_creating_any_yields_empty_list(empty_account_collection):
    user_id = str(uuid.uuid4())
    accounts = empty_account_collection.get_user_accounts(user_id)
    assert(accounts == [])

def test_can_create_account_with_positive_balance(empty_account_collection):
    user_id = str(uuid.uuid4())
    account = empty_account_collection.create_account(user_id, 5)
    assert(account.user_id == user_id)
    assert(account.balance == 5)

def test_can_create_account_with_zero_balance(empty_account_collection):
    user_id = str(uuid.uuid4())
    account = empty_account_collection.create_account(user_id, 0)
    assert(account.user_id == user_id)
    assert(account.balance == 0)

def test_cannot_create_account_with_negative_balance(empty_account_collection):
    user_id = str(uuid.uuid4())
    with pytest.raises(InvalidInitialBalanceError) as exc_info:   
        empty_account_collection.create_account(user_id, -1)
    assert exc_info.value.payload["balance"] == -1    

def test_cannot_create_account_with_decimal_balance(empty_account_collection):
    user_id = str(uuid.uuid4())
    with pytest.raises(InvalidInitialBalanceError) as exc_info:   
        empty_account_collection.create_account(user_id, 5.5)
    assert exc_info.value.payload["balance"] == 5.5

def test_cannot_create_account_with_not_a_number_balance(empty_account_collection):
    user_id = str(uuid.uuid4())
    with pytest.raises(InvalidInitialBalanceError) as exc_info:   
        empty_account_collection.create_account(user_id, "5")
    assert exc_info.value.payload["balance"] == "5"

@pytest.fixture
def account_collection_with_single_account():
    account_collection = AccountCollection(InMemoryAccountStore())
    user_id = str(uuid.uuid4())
    account = account_collection.create_account(user_id, 5)
    return (user_id, account.id, account_collection)

def test_can_get_existing_accounts(account_collection_with_single_account):
    user_id, account_id, collection = account_collection_with_single_account
    account = collection.get_user_account(user_id, account_id)
    assert(account.balance == 5)
    assert(account.user_id == user_id)
    
def test_can_get_all_existing_account(account_collection_with_single_account):
    user_id, account_id, collection = account_collection_with_single_account
    accounts = collection.get_user_accounts(user_id)
    assert(len(accounts) == 1)
    assert(accounts[0].balance == 5)
    assert(accounts[0].id == account_id)
    assert(accounts[0].user_id == user_id)

def test_user_cannot_get_non_existent_account(account_collection_with_single_account):
    user_id, _, collection = account_collection_with_single_account
    non_existing_account_id = str(uuid.uuid4())
    with pytest.raises(AccountNotFoundError) as exc_info:   
        collection.get_user_account(user_id, str(non_existing_account_id))
    assert exc_info.value.payload["account_id"] == non_existing_account_id

@pytest.fixture
def account_collection_with_accounts_for_two_users():
    account_collection = AccountCollection(InMemoryAccountStore())
    user1_id = str(uuid.uuid4())
    account1 = account_collection.create_account(user1_id, 5)
    user1 = TestUser(user1_id, account1)

    user2_id = str(uuid.uuid4())
    account2 = account_collection.create_account(user2_id, 5)
    user2 = TestUser(user2_id, account2)

    return (user1, user2, account_collection)


def test_users_cannot_fetch_each_others_accounts(account_collection_with_accounts_for_two_users):
    user1, user2, collection = account_collection_with_accounts_for_two_users

    # user 1 access account of user 2
    with pytest.raises(AccountNotFoundError) as exc_info:   
        collection.get_user_account(user1.id, user2.account.id)
    assert exc_info.value.payload["account_id"] == user2.account.id

    # user 2 access account of user 1
    with pytest.raises(AccountNotFoundError) as exc_info:   
        collection.get_user_account(user2.id, user1.account.id)
    assert exc_info.value.payload["account_id"] == user1.account.id


def test_users_cannot_list_each_others_accounts(account_collection_with_accounts_for_two_users):
    user1, user2, collection = account_collection_with_accounts_for_two_users
    
    # User 1 only has their own account in their list
    user1_accounts = collection.get_user_accounts(user1.id)
    assert(user1_accounts == [user1.account])

    # User 2 only has their own account in their list
    user2_accounts = collection.get_user_accounts(user2.id)
    assert(user2_accounts == [user2.account])


# TRANSFER TESTS
def test_users_can_perform_a_legal_transfer_to_another_users_account(account_collection_with_accounts_for_two_users):
    user1, user2, collection = account_collection_with_accounts_for_two_users
    
    collection.transfer(user1.id, user1.account.id, user2.account.id, 1)

    updated_user1_account = collection.get_user_account(user1.id, user1.account.id)
    assert(updated_user1_account.balance == 4)

    updated_user2_account = collection.get_user_account(user2.id, user2.account.id)
    assert(updated_user2_account.balance == 6)

def test_user_can_perform_a_legal_transfer_to_another_account_that_it_owns(account_collection_with_accounts_for_two_users):
    user1, _, collection = account_collection_with_accounts_for_two_users
    new_account =collection.create_account(user1.id, 5)
    
    collection.transfer(user1.id, user1.account.id, new_account.id, 1)
    assert True

def test_user_cannot_perform_a_transfer_from_a_non_existent_account(account_collection_with_accounts_for_two_users):
    user1, user2, collection = account_collection_with_accounts_for_two_users
    non_existent_id = str(uuid.uuid4())
    
    with pytest.raises(AccountNotFoundError) as exc_info:
        collection.transfer(user1.id, non_existent_id, user2.account.id, 1)
    assert exc_info.value.payload['account_id'] == non_existent_id


def test_user_cannot_perform_a_transfer_to_a_non_existent_account(account_collection_with_accounts_for_two_users):
    user1, _, collection = account_collection_with_accounts_for_two_users
    non_existent_id = str(uuid.uuid4())
    
    with pytest.raises(AccountNotFoundError) as exc_info:
        collection.transfer(user1.id, user1.account.id, non_existent_id, 1)
    assert exc_info.value.payload['account_id'] == non_existent_id    

def test_user_cannot_make_account_transfer_to_itself(account_collection_with_accounts_for_two_users):
    user1, _, collection = account_collection_with_accounts_for_two_users
    
    with pytest.raises(SelfTransferError) as exc_info:
        collection.transfer(user1.id, user1.account.id, user1.account.id, 1)
    assert exc_info.value.payload['account_id'] == user1.account.id

def test_user_cannot_transfer_zero_amount(account_collection_with_accounts_for_two_users):
    user1, user2, collection = account_collection_with_accounts_for_two_users
    
    with pytest.raises(IllegalTransferAmountError) as exc_info:
        collection.transfer(user1.id, user1.account.id, user2.account.id, 0)
    assert exc_info.value.payload['amount'] == 0
    assert exc_info.value.payload['balance'] == 5



def test_user_cannot_transfer_negative_amount(account_collection_with_accounts_for_two_users):
    user1, user2, collection = account_collection_with_accounts_for_two_users
    
    with pytest.raises(IllegalTransferAmountError) as exc_info:
        collection.transfer(user1.id, user1.account.id, user2.account.id, -1)
    assert exc_info.value.payload['amount'] == -1
    assert exc_info.value.payload['balance'] == 5
    
def test_user_cannot_transfer_amount_that_would_leave_account_with_negative_balance(account_collection_with_accounts_for_two_users):
    user1, user2, collection = account_collection_with_accounts_for_two_users
    
    with pytest.raises(IllegalTransferAmountError) as exc_info:
        collection.transfer(user1.id, user1.account.id, user2.account.id, 6)
    assert exc_info.value.payload['amount'] == 6
    assert exc_info.value.payload['balance'] == 5