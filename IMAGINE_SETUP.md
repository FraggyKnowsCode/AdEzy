# AI Poster Generator Setup Instructions

## Installation Steps

1. Install the required package:
```bash
pip install google-generativeai
```

Or install from requirements.txt:
```bash
pip install -r requirements.txt
```

## Configuration

2. Add your Gemini API key to `adezy/settings.py`:
```python
# Gemini API Configuration
GEMINI_API_KEY = 'YOUR_GEMINI_API_KEY_HERE'
```

3. Create the media/posters directory:
```bash
mkdir -p media/posters
```

## Usage

1. Navigate to the "Imagine" link in the navbar (visible when logged in)
2. Upload your product image (required)
3. Upload your brand logo (optional)
4. Add a description of what you want in the poster
5. Click "Generate Poster"
6. Wait 10-20 seconds for AI generation
7. Download your poster and copy the AI-generated caption

## Features

- **AI-Powered Captions**: Uses Gemini AI to create catchy social media captions
- **Beautiful Poster Design**: Automatically creates professional posters with:
  - Gradient backgrounds
  - Product image with shadow effects
  - Brand logo placement
  - Decorative banners
- **Instant Preview**: See your generated poster immediately
- **Easy Download**: One-click download in high quality
- **Copy Caption**: Copy AI-generated caption with emojis and hashtags

## Technical Details

- Poster Size: 1080x1080px (Instagram square format)
- Format: JPEG with 95% quality
- Image Processing: PIL/Pillow
- AI Model: Gemini Pro for caption generation
- Storage: Saved in media/posters/ directory

## API Endpoint

The generate poster API is available at:
- URL: `/api/generate-poster/`
- Method: POST
- Content-Type: multipart/form-data
- Parameters:
  - product_image (file, required)
  - logo_image (file, optional)
  - description (text, required)
- Response: JSON with poster_url and AI-generated description
