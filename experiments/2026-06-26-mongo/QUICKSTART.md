Great. Let’s turn this into a small **MongoDB learning lab for your cleaning-business app**.

We’ll use this path:

```txt
1. Launch MongoDB locally with Docker
2. Learn MongoDB basics in mongosh
3. Practice CRUD with cleaning-job documents
4. Add indexes and simple validation
5. Build FastAPI CRUD with PyMongo Async
```

MongoDB’s shell is called **mongosh**; it is a JavaScript-like REPL for working with local, Atlas, or remote MongoDB deployments. ([MongoDB][1]) For Python + FastAPI, I would use **PyMongo Async**, because MongoDB’s docs now recommend it over Motor; Motor was deprecated in favor of the GA PyMongo Async API. ([MongoDB][2])

---

# Part 1 — Local MongoDB launch

Create a folder:

```bash
mkdir mongo-cleaning-lab
cd mongo-cleaning-lab
```

Create `.env`:

```env
MONGO_ROOT_USER=root
MONGO_ROOT_PASSWORD=rootpass
MONGO_DB=cleaning_lab

MONGO_APP_USER=cleaning_app
MONGO_APP_PASSWORD=cleaning_pass

MONGO_PORT=27017

MONGO_ADMIN_URI=mongodb://root:rootpass@localhost:27017/admin
MONGO_URI=mongodb://cleaning_app:cleaning_pass@localhost:27017/cleaning_lab?authSource=cleaning_lab
```

Create `docker-compose.yml`:

```yaml
services:
  mongodb:
    image: mongo:8.0
    container_name: cleaning_mongodb
    restart: unless-stopped
    ports:
      - "${MONGO_PORT}:27017"
    environment:
      MONGO_INITDB_ROOT_USERNAME: ${MONGO_ROOT_USER}
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_ROOT_PASSWORD}
      MONGO_INITDB_DATABASE: ${MONGO_DB}
    volumes:
      - mongo_data:/data/db

volumes:
  mongo_data:
```

The important part is this:

```yaml
ports:
  - "27017:27017"
```

That maps MongoDB inside Docker to `localhost:27017` on your machine; MongoDB’s Docker docs use the same port mapping pattern for local Docker installs. ([MongoDB][3]) The official Mongo Docker image also supports `MONGO_INITDB_ROOT_USERNAME` and `MONGO_INITDB_ROOT_PASSWORD` for creating the initial root user. ([Docker Hub][4])

Start MongoDB:

```bash
docker compose up -d
```

Check logs:

```bash
docker logs cleaning_mongodb
```

Connect as root:

```bash
docker exec -it cleaning_mongodb mongosh \
  -u root \
  -p rootpass \
  --authenticationDatabase admin
```

Inside `mongosh`, create your project database user:

```js
use cleaning_lab

db.createUser({
  user: "cleaning_app",
  pwd: "cleaning_pass",
  roles: [
    { role: "readWrite", db: "cleaning_lab" }
  ]
})
```

Exit:

```js
exit
```

Now connect as your app user:

```bash
docker exec -it cleaning_mongodb mongosh \
  "mongodb://cleaning_app:cleaning_pass@localhost:27017/cleaning_lab?authSource=cleaning_lab"
```

The `authSource` part matters: it tells MongoDB which database stores the user credentials. MongoDB’s docs explain that if `authSource` is not specified, the client uses the default database from the connection string, or `admin` if no default database is specified. ([MongoDB][5])

---

# Part 2 — MongoDB mental model

Coming from Postgres:

| Postgres    | MongoDB                                    |
| ----------- | ------------------------------------------ |
| database    | database                                   |
| table       | collection                                 |
| row         | document                                   |
| column      | field                                      |
| primary key | `_id`                                      |
| index       | index                                      |
| JSONB       | document-like structure                    |
| SQL query   | MongoDB query document                     |
| join        | `$lookup`, but not the main modeling style |

MongoDB stores data as documents:

```js
{
  _id: ObjectId("..."),
  status: "requested",
  customerName: "Anna",
  location: {
    addressText: "Amsterdam, Netherlands",
    coordinates: {
      type: "Point",
      coordinates: [4.9041, 52.3676]
    }
  },
  requestedServices: ["regular_cleaning", "window_cleaning"],
  createdAt: ISODate("2026-06-26T10:00:00Z")
}
```

