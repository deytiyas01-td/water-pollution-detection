# Step-by-Step Guide: Push to GitHub & Deploy to Hugging Face Spaces

This guide walks you through pushing the code to **GitHub** and deploying the web application to **Hugging Face Spaces** (Free 16 GB RAM).

---

## 🔒 1. Security Check (Already Configured)
- **`.env`** is completely ignored by `.gitignore` — your private API keys and credentials are safe and will never be pushed.
- **`model.safetensors` (821 MB)** is excluded from the standard GitHub push so GitHub will never reject your upload due to its 100 MB file size limit.

---

## 🐙 Step 1: Push Code to GitHub

1. Open your browser and go to **[github.com/new](https://github.com/new)**.
2. Enter Repository name: `water-pollution-detection`
3. Set visibility to **Public** or **Private** (choose whichever you prefer).
4. **Do NOT** initialize with a README, `.gitignore`, or license (we already created them).
5. Click **Create repository**.
6. In your terminal, run the following commands (replace `YOUR_GITHUB_USERNAME` with your actual GitHub username):

```bash
cd "C:\Users\TIYAS DEY\.gemini\antigravity\scratch\water-pollution-detection"

# Rename branch to main
git branch -M main

# Add your GitHub repository as origin
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/water-pollution-detection.git

# Push the code to GitHub
git push -u origin main
```

Your code and frontend are now securely on GitHub!

---

## 🤗 Step 2: Deploy to Hugging Face Spaces (Free 16 GB RAM)

Hugging Face Spaces natively supports models over 800 MB using Git LFS and provides **16 GB RAM** on its free tier.

### Option A: Direct Push to Hugging Face Space with Git LFS (Easiest)

1. Go to **[huggingface.co/new-space](https://huggingface.co/new-space)**.
2. Configure your Space:
   - **Space name**: `water-pollution-detection`
   - **License**: `mit` or `apache-2.0`
   - **Space SDK**: Select **Docker** (Blank)
   - **Hardware**: **CPU Basic (2 vCPU · 16GB RAM · Free)**
3. Click **Create Space**.
4. In your terminal, enable Git LFS and push to Hugging Face:

```bash
cd "C:\Users\TIYAS DEY\.gemini\antigravity\scratch\water-pollution-detection"

# Initialize Git LFS (Large File Storage)
git lfs install
git lfs track "Models/model.safetensors"
git add .gitattributes Models/model.safetensors
git commit -m "Track model weights with Git LFS for Hugging Face"

# Add Hugging Face Space as a remote (replace YOUR_HF_USERNAME with your Hugging Face username)
git remote add space https://huggingface.co/spaces/YOUR_HF_USERNAME/water-pollution-detection.git

# Push to Hugging Face Space
git push space main
```

*(When prompted for credentials on git push, enter your Hugging Face username and your **Access Token** as the password from [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)).*

---

### Option B: Host Model on Hugging Face Model Hub & Connect Space to GitHub

If you prefer to keep your GitHub repo and Hugging Face Space automatically in sync:

1. **Upload weights to HF Model Hub**:
   - Go to [huggingface.co/new](https://huggingface.co/new) -> Create a new **Model** (e.g. `water-pollution-grounding-dino`).
   - Upload the files from your local `Models/` folder (`model.safetensors`, `config.json`, etc.).
2. **Create a Docker Space connected to GitHub**:
   - Go to [huggingface.co/new-space](https://huggingface.co/new-space) -> Docker.
   - In **Settings** -> **Variables and secrets**, add:
     - `MODEL_PATH`: `YOUR_HF_USERNAME/water-pollution-grounding-dino`
3. The Space will build from your GitHub repository, load the model directly from the Hub on startup, and launch!

---

## 🌐 Accessing Your Live Website
Once built, your web app will be live and accessible worldwide at:
```
https://YOUR_HF_USERNAME-water-pollution-detection.hf.space
```
You can share this link with anyone, embed it into another website, or use it as an interactive portfolio project!
