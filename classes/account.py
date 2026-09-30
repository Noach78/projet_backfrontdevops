import datetime

class Account():
    def __init__(self, user_id: int, sold: int):
        self.id = int(datetime.now().timestamp() * 1000)
        self.user_id = user_id
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