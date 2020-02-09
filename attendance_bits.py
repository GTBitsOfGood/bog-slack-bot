import xlrd, pymongo
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

people_attended = 0
attended = []
people_not_found = 0

for row in range(1,sheet.nrows):
    name = sheet.cell_value(row,0).title().strip()
    db_data = collection.find_one({"name": name})
    if db_data is None:
        print(name)
        people_not_found += 1
    else:
        attended.append(name)
        people_attended += 1

if people_not_found == 0:
    print("Everyone has been found")
    for name in attended:
        collection.find_one_and_update({'name': name}, {'$inc': {'bits': 2}})

print("Updated attendance for " + str(people_attended) + " people!")