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

file = "./attendance.xls"
workbook = xlrd.open_workbook(file)
sheet = workbook.sheet_by_index(0)

wb = xlwt.Workbook()
ws = wb.add_sheet('Attendance Sheet')

style0 = xlwt.easyxf('font: name Times New Roman, bold on')

ws.write(0,0, "Name", style0)
ws.write(0,1, "Major", style0)
ws.write(0,2, "Email", style0)


for row in range(1,sheet.nrows):
    email = sheet.cell_value(row,2)
    print(email)
    member = collection.find_one({"email": email})

    ws.write(row,0, member["name"])
    ws.write(row,1, member["major"])
    ws.write(row,2, member["email"])

wb.save('attendance.xls')