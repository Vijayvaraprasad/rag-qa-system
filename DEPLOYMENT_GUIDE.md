# GUIDE: Push to GitHub & Deploy on Render

---

## PART 1: PREPARE YOUR PROJECT FOR GIT

### Step 1: Verify .gitignore is correct

```bash
# Check what will be pushed (should not include data/, venv/, .env)
git status
```

Expected output (GOOD):
```
On branch main
Changes not staged for commit:
  modified:   app/main.py
  modified:   requirements.txt
  
Untracked files:
  .gitignore
  README.md
```

Expected NOT to show:
```
data/chroma_db/
data/raw_docs/
.env
__pycache__/
venv/
```

### Step 2: Update README.md (Make it presentable)

Your current README.md is good. Just make sure it has:

```markdown
# Advanced RAG QA System

A production-grade Retrieval Augmented Generation (RAG) system with 13 advanced features.

## Features
- Semantic + Keyword hybrid search
- Query expansion
- Multi-hop retrieval
- Answer verification
- Context compression
- Caching with feedback
- Knowledge graphs
- And more...

## Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key OR Groq API key (free)

### Installation

```bash
git clone <your-repo-url>
cd rag-qa-system
pip install -r requirements.txt
```

### Set API Key

```bash
# Using Groq (FREE!)
export GROQ_API_KEY='gsk-...'

# OR Using OpenAI (paid)
export OPENAI_API_KEY='sk-...'
```

### Run the Server

```bash
python -m uvicorn app.main:app --reload --port 8000
```

### Upload Document & Ask Question

```bash
# Upload
curl -X POST "http://localhost:8000/upload" \
  -F "file=@document.pdf"

# Ask
curl "http://localhost:8000/ask?question=Your%20question%20here"
```

## API Endpoints

- `POST /upload` - Upload documents
- `POST /ask` - Basic Q&A
- `POST /ask/advanced` - Advanced Q&A with all features
- `POST /ask/compare` - Compare retrieval methods
- `POST /feedback` - Provide feedback
- `GET /stats` - System statistics
- `GET /health` - Health check

## Architecture

[See ARCHITECTURE.md]

## Performance

- First query: 2-4 seconds
- Cached query: 0.05 seconds (50x faster!)
- Cost reduction: 80% with compression
- Free LLM: Groq (no OpenAI needed)

## Deployment

[See DEPLOYMENT_GUIDE.md]

---
```

### Step 3: Create DEPLOYMENT_GUIDE.md (For Render)

I'll create this in the next step.

---

## PART 2: INITIALIZE GIT & PUSH TO GITHUB

### Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `rag-qa-system`
3. Description: "Advanced Retrieval Augmented Generation QA System with 13 features"
4. Choose: **Public** (for Render to access)
5. Click "Create repository"
6. Copy the repository URL (e.g., `https://github.com/your-username/rag-qa-system.git`)

### Step 2: Initialize Git Locally

```bash
# Navigate to your project
cd c:\Users\VIJAY\OneDrive\Desktop\rag-qa-system

# Initialize git
git init

# Add all files (respects .gitignore)
git add .

# Check what will be committed
git status

# Commit
git commit -m "Initial commit: Complete RAG QA system with 13 advanced features"
```

### Step 3: Add Remote & Push

```bash
# Add remote (replace with your repo URL)
git remote add origin https://github.com/your-username/rag-qa-system.git

# Verify remote is set
git remote -v

# Push to GitHub
git branch -M main
git push -u origin main
```

**Expected output:**
```
Enumerating objects: 45, done.
Counting objects: 100% (45/45), done.
Delta compression using up to 8 threads
Compressing objects: 100% (42/42), done.
Writing objects: 100% (45/45), 156.23 KiB | 1.5 MiB/s, done.
...
 * [new branch]      main -> main
Branch 'main' is set up to track remote branch 'main' from 'origin'.
```

### Step 4: Verify on GitHub

Go to `https://github.com/your-username/rag-qa-system`

You should see:
- ✓ `app/` folder (all your code)
- ✓ `requirements.txt`
- ✓ `README.md`
- ✓ `ARCHITECTURE.md`
- ✗ `data/` folder (ignored)
- ✗ `venv/` folder (ignored)
- ✗ `.env` file (ignored)

**Perfect! Clean repository! ✅**

---

## PART 3: DEPLOY ON RENDER

### Best Platform for This Project: **RENDER**

Why Render?
- Free tier available
- Simple GitHub integration
- One-click deployment
- No credit card needed (free tier)
- Works with FastAPI
- Auto-deploy on git push

### Step 1: Create Render Account

1. Go to https://render.com
2. Sign up with GitHub (easier!)
3. Authorize Render to access your GitHub

### Step 2: Create New Web Service

1. Dashboard → New → Web Service
2. Connect your GitHub repository
3. Select: `rag-qa-system`
4. Choose: **Start with Render GitHub Integration**

### Step 3: Configure Deployment

Fill in these settings:

```
Name: rag-qa-system
Environment: Python 3.11
Region: Singapore (or closest to you)
Branch: main

Build Command:
pip install -r requirements.txt

Start Command:
uvicorn app.main:app --host 0.0.0.0 --port 10000
```

### Step 4: Add Environment Variables

1. In Render dashboard, go to your service
2. Click "Environment" (left sidebar)
3. Add these:

```
GROQ_API_KEY = gsk-...your-key...
```

OR

```
OPENAI_API_KEY = sk-...your-key...
```

### Step 5: Deploy!

1. Click "Deploy" button
2. Wait 3-5 minutes
3. Get your URL: `https://rag-qa-system.onrender.com`

---

## PART 4: TEST DEPLOYED API

### Upload Document

