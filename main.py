
import uvicorn
from fastapi import FastAPI,Request
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
import json


#intialize web app / pi
app = FastAPI()

client = MongoClient('mongodb+srv://admin:admin@cluster0.0wkqw.mongodb.net/myFirstDatabase?retryWrites=true&w=majority')


#BCG DB connection
db = client.get_database('BCG')

# Allows cors for everyone **Ignore**
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

@app.get("/")
def read_root(request: Request):
  from bson import json_util
  policies = db.BCG
  params = request.query_params
  pageNo = 1
  customerID = 0
  policyID = 0
  try:
    pageNo = int(params['pageNo'])
    if params['policyID']:
      policyID = int(params['policyID'])
    if params['customerID']:
      customerID = int(params['customerID'])
  except:
    pageNo = 1
  temp = []
  search_filter = {}
  #checking for filters applied from front end
  if customerID:
    search_filter['customer_id'] = customerID
  if policyID:
    search_filter['policy_id'] = policyID
  count = policies.find(search_filter).count()
  #page count reset
  if count/30 < pageNo:
    pageNo = 1
  #pagination logic
  cursor = policies.find(search_filter).skip((pageNo-1)*30).limit(30)
  for data in cursor:
    temp.append(json.loads(json_util.dumps(data)))
  resp = {"count":count,"data":temp}
  return resp


@app.get("/single")
def get_single_res(request: Request):
  from bson import json_util
  from bson.objectid import ObjectId
  policies = db.BCG
  params = request.query_params
  res = policies.find_one({'_id': ObjectId(params['objID']) })
  return json.loads(json_util.dumps(res))

@app.post("/update")
async def get_body(request: Request):
  from bson import ObjectId
  updatedPolicy = await request.json()
  #creating pymongo object
  _id = ObjectId(updatedPolicy['body']['_id'])
  del updatedPolicy['body']['_id']
  policies = db.BCG
  policies.update_one(
    {"_id" : _id},
    {"$set": updatedPolicy['body']},
    upsert=True)
  return "success"


@app.get("/chart")
def get_chart_info(request: Request):
  params = request.query_params
  from bson import json_util
  search_parameter = {}
  try:
    if params:
      region = params['region']
      if region != 'All':
        search_parameter = {'customer_region':region}
  except:
    search_parameter={}
  policies = db.BCG
  cursor = policies.find(search_parameter)
  policy_list = []
  for policy_info in cursor:
    policy_info = json.loads(json_util.dumps(policy_info))
    policy_list.append(policy_info)
  month_policy_data = get_monthly_policy_data(policy_list)
  return month_policy_data



def get_monthly_policy_data(policy_list):
  response_data = {'data':[['January',0], ['February',0], ['March',0], ['April',0], ['May',0], ['June',0],['July',0], ['August',0], ['September',0], ['October',0], ['November',0], ['December',0]]}
  for policy in policy_list:
    purchase_date_obj = get_data_object(policy['date_of_purchase'])
    response_data['data'][purchase_date_obj.month-1][1]= 1+ response_data['data'][purchase_date_obj.month-1][1]
  return response_data



def get_data_object(date_str):
  import datetime
  format_str = '%m/%d/%Y' # The format
  datetime_obj = datetime.datetime.strptime(date_str, format_str)
  return datetime_obj


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)