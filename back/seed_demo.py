"""Replace the local SQLite data with a ready-to-use demo banking dataset.

Run from the back directory with: .venv/Scripts/python.exe seed_demo.py
Demo password for every user: Demo2026!
"""

from datetime import datetime, timedelta, timezone
import random

from passlib.hash import bcrypt
from sqlmodel import Session, SQLModel, create_engine, delete

from classes.account import Account
from classes.beneficiary import Beneficiary
from classes.transaction import Transaction
from classes.user import User


engine = create_engine("sqlite:///database.db", connect_args={"check_same_thread": False})

# Repeatable, varied 13-digit identifiers for a stable demo dataset.
_id_rng = random.Random(1954782466354)
_used_ids: set[int] = set()


def new_demo_id() -> int:
    while True:
        value = _id_rng.randrange(1_000_000_000_000, 10_000_000_000_000)
        if value not in _used_ids:
            _used_ids.add(value)
            return value


PEOPLE = [
    (new_demo_id(), "Alice Martin", "alice.martin@demo.fr"),
    (new_demo_id(), "Karim Bernard", "karim.bernard@demo.fr"),
    (new_demo_id(), "Emma Dubois", "emma.dubois@demo.fr"),
    (new_demo_id(), "Lucas Thomas", "lucas.thomas@demo.fr"),
    (new_demo_id(), "Ines Robert", "ines.robert@demo.fr"),
    (new_demo_id(), "Hugo Richard", "hugo.richard@demo.fr"),
    (new_demo_id(), "Jade Petit", "jade.petit@demo.fr"),
    (new_demo_id(), "Noah Durand", "noah.durand@demo.fr"),
    (new_demo_id(), "Lea Leroy", "lea.leroy@demo.fr"),
    (new_demo_id(), "Adam Moreau", "adam.moreau@demo.fr"),
    (new_demo_id(), "Chloe Simon", "chloe.simon@demo.fr"),
    (new_demo_id(), "Ethan Laurent", "ethan.laurent@demo.fr"),
]

# Two users have three accounts; the other ten have two each.
ACCOUNT_OWNERS = [
    PEOPLE[0][0], PEOPLE[0][0], PEOPLE[0][0], PEOPLE[1][0], PEOPLE[1][0],
    PEOPLE[2][0], PEOPLE[2][0], PEOPLE[3][0], PEOPLE[3][0],
    PEOPLE[4][0], PEOPLE[4][0], PEOPLE[5][0], PEOPLE[5][0],
    PEOPLE[6][0], PEOPLE[6][0], PEOPLE[7][0], PEOPLE[7][0],
    PEOPLE[8][0], PEOPLE[8][0], PEOPLE[9][0], PEOPLE[9][0],
    PEOPLE[10][0], PEOPLE[10][0], PEOPLE[11][0], PEOPLE[11][0], PEOPLE[11][0],
]


def seed_demo_database() -> None:
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        previous = {
            "users": len(session.exec(select(User)).all()),
            "accounts": len(session.exec(select(Account)).all()),
            "transactions": len(session.exec(select(Transaction)).all()),
            "beneficiaries": len(session.exec(select(Beneficiary)).all()),
        }

        # Delete dependent rows first so this also works if foreign keys are enabled.
        for model in (Beneficiary, Transaction, Account, User):
            session.exec(delete(model))
        session.commit()

        password_hash = bcrypt.hash("Demo2026!")
        session.add_all(
            User(id=user_id, name=name, email=email, hashed_password=password_hash)
            for user_id, name, email in PEOPLE
        )

        now = datetime.now(timezone.utc)
        accounts = []
        balances = {}
        for index, owner_id in enumerate(ACCOUNT_OWNERS):
            account_id = new_demo_id()
            starting_balance = 1200 + (index * 137 % 6800)
            account = Account(
                id=account_id,
                user_id=owner_id,
                sold=starting_balance,
                date_created=now - timedelta(days=400 - index * 9),
            )
            accounts.append(account)
            balances[account_id] = starting_balance
        session.add_all(accounts)
        session.flush()

        # Seed transfers and update both balances so the ledger matches each balance.
        transfer_pairs = [
            (0, 3, 250), (3, 6, 180), (6, 9, 320), (9, 12, 150),
            (12, 15, 410), (15, 18, 275), (18, 21, 190), (21, 24, 360),
            (24, 1, 520), (1, 4, 125), (4, 7, 240), (7, 10, 330),
            (10, 13, 210), (13, 16, 390), (16, 19, 170), (19, 22, 450),
            (22, 25, 300), (25, 2, 225), (2, 5, 480), (5, 8, 160),
            (8, 11, 275), (11, 14, 350), (14, 17, 200), (17, 20, 425),
            (20, 23, 315), (23, 0, 275), (0, 6, 125), (3, 9, 220),
            (12, 18, 175), (15, 21, 260), (24, 4, 140), (7, 13, 185),
            (10, 16, 290), (19, 25, 230), (22, 2, 340), (5, 17, 155),
        ]
        for index, (source_index, recipient_index, amount) in enumerate(transfer_pairs):
            source_id = accounts[source_index].id
            recipient_id = accounts[recipient_index].id
            # The chosen demo amounts are small relative to opening balances.
            balances[source_id] -= amount
            balances[recipient_id] += amount
            session.add(
                Transaction(
                    id=new_demo_id(),
                    source_id=source_id,
                    recipient_id=recipient_id,
                    amount=amount,
                    created_at=now - timedelta(days=35 - index, hours=index % 8),
                    is_cancelled=False,
                )
            )

        for account in accounts:
            account.sold = balances[account.id]

        # Give each profile two external beneficiaries, pointing to real other users.
        account_by_owner = {}
        for account in accounts:
            account_by_owner.setdefault(account.user_id, []).append(account)

        for index, (owner_id, _name, _email) in enumerate(PEOPLE):
            first_recipient = PEOPLE[(index + 1) % len(PEOPLE)][0]
            second_recipient = PEOPLE[(index + 4) % len(PEOPLE)][0]
            for offset, recipient_id in enumerate((first_recipient, second_recipient)):
                recipient_account = account_by_owner[recipient_id][0]
                session.add(
                    Beneficiary(
                        id=new_demo_id(),
                        owner_id=owner_id,
                        name=PEOPLE[(index + (1 if offset == 0 else 4)) % len(PEOPLE)][1],
                        account_id=recipient_account.id,
                        added_at=now - timedelta(days=60 - index - offset),
                    )
                )

        session.commit()
        print(f"Base nettoyée ({previous}) puis remplie dans {engine.url.database}.")
        print(
            f"Jeu de démo : {len(PEOPLE)} utilisateurs, {len(accounts)} comptes, "
            f"{len(transfer_pairs)} virements et {len(PEOPLE) * 2} bénéficiaires."
        )
        print("Mot de passe commun : Demo2026!")
        print("Connexion : alice.martin@demo.fr (ou toute autre adresse @demo.fr listée dans le script).")


if __name__ == "__main__":
    from sqlmodel import select

    seed_demo_database()
