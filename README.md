# Flask App for Render Hosting

A complete, deploy-ready Flask application optimized for Render's free hosting tier.

## Project Structure

```
.
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies (includes gunicorn)
├── render.yaml         # Render deployment configuration
├── runtime.txt         # Python version specification
├── .gitignore          # Git ignore rules
├── index.html          # Frontend HTML (optional)
├── style.css           # Frontend styles (optional)
├── app.js              # Frontend JavaScript (optional)
└── README.md           # This file
```

## Features

- **Flask 3.0.0** - Modern Flask framework
- **Gunicorn 21.2.0** - Production WSGI server
- **Render-optimized** - Configured for free tier hosting
- **No "Exited with status 127" error** - Proper dependency management
- **Health check endpoint** - `/health` for monitoring
- **Environment-aware** - Detects Render environment
- **Static file serving** - Serves HTML, CSS, and JS files

## Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the app:**
   ```bash
   python app.py
   ```

3. **Access the app:**
   - Open http://localhost:5000 in your browser

## GitHub Upload Commands

1. **Initialize Git repository:**
   ```bash
   git init
   ```

2. **Add all files:**
   ```bash
   git add .
   ```

3. **Commit changes:**
   ```bash
   git commit -m "Initial Flask app for Render deployment"
   ```

4. **Create a new repository on GitHub** (if you haven't already)

5. **Add remote origin:**
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   ```

6. **Push to GitHub:**
   ```bash
   git branch -M main
   git push -u origin main
   ```

## Render Deployment Steps

### Method 1: Using render.yaml (Recommended)

1. **Push your code to GitHub** (see commands above)

2. **Go to [Render Dashboard](https://dashboard.render.com/)**

3. **Click "New +" → "Web Service"**

4. **Connect your GitHub account** (if not already connected)

5. **Select your repository**

6. **Render will automatically detect the render.yaml file**

7. **Click "Create Web Service"**

8. **Your app will deploy automatically**

### Method 2: Manual Configuration

1. **Push your code to GitHub** (see commands above)

2. **Go to [Render Dashboard](https://dashboard.render.com/)**

3. **Click "New +" → "Web Service"**

4. **Connect your GitHub account**

5. **Select your repository**

6. **Configure the following settings:**
   - **Name:** flask-app (or your preferred name)
   - **Region:** Oregon (or closest to you)
   - **Branch:** main
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`

7. **Click "Create Web Service"**

8. **Your app will deploy automatically**

## API Endpoints

- **GET /** - Home endpoint with app info
- **GET /health** - Health check endpoint (returns 200)
- **GET /api/info** - App information endpoint
- **GET /index.html** - Serves index.html file
- **GET /style.css** - Serves style.css file
- **GET /app.js** - Serves app.js file

## Troubleshooting

### "Exited with status 127" Error

This error occurs when gunicorn is not found. This project is configured to prevent this error by:
- Using `gunicorn==21.2.0` in requirements.txt
- Specifying Python version in runtime.txt
- Using correct start command in render.yaml: `gunicorn app:app`
- Ensuring gunicorn is installed during build

### App Not Starting

1. Check Render logs in the dashboard
2. Verify all files are pushed to GitHub
3. Ensure runtime.txt and requirements.txt are in the root directory
4. Make sure the start command is `gunicorn app:app`
5. Verify Flask and gunicorn are installed correctly

### Free Tier Optimization

This project is optimized for Render's free tier:
- Minimal dependencies (only Flask and Gunicorn)
- Lightweight Flask app
- No heavy background processes
- Efficient resource usage

## Environment Variables

Render automatically sets the `PORT` environment variable. The app reads this to determine which port to listen on (defaults to 5000).

## Important Notes

- Gunicorn is installed via requirements.txt, so it will be available during deployment
- The app uses `gunicorn app:app` as the start command, which tells gunicorn to use the Flask app object named `app` in the `app.py` file
- Make sure your Flask app object is named `app` for the start command to work correctly

## Support

For Render-specific issues, check the [Render documentation](https://render.com/docs).
