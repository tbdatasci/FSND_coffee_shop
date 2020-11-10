import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS, cross_origin

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
db_drop_and_create_all()

# ROUTES
'''
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
        returns status code 200 and json {"success": True, "drinks": drinks}
            where drinks is the list of drinks or appropriate status code
            indicating reason for failure
'''


@app.route('/drinks')
@cross_origin()
def get_drinks():
    try:
        drinks = Drink.query.all()

        # Use short form representation of the Drink model
        drinks = [drink.short() for drink in drinks]

        return ({
            'success': True,
            'drinks': drinks
        })

    # If the Drink query fails for whatever reason, throw a catch-all error
    except Exception:
        abort(500)


'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
        returns status code 200 and json {"success": True, "drinks": drinks}
            where drinks is the list of drinks or appropriate status code
            indicating reason for failure
'''


@app.route('/drinks-detail')
@cross_origin()
# Only allow roles with the get:drinks-detail permission to access this page
@requires_auth(permission='get:drinks-detail')
def get_drinks_detail(payload):
    try:
        drinks = Drink.query.all()

        # Use long form representation of the Drink model
        drinks = [drink.long() for drink in drinks]

        return ({
            'success': True,
            'drinks': drinks
        })

    # If the Drink query fails for whatever reason, throw a catch-all error
    except Exception:
        abort(500)


'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where
        drink an array containing only the newly created drink or appropriate
        status code indicating reason for failure
'''


@app.route('/drinks', methods=['POST'])
@cross_origin()
# Only allow roles with the post:drinks permission to access this page
@requires_auth(permission='post:drinks')
def post_drink(payload):
    data = request.json

    # A new drink must have both a title and a recipe
    if ('title' not in data) or ('recipe' not in data):
        abort(422)

    drink_title = data['title']
    drink_recipe = data['recipe']

    # Make sure the recipe dictionary is composed of
    # 'color', 'name', and 'parts' keys
    mandatory_components = ['color', 'name', 'parts']
    for component in drink_recipe:
        if all(component in drink_recipe
               for component in mandatory_components):
            pass
        else:
            abort(422)

    # Format the drink recipe for uploading to the Drink database
    drink_recipe_json = json.dumps(drink_recipe)

    # Post new drink recipe to Drink database
    try:
        drink = Drink(title=drink_title, recipe=drink_recipe_json)
        drink.insert()

    except Exception:
        abort(422)

    return jsonify({
        'success': True,
        'drinks': [drink.long()]
    })


'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink}
        where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks/<int:id>', methods=['PATCH'])
@cross_origin()
# Only allow roles with the patch:drinks permission to access this page
@requires_auth(permission='patch:drinks')
def patch_drink(payload, id):
    # Query drinks for specified drink
    drink = Drink.query.get(id)

    if drink is None:
        abort(404)

    data = request.json

    if ('title' in data) or ('recipe' in data):
        pass
    else:
        abort(422)

    if 'title' in data:
        drink.title = data['title']

    if 'recipe' in data:
        drink_recipe = data['recipe']

        # Make sure the recipe dictionary is composed of
        # 'color', 'name', and 'parts' keys
        mandatory_components = ['color', 'name', 'parts']
        for component in drink_recipe:
            if all(component in drink_recipe
                   for component in mandatory_components):
                pass
            else:
                abort(422)

        # Format the drink recipe for uploading to the Drink database
        drink.recipe = json.dumps(drink_recipe)

    # Apply the patch to the Drink database
    try:
        drink.update()

    except Exception:
        abort(422)

    return jsonify({
        'success': True,
        'drinks': [drink.long()]
    })


'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id}
        where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks/<int:id>', methods=['DELETE'])
@cross_origin()
# Only allow roles with the delete:drinks permission to access this page
@requires_auth(permission='delete:drinks')
def delete_drink(payload, id):
    # Query drinks for specified drink
    drink = Drink.query.get(id)

    if drink is None:
        abort(404)

    try:
        drink.delete()

    except Exception:
        abort(422)

    return jsonify({
        'success': True,
        'delete': id
    })


# Error Handling

'''
Example error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
                    "success": False,
                    "error": 422,
                    "message": "Unprocessable Entity"
                    }), 422


'''
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''

'''
@TODO implement error handler for 404
    error handler should conform to general task above
'''


@app.errorhandler(404)
def not_found(error):
    return jsonify({
                    "success": False,
                    "error": 404,
                    "message": "Not Found"
                    }), 404


@app.errorhandler(500)
def catch_all(error):
    return jsonify({
                    "success": False,
                    "error": 500,
                    "message": "Internal Server Error"
                    }), 500


'''
@TODO implement error handler for AuthError
    error handler should conform to general task above
'''


@app.errorhandler(AuthError)
def auth_error(ex):
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response
