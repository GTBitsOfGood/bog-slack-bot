import xlrd, xlwt, pymongo
import config
from pymongo import MongoClient

# Instantiate Mongo Client
mongo_client = MongoClient("mongodb+srv://"
    + config.username + ":" + config.password
    + config.db_link)

# Specify DB
db = mongo_client["Spring2020"]
collection = db["member-manager"]
posts = db.posts

file = "./attendance.xlsx"
workbook = xlrd.open_workbook(file)
sheet = workbook.sheet_by_index(0)

for row in range(1,sheet.nrows):
    name = sheet.cell_value(row,0).title().strip()
    email = sheet.cell_value(row,1).lower().strip()
    major = sheet.cell_value(row,2).upper().strip()

    db_data = collection.find_one({"name": name})

    if db_data is None:
        print("Not Found: " + name)
    else:
        print("Name: " + name + " updated!")
        collection.update_one({"name": name}, {"$set": {
            "email": email,
            "major": major}})