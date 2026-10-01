from fastapi import Depends, FastAPI
from pydantic import BaseModel
from passlib.hash import bcrypt
import jwt
from datetime import datetime
from typing import Any

from classes.account import Account

class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class LoginUser(BaseModel):
    email: str
    password: str

class BeneficiaryCreate(BaseModel):
    owner_id: int
    name: str
    account_id: int

app = FastAPI()

user_repository = None
account_repository = None
transaction_repository = None
beneficiary_repository = None

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

def get_beneficiary_repository():
    global beneficiary_repository
    if beneficiary_repository is None:
        from classes.beneficiary import InMemoryBeneficiaryRepository
        beneficiary_repository = InMemoryBeneficiaryRepository()
    return beneficiary_repository

@app.get("/users")
def get_users(user_repository: Any = Depends(get_user_repository)):
    users = user_repository.users
    return [{"id": user.id, "name": user.name, "email": user.email} for user in users]

@app.get("/user_info/{id}")
def get_user(id: int, user_repository: Any = Depends(get_user_repository)):
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
    
    create_account(user.id, user_repository)
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
def create_account(id: int, user_repository: Any = Depends(get_user_repository)):
    account_repository = get_account_repository()
    user = user_repository.find_user(id)
    if user is None:
        return {"error": "User not found"}
    
    account_count = sum(1 for acc in account_repository.accounts if acc.get_user_id() == user.id and not acc.is_closed())
    if account_count >= 3:
        return {"error": "User already has 3 accounts"}
    
    account = Account(user.id, 0)
    account_repository.add_account(account)
    return {"message": f"Account created successfully. (Account ID: {account.get_id()})"}

@app.post("/close_account/{account_id}")
def close_account(account_id: int, account_repository: Any = Depends(get_account_repository), transaction_repository: Any = Depends(get_transaction_repository)):
    account = account_repository.find_account(account_id)
    if account is None:
        return {"error": "Account not found"}

    has_pending_transaction = any(
        not transaction.is_cancelled
        and (transaction.source == account or transaction.recipient == account)
        for transaction in transaction_repository.transactions
    )
    if has_pending_transaction:
        return {"error": "Cannot close account with pending transactions"}

    accounts = account_repository.find_user_accounts(account.get_user_id())
    if accounts[0].get_id() == account_id:
        return {"error": "Cannot close the primary account"}

    account.debit(account.get_sold())
    accounts[0].credit(account.get_sold())

    account.close()
    return {"message": f"Account {account_id} closed"}

@app.post("/transaction/{source_account_id}/{recipient_account_id}/{amount}")
def transaction_endpoint(source_account_id: int, recipient_account_id: int, amount: int, account_repository: Any = Depends(get_account_repository), transaction_repository: Any = Depends(get_transaction_repository)):
    source_account = account_repository.find_account(source_account_id)
    recipient_account = account_repository.find_account(recipient_account_id)

    if source_account is None or recipient_account is None:
        return {"error": "Source or recipient account not found"}

    if source_account.is_closed() or recipient_account.is_closed():
        return {"error": "Source or recipient account is closed"}
    
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
    if account_id == 0:
        return {"error": "Account 0 is reserved"}
    if amount <= 0:
        return {"error": "Amount must be greater than zero"}
    account.credit(amount)
    return {"sold": account.sold}

@app.get("/accounts/{user_id}")
def get_user_accounts(user_id: int, account_repository: Any = Depends(get_account_repository)):
    accounts = account_repository.find_user_accounts(user_id)
    if not accounts:
        return {"error": "No accounts found for this user"}
    
    return {
        "accounts": [
            {
                "account_id": account.get_id(),
                "sold": account.get_sold(),
                "date_created": account.get_date_created()
            }
            for account in accounts
            if not account.is_closed()
        ]
    }

