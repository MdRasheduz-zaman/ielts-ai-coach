# LLM Provider Setup Guide

## Supported Providers

This IELTS AI Coach supports three major LLM providers through LangChain integration:

### 1. Google Gemini (Recommended for Beginners)

**Free Tier:** ✅ Yes  
**Setup Difficulty:** ⭐ Easy

```env
LLM_PROVIDER="google"
GOOGLE_API_KEY="your-api-key"
MODEL_NAME="gemini-2.5-flash"
```

**Get API Key:**
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy and paste into `.env`

**Models:**
- `gemini-2.5-flash` - Fast and efficient (recommended)
- `gemini-2.5-pro` - Most capable
- `gemini-1.5-flash` - Alternative fast model
- `gemini-1.5-pro` - Alternative capable model

---

### 2. OpenAI ChatGPT

**Free Tier:** ❌ Paid  
**Setup Difficulty:** ⭐⭐ Medium

```env
LLM_PROVIDER="openai"
OPENAI_API_KEY="sk-..."
MODEL_NAME="gpt-4o-mini"
```

**Get API Key:**
1. Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create account and add payment method
3. Generate API key

**Models:**
- `gpt-4o` - Most capable (expensive)
- `gpt-4o-mini` - Good balance (recommended)
- `gpt-3.5-turbo` - Fastest, cheapest
- `gpt-4-turbo` - Previous generation

---

### 3. Anthropic Claude

**Free Tier:** ❌ Paid  
**Setup Difficulty:** ⭐⭐ Medium

```env
LLM_PROVIDER="anthropic"
ANTHROPIC_API_KEY="sk-ant-..."
MODEL_NAME="claude-3-5-sonnet-20241022"
```

**Get API Key:**
1. Visit [Anthropic Console](https://console.anthropic.com/)
2. Create account and add payment method
3. Generate API key

**Models:**
- `claude-3-5-sonnet-20241022` - Best balance (recommended)
- `claude-3-opus-20240229` - Most capable
- `claude-3-haiku-20240307` - Fastest

---

## Choosing a Provider

### For Beginners
→ **Google Gemini**
- Free tier available
- Easy setup
- Good quality feedback
- Fast responses
- Pro is free for students. So check it out

### For Best Quality
→ **OpenAI GPT-4** or **Claude 3.5 Sonnet**
- Highest quality feedback
- Most detailed analysis
- Better understanding of nuances
- Worth the cost for serious preparation

### For Budget-Conscious Users
→ **Google Gemini** (free tier)
- No cost for moderate usage
- Decent quality feedback
- Good for practice and learning
- Pro is free for students. So check it out
---

## Environment Configuration

### Minimal Setup (Required)
```env
# Choose one provider
LLM_PROVIDER="google"           # or: openai, anthropic

# Add corresponding API key
GOOGLE_API_KEY="your-key"      # for Google
# OPENAI_API_KEY="sk-..."       # for OpenAI
# ANTHROPIC_API_KEY="sk-ant-..." # for Anthropic

# Optional: specify model
MODEL_NAME="gemini-2.5-flash"
```

### Advanced Configuration (Optional)
```env
# Response creativity (0.0-1.0)
MODEL_TEMPERATURE=0.7

# Maximum response length
MAX_TOKENS=4000

# Timeout and retries
MODEL_TIMEOUT=120
MODEL_MAX_RETRIES=3
```

---

## Common Issues

### API Key Not Working
- Check for extra spaces in `.env`
- Verify key is active on provider dashboard
- Ensure account has credits (for paid providers)
- Restart the application after updating `.env`

### Rate Limit Errors
- Wait and retry after a few minutes
- Upgrade plan (for paid providers)
- For Google Gemini: check your API quota
- Switch to different provider temporarily

### Model Not Found
- Check model name spelling in `.env`
- Verify model is available in your region
- Try alternative model from same provider
- Check provider documentation for available models

### Timeout Errors
- Increase `MODEL_TIMEOUT` in `.env`
- Check your internet connection
- Try a faster model (e.g., `gpt-4o-mini` instead of `gpt-4o`)

---

## Cost Comparison

| Provider | Free Tier | Typical Cost per Essay* |
|----------|-----------|------------------------|
| **Google Gemini** | ✅ Yes | Free (within quota) |
| **OpenAI GPT-4o-mini** | ❌ No | ~$0.02 |
| **OpenAI GPT-4o** | ❌ No | ~$0.15 |
| **Claude 3.5 Sonnet** | ❌ No | ~$0.08 |
| **Claude 3 Haiku** | ❌ No | ~$0.02 |

*Approximate cost for typical IELTS essay evaluation (including all rubrics and feedback)

---

## Recommendations by Use Case

### 1. Learning & Practice (Free)
**Provider:** Google Gemini  
**Model:** `gemini-2.5-flash`
- Perfect for beginners
- Unlimited practice with free tier
- Good quality feedback
- Fast responses

### 2. Serious Preparation (Paid)
**Provider:** OpenAI or Claude  
**Model:** `gpt-4o` or `claude-3-5-sonnet-20241022`
- Best quality feedback
- Most detailed analysis
- Worth investment for exam prep
- Professional-level evaluation

### 3. Budget-Conscious (Mixed)
**Strategy:** Use combination
- Google Gemini for practice
- GPT-4o-mini or Claude Haiku for final reviews
- Best of both worlds
- Optimize costs

---

## Testing Your Setup

### Quick Test
```bash
# Start the application
./startup.sh  # or startup.bat on Windows

# If successful, you'll see:
# ✅ LLM configured successfully
# ✅ Provider: google (or your chosen provider)
# ✅ Model: gemini-2.5-flash (or your chosen model)
```

### Manual Test
```python
# Test in Python
from backend.app.llm_config import UniversalLLMConfig

# This will show your configuration
config = UniversalLLMConfig.get_provider_info()
print(config)

# This will test the connection
llm = UniversalLLMConfig.get_llm()
print("✅ LLM configured successfully!")
```

---

## Need Help?

1. **Check Setup Guide:** [SETUP_GUIDE.md](SETUP_GUIDE.md)
2. **Read User Guide:** [USER_GUIDE.md](USER_GUIDE.md)
3. **Open Issue:** [GitHub Issues](https://github.com/MdRasheduz-zaman/ielts-ai-coach/issues)

Include in your issue:
- Provider you're trying to use
- Error message you're seeing
- Your `.env` configuration (⚠️ WITHOUT the API key!)
- Operating system and Python version

---

## Security Best Practices

1. **Never commit `.env` file** - Already in `.gitignore`
2. **Keep API keys secret** - Don't share in issues/discussions
3. **Rotate keys regularly** - Especially if exposed
4. **Use environment variables** - For production deployments
5. **Monitor usage** - Check provider dashboards for unusual activity

---

**Ready to start?** Choose your provider, set up your API key, and begin improving your IELTS Writing! 🚀
