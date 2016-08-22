from flask import Flask, render_template, url_for, redirect, request, jsonify
from flask import flash

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Category, Item, User, Base

from flask import session as login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
import sys
import logging

app = Flask(__name__)

app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.ERROR)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

APPLICATION_NAME = "Catalog App"

# Connect to DB
engine = create_engine('sqlite:///itemcatalogwithusers.db')
Base.metadata.bind = engine


DBSession = sessionmaker(bind=engine)
session = DBSession()

# ALL OAUTH METHODS
# Create anti-forgery state


@app.route('/')
@app.route('/login')
def showLogin():
    # Create a state token (string) of random uppercase chars and digits
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)
# Route and method to add Google Login


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain Auth Code
    code = request.data

    try:
        # Upgrade the auth code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)

    except FlowExchangeError:
        response = make_response(json.dumps
                                 ('Failed to upgrade the autorization code.'),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # If there was an error in the access token info, abort
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps
                                 ("Token's User ID doesn't match given User ID"),
                                 401)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps
                         ("Token's client ID does not match apps."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps
                                 ('Current User is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'

    # Store access token in the session for later use.
    login_session['provider'] = 'google'
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    #Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # See if user exists, if it doesn't, create new.
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1> Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;">'
    flash("You are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# Route and method to add FB Login
@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token recieved %s" % access_token
    # Exchange client token for long-lived server side token.
    app_id = json.loads(open('fb_client_secrets.json', 'r').
                        read())['web']['app_id']
    app_secret = json.loads(open('fb_client_secrets.json', 'r').
                            read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.4/me"
    # Strip expire rag from access token
    token = result.split("&")[0]

    url = 'https://graph.facebook.com/v2.4/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # Get user picture
    url = 'https://graph.facebook.com/v2.4/me/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    # Check if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px">'
    flash("Now logged in as %s" % login_session['username'])
    return output


# G DISCONNECT - Revoke a current users token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user
    access_token = login_session.get('access_token')
    print 'In gdisconnect access token is %s' % access_token
    print 'Username is:'
    print login_session['username']

    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Execute HTTP GET request to revoke current token.
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's session.
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(
            json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


# FB DISCONNECT - Revoke a current users token and reset their login session.
@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (
        facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]

    del login_session['user_id']
    del login_session['facebook_id']
    del login_session['username']
    del login_session['email']
    del login_session['picture']
    del login_session['provider']
    return "You have been logged out!"


# Master Disconnect function to call G/FB Disconnect as needed
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()

        if login_session['provider'] == 'facebook':
            fbdisconnect()

        flash("You have successfully logged out!")
        return redirect(url_for('showCategories'))

    else:
        flash("You were never logged in!")
        return redirect(url_for('showCategories'))


# ALL CRUD METHODS
# Create a route and method to show 'ALL' categories
@app.route('/categories/')
def showCategories():
    categories = session.query(Category).all()
    # Show public page to users not logged in.
    if 'username' not in login_session:
        return render_template('publiccategories.html',
                               categories=categories)
    else:
        return render_template('categories.html', categories=categories)


# Create a route and method to 'ADD/CREATE' a new category.
@app.route('/category/new/', methods=['GET', 'POST'])
def newCategory():
    # Only authorized users can add new categories.
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        new = Category(name=request.form['name'],
                       user_id=login_session['user_id'])
        session.add(new)
        session.commit()
        return redirect(url_for('showCategories'))
    else:
        return render_template('newCategory.html')


# Create a route and method to 'EDIT' a category.
@app.route('/category/<int:category_id>/edit/', methods=['GET', 'POST'])
def editCategory(category_id):
    # Check if user is logged in.
    if 'username' not in login_session:
        return redirect('/login')

    edittedCategory = session.query(Category).filter_by(id=category_id).one()

    # Check if user is owner of category.
    if edittedCategory.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to edit this category. Please create your own category in order to edit.');}</script><body onload='myFunction''>"
        return redirect(url_for('showCategories'))
    # If user is owner, edit request will be accepted.
    if request.method == 'POST':
        if request.form['name']:
            edittedCategory.name = request.form['name']
        session.add(edittedCategory)
        session.commit()
        return redirect(url_for('showCategories'))
    else:
        return render_template('editCategory.html', category_id=category_id,
                               i=edittedCategory)


# Create a route and method to 'DELETE' a category.
@app.route('/category/<int:category_id>/delete/', methods=['GET', 'POST'])
def deleteCategory(category_id):
    # Check if user is logged in.
    if 'username' not in login_session:
        return redirect('/login')

    categoryToDelete = session.query(Category).filter_by(id=category_id).one()

    # Check if user is owner of category.
    if categoryToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to delete this category. Please create your own category in order to delete.');}</script><body onload='myFunction()''>"
        return redirect(url_for('showCategories'))

    # If user is owner, Delete request will be accepted.
    if request.method == 'POST':
        session.delete(categoryToDelete)
        session.commit()
        return redirect(url_for('showCategories'))
    else:
        return render_template('deleteCategory.html',
                               category_id=category_id, i=categoryToDelete)


# Create a route and method to show ALL items in a category.
@app.route('/category/<int:category_id>/')
@app.route('/category/<int:category_id>/item/')
def showItems(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    item = session.query(Item).filter_by(category_id=category_id)
    creator = getUserInfo(category.user_id)

    # Check if user is logged in or if user is owner.
    if 'username' not in login_session or creator.id != login_session['user_id'
                                                                      ]:
        return render_template('showPublicItems.html', category=category,
                               item=item, creator=creator)
    else:
        return render_template('showItems.html', category=category,
                               item=item, creator=creator)


# Create a route and method to show ONE item in the category.
@app.route('/category/<int:category_id>/item/<int:item_id>/')
def showSingleItem(category_id, item_id):
    singleItem = session.query(Item).filter_by(id=item_id).one()
    category = session.query(Category).filter_by(
        id=singleItem.category_id).one()
    creator = getUserInfo(category.user_id)
    # Check if user is logged in or user is owner.
    if 'username' not in login_session or creator.id != login_session[
            'user_id']:
        return render_template('showPublicSingleItem.html', item=singleItem,
                               category=category)
    else:
        return render_template('showSingleItem.html', item=singleItem,
                               category=category)


# Create a route and mehtod to 'ADD/CREATE' a new item record.
@app.route('/category/<int:category_id>/item/new/', methods=['GET', 'POST'])
def newItem(category_id):
    # Check if user is logged in.
    if 'username' not in login_session:
        return redirect('/login')

    category = session.query(Category).filter_by(id=category_id).one()
    # Check if user is cateogory owner.
    # Only owners can add items to categories.
    if login_session['user_id'] != category.user_id:
        return "<script>function myFunction() {alert('You are not authorized to add items to this category. Please create your own category to add items.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        newItem = Item(name=request.form['name'],
                       description=request.form['description'],
                       category_id=category_id, user_id=login_session[
                       'user_id'])
        session.add(newItem)
        session.commit()
        return redirect(url_for('showItems', category_id=category_id))
    else:
        return render_template('newItem.html', category_id=category_id)


# Create a route and method to 'EDIT' an item record.
@app.route('/category/<int:category_id>/item/<int:item_id>/edit/',
           methods=['GET', 'POST'])
def editItem(category_id, item_id):
    # Check if user is logged in
    if 'username' not in login_session:
        return redirect('/login')

    edittedItem = session.query(Item).filter_by(id=item_id).one()
    category = session.query(Category).filter_by(id=category_id).one()
    # Check if user is category owner.
    if login_session['user_id'] != category.user_id:
        return "<script>function myFunction() {alert('You are not authorized to edit items in this category. Please create your own category in order to edit items.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            edittedItem.name = request.form['name']
        if request.form['description']:
            edittedItem.description = request.form['description']
        session.add(edittedItem)
        session.commit()
        return redirect(url_for('showItems', category_id=category_id))
    else:
        return render_template('editItem.html', category_id=category_id,
                               item=edittedItem)


# Create a route and method to 'DELETE' an item record.
@app.route('/category/<int:category_id>/item/<int:item_id>/delete/',
           methods=['GET', 'POST'])
def deleteItem(category_id, item_id):
    # Check if user is logged in.
    if 'username' not in login_session:
        return redirect('/login')

    itemToDelete = session.query(Item).filter_by(id=item_id).one()
    category = session.query(Category).filter_by(id=category_id).one()
    # Check if user is category owner.
    if login_session['user_id'] != category.user_id:
        return "<script>function myFunction() {alert('You are not authorized to delete items from this category. Please create your own category to delete items.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        return redirect(url_for('showItems', category_id=category_id))
    else:
        return render_template('deleteItem.html', category_id=category_id,
                               item=itemToDelete)


# ALL API ENDPOINT JSON AND XML-ATOM
# Create a JSON endpoint for all categories
@app.route('/categories/JSON/')
def showCategoriesJSON():
    categories = session.query(Category).all()
    return jsonify(Category=[i.serialize for i in categories])


# Create a JSON endpoint for items in a single category
@app.route('/category/<int:category_id>/item/JSON/')
def showItemsJSON(category_id):
    items = session.query(Item).filter_by(category_id=category_id)
    return jsonify(Item=[i.serialize for i in items])


# Create a JSON endpoint for a single item
@app.route('/category/<int:category_id>/item/<int:item_id>/JSON/')
def showSingleItemJSON(category_id, item_id):
    item = session.query(Item).filter_by(id=item_id).one()
    return jsonify(Item=item.serialize)


# Create an Atom format XML endpoint for all categories
@app.route('/categories/XML/')
def showCategoriesXML():
    categories = session.query(Category).all()
    return render_template('categories.xml', categories=categories)


# Create an Atom format XML endpoint for all items in one category
@app.route('/category/<int:category_id>/item/XML/')
def showItemsXML(category_id):
    items = session.query(Item).filter_by(category_id=category_id)
    category = session.query(Category).filter_by(id=category_id).one()
    return render_template('items.xml', items=items, category=category)


# Create an Atom format XML endpoint for a single item
@app.route('/category/<int:category_id>/item/<int:item_id>/XML/')
def showSingleItemXML(category_id, item_id):
    item = session.query(Item).filter_by(id=item_id).one()
    return render_template('singleItem.xml', item=item)


# ALL USER INFO METHODS
# Returns a user id for a registered user email in DB
def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# Gets user info associate with a user id
def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


# Create user in database from data in login_session
def createUser(login_session):
    newUser = User(name=login_session['username'],
                   email=login_session['email'],
                   picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
