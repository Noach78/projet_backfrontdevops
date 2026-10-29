import re
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel
from passlib.hash import bcrypt
import jwt
from datetime import datetime, timezone
from typing import Any
from fastapi.middleware.cors import CORSMiddleware
from classes.account import Account
from classes.beneficiary import Beneficiary
from classes.transaction import Transaction
from classes.user import User
from sqlmodel import SQLModel, Session, create_engine

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

class UserCreate(BaseModel):
    name: str | None = None
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
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_methods=["*"],
    allow_headers=["*"],
)

user_repository = None
account_repository = None
transaction_repository = None
beneficiary_repository = None
JWT_SECRET = "secret"

def get_current_user_id(authorization: str | None = Header(default=None)) -> int:
    parts = authorization.split() if authorization else []
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Veuillez vous connecter.")

    try:
        payload = jwt.decode(parts[1], JWT_SECRET, algorithms=["HS256"])
    except jwt.InvalidTokenError as error:
        raise HTTPException(status_code=401, detail="Session invalide, veuillez vous reconnecter.") from error

    user_id = payload.get("user_id")
    if type(user_id) is not int:
        raise HTTPException(status_code=401, detail="Session invalide, veuillez vous reconnecter.")
    return user_id

def get_user_repository(session: Session = Depends(get_session)):
    from classes.user import SQLUserRepository
    return SQLUserRepository(session)

def get_account_repository(session: Session = Depends(get_session)):
    from classes.account import SQLAccountRepository
    return SQLAccountRepository(session)

def get_transaction_repository(session: Session = Depends(get_session)):
    from classes.transaction import SQLTransactionRepository
    return SQLTransactionRepository(session)

def get_beneficiary_repository(session: Session = Depends(get_session)):
    from classes.beneficiary import SQLBeneficiaryRepository
    return SQLBeneficiaryRepository(session)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/users")
def get_users(user_repository: Any = Depends(get_user_repository)):
    users = user_repository.users
    return [{"id": user.id, "name": user.name, "email": user.email} for user in users]

@app.get("/user_info/{id}")
def get_user(id: int, user_repository: Any = Depends(get_user_repository)):
    user = user_repository.find_user(id)
    if user is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    return {"id": user.id, "name": user.name, "email": user.email}
            
@app.post("/create_user")
@app.post("/auth/register")
def create_user(user_data: UserCreate, user_repository: Any = Depends(get_user_repository), account_repository: Any = Depends(get_account_repository)):
    from classes.user import User
    email = user_data.email.strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise HTTPException(status_code=422, detail="Veuillez saisir une adresse email valide.")
    if len(user_data.password) < 8:
        raise HTTPException(status_code=422, detail="Le mot de passe doit contenir au moins 8 caractères.")
    if user_repository.find_user_by_email(email):
        raise HTTPException(status_code=409, detail="Cette adresse email est déjà utilisée.")

    name = user_data.name.strip() if user_data.name else email.split("@", 1)[0]
    user = User(name=name, email=email, hashed_password=bcrypt.hash(user_data.password))
    user_repository.add_user(user)
    
    create_account(user.id, user_repository, account_repository)
    account = account_repository.find_user_accounts(user.id)[0]
    account.credit(100)
    account_repository.session.add(account)
    account_repository.session.commit()
    return {"message": f"User {name} created successfully. (User ID: {user.id})"}

@app.post("/login_user")
@app.post("/auth/login")
def login_user(user_data: LoginUser, user_repository: Any = Depends(get_user_repository)):
    email = user_data.email.strip().lower()
    user = user_repository.find_user_by_email(email)
    if user is None:
        raise HTTPException(status_code=401, detail="Identifiants incorrects.")
    
    if bcrypt.verify(user_data.password, user.hashed_password):
        token = jwt.encode({"user_id": user.id}, JWT_SECRET, algorithm="HS256")
        return {
            "token": token,
            "accessToken": token,
            "user": {"id": user.id, "name": user.name, "email": user.email}
        }

    raise HTTPException(status_code=401, detail="Identifiants incorrects.")

@app.post("/create_account/{id}")
def create_account(id: int, user_repository: Any = Depends(get_user_repository), account_repository: Any = Depends(get_account_repository)):
    user = user_repository.find_user(id)
    if user is None:
        return {"error": "User not found"}
    
    account_count = sum(1 for acc in account_repository.accounts if acc.get_user_id() == user.id and not acc.is_closed())
    if account_count >= 3:
        return {"error": "User already has 3 accounts"}
    
    account = Account(user_id=user.id, sold=0)
    account_repository.add_account(account)
    return {"message": f"Account created successfully. (Account ID: {account.get_id()})"}

