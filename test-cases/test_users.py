from utils import *
from routers.users import get_db, get_current_user
from fastapi import status


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

def test_return_user(test_user):
    response = client.get("/user/")
    assert response.status_code == status.HTTP_200_OK

    assert response.json()['username'] == 'kevin'
    assert response.json()['email'] == 'kevin@gmail.com'
    assert response.json()['firstname'] == 'kevin'
    assert response.json()['lastname'] == 'rupera'
    assert response.json()['role'] == 'admin'
    assert response.json()['phone_number'] == '1234567890'


def test_change_password(test_user):
    response = client.put("/user/change_pwd/1", json={'password': 'Kevin@2003',
                                                       'new_password' : "Kevin172003"})
    assert response.status_code == status.HTTP_200_OK

def test_change_password_invalid_current_password():
    response = client.put("/user/change_pwd", json={'password': 'wrong_password',
                                                       'new_password' : "Kevin172003"})
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail' : 'Not Found'}


def test_change_phone_number_success(test_user):
    response = client.put("/user/phone_number/3423")
    assert response.status_code == status.HTTP_204_NO_CONTENT