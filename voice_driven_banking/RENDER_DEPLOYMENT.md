# Deploying Voice Banking System on Render

This guide explains how to deploy the Voice-Driven Banking System to Render.com.

## Deployment Options

### Option 1: Manual Deployment

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Use the following settings:
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
4. Click "Create Web Service"

### Option 2: Blueprint Deployment

1. Fork this repository to your GitHub account
2. Go to Render Dashboard: https://dashboard.render.com/
3. Click "New" and select "Blueprint"
4. Connect your GitHub repository
5. Render will automatically detect the `render.yaml` file and set up the service

## Environment Variables

If your application uses any API keys or sensitive information, add them as environment variables in the Render dashboard:

1. Go to your web service in the Render dashboard
2. Click on "Environment" tab
3. Add your environment variables (e.g., API keys)

## Persistent Storage (Optional)

If you need persistent storage for user data or voice prints:

1. Create a Render Disk
2. Attach it to your service
3. Update your code to use the disk path

## Custom Domain (Optional)

To use a custom domain:

1. Go to your web service in the Render dashboard
2. Click on "Settings" tab
3. Scroll to "Custom Domains" section
4. Add your domain and follow the DNS configuration instructions
