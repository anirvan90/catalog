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
@app.route('/category/<int:category_id>/items/')
def showItems(category_id):
	category = session.query(Category).filter_by(id=category_id).one()
	item = session.query(Item).filter_by(category_id=category_id)
	return render_template('showItems.html', category=category,
		item=item)




if __name__ == '__main__':
	app.debug = True
	app.run(host = '0.0.0.0', port = 8000)
