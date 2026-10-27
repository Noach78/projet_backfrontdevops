from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import uuid4
from sqlmodel import Field, SQLModel, Session, select

if TYPE_CHECKING:
    from classes.transaction import Transaction, TransactionRepository

def new_id() -> int:
    return uuid4().int % (2**63 - 1)

class Account(SQLModel, table=True):
    id: int = Field(default_factory=new_id, primary_key=True)
    user_id: int = Field(default=None)
    sold: int = Field(default=0)
    date_created: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    closed: bool = Field(default=False)

    def get_user_id(self):
        return self.user_id

    def get_id(self):   
        return self.id

    def get_sold(self):
        return self.sold

    def get_date_created(self):
        return self.date_created

    def credit(self, amount: int):
        if self.is_closed():
            raise ValueError("Account is closed")
        self.sold += amount
        return self.sold

    def debit(self, amount: int):
        if self.is_closed():
            raise ValueError("Account is closed")
        if amount > self.sold:
            raise ValueError("Insufficient funds")
        self.sold -= amount
        return self.sold

    def is_closed(self):
        return self.closed

    def close(self):
        self.closed = True

class AccountRepository(ABC):
    def __init__(self):
        self._accounts = []

    @property
    def accounts(self):
        return self._accounts

    @abstractmethod
    def add_account(self, account: Account):
        pass

    @abstractmethod
    def find_account(self, account_id: int):
        pass

    @abstractmethod
    def find_user_accounts(self, user_id: int):
        pass

    @abstractmethod
    def transaction(self, source: Account, recipient: Account, amount: int, transaction_repository: "TransactionRepository"):
        from classes.transaction import Transaction

        source.debit(amount)
        recipient.credit(amount)
        tx = Transaction(
            source_id=source.id,
            recipient_id=recipient.id,
            amount=amount,
        )
        transaction_repository.add_transaction(tx)
        return tx

class InMemoryAccountRepository(AccountRepository):
    def add_account(self, account: Account):
        self.accounts.append(account)

    def find_account(self, account_id: int):
        for account in self.accounts:
            if account.get_id() == account_id:
                return account
        return None

    def find_user_accounts(self, user_id: int):
        accounts_for_user = []
        for account in self.accounts:
            if account.get_user_id() == user_id:
                accounts_for_user.append(account)
        return accounts_for_user

    def transaction(self, source: Account, recipient: Account, amount: int, transaction_repository: "TransactionRepository"):
        from classes.transaction import Transaction

        source.debit(amount)
        recipient.credit(amount)
        tx = Transaction(
            source_id=source.id,
            recipient_id=recipient.id,
            amount=amount,
        )
        transaction_repository.add_transaction(tx)
        return tx

class SQLAccountRepository(AccountRepository):
    def __init__(self, session: Session):
        super().__init__()
        self.session = session

    @property
    def accounts(self):
        return self.session.exec(select(Account)).all()

    def add_account(self, account: Account):
        self.session.add(account)
        self.session.commit()
        self.session.refresh(account)

    def find_account(self, account_id: int):
        return self.session.get(Account, account_id)

    def find_user_accounts(self, user_id: int):
        return self.session.exec(select(Account).where(Account.user_id == user_id)).all()

    def transaction(self, source: Account, recipient: Account, amount: int, transaction_repository: "TransactionRepository"):
        from classes.transaction import Transaction

        source.debit(amount)
        recipient.credit(amount)
        self.session.add(source)
        self.session.add(recipient)
        self.session.commit()
        tx = Transaction(
            source_id=source.id,
            recipient_id=recipient.id,
            amount=amount,
        )
        transaction_repository.add_transaction(tx)
        return tx