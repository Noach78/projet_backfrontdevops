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

class User():
    def __init__(self, name: str):
        self.name = name

    def create_account(self):
        self.account = Account(10)

    def get_account(self):
        return self.account

class UserCreate(BaseModel):
    name: str

users = []

def find_user(name: str):
    for user in users:
        if user.name == name:
            return user
    return None

def transfer(source_name:User, recipient_name:User, amount : int):
    source_name.get_account().debit(amount)
    recipient_name.get_account().credit(amount)

@app.get("/users")
def get_users():
    return [{"name": user.name, "sold": user.account.sold} for user in users]

@app.get("/user/{name}")
def get_user(name: str):
    for user in users:
        if user.name == name:
            return {"name": user.name, "sold": user.account.sold}
    return {"error": "User not found"}
    

@app.post("/user")
def create_user(user_data: UserCreate):
    user = User(user_data.name)
    user.create_account()
    users.append(user)
    return {"message": f"User {user_data.name} created successfully."}

@app.post("/transfer/{source_name}/{recipient_name}/{amount}")
def transfer_endpoint(source_name: str, recipient_name: str, amount: int):
    source = find_user(source_name)
    recipient = find_user(recipient_name)
    if source is None or recipient is None:
        return {"error": "User not found"}
    transfer(source, recipient, amount)
    return {
        "source_sold": source.account.sold,
        "recipient_sold": recipient.account.sold,
    }