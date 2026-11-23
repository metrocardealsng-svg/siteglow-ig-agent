# SiteGlow NG — Autonomous Instagram AI Agent

An autonomous GitHub Actions agent that creates and publishes daily **viral Instagram Reels** (with Nigerian AI voiceover, glassmorphic motion graphics, your portfolio previews, and animated word-level captions) and **5-slide educational Carousels** teaching Nigerian businesses why they need a website — starting from **₦150,000**.

Every script and caption passes through the **instagram-agent-skill** quality gates (`hooks.json`, `hookscore.py`, `humanize.py`, `caption.py`) so posts never sound like generic AI slop.

---

## How It Works Daily (100% Automatic)
1. **GitHub Actions triggers daily at 6:00 PM WAT** (`17:00 UTC`).
2. **Topic & Format Rotation**: Alternates between a **Reel** and a **5-Slide Carousel** using `history.json` so topics never repeat back-to-back.
3. **AI Script & Humanizer Gate**: Gemini generates a fresh Nigerian-founder hook & script using the 26 proven formulas in `src/ig_skill/hooks.json`, scores it with `hookscore.py`, strips AI fingerprints with `humanize.py`, and lints the caption (max 5 niche hashtags, 1 clear DM `"GLOW"` ask, hook above the 125-char fold) with `caption.py`.
4. **HD Media Rendering**:
   - **Reels (`1080x1920`, 30fps)**: Nigerian neural voiceover (`edge-tts` `en-NG-AbeoNeural`), dark obsidian + glassmorphic cards, SiteGlow NG logo header, growth chart, portfolio showcase, subtle zoom motion, and word-level dynamic captions.
   - **Carousels (`5 x 1080x1350`)**: Matching dark-luxury glassmorphic tip slides with growth graphs, live website previews, and a ₦150,000 CTA cover.
5. **Auto-Publish**: Uploads media and publishes directly via the official **Meta Instagram Graph API v22.0**, then commits the updated `history.json`.

---

## Step-by-Step Deployment to GitHub (5 Minutes)

### 1. Push This Folder to a New GitHub Repo
```bash
cd siteglow-ig-agent
git init
git add .
git commit -m "Initial SiteGlow NG autonomous IG agent"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/siteglow-ig-agent.git
git push -u origin main
```

### 2. Get Your Free Keys
1. **Gemini API Key** (`GEMINI_API_KEY`): Free at [aistudio.google.com/apikey](https://aistudio.google.com/apikey).
2. **Instagram Graph API Credentials** (`IG_USER_ID` & `IG_ACCESS_TOKEN`):
   - Make sure your Instagram account is switched to **Business** and linked to a **Facebook Page**.
   - Go to [developers.facebook.com](https://developers.facebook.com) → Create an App (**Business** type) → Add **Instagram Graph API**.
   - Generate a **Long-Lived Page/System User Token** with permissions: `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement`.
   - Find your `IG_USER_ID` via Graph API Explorer: `GET /me/accounts?fields=instagram_business_account`.
3. *(Optional)* **Cloudinary** (`CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_UPLOAD_PRESET`): Free tier for permanent media hosting (if omitted, the agent automatically stages uploads via HTTPS for Meta to fetch).

### 3. Add Secrets in GitHub
Go to your GitHub repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**, and add:
- `GEMINI_API_KEY`
- `IG_USER_ID`
- `IG_ACCESS_TOKEN`
- *(Optional)* `CLOUDINARY_CLOUD_NAME` and `CLOUDINARY_UPLOAD_PRESET`

### 4. Test Run Before Going Live
1. Go to the **Actions** tab in your GitHub repo → select **SiteGlow NG Autonomous Instagram Agent**.
2. Click **Run workflow** → set `dry_run: true` and `mode: reel` (or `carousel`).
3. Download the generated MP4 / slides from the workflow **Artifacts** section to preview them.
4. Once happy, leave it enabled — it will automatically publish every day at **6:00 PM WAT** (or trigger manually anytime with `dry_run: false`).
