from sqlalchemy import create engine
from sqlalchemy.orm import sessionmaker

from database_setup import Category, Item, Base

engine = create_engine('sqlite:///itemcatalog.db')

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

#Items for Sleeping Bags
category1 = Category(name = 'Sleeping Bags')

session.add(category1)
session.commit()

item1 = Item(name = 'Sierra Designs Backcountry Bed', description = 'This remarkable 3-season sleeping bag has an integrated comforter and no zippers for a unique outdoor sleeping experience spring through fall.', category = category1)
session.add(item1)
session.commit()

item2 = Item(name = 'Kelty Cosmic Down 21', description = 'This lightweight sleeping bag is insulated with water-resistant DriDown that resists moisture, has exceptional loft and compresses down small, making it a great bag for backpacking spring thru fall.', category = category1)
session.add(item2)
session.commit()

category2 = Category(name = 'Tents')
session.add(category2)
session.commit()

item1 = Item(name = 'Marmot Tungsten 3P', description = 'With room for a comfortable night''s sleep, this 3-person, 3-season backpacking tent incorporates an intelligent design, durable fabrics and weather-enduring features to complement life on the trail.', category = category2)
session.add(item1)
session.commit()

item2 = Item(name = 'Mountain Hardware Shifter 2 Tent', description = 'This 3-season, 2-person tent''s innovative, switch-pitching design allows you to choose different configurations to meet changing conditions while backpacking.', category = category2)
session.add(item2)
session.commit()

category3 = Category(name = 'Backpacks')
session.add(category3)
session.commit()

item1 = Item(name = 'Gregory Baltoro 65', description = 'Winner of Backpacker magazine''s 2015 Editors'' Choice Gold Award, this multiday pack with customizable suspension excels equally on long winter weekends and extended trips with a minimalist gear list.', category = category3)
session.add(item1)
session.commit()

item2 = Item(name = 'Mountain Hardware Fluid 32', description = 'The perfect balance of lightweight, stability and volume. This pack moves easily from all-day hikes to fast and light overnight trips. Well-ventilated HardWave suspension keeps loads comfortably stable. Includes an easy access hydration sleeve with convenient tube exits that you can route high or low, left or right.', category = category3)
session.add(item2)
session.commit()

category4 = Category(name = 'Shoes & Boots')
session.add(category4)
session.commit()

item1 = Item(name = 'Merrell Moab Mid', description = 'The men''s Merrell Moab Mid waterproof light hikers work hard on all your warm- and wet-weather active endeavors.', category = category4)
session.add(item1)
session.commit()

item2 = Item(name = 'La Sportiva Miura VS', description = 'Slip into the La Sportiva Muira VS rock shoes, cinch the hook-and-loop straps and start up a steep climb with great control. The shoes excel when you''re edging or sticking your toes in tiny pockets.', category = category4)
session.add(item2)
session.commit()

category5 = Category(name = 'Jackets & Coats')
session.add(category5)
session.commit()

item1 = Item(name = 'Mountain Hardware Ghost Whisperer', description = 'Incredibly ultralight, this full-featured men''s jacket with Q.Shield™ 800-fill-power down resists moisture and retains critical loft even when wet.', category = category5)
session.add(item1)
session.commit()

item2 = Item(name = 'Patagonia Adze Hybrid', description = 'For high-energy activity in cold, windy conditions, the Adze Hybrid Jacket combines fleece-lined Polartec® Windbloc® stretch-woven fabric with breathable and stretchy side panels for insulated protection without overheating.', category = category5)
session.add(item2)
session.commit()

print "added categories and item!!"