A collection does not need to be created first. If you insert into `jobs`, MongoDB creates the collection automatically.

---

# Part 3 — Pure MongoDB exercises

Connect as app user:

```bash
docker exec -it cleaning_mongodb mongosh \
  "mongodb://cleaning_app:cleaning_pass@localhost:27017/cleaning_lab?authSource=cleaning_lab"
```

Check current database:

```js
db
```

Show collections:

```js
show collections
```

At first, there may be nothing.

---

## Exercise 1 — Insert one cleaning job

```js
const result = db.jobs.insertOne({
  tenantId: "demo-company",
  customer: {
    name: "Anna Ivanova",
    phone: "+31600000000"
  },
  status: "requested",
  location: {
    addressText: "Vondelpark, Amsterdam",
    city: "Amsterdam",
    country: "NL",
    coordinates: {
      type: "Point",
      coordinates: [4.8726, 52.3579]
    }
  },
  property: {
    type: "apartment",
    rooms: 2,
    bathrooms: 1,
    areaM2: 55
  },
  requestedServices: ["regular_cleaning", "window_cleaning"],
  photos: [],
  notes: "Customer wants cleaning before guests arrive.",
  createdAt: new Date(),
  updatedAt: new Date()
})

result
```

Save the generated id:

```js
const jobId = result.insertedId
jobId
```

Find it:

```js
db.jobs.findOne({ _id: jobId })
```

---

## Exercise 2 — Insert several jobs

```js
db.jobs.insertMany([
  {
    tenantId: "demo-company",
    customer: { name: "Mark", phone: "+31611111111" },
    status: "scheduled",
    location: {
      addressText: "Rotterdam Central Station",
      city: "Rotterdam",
      country: "NL",
      coordinates: {
        type: "Point",
        coordinates: [4.4699, 51.9244]
      }
    },
    property: {
      type: "office",
      areaM2: 120
    },
    requestedServices: ["office_cleaning"],
    photos: [],
    notes: "Evening cleaning only.",
    scheduledWindow: {
      startsAt: ISODate("2026-06-28T18:00:00Z"),
      endsAt: ISODate("2026-06-28T21:00:00Z")
    },
    createdAt: new Date(),
    updatedAt: new Date()
  },
  {
    tenantId: "demo-company",
    customer: { name: "Sophie", phone: "+31622222222" },
    status: "requested",
    location: {
      addressText: "Utrecht city center",
      city: "Utrecht",
      country: "NL",
      coordinates: {
        type: "Point",
        coordinates: [5.1214, 52.0907]
      }
    },
    property: {
      type: "house",
      rooms: 5,
      bathrooms: 2
    },
    requestedServices: ["deep_cleaning"],
    photos: [],
    notes: "House after renovation.",
    createdAt: new Date(),
    updatedAt: new Date()
  }
])
```

---

## Exercise 3 — Read/query documents

Find all jobs:

```js
db.jobs.find()
```

Make output readable:

```js
db.jobs.find().pretty()
```

Find requested jobs:

```js
db.jobs.find({ status: "requested" })
```

Find jobs in Amsterdam:

```js
db.jobs.find({ "location.city": "Amsterdam" })
```

Find jobs that include `window_cleaning`:

```js
db.jobs.find({ requestedServices: "window_cleaning" })
```

In MongoDB, querying an array like this means “array contains this value.”

Find large properties:

```js
db.jobs.find({
  "property.areaM2": { $gte: 100 }
})
```

Find jobs with a schedule:

```js
db.jobs.find({
  scheduledWindow: { $exists: true }
})
```

Find jobs with selected fields only:

```js
db.jobs.find(
  { status: "requested" },
  {
    customer: 1,
    status: 1,
    location: 1
  }
)
```

The second object is a projection. It means: “return only these fields.”

---

## Exercise 4 — Update documents

Change status:

```js
db.jobs.updateOne(
  { _id: jobId },
  {
    $set: {
      status: "scheduled",
      scheduledWindow: {
        startsAt: ISODate("2026-06-29T09:00:00Z"),
        endsAt: ISODate("2026-06-29T12:00:00Z")
      },
      updatedAt: new Date()
    }
  }
)
```

