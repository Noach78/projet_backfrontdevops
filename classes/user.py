from pydantic import BaseModel
from abc import ABC, abstractmethod
from uuid import uuid4
from sqlmodel import Field, SQLModel, Session, select

def new_id() -> int:
    return uuid4().int % (2**63 - 1)

class User(SQLModel, table=True):
    id: int = Field(default_factory=new_id, primary_key=True)
    name: str
    email: str
    hashed_password: str

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
        self._users = []

    @property
    def users(self):
        return self._users
    
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

class SQLUserRepository(UserRepository):
    def __init__(self, session: Session):
        super().__init__()
        self.session = session

    @property
    def users(self):
        return self.session.exec(select(User)).all()

    def find_user(self, id: int):
        return self.session.get(User, id)

    def find_user_by_email(self, email: str):
        return self.session.exec(select(User).where(User.email == email)).first()

    def add_user(self, user: User):
        self.session.add(user)
        self.session.commit()