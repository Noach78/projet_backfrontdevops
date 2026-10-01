from datetime import datetime
from abc import ABC, abstractmethod
from uuid import uuid4

class Beneficiary:
    def __init__(self, owner_id: int, name: str, account_id: int):
        self.id = uuid4().int
        self.owner_id = owner_id
        self.name = name
        self.account_id = account_id
        self.added_at = datetime.now()

class BeneficiaryRepository(ABC):
    def __init__(self):
        self.beneficiaries = []

    @abstractmethod
    def add_beneficiary(self, beneficiary: Beneficiary):
        pass

    @abstractmethod
    def find_beneficiary(self, beneficiary_id: int):
        pass

class InMemoryBeneficiaryRepository(BeneficiaryRepository):
    def add_beneficiary(self, beneficiary: Beneficiary):
        self.beneficiaries.append(beneficiary)

    def find_beneficiary(self, beneficiary_id: int):
        for beneficiary in self.beneficiaries:
            if beneficiary.id == beneficiary_id:
                return beneficiary
        return None