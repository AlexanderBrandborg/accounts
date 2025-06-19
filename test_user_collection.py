""" This module tests the UserCollection class"""
import base64
import pytest
from user_collection import UserCollection, InvalidUsernameError, UserNotFoundError, AuthenticationError
from in_memory_user_store import InMemoryUserStore

@pytest.fixture
def empty_user_collection():    
    return UserCollection(InMemoryUserStore())

def test_can_create_user_with_legal_username(empty_user_collection):
    user, _ = empty_user_collection.create_user("Stenaldermand")
    assert(user.username == "Stenaldermand")

def test_cannot_create_user_with_an_empty_name(empty_user_collection):
    with pytest.raises(InvalidUsernameError) as exc_info:   
        _, _ = empty_user_collection.create_user("")
    assert exc_info.value.payload["username"] == ""

def test_cannot_create_user_with_a_non_alphanumeric_name(empty_user_collection):
    with pytest.raises(InvalidUsernameError) as exc_info:   
        _, _ = empty_user_collection.create_user("Sten Aldermand")
    assert exc_info.value.payload["username"] == "Sten Aldermand"

def test_cannot_create_user_with_a_name_above_20_characters(empty_user_collection):
    with pytest.raises(InvalidUsernameError) as exc_info:   
        _, _ = empty_user_collection.create_user("StenaldermandOfTheSevenIsles")
        assert exc_info.value.payload["username"] == "StenaldermandOfTheSevenIsles"

@pytest.fixture
def non_empty_user_collection():
    collection = UserCollection(InMemoryUserStore())
    user = collection.create_user("Stenaldermand")
    return user, collection

def test_can_get_existing_user(non_empty_user_collection):
    user_result, collection = non_empty_user_collection
    user, _ = user_result

    fetched_user = collection.get_user(user.username)
    assert(fetched_user == user)

def test_cannot_get_non_existing_user(non_empty_user_collection):
    _ , collection = non_empty_user_collection

    with pytest.raises(UserNotFoundError) as exc_info:   
        _ = collection.get_user("Rejesalat")
    assert exc_info.value.payload["username"] == "Rejesalat"



def test_can_authenticate_existing_user_with_the_given_pwd(non_empty_user_collection):
    user_result, collection = non_empty_user_collection
    user, pwd = user_result

    authenticated_user = collection.authenticate(user.username, pwd)
    assert(user == authenticated_user)

def test_cannot_authenticate_existing_user_with_a_wrong_password(non_empty_user_collection):
    user_result, collection = non_empty_user_collection
    user, _ = user_result

    with pytest.raises(AuthenticationError) as exc_info:   
        _ = collection.authenticate(user.username, base64.urlsafe_b64encode("MyBirthday1234".encode("ascii")).decode('ascii'))
    assert exc_info.value.payload["username"] == user.username


def test_cannot_authenticate_non_existing_user(non_empty_user_collection):
    _, collection = non_empty_user_collection
    
    with pytest.raises(UserNotFoundError) as exc_info:   
        _ = collection.authenticate("Rejesalat",  base64.urlsafe_b64encode("IntetBordUdenBahncke".encode("ascii")).decode('ascii'))
    assert exc_info.value.payload["username"] == "Rejesalat"

def test_generated_password_is_different_between_users(non_empty_user_collection):
    user_result, collection = non_empty_user_collection
    _, pwd = user_result

    _, pwd2 = collection.create_user("Rejesalat")

    assert(pwd != pwd2)