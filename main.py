from fastapi import Depends, FastAPI
from pydantic import BaseModel
from passlib.hash import bcrypt
import jwt
from datetime import datetime
from typing import Any

from classes.account import Account, AccountRepository, InMemoryAccountRepository

class UserCreate(BaseModel):
    name: str
    email: str
    password: str


class LoginUser(BaseModel):
    email: str
    password: str

app = FastAPI()

user_repository = None
account_repository = None
transaction_repository = None

def get_user_repository():
    global user_repository
    if user_repository is None:
        from classes.user import InMemoryUserRepository
        user_repository = InMemoryUserRepository()
    return user_repository

def get_account_repository():
    global account_repository
    if account_repository is None:
        from classes.account import InMemoryAccountRepository
        account_repository = InMemoryAccountRepository()
    return account_repository

def get_transaction_repository():
    global transaction_repository
    if transaction_repository is None:
        from classes.transaction import InMemoryTransactionRepository
        transaction_repository = InMemoryTransactionRepository()
    return transaction_repository

@app.get("/user_info/{id}")
def get_user(id: int, user_repository: Any = Depends(get_user_repository)):
    print(f"{user_repository.users}")
    user = user_repository.find_user(id)
    return {"id": user.id, "name": user.name, "email": user.email}
            
@app.post("/create_user")
def create_user(user_data: UserCreate, user_repository: Any = Depends(get_user_repository), account_repository: Any = Depends(get_account_repository)):
    from classes.user import User
    for user in user_repository.users:
        if user.email == user_data.email:
            return {"error": "User with this email already exists"}
    
    if len(user_data.password) < 8 :
        return {"Error !": "Your password is too short"}

    user_data.password = bcrypt.hash(user_data.password)
    user = User(user_data.name, user_data.email, user_data.password)
    user_repository.add_user(user)
    
    create_account(user.id, user_repository, account_repository)
    account_repository.find_user_accounts(user.id)[0].credit(100)
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

@app.post("/create_account/{id}")
def create_account(id: int, user_repository: Any = Depends(get_user_repository), account_repository: Any = Depends(get_account_repository)):
    user = user_repository.find_user(id)
    if user is None:
        return {"error": "User not found"}
    
    account_count = sum(1 for acc in account_repository.accounts if acc.get_user_id() == user.id)
    if account_count >= 3:
        return {"error": "User already has to many accounts"}
    
    account = Account(user.id, 0)
    account_repository.add_account(account)
    return {"message": f"Account created for user {id}. (Account ID: {account.get_id()})"}

@app.post("/transaction/{source_account_id}/{recipient_account_id}/{amount}")
def transaction_endpoint(source_account_id: int, recipient_account_id: int, amount: int, account_repository: Any = Depends(get_account_repository), transaction_repository: Any = Depends(get_transaction_repository)):
    
    source_account = account_repository.find_account(source_account_id)
    recipient_account = account_repository.find_account(recipient_account_id)

    if source_account is None or recipient_account is None:
        return {"error": "Source or recipient account not found"}
    
    if amount <= 0:
        return {"error": "Amount must be greater than zero"}
    
    try:
        tx = account_repository.transaction(source_account, recipient_account, amount, transaction_repository)
        return {"message": f"Transaction successful. (Transaction ID: {tx.id})"}
    except ValueError as e:
        return {"error": str(e)}
    

@app.post("/credit/{account_id}/{amount}")
def credit_endpoint(account_id: int, amount: int, account_repository: Any = Depends(get_account_repository)):
    account = account_repository.find_account(account_id)
    if account is None:
        return {"error": "Account not found"}
    
    account.credit(amount)
    return {"sold": account.sold}


@app.get("/account_info/{account_id}")
def account_info(account_id: int, account_repository: Any = Depends(get_account_repository)):
    account = account_repository.find_account(account_id)
    if account is None:
        return {"error": "Account not found"}
    return {
        "account_id": account.get_id(),
        "sold": account.get_sold(),
        "date_created": account.get_date_created()
    }

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

    transaction.source.credit(transaction.amount)
    transaction.recipient.debit(transaction.amount)
    transaction.is_cancelled = True
    return {"message": "Transaction cancelled successfully"}

@app.post("/transaction-history/{account_id}")
def transaction_history(account_id: int, transaction_repository: Any = Depends(get_transaction_repository)):
    user_transactions = []
    for transaction in transaction_repository.transactions:
        if transaction.source.get_id() == account_id or transaction.recipient.get_id() == account_id:
            user_transactions.append({
                "transaction_id": transaction.id,
                "source": transaction.source.get_id(),
                "recipient": transaction.recipient.get_id(),
                "amount": transaction.amount,
                "created_at": transaction.created_at,
                "is_cancelled": transaction.is_cancelled
            })
    user_transactions.sort(key=lambda x: x["created_at"], reverse=True)
    return {"transactions": user_transactions}

@app.get("/transaction-info/{transaction_id}")
def transaction_info(transaction_id: int, transaction_repository: Any = Depends(get_transaction_repository)):
    transaction = None
    for transaction in transaction_repository.transactions:
        if transaction.id == transaction_id:
            break
    else:
        return {"error": "Transaction not found"}
    
    return {
        "transaction_id": transaction.id,
        "source": transaction.source.get_id(),
        "recipient": transaction.recipient.get_id(),
        "amount": transaction.amount,
        "created_at": transaction.created_at,
        "is_cancelled": transaction.is_cancelled
    }