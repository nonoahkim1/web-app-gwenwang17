#!/usr/bin/env python3

from flask import Flask, render_template, request, redirect, url_for, make_response
from markupsafe import escape
import pymongo
import datetime
from bson.objectid import ObjectId
import os
import subprocess

from bson.binary import Binary

# instantiate the app
app = Flask(__name__)

# load credentials and configuration options from .env file
# if you do not yet have a file named .env, make one based on the template in env.example
import credentials
config = credentials.get()

# turn on debugging if in development mode
if config['FLASK_ENV'] == 'development':
    # turn on debugging, if in development
    app.debug = True # debug mnode

# make one persistent connection to the database
connection = pymongo.MongoClient(config['MONGO_HOST'], 27017, 
                                username=config['MONGO_USER'],
                                password=config['MONGO_PASSWORD'],
                                authSource=config['MONGO_DBNAME'])
db = connection[config['MONGO_DBNAME']] # store a reference to the database

# set up the routes

@app.route('/')
def home():
    """
    Route for the home page
    """
    return render_template('index.html')


@app.route('/gallery')
def gallery():
    """
    Route for the gallery page
    """
    return render_template('gallery.html')

'''
@app.route('/read/<mongoid>')
def read(mongoid):
    """
    Route for displaying details of a specific recipe.
    """
    doc = db.recipeapp.find_one({"_id": ObjectId(mongoid)})
    return render_template('read.html', doc=doc)
'''
'''
@app.route('/read/<recipe_title>')
def recipe_details(recipe_title):
    """
    Route for displaying the details of a single recipe based on its title
    """
    doc = db.recipeapp.find_one({"recipe title": recipe_title})

    'if doc:'
    return render_template('read.html', doc=doc)



@app.route('/gallery/<recipe_title>')
def recipe_details(recipe_title):
    """
    Route for displaying the details of a single recipe based on its title
    """
    doc = db.recipeapp.find_one({"recipe title": recipe_title})
    return render_template('read.html', doc=doc)
'''


@app.route('/gallery/<recipe_title>')
def recipe_details(recipe_title):
    """
    Route for redirecting to the details of a single recipe based on its title
    """
    return redirect(url_for('read', recipe_title=recipe_title))


@app.route('/read')
def read():
    """
    Route for GET requests to the read page.
    Displays some information for the user with links to other pages.
    """
    docs = db.recipeapp.find({}).sort("created_at", -1) # sort in descending order of created_at timestamp
    return render_template('read.html', docs=docs) # render the read template


@app.route('/create')
def create():
    """
    Route for GET requests to the create page.
    Displays a form users can fill out to create a new document.
    """
    return render_template('create.html') # render the create template


@app.route('/create', methods=['POST'])
def create_recipe():
    """
    Route for POST requests to the create page.
    Accepts the form submission data for a new document and saves the document to the database.
    """
    title = request.form['recipe_title']
    description = request.form['recipe_description']
    ingredients = request.form['recipe_ingredients']
    instructions = request.form['recipe_instructions']

    image_file = request.files['dish_image']
    image_name = image_file.filename
    image_binary = Binary(image_file.read())

    '''image_path = os.path.join('static', 'images', image_name)
    image_file.save(image_path)'''


    # create a new document with the data the user entered
    doc = {
        "recipe_title": title,
        "description": description, 
        "ingredients": ingredients,
        "instructions": instructions,
        "dish_image": image_name,
        "dish_image_binary": image_binary,
        "created_at": datetime.datetime.utcnow()
    }
    db.recipeapp.insert_one(doc) # insert a new document

    return redirect(url_for('read')) # tell the browser to make a request for the /read route


@app.route('/edit/<mongoid>')
def edit(mongoid):
    """
    Route for GET requests to the edit page.
    Displays a form users can fill out to edit an existing record.
    """
    doc = db.recipeapp.find_one({"_id": ObjectId(mongoid)})
    return render_template('edit.html', mongoid=mongoid, doc=doc) # render the edit template


@app.route('/edit/<mongoid>', methods=['POST'])
def edit_post(mongoid):
    """
    Route for POST requests to the edit page.
    Accepts the form submission data for the specified document and updates the document in the database.
    """
    title = request.form['recipe_title']
    description = request.form['recipe_description']
    ingredients = request.form['recipe_ingredients']
    instructions = request.form['recipe_instructions']
    '''
    image_file = request.files['dish_image']
    image_name = image_file.filename
    image_path = os.path.join('static', 'images', image_name)
    image_file.save(image_path)
    '''

    image_file = request.files.get('dish_image') # returns None if 'dish_image' is not in the request
    if image_file:
        image_name = image_file.filename
        image_data = image_file.read()
        image_binary = Binary(image_data)

        '''image_path = os.path.join('static', 'images', image_name)
        image_file.save(image_path)'''
    else:
        image_name = db.recipeapp.find_one({"_id": ObjectId(mongoid)})['dish_image'] # get the existing image name if no new image is uploaded
        image_binary = db.recipeapp.find_one({"_id": ObjectId(mongoid)})['dish_image_binary']  # get the existing image binary data


    doc = {
        # "_id": ObjectId(mongoid), 
        "recipe_title": title,
        "description": description, 
        "ingredients": ingredients,
        "instructions": instructions,
        "dish_image": image_name,
        "dish_image_binary": image_binary,
        "created_at": datetime.datetime.utcnow()
    }

    db.recipeapp.update_one(
        {"_id": ObjectId(mongoid)}, # match criteria
        { "$set": doc }
    )

    return redirect(url_for('read')) # tell the browser to make a request for the /read route


@app.route('/delete/<mongoid>')
def delete(mongoid):
    """
    Route for GET requests to the delete page.
    Deletes the specified record from the database, and then redirects the browser to the read page.
    """
    db.recipeapp.delete_one({"_id": ObjectId(mongoid)})
    return redirect(url_for('read')) # tell the web browser to make a request for the /read route.

'''
@app.route('/webhook', methods=['POST'])
def webhook():
    """
    GitHub can be configured such that each time a push is made to a repository, GitHub will make a request to a particular web URL... this is called a webhook.
    This function is set up such that if the /webhook route is requested, Python will execute a git pull command from the command line to update this app's codebase.
    You will need to configure your own repository to have a webhook that requests this route in GitHub's settings.
    Note that this webhook does do any verification that the request is coming from GitHub... this should be added in a production environment.
    """
    # run a git pull command
    process = subprocess.Popen(["git", "pull"], stdout=subprocess.PIPE)
    pull_output = process.communicate()[0]
    # pull_output = str(pull_output).strip() # remove whitespace
    process = subprocess.Popen(["chmod", "a+x", "flask.cgi"], stdout=subprocess.PIPE)
    chmod_output = process.communicate()[0]
    # send a success response
    response = make_response('output: {}'.format(pull_output), 200)
    response.mimetype = "text/plain"
    return response
'''
@app.errorhandler(Exception)
def handle_error(e):
    """
    Output any errors - good for debugging.
    """
    return render_template('error.html', error=e) # render the error template


if __name__ == "__main__":
    #import logging
    #logging.basicConfig(filename='/home/akg451/error.log',level=logging.DEBUG)
    app.run(debug = True)