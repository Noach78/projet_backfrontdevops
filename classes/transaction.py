from datetime import datetime
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from classes.account import Account

class Transaction:
    def __init__(self, source: "Account", recipient: "Account", amount: int):
        self.id = int(datetime.now().timestamp() * 1000)
        self.source = source
        self.recipient = recipient
        self.amount = amount
        self.created_at = datetime.now()
        self.is_cancelled = False

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