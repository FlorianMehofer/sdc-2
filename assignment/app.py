import os
from pathlib import Path
from uuid import uuid4
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import Response
from pydantic import BaseModel
from dotenv import load_dotenv
from image_generator import ImageGenerator

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# ============ STEP 1: Setup & Initialization ============
# Initialize ImageGenerator with API key (leave space for API key)
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY", "")
image_generator = ImageGenerator(STABILITY_API_KEY)

# Create images directory for storing generated images
IMAGES_DIR = Path("generated_images")
IMAGES_DIR.mkdir(exist_ok=True)

# ============ STEP 2: Data Models & State Management ============
class ImageRequest(BaseModel):
    prompt: str

# In-memory storage for image generation status
# Format: {image_id: {"status": "processing" | "ready" | "failed", "filepath": str, "error": str}}
image_storage: dict = {}


# ============ STEP 3: Background Task Function ============
def gen_image_task(image_id: str, prompt: str):
    """
    Background task that generates an image using the ImageGenerator service
    and saves it to disk.
    """
    try:
        # Generate image using the ImageGenerator service
        image_bytes = image_generator.generate_image(prompt)
        
        if image_bytes is None:
            image_storage[image_id]["status"] = "failed"
            image_storage[image_id]["error"] = "Failed to generate image"
            return
        
        # Save image to disk
        filepath = IMAGES_DIR / f"{image_id}.png"
        with open(filepath, "wb") as f:
            f.write(image_bytes)
        
        # Update storage with ready status and filepath
        image_storage[image_id]["status"] = "ready"
        image_storage[image_id]["filepath"] = str(filepath)
    except Exception as e:
        image_storage[image_id]["status"] = "failed"
        image_storage[image_id]["error"] = str(e)


# ============ STEP 4: API Endpoints ============

@app.get("/")
def root():
    return {"message": "FastAPI Image Generation Service"}


@app.post("/images")
async def generate_image(request: ImageRequest, background_tasks: BackgroundTasks):
    """
    Endpoint to request image generation.
    Accepts a prompt and queues the image generation as a background task.
    Returns an image_id for later retrieval.
    """
    # Generate unique image ID
    image_id = str(uuid4())
    
    # Initialize image tracking in storage
    image_storage[image_id] = {
        "status": "processing",
        "filepath": None,
        "error": None
    }
    
    # Queue the background task
    background_tasks.add_task(gen_image_task, image_id, request.prompt)
    
    return {
        "image_id": image_id,
        "status": "processing",
        "message": "Image generation has started. Use the image_id to retrieve your image."
    }


@app.get("/image/{image_id}")
def get_image(image_id: str):
    """
    Endpoint to retrieve a generated image by image_id.
    Returns the image if ready, or a status message otherwise.
    """
    # Check if image_id exists in storage
    if image_id not in image_storage:
        return {"error": "Image not found", "image_id": image_id}, 404
    
    image_data = image_storage[image_id]
    
    # If still processing, return status
    if image_data["status"] == "processing":
        return {
            "image_id": image_id,
            "status": "processing",
            "message": "Image is still being generated. Please try again later."
        }
    
    # If failed, return error
    if image_data["status"] == "failed":
        return {
            "image_id": image_id,
            "status": "failed",
            "error": image_data["error"]
        }, 500
    
    # If ready, return the image
    if image_data["status"] == "ready":
        filepath = image_data["filepath"]
        with open(filepath, "rb") as f:
            image_bytes = f.read()
        return Response(content=image_bytes, media_type="image/png")
    
    return {"error": "Unknown status", "image_id": image_id}, 500


@app.get("/example")
async def example_endpoint(background_tasks: BackgroundTasks):
    # This endpoint demonstrates how to add a background task.
    # The `write_log` function will be executed after the response is sent.
    # Note: The task runs in the same process but does not block the response.
    background_tasks.add_task(lambda: None)  # Placeholder
    return {"message": "This is an example endpoint"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
