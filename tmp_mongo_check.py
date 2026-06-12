from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=3000)
try:
    client.server_info()
except Exception as e:
    print('MONGO_CONNECTION_FAILED', e)
    raise SystemExit(1)

# check database and collection counts
client_db = client['tourism_db']
for name in ['users', 'tourist_spots', 'reviews', 'popular_spots', 'saved_courses']:
    print(name, client_db[name].count_documents({}))
