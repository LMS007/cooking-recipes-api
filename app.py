import datetime
from bson.objectid import ObjectId
from bson import json_util
from dotenv import load_dotenv, dotenv_values

from flask import Flask, request
import fastjsonschema
from flask import Flask
from pymongo.mongo_client import MongoClient


load_dotenv()
config = dotenv_values(".env")

# connects to an free tier mongodb Atlas cluster
uri = 'mongodb+srv://' + config['DB_USERNAME'] + ':' + config['DB_PASSWORD'] + '@'+ config['DB_CLUSTER'] + \
    '.lr1tn.mongodb.net/?retryWrites=true&w=majority'
client = MongoClient(uri)
db = None

try:
    db = client['Recipes']
    client.admin.command('ping')
    print("You successfully connected to MongoDB")

except Exception as e:
    print(e)

app = Flask(__name__)


deleteRecipeInput = fastjsonschema.compile({
    'type': 'object',
    'properties': {
        '_id': {
            'type': 'string'
        }
    },
    "required": ['_id']
})
 
insertRecipeSchema = {
    'type': 'object',
    'additionalProperties': False,
    'properties': {
        'name': {
            'type': 'string',
            'default': ''
        },
        'ingredients': {
            'type': 'array',
            'default': [],
            'additionalProperties': False,
            'items': {
                'anyOf': [
                    {
                        'type': 'object',
                        "required": ["tsp", "foodItem"],
                        'additionalProperties': False,
                        'properties': {
                             "tsp": {
                                'type': 'number', 
                                'default': 1,
                            },
                            "foodItem":{
                                'type': 'string', 
                                'default': '',
                            }
                        }
                    },
                    {
                        'type': 'object',
                        'additionalProperties': False,
                        "required": ["tbsp", "foodItem"],
                        'properties': {
                             "tbsp": {
                                'type': 'number', 
                                'default': 1,
                            },
                            "foodItem":{
                                'type': 'string', 
                                'default': '',
                            }
                        }
                    },
                    {
                        'type': 'object',
                        'additionalProperties': False,
                        "required": ["cups", "foodItem"],
                        'properties': {
                             "cups": {
                                'type': 'number', 
                                'default': 1,
                            },
                            "foodItem":{
                                'type': 'string', 
                                'default': '',
                            }
                        }
                    },
                    {
                        'type': 'object',
                        'additionalProperties': False,
                        "required": ["quantity", "foodItem"],
                        'properties': {
                             "quantity": {
                                'type': 'number', 
                                'default': 1,
                            },
                            "foodItem":{
                                'type': 'string', 
                                'default': '',
                            }
                        }
                    },
                ]
            }
        },
        'instructions': {
            'type': 'array', 
            'default': [],
            'items': {
                "type": "string"
            }
        },
        'servingSize': {
            'type': 'number', 
            'default': 1
        },
        'category': {
            "enum": ["dinner", "breakfast", "dessert"]
        },
        'notes': {
            'type': 'string',
            'default': ''
        },
    },
    'required': ['name', 'category', 'ingredients', 'instructions', 'servingSize'],
}
insertRecipeInput = fastjsonschema.compile(insertRecipeSchema)


updateRecipeSchema = insertRecipeSchema.copy()
updateRecipeSchema['required'] = [] # updates are optional
updateRecipeInput = fastjsonschema.compile({
    'type': 'object',
    'additionalProperties': False,
    'properties': {
        '_id': {
            'type': 'string'
        },
        'updates': updateRecipeSchema,
    },
    'required': ['_id', 'updates']
})


@app.route("/recipe", methods = ['GET', 'PUT', 'POST', 'DELETE'])
def recipe():
    if request.method == 'GET':
        try:
            paramId = request.args.get('_id')
            id = ObjectId(paramId)
            result = db.recipes.find_one({'_id': id})
            if result == None:
                return 'Recipe not found', 404
            return json_util.dumps(result)
        except Exception as e:
            return str(e), 400
    
    if request.method == 'DELETE':
        try:
            json_data = request.get_json()
            deleteRecipeInput(json_data)
            id = ObjectId(json_data['_id'])
            result = db.recipes.find_one({'_id': id})
            if result == None:
                return 'Recipe not found', 404
            db.recipes.delete_one({'_id': id})
            return 'Recipe deleted', 200
        except Exception as e:
            return str(e), 400
    
    if request.method == 'PUT':
        try:
            json_data = request.get_json()
            timestamp = datetime.datetime.utcnow()
            insertRecipeInput(json_data) # validate
            json_data.update({
                'dateAdded': timestamp,
                'dateModified': timestamp
            })
            result = db.recipes.insert_one(json_data)
            return 'Recipe id "' + str(result.inserted_id) + '" inserted', 201
        except Exception as e:
            return str(e), 400
        
    if request.method == 'POST':
        try:
            json_data = request.get_json()
            updateRecipeInput(json_data)  # validate
            updates = json_data['updates']
            updates.update({
                'dateModified': datetime.datetime.utcnow()
            })
            updateSet = {
                '$set': updates
            }
            filter = {
                '_id': ObjectId(json_data['_id'])
            }
            result = db.recipes.update_one(filter, updateSet)

            return "Recipe updated"
        except Exception as e:
            return str(e), 400
        
    return "okay"


@app.route("/recipes", methods = ['GET'])
def recipes():
    if request.method == 'GET':
        try:
            offset = int(request.args.get('offset', 0))
            limit = int(request.args.get('limit', 10))
            if limit > 100:
                limit = 100
            result = db.recipes.find().skip(offset).limit(limit)
            return json_util.dumps(result)
        except Exception as e:
            return str(e), 400
