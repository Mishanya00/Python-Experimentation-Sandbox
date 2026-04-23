from pathlib import Path

from miniopy_async import Minio


BASE_DIR = Path(__file__).resolve().parent.parent
FILES_DIR = BASE_DIR / "files"
FILES_DIR.mkdir(exist_ok=True)

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
