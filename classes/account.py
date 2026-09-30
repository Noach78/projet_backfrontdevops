from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from classes.transaction import Transaction, TransactionRepository

class Account():
    def __init__(self, user_id: int, sold: int, date_created: datetime = None):
        self.id = int(datetime.now().timestamp() * 1000)
        self.user_id = user_id
        self.sold = sold
        self.date_created = date_created or datetime.now()

    def get_user_id(self):
        return self.user_id

    def get_id(self):   
        return self.id

    def get_sold(self):
        return self.sold

    def get_date_created(self):
        return self.date_created

    def credit(self, amount: int):
        self.sold += amount
        return self.sold

    def debit(self, amount: int):
        if amount > self.sold:
            raise ValueError("Insufficient funds")
        self.sold -= amount
        return self.sold

class AccountRepository(ABC):
    def __init__(self):
        self.accounts = []

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
        tx = Transaction(source, recipient, amount)
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
        tx = Transaction(source, recipient, amount)
        transaction_repository.add_transaction(tx)
        return tx