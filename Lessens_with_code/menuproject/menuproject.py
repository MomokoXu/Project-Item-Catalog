from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
app = Flask(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Restaurant, Base, MenuItem

engine = create_engine('sqlite:///restaurantmenu.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


############# Restaurants ###########
# 1. Show all restaurants
# 2. Create a new restaurant
# 3. Edit a restaurant
# 4. Delete a restaurant

# @: decorators
# decorators can be stacked on on top of the other,
# so app.route('/') will call app.route('/')
# which will call the HelloWorld function

# 1. Show all restaurants
@app.route('/')
@app.route('/restaurants/')
def restaurantAll():
    restaurants = session.query(Restaurant).all()
    return render_template('restaurants.html', restaurants=restaurants)

# 2. Create a new restaurant
@app.route('/restaurants/new', methods=['GET', 'POST'])
def newRestaurant():
    if request.method == 'POST':
        newRestaurantItem = Restaurant(name=request.form['name'])
        session.add(newRestaurantItem)
        session.commit()
        flash("New restaurant created!")
        return redirect(url_for('restaurantAll'))
    else:
        return render_template('newrestaurant.html')
    return None

# 3. Edit a restaurant
@app.route('/restaurants/<int:restaurant_id>/edit', methods=['GET', 'POST'])
def editRestaurant(restaurant_id):
    editedRestaurantItem = session.query(Restaurant).filter_by(id=restaurant_id).one()
    if request.method == 'POST':
        if editedRestaurantItem:
            editedRestaurantItem.name = request.form['name']
        session.add(editedRestaurantItem)
        session.commit()
        flash("Restaurant updated!")
        return redirect(url_for('restaurantAll'))
    else:
        return render_template('editrestaurant.html', restaurant_id=restaurant_id, editedRestaurantItem=editedRestaurantItem)

# 4. Delete a restaurant
@app.route('/restaurants/<int:restaurant_id>/delete', methods=['GET', 'POST'])
def deleteRestaurant(restaurant_id):
    deleteRestaurantItem = session.query(Restaurant).filter_by(id=restaurant_id).one()
    if request.method == 'POST':
        session.delete(deleteRestaurantItem)
        session.commit()
        flash("Restaurant deleted!")
        return redirect(url_for('restaurantAll'))
    else:
        return render_template('deleterestaurant.html', restaurant_id=restaurant_id)

########### Restaurant Menu ############
# 1. Show all menu items
# 2. Create a new menu item
# 3. Edit a menu item
# 4. Delete a menu item

# 1. Show all menu items
@app.route('/restaurants/<int:restaurant_id>/')
def restaurantMenu(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    items = session.query(MenuItem).filter_by(restaurant_id=restaurant.id)
    return render_template('menu.html', items=items, restaurant=restaurant)

# 2. Create a new menu item
@app.route('/restaurants/<int:restaurant_id>/new/', methods=['GET', 'POST'])
def newMenuItem(restaurant_id):
    if request.method == 'POST':
        newItem = MenuItem(name=request.form['name'],
                           restaurant_id=restaurant_id,
                           description=request.form['description'],
                           price=request.form['price'])
        session.add(newItem)
        session.commit()
        flash("New menu item created!")
        return redirect(url_for('restaurantMenu', restaurant_id=restaurant_id))
    else:
        return render_template('newmenuitem.html', restaurant_id=restaurant_id)

# 3. Edit a menu item
@app.route('/restaurants/<int:restaurant_id>/<int:menu_id>/edit/', methods=['GET', 'POST'])
def editMenuItem(restaurant_id, menu_id):
    editedItem = session.query(MenuItem).filter_by(id=menu_id).one()
    if request.method == 'POST':
        if editedItem:
            editedItem.name = request.form['name']
            editedItem.description = request.form['description']
            editedItem.price=request.form['price']
        session.add(editedItem)
        session.commit()
        flash("Menu item updated!")
        return redirect(url_for('restaurantMenu', restaurant_id=restaurant_id))
    else:
        return render_template('editmenuitem.html', restaurant_id=restaurant_id, editedItem=editedItem)

# 4. Delete a menu item
@app.route('/restaurants/<int:restaurant_id>/<int:menu_id>/delete/', methods=['GET', 'POST'])
def deleteMenuItem(restaurant_id, menu_id):
    itemTodelete = session.query(MenuItem).filter_by(id=menu_id).one()
    if request.method == 'POST':
        session.delete(itemTodelete)
        session.commit()
        flash("Menu item deleted!")
        return redirect(url_for('restaurantMenu', restaurant_id=restaurant_id))
    else:
        return render_template('deletemenuitem.html', restaurant_id=restaurant_id, menu_id=menu_id)


######## JSON endpoint APIs #########
# 1. Add JSON endpoint API for all restaurants
@app.route('/restaurants/JSON')
def restaurantJSON():
    restaurants = session.query(Restaurant).all()
    return jsonify(Restaurants=[i.serialize for i in restaurants])


# 2. Add JSON endpoint API for a restaurant
@app.route('/restaurants/<int:restaurant_id>/menu/JSON')
def restaurantMenuJSON(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    items = session.query(MenuItem).filter_by(restaurant_id=restaurant_id).all()
    return jsonify(MenuItems=[i.serialize for i in items])

# 3. Add JSON endpoint API for a menu item
@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/JSON')
def menuItemJSON(restaurant_id, menu_id):
    menuItem = session.query(MenuItem).filter_by(id=menu_id).one()
    return jsonify(MenuItem=menuItem.serialize)

if __name__ == '__main__':
    # debug is true: the server will reload itself
    # each time it notices a code change and also provides
    # a helpful debugger in the browser if things go wrong.
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port = 5000)
