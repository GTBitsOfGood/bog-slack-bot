import xlwt, pymongo
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

style0 = xlwt.easyxf('font: name Times New Roman, bold on')

wb = xlwt.Workbook()
ws = wb.add_sheet('Attendance Sheet')

ws.write(0,0, "Name", style0)
ws.write(0,1, "Major", style0)
ws.write(0,2, "Email", style0)

checked_in_members = collection.find({"checkedIn": True})

i = 1
for member in checked_in_members:
    print(member["name"] + " checked in.")
    ws.write(i,0, member["name"])
    ws.write(i,1, member["major"])
    ws.write(i,2, member["email"])
    collection.update_one({"name": member["name"]},
        {"$set": {"checkedIn": False}},
        {"$inc": {"bits": 2}})
    i+=1

wb.save('attendance.xls')