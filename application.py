from flask import Flask, render_template, url_for, redirect, request, jsonify

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Category, Item, Base

app = Flask(__name__)


engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine


DBSession = sessionmaker(bind = engine)
session = DBSession()

@app.route('/')
@app.route('/categories/')
def showCategories():
	categories = session.query(Category).all()
	return render_template('categories.html', categories = categories)

@app.route('/category/new/', methods = ['GET', 'POST'])
def newCategory():
	if request.method == 'POST':
		new = Category(name = request.form['name'])
		session.add(new)
		session.commit()
		return redirect(url_for('showCategories'))
	else:
		return render_template('newCategory.html')

@app.route('/category/<int:category_id>/edit/', methods = ['GET','POST'])
def editCategory(category_id):
	edittedCategory = session.query(Category).filter_by(id=category_id).one()
	if request.method == 'POST':
		if request.form['name']:
			edittedCategory.name = request.form['name']
		session.add(edittedCategory)
		session.commit()
		return redirect(url_for('showCategories'))
	else:
		return render_template('editCategory.html', category_id = category_id,
			i = edittedCategory)

@app.route('/category/<int:category_id>/delete/', methods = ['GET', 'POST'])
def deleteCategory(category_id):
	categoryToDelete = session.query(Category).filter_by(id=category_id).one()
	if request.method == 'POST':
		session.delete(categoryToDelete)
		session.commit()
		return redirect(url_for('showCategories'))
	else:
		return render_template('deleteCategory.html',
			category_id = category_id, i = categoryToDelete)

@app.route('/category/<int:category_id>/')
@app.route('/category/<int:category_id>/item/')
def showItems(category_id):
	category = session.query(Category).filter_by(id=category_id).one()
	item = session.query(Item).filter_by(category_id=category_id)
	return render_template('showItems.html', category=category,
		item=item)

@app.route('/category/<int:category_id>/item/new/', methods = ['GET', 'POST'])
def newItem(category_id):
	category = session.query(Category).filter_by(id=category_id).one()
	if request.method == 'POST':
		newItem = Item(name=request.form['name'],
			description=request.form['description'],
			category_id=category_id)
		session.add(newItem)
		session.commit()
		return redirect(url_for('showItems', category_id=category_id))
	else:
		return render_template('newItem.html', category_id=category_id)

@app.route('/category/<int:category_id>/item/<int:item_id>/edit/',
	methods = ['GET','POST'])
def editItem(category_id, item_id):
	edittedItem = session.query(Item).filter_by(id=item_id).one()
	if request.method == 'POST':
		if request.form['name']:
			edittedItem.name = request.form['name']
		if request.form['description']:
			edittedItem.description = request.form['description']
		session.add(edittedItem)
		session.commit()
		return redirect(url_for('showItems', category_id = category_id))
	else:
		return render_template('editItem.html', category_id=category_id,
			item = edittedItem)

@app.route('/category/<int:category_id>/item/<int:item_id>/delete/',
	methods = ['GET', 'POST'])
def deleteItem(category_id, item_id):
	itemToDelete = session.query(Item).filter_by(id=item_id).one()
	if request.method == 'POST':
		session.delete(itemToDelete)
		session.commit()
		return redirect(url_for('showItems', category_id=category_id))
	else:
		return render_template('deleteItem.html', category_id=category_id,
			item=itemToDelete)

@app.route('/categories/JSON/')
def showCategoriesJSON():
	categories = session.query(Category).all()
	return jsonify(Category=[i.serialize for i in categories])

@app.route('/category/<int:category_id>/item/JSON/')
def showItemsJSON(category_id):
	items = session.query(Item).filter_by(category_id=category_id)
	return jsonify(Item = [i.serialize for i in items])

@app.route('/category/<int:category_id>/item/<int:item_id>/JSON/')
def showSingleItemJSON(category_id, item_id):
	item = session.query(Item).filter_by(id=item_id).one()
	return jsonify(Item = item.serialize)









































if __name__ == '__main__':
	app.debug = True
	app.run(host = '0.0.0.0', port = 8000)

