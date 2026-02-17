# 🚀 Deployment Guide: Render

This guide walks you through deploying Smart-Citizen API to Render.

---

## ✅ Prerequisites Checklist

Before deploying, ensure:

- [ ] Git repository is pushed to GitHub/GitLab/Bitbucket
- [ ] OpenAI API key is available (required for embeddings and LLM)
- [ ] PDF files are committed to git in `data/raw/`
- [ ] All changes are committed and pushed

---

## 📋 Step-by-Step Deployment

### 1. Create Render Account
- Go to [render.com](https://render.com)
- Sign up (free tier available)
- Connect your Git provider (GitHub recommended)

### 2. Create New Web Service

1. Click **"New +"** → **"Web Service"**
2. Connect your repository
3. Select the `Smart-Citizen` repository
4. Configure the service:

```
Name: smart-citizen-api
Runtime: Python 3
Region: Oregon (or your preferred region)
Branch: main
Build Command: ./build.sh
Start Command: uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

**Important**: Select **Python 3.10** or **Python 3.11**

### 3. Set Environment Variables

In the Render dashboard, add these environment variables:

| Key | Value | Notes |
|-----|-------|-------|
| `OPENAI_API_KEY` | `sk-proj-...` | **REQUIRED** - Your OpenAI API key |
| `PYTHON_VERSION` | `3.10.0` | Specify Python version |

**⚠️ CRITICAL**: The `OPENAI_API_KEY` is **required** for:
- OpenAI embeddings (text-embedding-3-small)
- LLM inference (gpt-4o-mini)
- Query translation (EN/Kiswahili/Sheng)

Without it, deployment will fail.

### 4. Deploy

1. Click **"Create Web Service"**
2. Render will:
   - Clone your repository
   - Run `build.sh` (installs dependencies, builds vector store)
   - Start the FastAPI server
3. First deployment takes **5-15 minutes** (vector store build)

### 5. Monitor Build Logs

Watch the logs for:
```
📦 Installing Python dependencies...
📄 Checking for PDF documents...
✅ PDF documents found
🔨 Building vector store...
✅ Vector store built successfully!
✅ Build completed successfully!
🚀 Loading Haki Sovereign AI Engine...
✅ Engine loaded successfully!
```

### 6. Test Your Deployment

Once deployed, test these endpoints:

**Health Check:**
```bash
curl https://your-app-name.onrender.com/health
```

**Ask Question:**
```bash
curl -X POST https://your-app-name.onrender.com/api/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the qualifications to be president?",
    "language": "en"
  }'
```

---

## 🔧 Common Issues & Solutions

### Issue 1: Build Fails - "OPENAI_API_KEY not set"
**Solution**: Add `OPENAI_API_KEY` to Environment Variables in Render dashboard

### Issue 2: Build Times Out
**Cause**: Vector store build takes too long on free tier
**Solution**: 
- Upgrade to Starter plan for more build time
- Or pre-build vector store and commit to git (not recommended for large stores)

### Issue 3: "PDF documents not found"
**Cause**: PDFs not committed to git
**Solution**:
```bash
git add data/raw/*.pdf
git commit -m "Add PDF documents for deployment"
git push
```

### Issue 4: ImportError for langdetect or langchain-huggingface
**Cause**: Missing dependencies
**Solution**: Already fixed in `requirements.txt` - redeploy

### Issue 5: Windows Path Errors (TESSERACT_CMD)
**Cause**: Hard-coded Windows paths
**Solution**: Already fixed in `config.py` - redeploy

---

## 🎯 Performance Tips

### For Free Tier:
- First request may be slow (cold start)
- Service sleeps after 15 min of inactivity
- 512MB RAM limit

### For Production:
- Use **Starter** plan ($7/mo) for:
  - No cold starts
  - More RAM (1GB+)
  - Faster builds
- Consider caching common queries
- Monitor usage in Render dashboard

---

## 🔄 Updating Your Deployment

After making changes locally:

```bash
# 1. Test locally first
uvicorn api.main:app --reload

# 2. Commit and push
git add .
git commit -m "Update API"
git push

# 3. Render auto-deploys (if auto-deploy enabled)
# Or manually trigger deploy in Render dashboard
```

---

## 📊 Monitoring

### Check Logs:
- Render Dashboard → Your Service → Logs tab
- Look for startup messages and errors

### Check Metrics:
- CPU usage
- Memory usage  
- Request counts

### Set Up Alerts:
- Failed deployments
- High error rates
- Memory/CPU spikes

---

## 🌐 Custom Domain (Optional)

To use your own domain:
1. Render Dashboard → Settings → Custom Domain
2. Add your domain (e.g., `api.smartcitizen.ke`)
3. Update DNS records as shown
4. Enable HTTPS (automatic with Render)

---

## 🔐 Security Best Practices

1. **Never commit secrets** - Use environment variables
2. **CORS Configuration** - Update `CORSMiddleware` in `api/main.py`:
   ```python
   allow_origins=["https://yourfrontend.com"]  # Not ["*"]
   ```
3. **Rate Limiting** - Add rate limiting for production
4. **API Keys** - Consider adding API key authentication
5. **HTTPS Only** - Render provides this automatically

---

## 📝 Troubleshooting Commands

**View recent logs:**
```bash
# From Render dashboard Logs tab, or use Render CLI:
render logs -s your-service-name --tail 100
```

**Rebuild vector store:**
```bash
# SSH into Render (paid plans only), or trigger rebuild:
# Add a dummy environment variable to force rebuild
```

**Check Python version:**
Look for in build logs: `Python 3.10.x`

---

## 🆘 Need Help?

1. Check build logs in Render dashboard
2. Review error messages carefully
3. Common errors are documented above
4. Render documentation: [render.com/docs](https://render.com/docs)

---

## ✅ Post-Deployment Checklist

After successful deployment:

- [ ] Test `/health` endpoint
- [ ] Test `/api/ask` with sample questions
- [ ] Test multilingual support (EN, Kiswahili, Sheng)
- [ ] Verify sources/citations in responses
- [ ] Check `/docs` (Swagger UI) is accessible
- [ ] Monitor first few requests for errors
- [ ] Set up error alerts
- [ ] Document your API URL for frontend team

---

## 🎉 Success!

Your Smart-Citizen API is now live! Share your API URL:
```
https://your-app-name.onrender.com
```

Next steps:
- Build frontend to consume this API
- Add more documents to knowledge base
- Monitor usage and performance
- Iterate based on user feedback