```bash
curl -X POST "https://rag-qa-system.onrender.com/upload" \
  -F "file=@document.pdf"
```

### Ask Question

```bash
curl "https://rag-qa-system.onrender.com/ask?question=What%20did%20Newton%20invent?"
```

### Advanced Q&A

```bash
curl -X POST "https://rag-qa-system.onrender.com/ask/advanced" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What did Newton invent?",
    "use_hybrid_search": true,
    "expand_queries": true,
    "compress_context": true,
    "verify_answer": true
  }'
```

---

## PART 5: ALTERNATIVE DEPLOYMENT PLATFORMS

### Option 1: Railway (Recommended if Render free tier expires)

**Pros:**
- Clean interface
- $5/month free credit
- Auto-scaling
- GitHub integration

**Steps:**
1. Go to https://railway.app
2. Sign up with GitHub
3. Create new project → GitHub repo
4. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port 8080`
5. Add environment variables
6. Deploy

### Option 2: Heroku (Now paid)

Note: Heroku free tier ended. Now charges $5+/month.

**If you want to use it:**
1. Go to https://heroku.com
2. Create new app
3. Connect GitHub repository
4. Deploy

### Option 3: AWS EC2 (More control, more complex)

**Pros:**
- Free tier available (1 year)
- More control
- Better performance

**Steps:**
1. Create AWS account
2. Launch EC2 instance (t2.micro free tier)
3. SSH into instance
4. Install Python, pip
5. Clone your repo
6. Install dependencies
7. Run with Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app.main:app
```
8. Set up Nginx as reverse proxy
9. Get domain name

### Option 4: PythonAnywhere

**Pros:**
- Easiest for Flask/FastAPI
- Free tier available
- No DevOps needed

**Steps:**
1. Go to https://pythonanywhere.com
2. Sign up
3. Upload code via GitHub
4. Configure WSGI file
5. Deploy

---

## PART 6: PRODUCTION CHECKLIST

Before deployment, ensure:

### Code Quality
- [ ] All imports work
- [ ] No hardcoded API keys (use .env)
- [ ] Error handling in place
- [ ] Logging configured

### Configuration
- [ ] .gitignore has all sensitive files
- [ ] Environment variables configured on platform
- [ ] requirements.txt has all dependencies
- [ ] Python version specified (3.8+)

### API
- [ ] Health endpoint working
- [ ] Endpoints tested locally
- [ ] Error responses formatted
- [ ] CORS headers if needed

### Documentation
- [ ] README.md complete
- [ ] API docs (FastAPI auto-generates at /docs)
- [ ] Deployment guide included
- [ ] Setup instructions clear

---

## PART 7: OPTIMIZE FOR PRODUCTION

### Update requirements.txt (Clean version)

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
sentence-transformers==2.2.2
chromadb==0.4.15
PyPDF2==3.0.1
nltk==3.8.1
torch==2.1.1
python-multipart==0.0.6
openai==1.3.5
rank-bm25==0.2.2
requests==2.31.0
numpy==1.26.2
groq==0.4.1
spacy==3.7.2
```

### Optional: Create startup script

Create `start.sh`:

```bash
#!/bin/bash
pip install -r requirements.txt
python -m nltk.downloader punkt
python -m nltk.downloader punkt_tab
python -m spacy download en_core_web_sm
uvicorn app.main:app --host 0.0.0.0 --port 10000
```

### Optional: Create Procfile (for Heroku)

```
web: gunicorn -w 4 -b 0.0.0.0:$PORT app.main:app
```

---

## PART 8: FINAL COMMANDS SUMMARY

### Local Setup
```bash
cd c:\Users\VIJAY\OneDrive\Desktop\rag-qa-system
git init
git add .
git commit -m "Initial commit: RAG QA System"
git remote add origin https://github.com/YOUR_USERNAME/rag-qa-system.git
git push -u origin main
```

### Create on Render
1. Connect GitHub to Render
2. Select `rag-qa-system` repo
3. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port 10000`
4. Add `GROQ_API_KEY` environment variable
5. Deploy!

### Test Live
```bash
curl https://rag-qa-system.onrender.com/health
```

---

## PART 9: AFTER DEPLOYMENT

### Monitor Your App
```bash
# Check logs on Render dashboard
# Check uptime
# Monitor API usage
```

### Update Code
```bash
# Make changes locally
git add .
git commit -m "Fix: Description of change"
git push origin main

# Render automatically redeploys!
# Takes 2-5 minutes
```

### Share Your Project
```
GitHub: https://github.com/YOUR_USERNAME/rag-qa-system
Live API: https://rag-qa-system.onrender.com
API Docs: https://rag-qa-system.onrender.com/docs
```

---

## QUICK TROUBLESHOOTING

### "502 Bad Gateway" on Render
- Check environment variables are set
- Check logs on Render dashboard
- Verify start command is correct

### "Module not found" error
- Add missing package to requirements.txt
- Push to GitHub (auto-redeploys)

### API key not working
- Check environment variable name matches code
- Restart service on Render

### Out of storage on free tier
- Delete old data on service restart
- Or upgrade to paid plan

---

## RECOMMENDED DEPLOYMENT FLOW

```
1. Code locally + Test
   ↓
2. Commit & Push to GitHub
   ↓
3. Deploy on Render (free tier)
   ↓
4. Monitor for 24 hours
   ↓
5. If issues → Fix locally → Push
   ↓
6. Share with others!
   ↓
7. Get feedback
   ↓
8. Iterate (rinse and repeat)
```

---

**You're ready to go live! 🚀**

Your RAG QA System will be available at: `https://rag-qa-system.onrender.com`

Anyone can upload documents and ask questions!
