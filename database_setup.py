import os
import sys
from sqlalchemy import Column, Integer, ForeignKey, String, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm	import relationship
from sqlalchemy import create_engine

Base = declarative_base()

#Create table as class to store Item Categories
class Category(Base):
	__tablename__='category'

	name = Column(String(80), nullable = False)
	id = Column(Integer, primary_key = True)

#Define property to return object in serializable format. 	
	@property
	def serialize(self):
		return {
			'name': self.name,
			'id': self.id
		}


#Create table as class to store items.
class Item(Base):
	__tablename__='item'

	name = Column(String(80), nullable = False)
	id = Column(Integer, primary_key = True)
	description = Column(String)
	category_id = Column(Integer, ForeignKey('category.id'))
	category = relationship(Category)

	#Define property to return object in serializable format
	@property
	def serialize(self):

		return {
			'description': self.description,
			'category_id': self.category_id,
			'id': self.id,
			'name': self.name,
		}

engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.create_all(engine)
