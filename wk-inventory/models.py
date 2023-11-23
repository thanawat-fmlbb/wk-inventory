import os
from dotenv import load_dotenv
from typing import Optional
from sqlmodel import Relationship, SQLModel, Field, Session, create_engine, select

class Thing(SQLModel, table=True):
    # this is item_id
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    price: float
    stock: int = Field(default=0)
    
    # item_checks: List["ItemCheck"] = Relationship(back_populates="item")

class ItemCheck(SQLModel, table=True):
    # check_id
    id: Optional[int] = Field(default=None, primary_key=True)
    main_id: int
    item_id: int = Field(foreign_key="thing.id")
    quantity: int
    valid: bool = True

    # Relationship (allows for something like: item_check.item.name)
    item: Thing = Relationship(back_populates="item_checks")



load_dotenv()
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'password')
DB_HOSTNAME = os.environ.get('DB_HOSTNAME', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'postgres')

db_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOSTNAME}:{DB_PORT}/{DB_NAME}"
engine = create_engine(db_url)
SQLModel.metadata.create_all(engine)


def create_items(name: str, price: float, stock: int):
    with Session(engine) as session:
        item = Thing(name=name, price=price, stock=stock)
        session.add(item)
        session.commit()
        session.refresh(item)
        return item

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

def rollback():
    pass
