# Setup Guide

## Prerequisites

- Python 3.9 or higher
- pip or conda
- API key for at least one LLM provider

## Installation Steps

### 1. Clone Repository

```bash
git clone https://github.com/MdRasheduz-zaman/ielts-ai-coach.git
cd ielts-ai-coach
```

### 2. Choose Environment Manager

**Option A: Using pip (Recommended for most users)**
```bash
python -m venv venv
source venv/bin/activate  # Unix/macOS
# or
venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

**Option B: Using Conda**
```bash
conda env create -f environment.yml
conda activate ielts-coach
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` file:
```env
LLM_PROVIDER="google"
GOOGLE_API_KEY="your-api-key-here"
MODEL_NAME="gemini-2.5-flash"
```

### 4. Run Application

```bash
./startup.sh        # Unix/macOS
startup.bat         # Windows
```

### 5. Access Application

Open browser: http://localhost:8501

## LLM Provider Setup

See [LLM_PROVIDERS.md](LLM_PROVIDERS.md) for detailed provider setup instructions.

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000           # Unix/macOS
netstat -ano | findstr :8000  # Windows

# Kill the process or change port in .env
```

### Import Errors

```bash
pip install --upgrade -r requirements.txt
```

### API Key Issues

- Verify key is correct in `.env`
- Check provider account status
- Ensure no extra spaces in `.env` file

## Next Steps

See [USER_GUIDE.md](USER_GUIDE.md) for usage instructions.
