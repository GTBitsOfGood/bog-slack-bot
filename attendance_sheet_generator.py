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

wb = xlwt.Workbook()
ws = wb.add_sheet('Attendance Sheet')

ws.write(0,0, "Name")
ws.write(0,1, "Major")
ws.write(0,2, "Email")

wb.save('attendance_2_13.xlsx')