# Deployment Guide: Water Surface Pollution Detection (AquaGuard)

## Why Vercel & Render Fail for this Model
1. **Model Weight Size**: The Grounding DINO weights are **~860 MB compressed / 933 MB uncompressed**.
2. **Vercel Limitations**:
   - Vercel is designed for serverless static frontends and micro-functions.
   - Maximum serverless function bundle limit: **50 MB** (zipped) / **250 MB** (unzipped).
   - Execution timeout: 10s (Hobby) to 60s (Pro), which cuts off ML inference.
3. **Render Free Tier Limitations**:
   - RAM limit: **512 MB**. Loading PyTorch + Grounding DINO requires ~1.2 GB - 2.0 GB of RAM, causing immediate **`Out Of Memory (OOM) / SIGKILL (exit code 137)`** crashes.
   - Free instances spin down after inactivity, causing 3-minute cold starts.

---

## 4 Production-Ready Solutions for Deploying this 821MB Model

---

### Solution 1: Hugging Face Spaces (Recommended — 100% Free & No Memory Crashes)
Hugging Face Spaces provides **16 GB RAM**, 2 vCPUs for **free**, with built-in Git LFS support for large files (up to 50 GB).

#### Steps to Deploy:
1. Go to [huggingface.co](https://huggingface.co) and create a free account.
2. Click **New Space** -> Name it `water-pollution-detection`.
3. Select **Docker** (Blank) as the Space SDK.
4. Set Space visibility to **Public** or **Private**.
5. Clone your space locally:
   ```bash
   git clone https://huggingface.co/spaces/YOUR_USERNAME/water-pollution-detection
   ```
6. Copy the project files into the cloned folder:
   - `backend/`
   - `static/`
   - `Models/`
   - `Dockerfile`
   - `requirements.txt`
   - `run.py`
7. In the Dockerfile for Hugging Face Spaces, ensure the port is set to `7860`:
   ```dockerfile
   EXPOSE 7860
   CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
   ```
8. Commit and push:
   ```bash
   git add .
   git commit -m "Deploy AquaGuard Water Pollution Detection"
   git push
   ```
9. Hugging Face will automatically build the container and provide a live URL (`https://your-username-water-pollution-detection.hf.space`).

---

### Solution 2: Decoupled Architecture (Hugging Face Model Hub + Railway / Fly.io / Cloud Run)
Instead of shipping the 821 MB model directly in your Git repository, host the model weights on Hugging Face Model Hub, and host the web app on any container platform.

#### Step 1: Upload Weights to a Private Hugging Face Model Repository
1. On [huggingface.co](https://huggingface.co), click **New Model**.
2. Name it `water-pollution-grounding-dino` (Set to **Private**).
3. Upload the files inside `Models/` (`model.safetensors`, `config.json`, etc.) using the web interface or `huggingface-cli`.

#### Step 2: Configure Your App to Load from Hugging Face
In your `.env` file:
```env
MODEL_PATH=YOUR_USERNAME/water-pollution-grounding-dino
HF_TOKEN=hf_your_private_read_token
```
Because `AutoProcessor` and `AutoModelForZeroShotObjectDetection` natively support Hugging Face repository IDs, your backend will automatically download and cache the model securely at startup!

#### Step 3: Deploy on Railway / Fly.io
Now your GitHub repository is only **~2 MB**, allowing you to deploy on:
- **Railway.app** (Offers $5 free credit / inexpensive pay-per-use, 8GB RAM).
- **Fly.io** (Deploy with `fly launch` with 2GB - 4GB RAM).
- **Google Cloud Run**.

---

### Solution 3: Google Cloud Run (Serverless Container with up to 32GB RAM)
Google Cloud Run provides **2 million free requests per month** and scales containers to zero when not in use.

1. Install Google Cloud SDK (`gcloud`).
2. Build and submit your Docker image to Google Artifact Registry:
   ```bash
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/aquaguard-detection
   ```
3. Deploy to Cloud Run with 2GB - 4GB RAM:
   ```bash
   gcloud run deploy aquaguard \
     --image gcr.io/YOUR_PROJECT_ID/aquaguard-detection \
     --platform managed \
     --region us-central1 \
     --memory 4Gi \
     --cpu 2 \
     --allow-unauthenticated \
     --port 8000
   ```
4. Cloud Run will output a public HTTPS URL.

---

### Solution 4: Self-Hosted Cloud VPS (DigitalOcean / Hetzner / AWS EC2)
A basic cloud VPS gives you full control and no file size limits:
- **Hetzner Cloud**: ~€4.50/month for 4GB RAM.
- **DigitalOcean Droplet**: $6 - $12/month.

#### Steps on VPS:
```bash
# 1. Install Docker & Git
sudo apt-get update && sudo apt-get install -y docker.io docker-compose git

# 2. Clone your repository
git clone https://github.com/YOUR_USERNAME/water-pollution-detection.git
cd water-pollution-detection

# 3. Add .env configuration
cp .env.example .env
nano .env

# 4. Start the application
docker-compose up -d --build
```
Your website will be live at `http://your-server-ip:8000`!

---

## Security & GitHub Protection Checklist

1. **Never commit `.env`**:
   - The `.gitignore` is pre-configured to strictly ignore `.env`, `.env.local`, and any API credentials.
   - Use `.env.example` as a template for other collaborators.

2. **Never commit the 821MB Model weights to standard GitHub**:
   - GitHub has a strict **100 MB per file limit** and will reject pushes containing `model.safetensors`.
   - The `.gitignore` already excludes `*.safetensors`, `*.zip`, and `*.bin`.

3. **Protecting your API Key**:
   - In `.env`, you can set `API_SECRET_KEY=your_secret_password_here`.
   - Any external requests to `/api/detect/image` or `/api/detect/video` must provide the HTTP header `X-API-Key: your_secret_password_here`.
   - In the frontend UI, click the key icon (top right) to save your key in local storage.
