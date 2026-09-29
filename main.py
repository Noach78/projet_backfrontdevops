from fastapi import FastAPI
from pydantic import BaseModel
from abc import ABC, abstractmethod
from datetime import datetime
from passlib.hash import bcrypt

app = FastAPI()

class Account():
    def __init__(self, user_id: int, sold: int):
        self.user_id = user_id
        self.sold = sold

    def credit(self, amount: int):
        self.sold += amount
        return self.sold

    def debit(self, amount: int):
        if amount > self.sold:
            raise ValueError("Insufficient funds")
        self.sold -= amount
        return self.sold

    def show_sold(self):
        print(self.sold)    

class User():
    def __init__(self, name: str, email: str, hashed_password: str):
        self.name = name
        self.user_id = len(users) + 1
        self.account = None
        self.email = email
        self.hashed_password = hashed_password


    def create_account(self):
        self.account = Account(self.user_id, 0)

    def get_account(self):
        return self.account


class UserOperations(ABC):
    @abstractmethod
    def find_user(self, name: str):
        pass

    @abstractmethod
    def transfer(self, source: User, recipient: User, amount: int):
        pass

class UserCreate(BaseModel):
    name: str
    email : str
    password: str

class Transaction:
    def __init__(self, tx_id: int, source: User, recipient: User, amount: int):
        self.id = tx_id
        self.source = source
        self.recipient = recipient
        self.amount = amount
        self.created_at = datetime.now()
        self.is_cancelled = False
    
users = []
transactions = []
transaction_counter = 1

class UserService(UserOperations):
    def find_user(self, name: str):
        for user in users:
            if user.name == name:
                return user
        return None
    

    def transfer(source: User, recipient: User, amount: int):
        global transaction_counter
        source.get_account().debit(amount)
        recipient.get_account().credit(amount)
        
        tx = Transaction(transaction_counter, source, recipient, amount)
        transactions.append(tx)
        transaction_counter += 1
        return tx

user_service = UserService()

@app.get("/users")
def get_users():
    return [{"id": user.user_id, "name": user.name, "email": user.email, "password": user.hashed_password, "sold": user.account.sold} for user in users]

@app.post("/user")
def create_user(user_data: UserCreate):
    if user in users:
        if user.email == user_data.email:
            return {"error": "User with this email already exists"}
    
    if len(user_data.password) < 8 :
        return {"Error !": "Your password is too short"}
    user_data.password = bcrypt.hash(user_data.password)
    user = User(user_data.name, user_data.email, user_data.password)
    user.create_account()
    users.append(user)
    return {"message": f"User {user_data.name} created successfully. (User ID: {user.user_id})"}

@app.post("/transfer/{source_name}/{recipient_name}/{amount}")
def transfer_endpoint(source_name: str, recipient_name: str, amount: int):
    source = user_service.find_user(source_name)
    recipient = user_service.find_user(recipient_name)
    if source is None or recipient is None:
        return {"error": "User not found"}
    user_service.transfer(source, recipient, amount)
    return {
        "source_sold": source.account.sold,
        "recipient_sold": recipient.account.sold,
    }

@app.post("/credit/{name}/{amount}")
def credit_endpoint(name: str, amount: int):
    user = user_service.find_user(name)
    if user is None:
        return {"error": "User not found"}
    user.get_account().credit(amount)
    return {"sold": user.account.sold}

@app.post("/cancel-transaction/{transaction_id}")
def cancel_transaction(transaction_id: int):
    for transaction in transactions :
        if transaction.id != transaction_id or transaction.is_cancelled == False:
            continue

    if (datetime.now() - transaction.created_at).total_seconds() > 5:
        return {"error": "Transaction cannot be cancelled after 5 seconds"}

    transaction.source.get_account().credit(transaction.amount)
    transaction.recipient.get_account().debit(transaction.amount)
    transaction.is_cancelled = True
    return {"message": "Transaction cancelled successfully"}