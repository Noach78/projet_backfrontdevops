from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Compte(BaseModel):
    nom: str
    solde: int

comptes = [Compte(nom="A", solde=10), Compte(nom="B", solde=0)]

def virement(source: Compte, destitation: Compte, montant:int):
    if verifierVirement(source, montant):
        source.solde -= montant
        destitation.solde += montant

def verifierVirement(source: Compte, montant:int):
    if montant <= source.solde:
        return True
    return False

virement(comptes[0], comptes[1], 5)
virement(comptes[0], comptes[1], 100)
print(comptes)
    
    