Check result:

```js
db.jobs.findOne({ _id: jobId })
```

Add a photo metadata entry:

```js
db.jobs.updateOne(
  { _id: jobId },
  {
    $push: {
      photos: {
        kind: "before",
        storageKey: "jobs/demo/before/photo-1.jpg",
        uploadedAt: new Date()
      }
    },
    $set: {
      updatedAt: new Date()
    }
  }
)
```

This is the MongoDB style: instead of rewriting the whole document, you often use operators like:

```txt
$set   -> set fields
$push  -> append to array
$inc   -> increment number
$unset -> remove field
```

---

## Exercise 5 — Delete documents

Delete one job:

```js
db.jobs.deleteOne({ _id: jobId })
```

For learning, you can delete everything:

```js
db.jobs.deleteMany({})
```

Be careful with that one. It is the MongoDB equivalent of “wipe this collection.”

---

# Part 4 — Indexes for your cleaning app

Indexes are essential. Without them, MongoDB may scan lots of documents.

Create common indexes:

```js
db.jobs.createIndex({
  tenantId: 1,
  status: 1,
  "scheduledWindow.startsAt": 1
})
```

For geolocation:

```js
db.jobs.createIndex({
  "location.coordinates": "2dsphere"
})
```

MongoDB’s `2dsphere` index is designed for geospatial queries on an earth-like sphere, which is exactly what you want for finding jobs near a cleaner or within a service radius. ([MongoDB][3])

List indexes:

```js
db.jobs.getIndexes()
```

Find jobs near Amsterdam center:

```js
db.jobs.find({
  "location.coordinates": {
    $near: {
      $geometry: {
        type: "Point",
        coordinates: [4.9041, 52.3676]
      },
      $maxDistance: 10000
    }
  }
})
```

Important: GeoJSON uses:

```txt
[longitude, latitude]
```

Not:

```txt
[latitude, longitude]
```

---

# Part 5 — Add basic MongoDB validation

Pydantic will validate your FastAPI input, but MongoDB can also validate documents at the collection level. MongoDB supports schema validation rules for fields, types, and allowed values. ([MongoDB][6]) MongoDB also supports JSON Schema-style validation through `$jsonSchema`. ([MongoDB][7])

Create a validated collection:

```js
db.createCollection("validated_jobs", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["tenantId", "status", "location", "createdAt", "updatedAt"],
      properties: {
        tenantId: {
          bsonType: "string"
        },
        status: {
          enum: [
            "requested",
            "scheduled",
            "in_progress",
            "completed",
            "cancelled"
          ]
        },
        location: {
          bsonType: "object",
          required: ["addressText"],
          properties: {
            addressText: {
              bsonType: "string"
            },
            city: {
              bsonType: "string"
            },
            country: {
              bsonType: "string"
            }
          }
        },
        createdAt: {
          bsonType: "date"
        },
        updatedAt: {
          bsonType: "date"
        }
      }
    }
  }
})
```

Try invalid insert:

```js
db.validated_jobs.insertOne({
  tenantId: "demo-company",
  status: "wrong_status",
  createdAt: new Date(),
  updatedAt: new Date()
})
```

MongoDB should reject it.

Try valid insert:

```js
db.validated_jobs.insertOne({
  tenantId: "demo-company",
  status: "requested",
  location: {
    addressText: "Amsterdam"
  },
  createdAt: new Date(),
  updatedAt: new Date()
})
```

This is the layered protection idea:

```txt
FastAPI/Pydantic validates incoming API data.
MongoDB validation prevents obviously invalid stored documents.
Indexes protect uniqueness and performance.
Business services protect workflow logic.
```

---

# Part 6 — FastAPI CRUD setup

Now create a Python app.

Folder structure:

```txt
mongo-cleaning-lab/
├── .env
├── docker-compose.yml
└── api/
    ├── main.py
    └── requirements.txt
```

Create `api/requirements.txt`:

```txt
fastapi
uvicorn[standard]
pymongo
pydantic-settings
python-dotenv
```

Install:

```bash
cd api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create `api/main.py`:

```python
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Literal, Optional

from bson import ObjectId
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from pymongo import AsyncMongoClient


