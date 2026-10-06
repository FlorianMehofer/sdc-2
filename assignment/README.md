# FastAPI Image Generation Service with Stable Diffusion

A FastAPI application that integrates Stable Diffusion via Stability AI to generate images from text prompts asynchronously.

## Setup & Installation

1. Install dependencies:
```bash
cd assignment
uv sync
```

2. Configure API key in `.env`:
```
STABILITY_API_KEY=your-api-key-here
```

3. Run the server:
```bash
uv run uvicorn app:app --reload
```

API documentation: `http://127.0.0.1:8000/docs`

## API Usage

### POST `/images` - Request Image Generation
```json
{
  "prompt": "A crocodile and a bear fighting"
}
```
Returns: `image_id` for later retrieval

### GET `/image/{image_id}` - Retrieve Image
Returns the generated PNG image if ready, status message if processing, or error if failed.

## Implementation Notes

- **FastAPI Setup**: Basic FastAPI application with pydantic models (from FastAPI tutorial example 6)
- **Asynchronous Processing**: Uses FastAPI's `BackgroundTasks` to queue image generation without blocking responses
- **Background Task**: `gen_image_task()` calls `ImageGenerator.generate_image()`, saves image to disk, and tracks status
- **Image Storage**: In-memory dictionary tracks image states (processing/ready/failed); images saved locally
- **Prompt System**: Users provide simple text prompts; `ImageGenerator` enhances them with template details (comical sketch, high resolution, etc.) for better results
- **Error Handling**: Catches exceptions during generation and reports failure status

The core implementation closely follows the patterns from `1_fast_api_tutorial/examples/6_fast_main.py` using Pydantic models and BackgroundTasks.