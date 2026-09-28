from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

comptes = {"A": 10, "B": 0}

def virement(source: str, destitation:str, montant:int):
    comptes[source] -= montant
    comptes[destitation] += montant

virement("A", "B", 5)
print(comptes)