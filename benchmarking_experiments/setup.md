# Speech Benchmarking Experiments - Complete Setup

## Prerequisites
Python 3.10+, Git

## 1. Navigate
```
cd community-ai/benchmarking_experiments
```

## 2. Virtual Env
```
python -m venv venv
# Activate:
# Win: venv/Scripts/activate
# Unix: source venv/bin/activate
```

## 3. Dependencies
```
pip install -r requirements.txt
```

## 4. Config (.env)
Copy & edit:
```
cp .env.example .env
```
Add keys:
```
HUME_API_KEY=hk-...
DEEPGRAM_API_KEY=...
# etc.
```

## 5. Download ffmpeg-8.1-full_build-shared

url = https://www.gyan.dev/ffmpeg/builds/
version =  ffmpeg-8.1-full_build-shared and paste the path on local env variable

```


