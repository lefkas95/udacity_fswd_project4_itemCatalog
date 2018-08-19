#!/usr/bin/env python3

from flask import Flask, render_template, request
from flask import redirect, jsonify, url_for, flash

from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User

from flask import session as login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

# Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    code = request.data

    try:
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('User is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['provider'] = 'google'
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # Check if user exists, otherwise create new one
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
    output += ' " style = "width: 300px; height: 300px;border-radius:'
    +' 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke'
    + '?token=%s' % login_session['access_token']

    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        response = make_response(
            json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showCategories'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showCategories'))


# JSON endpoints
@app.route('/api/categories')
def categoriesJSON():
    session = DBSession()
    categories = session.query(Category).all()
    return jsonify(categories=[r.serialize for r in categories])


@app.route('/api/categories/<string:category_name>/items')
def itemsJSON(category_name):
    session = DBSession()
    category = session.query(Category).filter_by(name=category_name).one()
    items = session.query(Item).filter_by(category_id=category.id)
    return jsonify(items=[r.serialize for r in items])


@app.route('/api/categories/<string:category_name>/items/<string:item_name>')
def itemJSON(category_name, item_name):
    session = DBSession()
    item = session.query(Item).filter_by(name=item_name).one()
    return jsonify(item=item.serialize)

# APIs to see and manipulate catalog items


# Show all categories and the most recent items
@app.route('/')
def showCategories():
    session = DBSession()
    categories = session.query(Category).order_by(asc(Category.name))
    # TODO: limit to 6 items
    items = session.query(Item).order_by(desc(Item.id)).limit(6)
    return render_template(
        'dashboard.html',
        title="Latest Items",
        categories=categories,
        items=items,
        loggedIn=('username' in login_session))


# Show category
@app.route('/categories/<string:category_name>')
def showCategory(category_name):
    session = DBSession()
    categories = session.query(Category).order_by(asc(Category.name))
    category = session.query(Category).filter_by(name=category_name).one()
    items = session.query(Item).filter_by(
        category_id=category.id).order_by(asc(Item.name))

    return render_template(
        'dashboard.html',
        title=category.name + " Items (" + str(items.count()) + ")",
        categories=categories,
        items=items,
        loggedIn=('username' in login_session))


# Show item
@app.route('/categories/<string:category_name>/items/<int:item_id>')
def showItem(category_name, item_id):
    session = DBSession()
    item = session.query(Item).filter_by(id=item_id).one()
    return render_template(
        'showItem.html',
        item=item,
        loggedIn=('username' in login_session),
        allowedToEdit=isUserAuthorized(item.user.name))


# Create new item
@app.route('/item/new/', methods=['GET', 'POST'])
def newItem():
    if 'username' not in login_session:
        return redirect('/login')
    session = DBSession()
    if request.method == 'POST':
        newItem = Item(
            name=request.form['name'],
            description=request.form['description'],
            category_id=request.form['category'],
            user_id=login_session['user_id'])
        session.add(newItem)
        session.commit()
        flash('New Item %s Successfully Created' % (newItem.name))
        return redirect(url_for('showCategories'))
    else:
        categories = session.query(Category).order_by(asc(Category.name))
        return render_template(
            'newitem.html',
            categories=categories,
            loggedIn=('username' in login_session))


# Edit item
@app.route(
    '/categories/<string:category_name>/items/<int:item_id>/edit',
    methods=['GET', 'POST'])
def editItem(category_name, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    session = DBSession()
    categories = session.query(Category).order_by(asc(Category.name))
    editedItem = session.query(Item).filter_by(id=item_id).one()
    if login_session['user_id'] != editedItem.user_id:
        return "<script>function myFunction() "
        + "{alert('You are not authorized to edit this item.');}"
        + "</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['category']:
            editedItem.category_id = request.form['category']
        session.add(editedItem)
        session.commit()
        flash('Item Successfully Edited')
        return redirect(url_for('showCategories'))
    else:
        return render_template(
            'edititem.html',
            categories=categories,
            item=editedItem,
            loggedIn=('username' in login_session))


# Delete item
@app.route(
    '/categories/<string:category_name>/items/<int:item_id>/delete',
    methods=['GET', 'POST'])
def deleteItem(category_name, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    session = DBSession()
    itemToDelete = session.query(Item).filter_by(id=item_id).one()
    if login_session['user_id'] != itemToDelete.user_id:
        return "<script>function myFunction() "
        + "{alert('You are not authorized to delete this item.');}"
        + "</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Menu Item Successfully Deleted')
        return redirect(url_for('showCategories'))
    else:
        return render_template(
            'deleteItem.html',
            item=itemToDelete,
            loggedIn=('username' in login_session))


# Helpers

def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session = DBSession()
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    session = DBSession()
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        session = DBSession()
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


def isUserAuthorized(name):
    if 'username' in login_session:
        return (login_session['username'] == name)
    return False


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
