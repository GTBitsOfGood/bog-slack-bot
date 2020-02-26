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
    print("Found everyone!")
    for name in attended:
        num_inc = 2
        member = collection.find_one({"name": name})
        teams = member["team"].split(";")
        if 'Exec' in teams:
            num_inc = 0
        if 'MedShare' in teams:
            num_inc = 4

        collection.update_one({"name": member["name"]}, {"$inc": {"bits": num_inc}})
        print(member["name"] + " checked in for %d bits." % num_inc)

print("Updated attendance for " + str(people_attended) + " people!")