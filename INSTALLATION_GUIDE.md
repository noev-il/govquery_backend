# GovQuery Templated API - Installation Guide

## 🚀 Quick Installation

### Option 1: One-Command Setup (Recommended)
```bash
python setup.py
```

### Option 2: Manual Installation
```bash
# Install requirements
pip install -r requirements.txt

# Verify installation
python verify_installation.py
```

## 📦 Requirements

### System Requirements
- Python 3.8 or higher
- pip package manager
- Internet connection (for Modal API)

### Python Packages
All packages are listed in `requirements.txt`:

**Core API Dependencies:**
- `modal>=0.65.0` - Modal client for ML inference
- `fastapi>=0.104.0` - Web framework
- `uvicorn>=0.24.0` - ASGI server
- `pydantic>=2.5.0` - Data validation
- `python-multipart>=0.0.6` - File upload support
- `httpx>=0.25.0` - Async HTTP client
- `python-dotenv>=1.0.0` - Environment variables
- `requests>=2.31.0` - HTTP client for testing

**ML/AI Dependencies:**
- `torch>=2.0.0` - PyTorch
- `transformers>=4.35.0` - Hugging Face transformers
- `rapidfuzz>=3.9.6` - Fuzzy string matching

## 🔧 Installation Steps

### 1. Clone/Download the Repository
```bash
# If using git
git clone <repository-url>
cd govquery_backend

# Or download and extract the files
```

### 2. Install Python Dependencies
```bash
# Using pip
pip install -r requirements.txt

# Or using the installer script
python install_requirements.py
```

### 3. Verify Installation
```bash
python verify_installation.py
```

### 4. Set Up Environment (Optional)
```bash
# Create .env file with your Modal credentials
cp .env.example .env
# Edit .env with your Modal token and app name
```

## 🧪 Testing the Installation

### Test 1: Verify Packages
```bash
python verify_installation.py
```

### Test 2: Test API Endpoints
```bash
# Start the API server
python templated_api.py

# In another terminal, test the API
python test_templated_api.py
```

### Test 3: Run Full Demo
```bash
python launch_demo.py
```

## 🚨 Troubleshooting

### Common Issues

**1. Import Errors**
```bash
# Reinstall requirements
pip install -r requirements.txt --force-reinstall
```

**2. Modal Authentication Errors**
```bash
# Set environment variables
export MODAL_TOKEN_ID="your-token-id"
export MODAL_TOKEN_SECRET="your-token-secret"
export MODAL_APP_NAME="your-app-name"
```

**3. Port Already in Use**
```bash
# Kill process using port 8000
lsof -ti:8000 | xargs kill -9

# Or use a different port
python templated_api.py --port 8001
```

**4. Python Version Issues**
```bash
# Check Python version
python --version

# Install Python 3.8+ if needed
# macOS: brew install python@3.11
# Ubuntu: sudo apt install python3.11
```

### Getting Help

1. **Check Logs**: Look at the console output for error messages
2. **Verify Environment**: Run `python verify_installation.py`
3. **Test Individual Components**: Try importing packages one by one
4. **Check Dependencies**: Ensure all requirements are installed

## 📁 File Structure

```
govquery_backend/
├── templated_api.py          # Main API server
├── frontend.html             # Frontend interface
├── launch_demo.py            # Demo launcher
├── setup.py                  # Setup script
├── install_requirements.py   # Requirements installer
├── verify_installation.py    # Installation verifier
├── test_templated_api.py     # API tests
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (create this)
├── core/                     # Core modules
│   ├── modal_client.py       # Modal client
│   └── api.py               # Original API
├── schemas/                  # Database schemas
│   ├── B01001.json
│   ├── B02001.json
│   └── ...
└── smart_modal_client.py     # Smart Modal wrapper
```

## 🎯 Quick Start Commands

```bash
# 1. Install everything
python setup.py

# 2. Run the demo
python launch_demo.py

# 3. Or start manually
python templated_api.py
# Then open frontend.html in your browser
```

## 🔐 Environment Variables

Create a `.env` file with:

```bash
# Modal API credentials
MODAL_TOKEN_ID=your-modal-token-id
MODAL_TOKEN_SECRET=your-modal-token-secret
MODAL_APP_NAME=govquery-nl2sql-main

# Optional overrides
# MODAL_APP_NAME=your-custom-app-name
```

## 📊 Verification Checklist

- [ ] Python 3.8+ installed
- [ ] All packages installed (`pip list`)
- [ ] API files present
- [ ] Schema files present
- [ ] Environment variables set
- [ ] API server starts without errors
- [ ] Frontend loads in browser
- [ ] Test queries work

## 🆘 Support

If you encounter issues:

1. Run `python verify_installation.py` to diagnose
2. Check the console output for specific error messages
3. Ensure all dependencies are installed correctly
4. Verify your Modal credentials are correct
5. Check that port 8000 is available

## 🎉 Success!

Once everything is installed and working, you should see:

- ✅ API server running on http://localhost:8000
- ✅ Frontend interface in your browser
- ✅ Health check returning "healthy" status
- ✅ Test queries generating SQL responses

You're ready to start building with the GovQuery templated API! 🚀
