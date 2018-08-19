#!/usr/bin/env python3

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Category, Base, Item, User

engine = create_engine('sqlite:///catalog.db')

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create dummy user
User1 = User(name="John Doe", email="john@doe.com",
             picture='')
session.add(User1)
session.commit()

# Create Categories
category1 = Category(name="Soccer")

session.add(category1)
session.commit()

category2 = Category(name="Basketball")

session.add(category2)
session.commit()

category3 = Category(name="Baseball")

session.add(category3)
session.commit()

category4 = Category(name="Football")

session.add(category4)
session.commit()

# Create Items for Soccer

item1 = Item(user=User1,
             name="Stick",
             description="A very fancy stick",
             category=category1)

session.add(item1)
session.commit()

item2 = Item(user_id=1,
             name="Soccer-Ball",
             description="A very fancy and round ball",
             category=category1)

session.add(item2)
session.commit()

item3 = Item(user_id=1,
             name="Triccot",
             description="I don't know if this is spelled correctly",
             category=category1)

session.add(item3)
session.commit()

# Create Items for Basketball

item4 = Item(
    user_id=1,
    name="Bat",
    description="A fat bat which is totally needed when playing Basketball",
    category=category2)

session.add(item4)
session.commit()

item5 = Item(user_id=1,
             name="Net",
             description="A basketball net",
             category=category2)

session.add(item5)
session.commit()

# Create Items for Baseball
item6 = Item(user_id=1,
             name="Baseball-Stick",
             description="A baseball stick",
             category=category3)

session.add(item6)
session.commit()

item7 = Item(user_id=1,
             name="Baseball",
             description="A baseball ball",
             category=category3)

session.add(item7)
session.commit()
# Create Items for Football
item8 = Item(user_id=1,
             name="Shoes",
             description="Perfect shoes for football",
             category=category4)

session.add(item8)
session.commit()

item9 = Item(user_id=1,
             name="Second lung",
             description="Just in case",
             category=category4)

session.add(item9)
session.commit()
print "added categories & items!"