class Settings(BaseSettings):
    mongo_uri: str = "mongodb://cleaning_app:cleaning_pass@localhost:27017/cleaning_lab?authSource=cleaning_lab"
    mongo_db: str = "cleaning_lab"

    class Config:
        env_file = "../.env"
        extra = "ignore"


settings = Settings()


class CustomerInput(BaseModel):
    name: str
    phone: Optional[str] = None


class GeoPoint(BaseModel):
    type: Literal["Point"] = "Point"
    coordinates: tuple[float, float] = Field(
        description="GeoJSON coordinates: (longitude, latitude)"
    )


class LocationInput(BaseModel):
    addressText: str
    city: Optional[str] = None
    country: Optional[str] = None
    coordinates: Optional[GeoPoint] = None


class PropertyInput(BaseModel):
    type: Optional[str] = None
    rooms: Optional[int] = None
    bathrooms: Optional[int] = None
    areaM2: Optional[float] = None


class JobCreate(BaseModel):
    customer: CustomerInput
    location: LocationInput
    property: Optional[PropertyInput] = None
    requestedServices: list[str] = []
    notes: Optional[str] = None


class JobStatusUpdate(BaseModel):
    status: Literal[
        "requested",
        "scheduled",
        "in_progress",
        "completed",
        "cancelled",
    ]


def serialize_job(doc: dict) -> dict:
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return doc


def object_id_or_404(value: str) -> ObjectId:
    if not ObjectId.is_valid(value):
        raise HTTPException(status_code=404, detail="Job not found")
    return ObjectId(value)


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = AsyncMongoClient(settings.mongo_uri)
    db = client[settings.mongo_db]

    app.state.mongo_client = client
    app.state.db = db

    await db.jobs.create_index([
        ("tenantId", 1),
        ("status", 1),
        ("createdAt", -1),
    ])

    await db.jobs.create_index([
        ("location.coordinates", "2dsphere"),
    ])

    yield

    await client.close()


app = FastAPI(lifespan=lifespan)


@app.post("/jobs")
async def create_job(payload: JobCreate):
    now = datetime.now(timezone.utc)

    doc = payload.model_dump()
    doc.update({
        "tenantId": "demo-company",
        "status": "requested",
        "photos": [],
        "createdAt": now,
        "updatedAt": now,
        "version": 1,
    })

    result = await app.state.db.jobs.insert_one(doc)
    created = await app.state.db.jobs.find_one({"_id": result.inserted_id})

    return serialize_job(created)


@app.get("/jobs")
async def list_jobs(
    status: Optional[str] = None,
    city: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
):
    query = {"tenantId": "demo-company"}

    if status:
        query["status"] = status

    if city:
        query["location.city"] = city

    cursor = (
        app.state.db.jobs
        .find(query)
        .sort("createdAt", -1)
        .limit(limit)
    )

    jobs = []
    async for doc in cursor:
        jobs.append(serialize_job(doc))

    return jobs


@app.get("/jobs/{job_id}")
async def get_job(job_id: str):
    _id = object_id_or_404(job_id)

    doc = await app.state.db.jobs.find_one({
        "_id": _id,
        "tenantId": "demo-company",
    })

    if not doc:
        raise HTTPException(status_code=404, detail="Job not found")

    return serialize_job(doc)


@app.patch("/jobs/{job_id}/status")
async def update_job_status(job_id: str, payload: JobStatusUpdate):
    _id = object_id_or_404(job_id)

    result = await app.state.db.jobs.update_one(
        {
            "_id": _id,
            "tenantId": "demo-company",
        },
        {
            "$set": {
                "status": payload.status,
                "updatedAt": datetime.now(timezone.utc),
            },
            "$inc": {
                "version": 1,
            },
        },
    )

    if result.matched_count != 1:
        raise HTTPException(status_code=404, detail="Job not found")

    doc = await app.state.db.jobs.find_one({"_id": _id})
    return serialize_job(doc)


@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    _id = object_id_or_404(job_id)

    result = await app.state.db.jobs.delete_one({
        "_id": _id,
        "tenantId": "demo-company",
    })

    if result.deleted_count != 1:
        raise HTTPException(status_code=404, detail="Job not found")

    return {"deleted": True}
