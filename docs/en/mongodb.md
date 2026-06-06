# MongoDB setup

<p align="right">
  <a href="../ko/mongodb.md">한국어</a> ·
  <strong>English</strong>
</p>

The default connection string is `mongodb://localhost:27017/tourism_db`. Override it with the `MONGO_URI` environment variable.

## Prerequisites

- MongoDB installed and running
- [MongoDB Compass](https://www.mongodb.com/products/compass) recommended

## Import with `tourism_db.zip`

Use the bundled **`tourism_db.zip`** and JSON files to populate the database.

### 1. Create database and collections

JSON files contain **document data only**, not database or collection names. Create the structure first.

1. In Compass, click **[+] Create database**
2. **Database Name:** `tourism_db`
3. **Collection Name:** match one JSON filename, then create
4. Use **[+]** next to the database to create remaining collections matching each JSON filename

### 2. Import JSON

For each collection:

1. Select the collection
2. **Add Data** → **Import JSON or CSV file**
3. Choose the matching JSON file and click **Import**

### 3. Verify connection

Example `.env`:

```env
MONGO_URI=mongodb://localhost:27017/tourism_db
```

On startup, index creation in `app.py` runs idempotently.

## MongoDB Atlas (cloud)

1. Create an Atlas M0 cluster
2. Allow network access (IP allowlist)
3. Set the connection string in `MONGO_URI`:

```env
MONGO_URI=mongodb+srv://USER:PASSWORD@cluster.mongodb.net/tourism_db
```

See [Deployment](deployment.md) for hosting notes.
