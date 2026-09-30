from fastapi import Depends, FastAPI
from pydantic import BaseModel
from passlib.hash import bcrypt
import jwt
from datetime import datetime
from typing import Any

class UserCreate(BaseModel):
    name: str
    email: str
    password: str


class LoginUser(BaseModel):
    email: str
    password: str

app = FastAPI()

user_repository = None
transaction_repository = None

def get_user_repository():
    global user_repository
    if user_repository is None:
        from classes.user import InMemoryUserRepository
        user_repository = InMemoryUserRepository()
    return user_repository

def get_transaction_repository():
    global transaction_repository
    if transaction_repository is None:
        from classes.transaction import InMemoryTransactionRepository
        transaction_repository = InMemoryTransactionRepository()
    return transaction_repository

@app.get("/user_info/{name}")
def get_user(name: str, user_repository: Any = Depends(get_user_repository)):
    print(f"{user_repository.users}")
    user = user_repository.find_user(name)
    return {"id": user.id, "name": user.name, "email": user.email}
            
@app.post("/create_user")
def create_user(user_data: UserCreate, user_repository: Any = Depends(get_user_repository)):
    from classes.user import User
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
def login_user(user_data: LoginUser, user_repository: Any = Depends(get_user_repository)):
    user = user_repository.find_user_by_email(user_data.email)
    if user is None:
        return {"error": "User with this email not found"}
    
    if bcrypt.verify(user_data.password, user.hashed_password):
        token = jwt.encode({"user_id": user.id}, "secret", algorithm="HS256")
        return {"token": token}

    return {"error": "Invalid credentials"}

@app.post("/create_account/{name}")
def create_account(name: str, user_repository: Any = Depends(get_user_repository)):
    user = user_repository.find_user(name)
    if user is None:
        return {"error": "User not found"}
    user.create_account()
    if len(user.account) > 1:
        return {"error": "User already has an account"}
    return {"message": f"Account created for user {name}"}

@app.post("/transfer/{source_name}/{recipient_name}/{amount}")
def transfer_endpoint(source_name: str, recipient_name: str, amount: int, user_repository: Any = Depends(get_user_repository), transaction_repository: Any = Depends(get_transaction_repository)):
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
def credit_endpoint(name: str, amount: int, user_repository: Any = Depends(get_user_repository)):
    user = user_repository.find_user(name)
    if user is None:
        return {"error": "User not found"}
    user.get_account()[0].credit(amount)
    return {"sold": user.account[0].sold}

@app.post("/cancel-transaction/{transaction_id}")
def cancel_transaction(transaction_id: int, transaction_repository: Any = Depends(get_transaction_repository)):
    transaction = None
    for transaction in transaction_repository.transactions:
        if transaction.id == transaction_id and not transaction.is_cancelled:
            break
    else:
        return {"error": "Transaction not found or already cancelled"}

    if (datetime.now() - transaction.created_at).total_seconds() > 5:
        return {"error": "Transaction cannot be cancelled after 5 seconds"}

    transaction.source.get_account().credit(transaction.amount)
    transaction.recipient.get_account().debit(transaction.amount)
    transaction.is_cancelled = True
    return {"message": "Transaction cancelled successfully"}

@app.post("/transaction-history/{name}")
def transaction_history(name: str, user_repository: Any = Depends(get_user_repository), transaction_repository: Any = Depends(get_transaction_repository)):
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
            
    user_transactions.sort(key=lambda tx: tx["created_at"], reverse=True)
    
    return {"transactions": user_transactions}
    