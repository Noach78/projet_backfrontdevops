from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

comptes = {"A": 10, "B": 0}

def virement(source: str, destitation:str, montant:int):
    if verifierVirement(source, montant):
        comptes[source] -= montant
        comptes[destitation] += montant

def verifierVirement(source: str, montant:int):
    if montant <= comptes[source]:
        return True
    return False

virement("A", "B", 5)
virement("A", "B", 100)
print(comptes)
    
    