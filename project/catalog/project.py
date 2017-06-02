from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Catagory, Item, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
from functools import wraps

app = Flask(__name__)

# Connect to Database and create database session
engine = create_engine('sqlite:///item_catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Item Catalog Application"

# decorator function to check for user login status



# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in login_session:
            return redirect(url_for('/login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.9/me"
    # strip expire tag from access token
    data = json.loads(result)
    token = 'access_token=' + data['access_token']


    url = 'https://graph.facebook.com/v2.9/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout,
    # let's strip out the information before the equals sign in our token
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    # Get user picture
    url = 'https://graph.facebook.com/v2.9/me/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
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
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    flash("Now logged in as %s" % login_session['username'])
    return output


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
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

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['gplus_id'] = gplus_id
    login_session['credentials'] = credentials.access_token

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

# DISCONNECT - Revoke a current user's token and reset their login_session


@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] != '200':
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        del login_session['gplus_id']
        del login_session['credentials']
        return "You have successfully been logged out."
# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        print login_session
        if login_session['provider'] == 'google':
            gdisconnect()
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have been successfully logged out.")
        return redirect(url_for('showCatagories'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showCatagories'))

# JSON APIs to view Restaurant Information
@app.route('/catagory/<int:catagory_id>/item/JSON')
def catagoryItemsJSON(catagory_id):
    catagory = session.query(Catagory).filter_by(id=catagory_id).one()
    items = session.query(Item).filter_by(
        catagory_id=catagory_id).all()
    return jsonify(Items=[i.serialize for i in items])


@app.route('/catagory/<int:catagory_id>/item/<int:item_id>/JSON')
def catagoryItemJSON(catagory_id, item_id):
    item = session.query(Item).filter_by(id=item_id).one()
    return jsonify(Item=item.serialize)


@app.route('/catagory/JSON')
def catagoriesJSON():
    catagories = session.query(Catagory).all()
    return jsonify(catagories=[r.serialize for r in catagories])

# Show all Catagories
@app.route('/')
@app.route('/catagory/')
def showCatagories():
    catagories = session.query(Catagory).order_by(asc(Catagory.name))
    items = session.query(Item).order_by(Item.id.desc())
    info = zip(catagories, items)
    c_count = session.query(Catagory).count()
    i_count = session.query(Item).count()
    catagories_more=[]
    items_more=[]
    if c_count > i_count:
        catagories_more = catagories[i_count:]
    elif c_count < i_count:
        items_more = items[c_count:]
    if 'username' not in login_session:
        return render_template('publiccatagories.html', info=info,
                                items=items_more, catagories=catagories_more)
    else:
        return render_template('catagories.html', info=info, items=items_more,
                                catagories=catagories_more,
                                username=login_session['username'])


# Create a new Catagory
@app.route('/catagory/new/', methods=['GET', 'POST'])
@login_required
def newCatagory():
    if request.method == 'POST':
        newCatagory = Catagory(
            name=request.form['name'], user_id=login_session['user_id'])
        flash('New Catagory %s Successfully Created' % newCatagory.name)
        session.add(newCatagory)
        session.commit()
        return redirect(url_for('showCatagories'))
    else:
        return render_template('newCatagory.html')

# Edit a Catagory

@app.route('/catagory/<int:catagory_id>/edit/', methods=['GET', 'POST'])
@login_required
def editCatagory(catagory_id):
    try:
        editedCatagory = session.query(Catagory).filter_by(id=catagory_id).one()
        if editedCatagory.user_id != login_session['user_id']:
            message = "You are not authorized to edit this catagory. "\
                      "Please create your own catagory in order to edit."
            return render_template("redirecting.html", message=message)
        if request.method == 'POST':
            if request.form['name']:
                editedCatagory.name = request.form['name']
                flash('Catagory %s Successfully Edited' % editedCatagory.name)
            return redirect(url_for('showCatagories'))
        else:
            return render_template('editCatagory.html', catagory=editedCatagory)
    except:
        message = "No such category!"
        return render_template("redirecting.html", message=message)


# Delete a Catagory
@app.route('/catagory/<int:catagory_id>/delete/', methods=['GET', 'POST'])
@login_required
def deleteCatagory(catagory_id):
    try:
        catagoryToDelete = session.query(
            Catagory).filter_by(id=catagory_id).one()
        if catagoryToDelete.user_id != login_session['user_id']:
            message = "You are not authorized to delete this catagory."\
                      "Please create your own catagory in order to delete."
            return render_template("redirecting.html", message=message)
        if request.method == 'POST':
            session.delete(catagoryToDelete)
            flash('%s Successfully Deleted' % catagoryToDelete.name)
            session.commit()
            return redirect(url_for('showCatagories', catagory_id=catagory_id))
        else:
            return render_template('deleteCatagory.html', catagory=catagoryToDelete)
    except:
        message = "No such category!"
        return render_template("redirecting.html", message=message)

# Show items for a Catagory
@app.route('/catagory/<int:catagory_id>/')
@app.route('/catagory/<int:catagory_id>/items/', methods=['GET', 'POST'])
def CatagoryItems(catagory_id):
    try:
        catagory = session.query(Catagory).filter_by(id=catagory_id).one()
        creator = getUserInfo(catagory.user_id)
        items = session.query(Item).filter_by(catagory_id=catagory_id).all()
        if 'username' not in login_session or creator.id != login_session['user_id']:
            return render_template('publicitems.html', items=items,
                                    catagory=catagory, creator=creator)
        else:
            return render_template('catagoryItems.html', catagory_id=catagory_id,
                                    items=items, catagory=catagory,creator=creator)
    except:
        message = "No such category!"
        return render_template("redirecting.html", message=message)

# Create a new catagory item
@app.route('/catagory/<int:catagory_id>/item/new/', methods=['GET', 'POST'])
@login_required
def newCatagoryItem(catagory_id):
    try:
        catagory = session.query(Catagory).filter_by(id=catagory_id).one()
        if request.method == 'POST':
            newItem = Item(name=request.form['name'],
                           description=request.form['description'],
                           price=request.form['price'],catagory_id=catagory_id,
                           user_id=login_session['user_id'])
            session.add(newItem)
            session.commit()
            flash('New Catagory Item %s Successfully Created' % (newItem.name))
            return redirect(url_for('CatagoryItems', catagory_id=catagory_id))
        else:
            return render_template('newCatagoryItem.html', catagory_id=catagory_id)
    except:
        message = "No such category!"
        return render_template("redirecting.html", message=message)


# Edit a catagory item
@app.route('/catagory/<int:catagory_id>/item/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def editCatagoryItem(catagory_id, item_id):
    try:
        editedItem = session.query(Item).filter_by(id=item_id).one()
        catagory = session.query(Catagory).filter_by(id=catagory_id).one()
        catagories = session.query(Catagory).all()
        if login_session['user_id'] != editedItem.user_id:
            message = "You are not authorized to edit this item."\
                      "Please create your own item in order to edit."
            return render_template("redirectingItems.html", message=message,
                                    catagory_id=catagory_id)
        if request.method == 'POST':
            if request.form['name']:
                editedItem.name = request.form['name']
            if request.form['description']:
                editedItem.description = request.form['description']
            if request.form['price']:
                editedItem.price = request.form['price']
            if request.form['catagory']:
                temp_catagory = session.query(Catagory).filter_by(
                                id=request.form['catagory']).one()
                editedItem.catagory_id = temp_catagory.id
            session.add(editedItem)
            session.commit()
            flash('Item Successfully Edited')
            return redirect(url_for('CatagoryItems', catagory_id=catagory_id,
                                                     catagory=catagory))
        else:
            return render_template('editcatagoryitem.html',
                                    catagory_id=catagory_id, item_id=item_id,
                                    item=editedItem, catagories=catagories)
    except:
        message = "Not possible to edit this item"
        return render_template("redirecting.html", message=message)


# Delete a catagory item
@app.route('/catagory/<int:catagory_id>/item/<int:item_id>/delete', methods=['GET', 'POST'])
@login_required
def deleteCatagoryItem(catagory_id, item_id):
    try:
        catagory = session.query(Catagory).filter_by(id=catagory_id).one()
        itemToDelete = session.query(Item).filter_by(id=item_id).one()
        if login_session['user_id'] != itemToDelete.user_id:
            message = "You are not authorized to delete this item."\
                      "Please create your own item in order to delete."
            return render_template("redirectingItems.html", message=message,
                                    catagory_id=catagory_id)
        if request.method == 'POST':
            session.delete(itemToDelete)
            session.commit()
            flash('Item Successfully Deleted')
            return redirect(url_for('CatagoryItems', catagory_id=catagory_id,
                                     catagory=catagory))
        else:
            return render_template('deleteCatagoryItem.html',
                                    catagory_id=catagory_id, catagory=catagory,
                                    item=itemToDelete)
    except:
        message = "Not possible to delete this item"
        return render_template("redirecting.html", message=message)

# retrive a catagory item information
@app.route('/catagory/<int:catagory_id>/item/<int:item_id>/info')
def catagoryItemInfo(catagory_id, item_id):
    try:
        catagory = session.query(Catagory).filter_by(id=catagory_id).one()
        itemToView = session.query(Item).filter_by(id=item_id).one()
        if 'username' not in login_session:
            return render_template('publicCatagoryItem.html',catagory=catagory,
                                    item=itemToView)
        else:
            return render_template('showCatagoryItem.html', catagory=catagory,
                                    item=itemToView)
    except:
        message = "No such item!"
        return render_template("redirecting.html", message=message)

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)