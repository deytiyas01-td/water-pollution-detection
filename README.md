# AquaGuard: AI Water Surface Pollution & Debris Detection System

AquaGuard is an end-to-end intelligent computer vision web application designed to detect and localize 14 specific types of water surface pollutants from images and drone/surveillance video footage using **Grounding DINO** zero-shot object detection.

---

## 🌊 Supported Detection Classes

The system can detect and differentiate:
1. **Plastic bottle**
2. **Plastic bag**
3. **Plastic wrapper**
4. **Floating garbage**
5. **Fishing net**
6. **Wood debris**
7. **Water hyacinth**
8. **Aquatic weeds**
9. **Oil spill**
10. **Surface foam**
11. **Dead fish**
12. **Dead animal**
13. **Ship**
14. **Sea creature on water surface**

---

## 🚀 Key Features

- **Multi-Format Media Input**:
  - **Images**: PNG, JPG, JPEG (High-resolution bounding box visualization).
  - **Videos**: MP4, MKV (Frame sampling, event timeline, debris timestamps, annotated video generator).
- **User-Friendly Web Interface**:
  - Dark-mode responsive design built with Tailwind CSS and Lucide icons.
  - Interactive sensitivity sliders (Confidence threshold, Text correlation threshold).
  - Category filter toggles to focus on specific debris types or all 14 pollutants.
  - Pollution severity meter (*Clean, Low, Moderate, Critical*).
  - Downloadable annotated images and videos with detected bounding boxes and labels.
- **Secure Backend**:
  - FastAPI asynchronous server architecture.
  - Protected API key verification via `X-API-Key` and `.env`.
  - Filename sanitization (UUID4) preventing path traversal.
  - Upload size validation and automatic purging of raw files after inference.
  - Pre-configured `.gitignore` to prevent leaking private keys or large model weights to GitHub.

---

## 🛠️ Project Structure

```
water-pollution-detection/
├── Models/                     # Grounding DINO model weights & configurations
│   ├── config.json
│   ├── model.safetensors
│   ├── preprocessor_config.json
│   ├── special_tokens_map.json
│   ├── tokenizer.json
│   ├── tokenizer_config.json
│   └── vocab.txt
├── backend/
│   ├── __init__.py
│   ├── config.py              # Configuration & environment variable loader
│   ├── detector.py            # Grounding DINO detection engine (Image & Video)
│   ├── security.py            # API key validation & file sanitization
│   └── main.py                # FastAPI REST API & static file server
├── static/
│   ├── css/style.css          # Styling & animations
│   ├── js/app.js              # Client application logic & UI reactivity
│   └── index.html             # Responsive user interface
├── uploads/                   # Temporary upload directory (auto-purged)
├── outputs/                   # Processed annotated images & videos
├── .env.example               # Safe environment variable template
├── .env                       # Local environment settings (gitignored)
├── .gitignore                 # Excludes .env, weights, logs, and uploads
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Production container definition
├── docker-compose.yml         # Container orchestration
├── run.py                     # Local startup script
└── DEPLOYMENT_GUIDE.md        # Comprehensive deployment options for 821MB models
```

---

## 💻 Quickstart (Local Development)

### 1. Ensure Dependencies are Installed
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
A `.env` file is already created locally. You can customize port or secret keys:
```env
PORT=8000
HOST=0.0.0.0
API_SECRET_KEY=             # Leave blank for public demo mode, or set a secret key
DEFAULT_BOX_THRESHOLD=0.25
```

### 3. Run the Application
```bash
python run.py
```
Open your browser at: **[http://localhost:8000](http://localhost:8000)**

---

## 📦 Deployment for 821 MB Model

Because this model is ~821 MB - 933 MB, serverless hosts like **Vercel** (50MB function limit) and **Render free tier** (512MB RAM cap) will fail.

Recommended alternatives (see `DEPLOYMENT_GUIDE.md` for full step-by-step instructions):
1. **Hugging Face Spaces (Free — 16GB RAM)**: Direct Docker space deployment.
2. **Decoupled Architecture**: Host weights on private Hugging Face Model Hub, deploy code on Railway / Fly.io / Google Cloud Run.
3. **Google Cloud Run**: Container deployment with 4GB RAM.
4. **Cloud VPS**: Docker Compose on DigitalOcean, Hetzner, or AWS.

---

## 🔒 Security Best Practices

- **Never remove `.env` from `.gitignore`**: All API keys and secrets stay on your server.
- **Never push large `.safetensors` files to standard GitHub**: Git repositories fail on files > 100MB. Use Git LFS or Hugging Face Model Hub.
