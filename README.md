# 🎯 IELTS AI Writing Coach

**AI-powered IELTS Writing practice system with instant, personalized feedback.**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red.svg)](https://streamlit.io)

## ✨ Features

- 🤖 **Multi-LLM Support** - Google Gemini, OpenAI GPT, and Anthropic Claude
- 📊 **Visual Task 1** - Upload charts/graphs for automatic analysis
- 📚 **Question Bank** - Save and reuse questions with full history tracking
- 📈 **Progress Tracking** - Comparative feedback across attempts
- ⏱️ **Timed Practice** - Realistic exam conditions (20/40 min timers)
- 🖥️ **Cross-Platform** - Windows, macOS, and Linux support

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/MdRasheduz-zaman/ielts-ai-coach.git
cd ielts-ai-coach
```

### 2. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API key
# Minimum required:
# LLM_PROVIDER="google"
# GOOGLE_API_KEY="your-api-key-here"
```

### 3. Run the Application

**Unix/macOS:**
```bash
chmod +x startup.sh
./startup.sh
```

**Windows:**
```cmd
startup.bat
```

### 4. Open in Browser

Navigate to: **http://localhost:8501**

## 📖 Documentation

- [Setup Guide](docs/SETUP_GUIDE.md) - Detailed installation and configuration
- [User Guide](docs/USER_GUIDE.md) - How to use the system
- [LLM Providers](docs/LLM_PROVIDERS.md) - Supported providers and setup


## 🎯 Supported LLM Providers

| Provider | Free Tier | Setup | Best For |
|----------|-----------|-------|----------|
| **Google Gemini** | ✅ Yes | Easy | Getting started |
| **OpenAI GPT** | ❌ Paid | Medium | Best quality |
| **Anthropic Claude** | ❌ Paid | Medium | Detailed feedback |

## 🏗️ Project Structure

```
ielts-ai-coach/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI application
│   │   ├── llm_config.py     # Multi-provider LLM setup
│   │   ├── graph_nodes.py    # Evaluation logic
│   │   └── data_manager.py   # Question bank & history
│   └── rubrics/              # IELTS criteria
├── frontend/
│   └── app.py                # Streamlit UI
├── data/
│   ├── question_bank/        # Saved questions
│   └── evaluation_history/   # Evaluation records
├── docs/                     # Documentation
├── .env.example              # Environment template
├── requirements.txt          # Python dependencies
└── startup.sh/bat            # Launch scripts
```

## 🔧 Environment Configuration

Create `.env` file with:

```env
# Required
LLM_PROVIDER="google"              # or: openai, anthropic, groq, etc.
GOOGLE_API_KEY="your-key-here"    # Your API key

# Optional
MODEL_NAME="gemini-2.5-flash" # Model to use
TEMPERATURE=0.2                    # Response creativity (0.0-1.0)
MAX_TOKENS=4000                    # Maximum response length
```

See [LLM_PROVIDERS.md](docs/LLM_PROVIDERS.md) for provider-specific setup.

## 🧪 Testing

```bash
# Verify setup
python -c "import streamlit; import fastapi; print('✅ Dependencies OK')"

# Test LLM connection
python -c "from backend.app.llm_config import get_llm; print('✅ LLM configured')"
```

## 📚 Usage

### Basic Workflow

1. **Setup Question**
   - Choose Task 1 (with image) or Task 2
   - Upload image or paste question text
   - Save to question bank (optional)

2. **Timed Practice**
   - Click "Start Timed Writing Practice"
   - Write your essay (20/40 minutes)
   - Submit for AI evaluation

3. **Review Feedback**
   - Get detailed band score breakdown
   - See specific improvements needed
   - Compare with previous attempts

4. **Track Progress**
   - View evaluation history
   - See improvement over time
   - Identify persistent issues

## 🛑 Stopping the Application

```bash
./startup.sh stop          # Unix/macOS
# or
stop.bat                   # Windows
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **LangChain & LangGraph** - AI orchestration framework
- **FastAPI** - High-performance backend
- **Streamlit** - Interactive frontend
- **All LLM Providers** - Making AI accessible

## 🐛 Bug Reports

Found a bug? Please [open an issue](https://github.com/MdRasheduz-zaman/ielts-ai-coach/issues) with:
- Description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Your environment (OS, Python version)

## 📧 Support

- 📖 [Documentation](docs/)
- 🐛 [Issue Tracker](https://github.com/MdRasheduz-zaman/ielts-ai-coach/issues)
- 💬 [Discussions](https://github.com/MdRasheduz-zaman/ielts-ai-coach/discussions)

---

**Happy practicing! Improve your IELTS Writing score with AI-powered feedback.** 🚀
