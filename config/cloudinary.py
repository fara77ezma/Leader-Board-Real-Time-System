import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv
from fastapi import HTTPException, status, UploadFile
import logging

load_dotenv()
logger = logging.getLogger(__name__)

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)


async def upload_avatar(file: UploadFile, user_name: str) -> str:

    allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/webp"]

    if file.content_type not in allowed_types:
        logger.warning(f"Invalid file type: {file.content_type}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: JPEG, PNG, WebP",
        )

    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB in bytes

    # Read file content
    file_content = await file.read()
    file_size = len(file_content)

    if file_size > MAX_FILE_SIZE:
        logger.warning(f"File too large: {file_size} bytes")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: 5MB",
        )

    # Reset file pointer for upload
    await file.seek(0)

    logger.info(f"Uploading avatar for user {user_name}, size: {file_size} bytes")

    try:
        result = cloudinary.uploader.upload(
            file.file,
            folder="leaderboard/avatars",  # Organize in folder
            public_id=f"user_{user_name}",  # Unique ID per user
            overwrite=True,  # Replace old avatar
            transformation=[
                {
                    "width": 200,
                    "height": 200,
                    "crop": "fill",
                    "gravity": "face",
                },  # Auto crop to face
                {"quality": "auto"},  # Auto quality optimization
                {"fetch_format": "auto"},  # Auto format (WebP for modern browsers)
            ],
        )

        avatar_url = result["secure_url"]
        logger.info(f"✅ Avatar uploaded successfully: {avatar_url}")

        return avatar_url

    except Exception as e:
        logger.error(f"Cloudinary upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload avatar. Please try again.",
        )


async def delete_avatar(user_name: str) -> bool:
    try:
        public_id = f"leaderboard/avatars/user_{user_name}"
        result = cloudinary.uploader.destroy(public_id)

        logger.info(f"Avatar deleted for user {user_name}: {result}")
        return result.get("result") == "ok"

    except Exception as e:
        logger.error(f"Failed to delete avatar: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete avatar. Please try again.",
        )
        return False
