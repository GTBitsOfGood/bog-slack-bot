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

file = "./bootcamp_attendance.xlsx"
workbook = xlrd.open_workbook(file)
sheet = workbook.sheet_by_index(0)

for row in range(2,sheet.nrows-1):
    name = sheet.cell_value(row,0).title().strip()
    db_data = collection.find_one({"name": name})
    present = 0
    for day in range(5,8,2):
        if(sheet.cell_value(row,day) == 1):
            present += 1
            # collection.find_one_and_update({'name': name}, {'$inc': {'bits': 2}})
    print(name + " was present on " + str(present) + " Thursdays")

print("Updated attendance for bootcampers!")
