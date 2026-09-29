from fastapi import Depends, FastAPI
from pydantic import BaseModel
from abc import ABC, abstractmethod
from datetime import datetime
from passlib.hash import bcrypt
import jwt

app = FastAPI()

def random_id():
    return int(datetime.now().timestamp() * 1000)

class Account():
    def __init__(self, user_id: int, sold: int):
        self.id = random_id()
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
        self.id = random_id()
        self.name = name
        self.email = email
        self.hashed_password = hashed_password
        self.account = []

    def create_account(self):
        self.account = [Account(self.id, 0)]

    def get_account(self):
        return self.account

class Transaction:
    def __init__(self, tx_id: int, source: User, recipient: User, amount: int):
        self.id = tx_id
        self.source = source
        self.recipient = recipient
        self.amount = amount
        self.created_at = datetime.now()
        self.is_cancelled = False

class UserCreate(BaseModel):
    name: str
    email : str
    password: str

class LoginUser(BaseModel):
    email: str
    password: str

class TransactionRepository(ABC):
    def __init__(self):
        self.transactions = []
        self.transaction_counter = 1

    @abstractmethod
    def add_transaction(self, transaction: Transaction):
        pass

    @abstractmethod
    def find_transaction(self, transaction_id: int):
        pass

class InMemoryTransactionRepository(TransactionRepository):
    def add_transaction(self, transaction: Transaction):
        self.transactions.append(transaction)

    def find_transaction(self, transaction_id: int):
        for transaction in self.transactions:
            if transaction.id == transaction_id:
                return transaction
        return None

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

    def transfer(self, source: User, recipient: User, amount: int, transaction_repository: TransactionRepository):
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

    def transfer(self, source: User, recipient: User, amount: int, transaction_repository: TransactionRepository):
        global transaction_counter
        source.get_account().debit(amount)
        recipient.get_account().credit(amount)
        
        tx = Transaction(transaction_counter, source, recipient, amount)
        transaction_repository.add_transaction(tx)
        transaction_counter += 1
        return tx


user_repository = InMemoryUserRepository()
transaction_repository = InMemoryTransactionRepository()

def get_user_repository():
    return user_repository

def get_transaction_repository():
    return transaction_repository

@app.get("/user_info/{name}")
def get_user(name: str, user_repository: UserRepository = Depends(get_user_repository)):
    print(f"{user_repository.users}")
    user = user_repository.find_user(name)
    return {"id": user.id, "name": user.name, "email": user.email}
            
@app.post("/create_user")
def create_user(user_data: UserCreate, user_repository: UserRepository = Depends(get_user_repository)):
    for user in user_repository.users:
        if user.email == user_data.email:
            return {"error": "User with this email already exists"}
    
    if len(user_data.password) < 8 :
        return {"Error !": "Your password is too short"}
    user_data.password = bcrypt.hash(user_data.password)
    user = User(user_data.name, user_data.email, user_data.password)
    user_repository.add_user(user)
    return {"message": f"User {user_data.name} created successfully. (User ID: {user.id})"}

@app.post("/login_user")
def login_user(user_data: LoginUser, user_repository: UserRepository = Depends(get_user_repository)):
    user = user_repository.find_user_by_email(user_data.email)
    if user is None:
        return {"error": "User with this email not found"}
    
    if bcrypt.verify(user_data.password, user.hashed_password):
        token = jwt.encode({"user_id": user.id}, "secret", algorithm="HS256")
        return {"token": token}

    return {"error": "Invalid credentials"}

@app.post("/create_account/{name}")
def create_account(name: str, user_repository: UserRepository = Depends(get_user_repository)):
    user = user_repository.find_user(name)
    if user is None:
        return {"error": "User not found"}
    user.create_account()
    if len(user.account) > 1:
        return {"error": "User already has an account"}
    return {"message": f"Account created for user {name}"}

@app.post("/transfer/{source_name}/{recipient_name}/{amount}")
def transfer_endpoint(source_name: str, recipient_name: str, amount: int, user_repository: UserRepository = Depends(get_user_repository), transaction_repository: TransactionRepository = Depends(get_transaction_repository)):
    source = user_repository.find_user(source_name)
    recipient = user_repository.find_user(recipient_name)
    if source is None or recipient is None:
        return {"error": "User not found"}
    user_repository.transfer(source, recipient, amount, transaction_repository)
    return {
        "source_sold": source.account.sold,
        "recipient_sold": recipient.account.sold,
    }

@app.post("/credit/{name}/{amount}")
def credit_endpoint(name: str, amount: int, user_repository: UserRepository = Depends(get_user_repository)):
    user = user_repository.find_user(name)
    if user is None:
        return {"error": "User not found"}
    user.get_account()[0].credit(amount)
    return {"sold": user.account[0].sold}

@app.post("/cancel-transaction/{transaction_id}")
def cancel_transaction(transaction_id: int, transaction_repository: TransactionRepository = Depends(get_transaction_repository)):
    for transaction in transaction_repository.transactions:
        if transaction.id != transaction_id or transaction.is_cancelled == False:
            continue

    if (datetime.now() - transaction.created_at).total_seconds() > 5:
        return {"error": "Transaction cannot be cancelled after 5 seconds"}

    transaction.source.get_account().credit(transaction.amount)
    transaction.recipient.get_account().debit(transaction.amount)
    transaction.is_cancelled = True
    return {"message": "Transaction cancelled successfully"}

@app.post("/transaction-history/{name}")
def transaction_history(name: str, user_repository: UserRepository = Depends(get_user_repository), transaction_repository: TransactionRepository = Depends(get_transaction_repository)):
    user = user_repository.find_user(name)
    if user is None:
        return {"error": "User not found"}
    
    user_transactions = []
    for transaction in transaction_repository.transactions:
        if transaction.source == user or transaction.recipient == user:
            user_transactions.append({
                "transaction_id": transaction.id,
                "source": transaction.source.name,
                "recipient": transaction.recipient.name,
                "amount": transaction.amount,
                "created_at": transaction.created_at,
                "is_cancelled": transaction.is_cancelled
            })
            
    # tri du plus récent au plus ancien
    user_transactions.sort(key=lambda tx: tx["created_at"], reverse=True)
    
    return {"transactions": user_transactions}
    