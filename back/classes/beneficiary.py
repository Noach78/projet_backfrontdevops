from datetime import datetime, timezone
from abc import ABC, abstractmethod
from uuid import uuid4
from sqlmodel import Field, SQLModel, Session, select

def new_id() -> int:
    return uuid4().int % (2**63 - 1)

class Beneficiary(SQLModel, table=True):
    id: int = Field(default_factory=new_id, primary_key=True)
    owner_id: int = Field(default=None)
    name: str = Field(default=None)
    account_id: int = Field(default=None)
    added_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BeneficiaryRepository(ABC):
    def __init__(self):
        self._beneficiaries = []

    @property
    def beneficiaries(self):
        return self._beneficiaries

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

class SQLBeneficiaryRepository(BeneficiaryRepository):
    def __init__(self, session: Session):
        super().__init__()
        self.session = session

    @property
    def beneficiaries(self):
        return self.session.exec(select(Beneficiary)).all()

    def add_beneficiary(self, beneficiary: Beneficiary):
        self.session.add(beneficiary)
        self.session.commit()
        self.session.refresh(beneficiary)

    def find_beneficiary(self, beneficiary_id: int):
        return self.session.get(Beneficiary, beneficiary_id)