@app.get("/account_info/{account_id}")
def account_info(account_id: int, account_repository: Any = Depends(get_account_repository)):
    account = account_repository.find_account(account_id)
    if not account:
        return {"error": "Account not found"}
    if account.is_closed():
        return {"error": "Account is closed"}

    return {
        "account": {
            "account_id": account.get_id(),
            "sold": account.get_sold(),
            "date_created": account.get_date_created()
        }
    }

@app.get("/account_info/{user_id}")
def account_info(user_id: int, account_repository: Any = Depends(get_account_repository)):
    accounts = account_repository.find_user_accounts(user_id)
    if not accounts:
        return {"error": "No accounts found for this user"}

    return {
        "accounts": [
            {
                "account_id": account.get_id(),
                "sold": account.get_sold(),
                "date_created": account.get_date_created()
            }
            for account in accounts
            if not account.is_closed()
        ]
    }

@app.post("/cancel_transaction/{transaction_id}")
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

@app.post("/transaction_history/{account_id}")
def transaction_history(account_id: int, account_repository: Any = Depends(get_account_repository), transaction_repository: Any = Depends(get_transaction_repository)):
    account = account_repository.find_account(account_id)
    if account is None: 
        return {"error": "Account not found"}

    if account.is_closed():
        return {"error": "Account is closed"}
    
    transactions = []
    for transaction in transaction_repository.transactions:
        if transaction.source == account or transaction.recipient == account:
            transactions.append({
                "transaction_id": transaction.id,
                "source": transaction.source.get_id(),
                "recipient": transaction.recipient.get_id(),
                "amount": transaction.amount,
                "created_at": transaction.created_at,
                "is_cancelled": transaction.is_cancelled
            })
    transactions.sort(key=lambda x: x["created_at"], reverse=True)
    return {"transactions": transactions}

@app.get("/transaction_info/{transaction_id}")
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

@app.post("/add_beneficiary")
def add_beneficiary(beneficiary_data: BeneficiaryCreate, beneficiary_repository: Any = Depends(get_beneficiary_repository), account_repository: Any = Depends(get_account_repository)):
    owner_account = account_repository.find_account(beneficiary_data.owner_id)
    if owner_account is None:
        return {"error": "Owner account not found"}

    if owner_account.get_user_id() == beneficiary_data.account_id:
        return {"error": "Beneficiary cannot be the same as the owner's account"}

    beneficiary_account = account_repository.find_account(beneficiary_data.account_id)
    if beneficiary_account is None:
        return {"error": "Beneficiary account not found"}

    for existing_beneficiary in beneficiary_repository.beneficiaries:
        if existing_beneficiary.owner_id == beneficiary_data.owner_id and existing_beneficiary.account_id == beneficiary_data.account_id:
            return {"error": "Beneficiary already added"}

    if not beneficiary_data.name.strip():
        return {"error": "Beneficiary name must be provided"}

    from classes.beneficiary import Beneficiary
    new_beneficiary = Beneficiary(beneficiary_data.owner_id, beneficiary_data.name, beneficiary_data.account_id)
    beneficiary_repository.add_beneficiary(new_beneficiary)

    return {"message": f"Beneficiary {beneficiary_data.name} added successfully. (Beneficiary ID: {new_beneficiary.id})"}

@app.get("/beneficiaries/{owner_id}")
def get_beneficiaries(owner_id: int, beneficiary_repository: Any = Depends(get_beneficiary_repository), account_repository: Any = Depends(get_account_repository)):
    owner_account = account_repository.find_account(owner_id)
    if owner_account is None:
        return {"error": "Owner account not found"}

    beneficiaries = [
        {
            "id": beneficiary.id,
            "name": beneficiary.name,
            "account_id": beneficiary.account_id,
            "added_at": beneficiary.added_at
        }
        for beneficiary in beneficiary_repository.beneficiaries
        if beneficiary.owner_id == owner_id
    ]

    return {"beneficiaries": beneficiaries}