@app.post("/close_account/{account_id}")
def close_account(account_id: int, account_repository: Any = Depends(get_account_repository), transaction_repository: Any = Depends(get_transaction_repository)):
    account = account_repository.find_account(account_id)
    if account is None:
        return {"error": "Account not found"}

    now = datetime.now(timezone.utc)
    has_pending_transaction = any(
        not transaction.is_cancelled
        and (transaction.source_id == account.id or transaction.recipient_id == account.id)
        and (now - transaction.created_at).total_seconds() <= 5
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
    account_repository.session.add(account)
    account_repository.session.add(accounts[0])
    account_repository.session.commit()
    return {"message": f"Account {account_id} closed"}

@app.post("/transaction/{source_account_id}/{recipient_account_id}/{amount}")
def transaction_endpoint(source_account_id: int, recipient_account_id: int, amount: int, user_id: int = Depends(get_current_user_id), account_repository: Any = Depends(get_account_repository), transaction_repository: Any = Depends(get_transaction_repository)):
    if not 0 < source_account_id < 2**63 - 1 or not 0 < recipient_account_id < 2**63 - 1:
        raise HTTPException(status_code=404, detail="Compte source ou destinataire introuvable.")

    source_account = account_repository.find_account(source_account_id)
    recipient_account = account_repository.find_account(recipient_account_id)

    if source_account is None or recipient_account is None:
        raise HTTPException(status_code=404, detail="Compte source ou destinataire introuvable.")

    if source_account.user_id != user_id:
        raise HTTPException(status_code=403, detail="Vous ne pouvez pas débiter ce compte.")

    if source_account.id == recipient_account.id:
        raise HTTPException(status_code=400, detail="Le compte destinataire doit être différent du compte source.")

    if source_account.is_closed() or recipient_account.is_closed():
        raise HTTPException(status_code=400, detail="Le compte source ou destinataire est clôturé.")
    
    if amount <= 0:
        raise HTTPException(status_code=422, detail="Le montant doit être supérieur à zéro.")

    if amount > source_account.sold:
        raise HTTPException(status_code=400, detail="Solde insuffisant.")
    
    try:
        tx = account_repository.transaction(source_account, recipient_account, amount, transaction_repository)
        return {"message": f"Transaction successful. (Transaction ID: {tx.id})"}
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    

@app.post("/credit/{account_id}/{amount}")
def credit_endpoint(
    account_id: int, 
    amount: float, 
    account_repository: Any = Depends(get_account_repository),
    current_user_id: int = Depends(get_current_user_id)
):
    account = account_repository.find_account(account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Compte introuvable.")
    if account_id == 0:
        raise HTTPException(status_code=400, detail="Compte réservé.")
    if account.is_closed():
        raise HTTPException(status_code=400, detail="Ce compte est clôturé.")
    if account.get_user_id() != current_user_id:
        raise HTTPException(status_code=403, detail="Ce compte ne vous appartient pas.")
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Le montant doit être supérieur à zéro.")
    if amount > 10000:
        raise HTTPException(status_code=400, detail="Le montant ne peut pas dépasser 10 000 €.")
    account.credit(amount)
    account_repository.session.add(account)
    account_repository.session.commit()
    return {"sold": account.sold}

@app.get("/accounts/{user_id}")
def get_user_accounts(
    user_id: int, 
    account_repository: Any = Depends(get_account_repository),
    current_user_id: int = Depends(get_current_user_id)
):
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Vous ne pouvez pas consulter les comptes d'un autre utilisateur.")
    accounts = account_repository.find_user_accounts(user_id)
    if not accounts:
        return {"accounts": []}
    return {
        "accounts": [
            {
                "account_id": str(account.get_id()),
                "sold": account.get_sold(),
                "date_created": account.get_date_created()
            }
            for account in accounts
            if not account.is_closed()
        ]
    }

@app.get("/my_accounts")
@app.get("/accounts")
def get_my_accounts(user_id: int = Depends(get_current_user_id), account_repository: Any = Depends(get_account_repository)):
    raw_accounts = [acc for acc in account_repository.find_user_accounts(user_id) if not acc.is_closed()]
    
    sorted_by_creation = sorted(raw_accounts, key=lambda a: a.date_created)
    primary_id = sorted_by_creation[0].get_id() if sorted_by_creation else None

    sorted_accounts = sorted(raw_accounts, key=lambda a: a.date_created, reverse=True)

    return {
        "accounts": [
            {
                "account_id": str(account.get_id()),
                "sold": account.get_sold(),
                "date_created": account.get_date_created(),
                "type": "principal" if account.get_id() == primary_id else "secondaire"
            }
            for account in sorted_accounts
        ]
    }

@app.get("/account_info/{account_id}")
def account_info(
    account_id: int, 
    account_repository: Any = Depends(get_account_repository),
    current_user_id: int = Depends(get_current_user_id)
):
    account = account_repository.find_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Compte introuvable.")
    if account.is_closed():
        raise HTTPException(status_code=400, detail="Ce compte est clôturé.")
    if account.get_user_id() != current_user_id:
        raise HTTPException(status_code=403, detail="Ce compte ne vous appartient pas.")

    user_accounts = account_repository.find_user_accounts(current_user_id)
    is_primary = len(user_accounts) > 0 and user_accounts[0].get_id() == account.get_id()

    return {
        "account": {
            "account_id": str(account.get_id()),
            "sold": account.get_sold(),
            "date_created": account.get_date_created(),
            "type": "principal" if is_primary else "secondaire"
        }
    }

@app.post("/cancel_transaction/{transaction_id}")
def cancel_transaction(transaction_id: int, transaction_repository: Any = Depends(get_transaction_repository)):
    transaction = None
    for transaction in transaction_repository.transactions:
        if transaction.id == transaction_id and not transaction.is_cancelled:
            break
    else:
        return {"error": "Transaction not found or already cancelled"}

    if (datetime.now(timezone.utc) - transaction.created_at).total_seconds() > 5:
        return {"error": "Transaction cannot be cancelled after 5 seconds"}

    source = account_repository.find_account(transaction.source_id)
    recipient = account_repository.find_account(transaction.recipient_id)
    if source is None or recipient is None:
        return {"error": "Transaction accounts not found"}
    source.credit(transaction.amount)
    recipient.debit(transaction.amount)
    account_repository.session.add(source)
    account_repository.session.add(recipient)
    account_repository.session.commit()
    transaction.is_cancelled = True
    transaction_repository.session.add(transaction)
    transaction_repository.session.commit()
    return {"message": "Transaction cancelled successfully"}

@app.post("/transaction_history/{account_id}")
def transaction_history(account_id: int, account_repository: Any = Depends(get_account_repository), transaction_repository: Any = Depends(get_transaction_repository), current_user_id: int = Depends(get_current_user_id)):
    account = account_repository.find_account(account_id)
    if account is None: 
        return {"error": "Account not found"}

    if account.is_closed():
        return {"error": "Account is closed"}

    if account.get_user_id() != current_user_id:
        raise HTTPException(status_code=403, detail="Ce compte ne vous appartient pas.")
    
    transactions = []
    for transaction in transaction_repository.transactions:
        if transaction.source_id == account.id or transaction.recipient_id == account.id:
            transactions.append({
                "transaction_id": transaction.id,
                "source": transaction.source_id,
                "recipient": transaction.recipient_id,
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
        "source": transaction.source_id,
        "recipient": transaction.recipient_id,
        "amount": transaction.amount,
        "created_at": transaction.created_at,
        "is_cancelled": transaction.is_cancelled
    }

@app.post("/add_beneficiary")
def add_beneficiary(beneficiary_data: BeneficiaryCreate, beneficiary_repository: Any = Depends(get_beneficiary_repository), account_repository: Any = Depends(get_account_repository), user_repository: Any = Depends(get_user_repository)):
    owner_user = user_repository.find_user(beneficiary_data.owner_id)
    if owner_user is None:
        return {"error": "Owner user not found"}

    beneficiary_account = account_repository.find_account(beneficiary_data.account_id)
    if beneficiary_account is None:
        return {"error": "Beneficiary account not found"}

    if beneficiary_account.get_user_id() == owner_user.id:
        return {"error": "Beneficiary cannot be the same as the owner's account"}

    for existing_beneficiary in beneficiary_repository.beneficiaries:
        if existing_beneficiary.owner_id == beneficiary_data.owner_id and existing_beneficiary.account_id == beneficiary_data.account_id:
            return {"error": "Beneficiary already added"}

    if not beneficiary_data.name.strip():
        return {"error": "Beneficiary name must be provided"}

    from classes.beneficiary import Beneficiary
    new_beneficiary = Beneficiary(
        owner_id=beneficiary_data.owner_id,
        name=beneficiary_data.name,
        account_id=beneficiary_data.account_id,
    )
    beneficiary_repository.add_beneficiary(new_beneficiary)

    return {"message": f"Beneficiary {beneficiary_data.name} added successfully. (Beneficiary ID: {new_beneficiary.id})"}

@app.get("/beneficiaries/{owner_id}")
def get_beneficiaries(owner_id: int, beneficiary_repository: Any = Depends(get_beneficiary_repository), user_repository: Any = Depends(get_user_repository)):
    owner_user = user_repository.find_user(owner_id)
    if owner_user is None:
        return {"error": "Owner user not found"}

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
