import os
from dotenv import load_dotenv
from typing import Optional, List
from sqlmodel import Relationship, SQLModel, Field, Session, create_engine, select

class Thing(SQLModel, table=True):
    # this is item_id
    id: Optional[int] = Field(default=None, primary_key=True)
    stock: int = Field(default=0)
    
    item_checks: List["ItemCheck"] = Relationship(back_populates="item")

class ItemCheck(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True) # check_id
    main_id: int
    item_id: int = Field(foreign_key="thing.id")
    quantity: int
    valid: bool = Field(default=True)

    # Relationship (allows for something like: item_check.item.name)
    item: Thing = Relationship(back_populates="item_checks")



load_dotenv()
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'password')
DB_HOSTNAME = os.environ.get('DB_HOSTNAME', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'inventory')

db_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOSTNAME}:{DB_PORT}/{DB_NAME}"
engine = create_engine(db_url)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def set_item_stock(item_id: int, stock: int):
    with Session(engine) as session:
        statement = select(Thing).where(Thing.id == item_id)
        try:
            item = session.exec(statement).one()
            item.stock = stock
        except Exception:
            item = Thing(id=item_id, stock=stock)
        finally:
            session.add(item)
            session.commit()
            session.refresh(item)


def create_item_check(main_id: int, item_id: int, quantity: int):
    with Session(engine) as session:
        statement = select(Thing).where(Thing.id == item_id)
        item = session.exec(statement).one()

        if item.stock < quantity:
            raise ValueError("Not enough stock")

        # update stock
        item.stock -= quantity
        
        # create item_check
        item_check = ItemCheck(main_id=main_id, item_id=item_id, quantity=quantity)
        
        session.add(item)
        session.add(item_check)
        session.commit()
        session.refresh(item_check)
        return item_check

def return_item(main_id: int):
    with Session(engine) as session:
        # get item_check with main_id
        statement = select(ItemCheck).where(ItemCheck.main_id == main_id).where(ItemCheck.valid == True)
        item_check = session.exec(statement).one()
        
        # invalidate item_check
        item_check.valid = False

        # return item to stock
        statement = select(Thing).where(Thing.id == item_check.item_id)
        item = session.exec(statement).one()
        item.stock += item_check.quantity

        session.add(item)
        session.add(item_check)
        session.commit()
        session.refresh(item_check)
        return item_check
