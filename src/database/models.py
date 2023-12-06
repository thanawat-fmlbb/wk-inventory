from typing import Optional, List
from sqlmodel import Relationship, SQLModel, Field, Session, create_engine, select
from .engine import get_engine

engine = get_engine()

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


def create_item_check(main_id: int, item_id: int, quantity: int) -> ItemCheck:
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

def return_item(main_id: int) -> Optional[ItemCheck]:
    with Session(engine) as session:
        # get item_check with main_id
        statement = select(ItemCheck).where(ItemCheck.main_id == main_id).where(ItemCheck.valid == True)
        try:
            item_check = session.exec(statement).one()
        except Exception:
            return None
        
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

def setup():
    with Session(engine) as session:
        item = session.get(Thing, 1)
        if item is None:
            item = Thing(id=1)
        item.stock = 999999
        session.add(item)
        session.commit()

        item = session.get(Thing, 2)
        if item is None:
            item = Thing(id=2)
        item.stock = 0
        session.add(item)
        session.commit()

        item = session.get(Thing, 3)
        if item is None:
            item = Thing(id=3)
        item.stock = 10
        session.add(item)
        session.commit()
