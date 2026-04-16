from miniopy_async import Minio


BUCKET_NAME = "my-bucket"
ENDPOINT = "localhost:9010"
ACCESS_KEY = "admin"
SECRET_KEY = "password"


minio_client = Minio(
    ENDPOINT,
    access_key=ACCESS_KEY,
    secret_key=SECRET_KEY,
    secure=False
)