```

PyMongo’s current docs show `AsyncMongoClient` as the async client and note that async methods performing network operations must be awaited. ([MongoDB][8]) MongoDB also has an official FastAPI integration guide for PyMongo. ([MongoDB][9])

Run API:

```bash
uvicorn main:app --reload
```

Open:

```txt
http://127.0.0.1:8000/docs
```

FastAPI will give you interactive Swagger docs.

---

# Part 7 — Test the API

Create a job:

```bash
curl -X POST http://127.0.0.1:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "customer": {
      "name": "Anna Ivanova",
      "phone": "+31600000000"
    },
    "location": {
      "addressText": "Vondelpark, Amsterdam",
      "city": "Amsterdam",
      "country": "NL",
      "coordinates": {
        "type": "Point",
        "coordinates": [4.8726, 52.3579]
      }
    },
    "property": {
      "type": "apartment",
      "rooms": 2,
      "bathrooms": 1,
      "areaM2": 55
    },
    "requestedServices": [
      "regular_cleaning",
      "window_cleaning"
    ],
    "notes": "Customer wants cleaning before guests arrive."
  }'
```

List jobs:

```bash
curl http://127.0.0.1:8000/jobs
```

Filter by city:

```bash
curl "http://127.0.0.1:8000/jobs?city=Amsterdam"
```

Update status:

```bash
curl -X PATCH http://127.0.0.1:8000/jobs/<JOB_ID>/status \
  -H "Content-Type: application/json" \
  -d '{
    "status": "scheduled"
  }'
```

Delete:

```bash
curl -X DELETE http://127.0.0.1:8000/jobs/<JOB_ID>
```

---

# Your first tasks

Do these in order:

```txt
Task 1:
Launch MongoDB with Docker Compose.

Task 2:
Connect with mongosh as root.

Task 3:
Create cleaning_app user.

Task 4:
Connect with mongosh as cleaning_app.

Task 5:
Insert 3 cleaning jobs manually.

Task 6:
Query by:
- status
- city
- requested service
- property area

Task 7:
Update one job status from requested to scheduled.

Task 8:
Create the FastAPI app.

Task 9:
Create a job through /docs.

Task 10:
Verify in mongosh that the API-created job exists.
```

For now, the most important MongoDB ideas to absorb are:

```txt
Document = one JSON-like business object.
Collection = group of similar documents.
_id = automatic primary identifier.
Nested fields are normal.
Arrays are normal.
Indexes are mandatory for real queries.
Validation exists, but you choose to add it.
```

The big mental shift from Postgres is this:

```txt
In Postgres, you usually design tables first.

In MongoDB, you usually design around the main thing your app reads/writes together.
```

For your app, that main thing is probably:

```txt
cleaning job / cleaning request
```

Everything else — photos, events, messages, invoices — can come later once you feel comfortable with the basics.

[1]: https://www.mongodb.com/docs/mongodb-shell/?utm_source=chatgpt.com "Welcome to MongoDB Shell (mongosh)"
[2]: https://www.mongodb.com/docs/languages/python/?utm_source=chatgpt.com "MongoDB with Python"
[3]: https://www.mongodb.com/docs/v7.0/tutorial/install-mongodb-community-with-docker/?utm_source=chatgpt.com "Install MongoDB Community with Docker"
[4]: https://hub.docker.com/_/mongo?utm_source=chatgpt.com "mongo - Official Image | Docker Hub"
[5]: https://www.mongodb.com/docs/mongodb-shell/connect/?utm_source=chatgpt.com "Connect to a Deployment - mongosh - MongoDB Docs"
[6]: https://www.mongodb.com/docs/manual/core/schema-validation/?utm_source=chatgpt.com "Schema Validation - Database Manual - MongoDB Docs"
[7]: https://www.mongodb.com/docs/manual/core/schema-validation/specify-json-schema/?utm_source=chatgpt.com "Specify JSON Schema Validation - Database Manual"
[8]: https://www.mongodb.com/docs/languages/python/pymongo-driver/current/reference/migration/?utm_source=chatgpt.com "Migrate to PyMongo Async"
[9]: https://www.mongodb.com/docs/languages/python/pymongo-driver/current/integrations/fastapi-integration/?utm_source=chatgpt.com "Tutorial: FastAPI Integration - PyMongo Driver"
