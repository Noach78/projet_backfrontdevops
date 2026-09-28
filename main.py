from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Account():
    def __init__(self, sold: int):
        self.sold = sold

    def credit(self, amount: int):
        self.sold += amount
        return self.sold

    def debit(self, amount: int):
        if amount > self.sold:
            raise ValueError("Insufficient funds")
        self.sold -= amount
        return self.sold

    def show_sold(self):
        print(self.sold)    

def transfer(source : Account, recipient : Account, amount : int):
    source.debit(amount)
    recipient.credit(amount)

@app.post("/transfer/{amount}")
def transfer_endpoint(amount: int):
    source = Account(10)  
    recipient = Account(10)
    transfer(source, recipient, amount)
    return {
        "source_sold": source.sold,
        "recipient_sold": recipient.sold,
    }
    
    