# Streamlit Cloud Deployment Guide

## Finance RAG Application - Ready for Production

This guide walks you through deploying the Finance RAG application to Streamlit Cloud.

---

## Prerequisites

1. **GitHub Repository**: Push your code to GitHub
   ```bash
   git add .
   git commit -m "Fix RAG retrieval for financial tables"
   git push origin main
   ```

2. **API Keys Ready**:
   - ✓ OpenAI API key (`OPENAI_API_KEY`)
   - ✓ Groq API key (`GROQ_API_KEY`)

3. **Streamlit Account**: Create free account at [share.streamlit.io](https://share.streamlit.io)

---

## Step 1: Deploy to Streamlit Cloud

### Option A: Deploy from GitHub (Recommended)

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **"New app"**
3. Select:
   - **Repository**: `Girikannan2107/finance-quarterly-rag`
   - **Branch**: `main`
   - **Main file path**: `streamlit_app.py`
4. Click **"Deploy"**

Streamlit will build your app automatically (~2-3 minutes).

### Option B: Manual Upload

```bash
streamlit run streamlit_app.py --logger.level=info
```

---

## Step 2: Add Secrets to Streamlit Cloud

After deployment starts:

1. Go to your app's **Advanced Settings** (⚙️ menu)
2. Click **"Secrets"** tab
3. Copy and paste this format:

```toml
OPENAI_API_KEY = "sk-proj-xxxxxxxxxxxx"
GROQ_API_KEY = "gsk-xxxxxxxxxxxx"
```

Replace with your actual API keys.

**Security Note**: Secrets are encrypted and never exposed in logs.

---

## Step 3: Test Your Deployment

Once the app is live:

1. Open your Streamlit Cloud URL
2. Upload 4 HCLTech PDFs:
   - `HCLTech_Q1_FY25.pdf`
   - `HCLTech_Q2_FY25.pdf`
   - `HCLTech_Q3_FY25.pdf`
   - `HCLTech_Q4_FY25.pdf`
3. Click **"Index documents"**
4. Test with query: **"What was the total income each quarter?"**
5. Verify:
   - ✓ 205 chunks indexed
   - ✓ Retrieved chunks contain financial data
   - ✓ Similarity scores shown
   - ✓ Answer is grounded in context

---

## Configuration Files

### `.streamlit/config.toml`
Cloud-safe configuration:
- Theme colors and fonts
- Security settings (CORS disabled, XSRF enabled)
- Error display level
- Max upload size: 200MB

### `.streamlit/secrets.toml`
**Local reference only** (excluded from git via .gitignore).
Secrets in cloud are managed via dashboard.

### `requirements.txt`
All dependencies including:
- `openai` (embeddings + LLM)
- `chromadb` (vector database)
- `streamlit` (UI)
- `groq` (fallback LLM)
- `pypdf` (PDF extraction)

---

## Storage & Persistence

### ChromaDB on Streamlit Cloud

Streamlit Cloud provides 1GB file storage in `/home/appuser/.cache/` and `/tmp/`.

**Current Setup**:
- ChromaDB uses `chroma_db/chroma.sqlite3`
- Stored in workspace (fresh on each deploy)
- PDFs cached after first indexing

**Behavior**:
- First visit: Upload PDFs → Index → Cold start (~30s)
- Subsequent visits: Chunks already indexed → Instant retrieval
- App restart: Chroma data reloaded from persistent storage

**Upgrade Path** (when needed):
For production persistence across deployments, add:
- PostgreSQL (via Heroku/AWS/SupaBase)
- Cloud object storage (S3/GCS)
- See `FUTURE_DEPLOYMENT.md`

---

## Troubleshooting

### Issue: "API key missing" error
**Solution**: Add secrets to Streamlit Cloud dashboard
- Go to app Advanced Settings → Secrets
- Add `OPENAI_API_KEY` and `GROQ_API_KEY`
- Rerun the app

### Issue: Slow indexing on first visit
**Expected behavior**: 205 chunks × embedding model = ~10-30 seconds
- Using `text-embedding-3-small` (fast)
- Batch processing (64 chunks at a time)
- Only runs once per session

### Issue: PDF upload fails
**Check**:
- File size < 200MB (set in config.toml)
- PDF is machine-readable (not scanned image)
- Browser supports file upload

### Issue: Answer refuses to respond
**Check**:
1. Verify retrieval debug shows relevant chunks
2. Check chunks contain financial keywords
3. Check API quotas (OpenAI/Groq)

---

## Monitoring & Logs

### View Logs
In Streamlit Cloud dashboard:
1. Click your app name
2. Select **"Logs"** tab
3. Check for errors/warnings

### Performance Metrics
Monitor in dashboard:
- App uptime
- Python version
- Memory usage
- Recent deployments

---

## Deployment Checklist

- [ ] GitHub repository up to date
- [ ] `requirements.txt` has all dependencies
- [ ] `.streamlit/config.toml` configured
- [ ] `.streamlit/secrets.toml` added to `.gitignore`
- [ ] `.env` added to `.gitignore`
- [ ] API keys ready (OpenAI + Groq)
- [ ] Streamlit account created
- [ ] App deployed to cloud
- [ ] Secrets added to cloud dashboard
- [ ] PDFs uploaded and indexed
- [ ] Test question works: "What was the total income each quarter?"
- [ ] Retrieval debug shows relevant chunks
- [ ] Answer is grounded in context

---

## Useful Links

- **Streamlit Cloud**: https://share.streamlit.io
- **Streamlit Docs**: https://docs.streamlit.io
- **ChromaDB Persistence**: https://docs.trychroma.com/deployment/guide
- **OpenAI API**: https://platform.openai.com
- **Groq API**: https://console.groq.com/docs/quickstart

---

## After Deployment

### Share Your App
Your app URL: `https://share.streamlit.io/[username]/finance-quarterly-rag/streamlit_app.py`

### Get App Stats
- Dashboard shows:
  - Visitor count
  - Uptime
  - Memory/CPU usage
  - Python version running

### Update App
Simply push to GitHub:
```bash
git add .
git commit -m "Update RAG pipeline"
git push origin main
```
Streamlit auto-redeploys within 1-2 minutes.

---

## Production Deployment Notes

**Current State**: ✓ Production ready for ~50-100 concurrent users

For higher scale or persistence needs:
1. Add external database (PostgreSQL/SupaBase)
2. Use cloud object storage for ChromaDB
3. Implement FastAPI backend (+15 bonus points)
4. Add Docker containerization
5. Deploy to Kubernetes/AWS/GCP

See `FUTURE_DEPLOYMENT.md` for roadmap.

---

## Support

If you encounter issues:
1. Check Streamlit Cloud logs
2. Verify API key quotas
3. Test locally: `streamlit run streamlit_app.py`
4. Review error messages in browser console

Good luck! 🚀
