from datetime import datetime, timezone
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from uuid import uuid4
from sqlmodel import Field, SQLModel, Session, select

if TYPE_CHECKING:
    from classes.account import Account

def new_id() -> int:
    return uuid4().int % (2**63 - 1)

class Transaction(SQLModel, table=True):
    id: int = Field(default_factory=new_id, primary_key=True)
    source_id: int = Field(default=None)
    recipient_id: int = Field(default=None)
    amount: int = Field(default=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_cancelled: bool = Field(default=False)

class TransactionRepository(ABC):
    def __init__(self):
        self._transactions = []
        self.transaction_counter = 1

    @property
    def transactions(self):
        return self._transactions

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

class SQLTransactionRepository(TransactionRepository):
    def __init__(self, session: Session):
        super().__init__()
        self.session = session

    @property
    def transactions(self):
        return self.session.exec(select(Transaction)).all()

    def add_transaction(self, transaction: Transaction):
        self.session.add(transaction)
        self.session.commit()
        self.session.refresh(transaction)

    def find_transaction(self, transaction_id: int):
        return self.session.get(Transaction, transaction_id)