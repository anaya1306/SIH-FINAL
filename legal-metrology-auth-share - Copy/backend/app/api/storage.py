import hashlib
import io
import os
import secrets
import time

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import Response
from PIL import Image
from sqlalchemy.orm import Session

from app.config import settings
from app.db.audit import create_audit_log
from app.db.database import get_db
from app.db.models import UserModel
from app.dependencies import require_inspector
from app.storage import decrypt_file, encrypt_file, generate_file_id


router = APIRouter(
    prefix="/storage",
    tags=["Secure Storage"],
)


S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", "")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "")
S3_BUCKET = os.getenv(
    "S3_BUCKET",
    "legal-metrology-images",
)

LOCAL_STORAGE_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "storage_data",
    )
)

MAX_FILE_SIZE = 10 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}

ALLOWED_FORMATS = {
    "JPEG",
    "PNG",
    "WEBP",
}

SIGNED_URL_EXPIRE_SECONDS = 300


def using_object_storage() -> bool:
    return bool(
        S3_ENDPOINT_URL
        and S3_ACCESS_KEY
        and S3_SECRET_KEY
    )


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT_URL,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
        region_name=os.getenv(
            "AWS_REGION",
            "ap-south-1",
        ),
    )


def save_local(file_id: str, encrypted_data: bytes):
    os.makedirs(LOCAL_STORAGE_DIR, exist_ok=True)

    path = os.path.join(
        LOCAL_STORAGE_DIR,
        f"{file_id}.enc",
    )

    with open(path, "wb") as storage_file:
        storage_file.write(encrypted_data)


def load_local(file_id: str) -> bytes:
    path = os.path.join(
        LOCAL_STORAGE_DIR,
        f"{file_id}.enc",
    )

    if not os.path.isfile(path):
        raise HTTPException(
            status_code=404,
            detail="File not found",
        )

    with open(path, "rb") as storage_file:
        return storage_file.read()


def create_signed_token(file_id: str) -> str:
    expires = int(time.time()) + SIGNED_URL_EXPIRE_SECONDS

    value = f"{file_id}:{expires}"

    signature = hashlib.sha256(
        f"{value}:{settings.secret_key}".encode()
    ).hexdigest()

    return f"{expires}.{signature}"


def verify_signed_token(
    file_id: str,
    token: str,
) -> bool:

    try:
        expires_text, signature = token.split(".", 1)

        expires = int(expires_text)

    except (ValueError, AttributeError):
        return False

    if expires < int(time.time()):
        return False

    value = f"{file_id}:{expires}"

    expected_signature = hashlib.sha256(
        f"{value}:{settings.secret_key}".encode()
    ).hexdigest()

    return secrets.compare_digest(
        signature,
        expected_signature,
    )


@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
)
async def upload_product_label(
    file: UploadFile = File(...),
    current_user: UserModel = Depends(require_inspector),
    db: Session = Depends(get_db),
):
    filename = file.filename or ""

    extension = os.path.splitext(
        filename.lower()
    )[1]

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only JPG, JPEG, PNG and WEBP images are allowed",
        )

    data = await file.read()

    if not data:
        raise HTTPException(
            status_code=400,
            detail="Empty file is not allowed",
        )

    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File size must not exceed 10 MB",
        )

    try:
        image = Image.open(io.BytesIO(data))
        image.verify()

        image = Image.open(io.BytesIO(data))

        if image.format not in ALLOWED_FORMATS:
            raise HTTPException(
                status_code=400,
                detail="Invalid image format",
            )

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is not a valid image",
        )

    file_id = generate_file_id(filename)

    encrypted_data = encrypt_file(data)

    object_key = f"product-labels/{file_id}.enc"

    file_hash = hashlib.sha256(data).hexdigest()

    try:
        if using_object_storage():

            s3 = get_s3_client()

            s3.put_object(
                Bucket=S3_BUCKET,
                Key=object_key,
                Body=encrypted_data,
                ContentType="application/octet-stream",
                Metadata={
                    "original-filename": filename,
                    "file-sha256": file_hash,
                    "uploaded-by": str(current_user.id),
                },
            )

        else:
            save_local(
                file_id,
                encrypted_data,
            )

    except (BotoCoreError, ClientError) as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Secure storage unavailable: {exc}",
        )

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="UPLOAD",
        resource="product-label",
        details=f"Encrypted image uploaded: {file_id}",
    )

    return {
        "message": "Product label uploaded securely",
        "file_id": file_id,
        "sha256": file_hash,
        "size": len(data),
        "uploaded_by": current_user.id,
        "storage": (
            "s3/minio"
            if using_object_storage()
            else "local-encrypted"
        ),
    }


@router.get("/{file_id}/signed-url")
def generate_signed_url(
    file_id: str,
    current_user: UserModel = Depends(require_inspector),
    db: Session = Depends(get_db),
):
    token = create_signed_token(file_id)

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="SIGNED_URL_CREATED",
        resource="product-label",
        details=f"Temporary access granted for file {file_id}",
    )

    return {
        "file_id": file_id,
        "expires_in_seconds": SIGNED_URL_EXPIRE_SECONDS,
        "access_token": token,
        "download_path": (
            f"/storage/{file_id}/download"
            f"?token={token}"
        ),
    }


@router.get("/{file_id}/download")
def download_product_label(
    file_id: str,
    token: str = Query(...),
    current_user: UserModel = Depends(require_inspector),
    db: Session = Depends(get_db),
):
    if not verify_signed_token(
        file_id,
        token,
    ):
        raise HTTPException(
            status_code=403,
            detail="Invalid or expired signed access token",
        )

    try:
        if using_object_storage():

            s3 = get_s3_client()

            object_data = s3.get_object(
                Bucket=S3_BUCKET,
                Key=f"product-labels/{file_id}.enc",
            )

            encrypted_data = object_data["Body"].read()

        else:
            encrypted_data = load_local(file_id)

        decrypted_data = decrypt_file(
            encrypted_data
        )

    except (BotoCoreError, ClientError):
        raise HTTPException(
            status_code=404,
            detail="Stored file not found",
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to decrypt stored file",
        )

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="DOWNLOAD",
        resource="product-label",
        details=f"Secure image accessed: {file_id}",
    )

    return Response(
        content=decrypted_data,
        media_type="image/*",
    )