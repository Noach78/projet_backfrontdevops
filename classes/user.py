from datetime import datetime
from pydantic import BaseModel
from abc import ABC, abstractmethod

class User():
    def __init__(self, name: str, email: str, hashed_password: str):
        self.id = int(datetime.now().timestamp() * 1000)
        self.name = name
        self.email = email
        self.hashed_password = hashed_password

    def add_transaction(self, transaction):
        self.transactions.append(transaction)

class UserCreate(BaseModel):
    name: str
    email : str
    password: str

class LoginUser(BaseModel):
    email: str
    password: str

class UserRepository(ABC):
    def __init__(self):
        self.users = []
    
    @abstractmethod
    def find_user(self, id: int):
        pass

    @abstractmethod
    def add_user(self, user: User):
        pass

class InMemoryUserRepository(UserRepository):
    def find_user(self, id: int):
        for user in self.users:
            if user.id == id:
                return user
        return None

    def find_user_by_email(self, email: str):
        for user in self.users:
            if user.email == email:
                return user
        return None

    def add_user(self, user: User):
        self.users.append(user)