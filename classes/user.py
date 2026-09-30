import transaction 
import datetime
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
    def find_user(self, name: str):
        pass

    @abstractmethod
    def find_user_by_email(self, email: str):
        pass

    @abstractmethod
    def add_user(self, user: User):
        pass

    def transfer(self, source: User, recipient: User, amount: int, transaction_repository: transaction.TransactionRepository):
        pass

class InMemoryUserRepository(UserRepository):
    def find_user(self, name: str):
        for user in self.users:
            if user.name == name:
                return user
        return None

    def find_user_by_email(self, email: str):
        for user in self.users:
            if user.email == email:
                return user
        return None

    def add_user(self, user: User):
        self.users.append(user)

    def transfer(self, source: User, recipient: User, amount: int, transaction_repository: transaction.TransactionRepository):
        global transaction_counter
        source.get_account().debit(amount)
        recipient.get_account().credit(amount)
        
        tx = transaction.Transaction(source, recipient, amount)
        transaction_repository.add_transaction(tx)
        return tx