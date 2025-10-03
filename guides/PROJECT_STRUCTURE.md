# GovQuery Project Structure

## 📁 Folder Organization

```
govquery_backend/
├── core/                           # Core application files
│   ├── __init__.py
│   ├── api.py                      # FastAPI endpoints
│   ├── modal_client.py             # Modal client interface
│   ├── modal_deployment.py         # Modal app and inference logic
│   └── example_usage.py            # Usage examples
│
├── deployment/                     # Deployment scripts
│   ├── __init__.py
│   ├── deploy_modal.py             # Main deployment script
│   └── deploy_persistent_fixed.py  # Persistent deployment
│
├── tests/                          # Testing scripts
│   ├── __init__.py
│   ├── batch_test.py               # Sequential batch testing
│   ├── mass_test.py                # Comprehensive testing
│   ├── parallel_test.py            # Parallel testing
│   ├── run_tests.py                # Test runner menu
│   ├── test_api.py                 # API testing
│   ├── warm_cold_test.py           # Performance testing
│   └── warm_test.py                # Warm app testing
│
├── docs/                           # Documentation
│   └── TESTING_GUIDE.md            # Testing documentation
│
├── schemas/                        # Database schemas
│   ├── B01001.json                 # Population tables
│   ├── B02001.json                 # Race tables
│   ├── B15003.json                 # Education tables
│   ├── B19013.json                 # Income tables
│   └── ...                         # Other schema files
│
├── govquery-nl2sql-model-6.ipynb   # Jupyter notebook
├── README.md                       # Project documentation
├── requirements.txt                # Python dependencies
├── run_api.py                      # API server runner
├── POSTMAN_GUIDE.md                # Postman testing guide
├── GovQuery_Postman_Collection.json # Postman collection
└── PROJECT_STRUCTURE.md            # This file
```

## 🎯 Purpose of Each Folder

### **core/**
Contains the main application logic:
- **api.py**: FastAPI web server with REST endpoints
- **modal_client.py**: Interface for interacting with Modal-hosted models
- **modal_deployment.py**: Modal app definition and NL2SQL inference logic
- **example_usage.py**: Code examples and usage patterns

### **deployment/**
Contains scripts for deploying the application:
- **deploy_modal.py**: Main deployment script for Modal functions
- **deploy_persistent_fixed.py**: Deploys a persistent app to avoid cold starts

### **tests/**
Contains comprehensive testing scripts:
- **batch_test.py**: Run multiple queries sequentially
- **mass_test.py**: Interactive testing with different categories
- **parallel_test.py**: Run multiple queries in parallel
- **run_tests.py**: Menu-driven test runner
- **test_api.py**: Test API endpoints
- **warm_cold_test.py**: Compare cold vs warm app performance
- **warm_test.py**: Test with persistent (warm) apps

### **docs/**
Contains project documentation:
- **TESTING_GUIDE.md**: Comprehensive guide on how to test the system

### **schemas/**
Contains JSON schema files for different database tables:
- Population tables (B01001, etc.)
- Race/ethnicity tables (B02001, etc.)
- Education tables (B15003, etc.)
- Income tables (B19013, etc.)

## 🚀 Quick Start

### **Deploy the App:**
```bash
cd deployment/
python deploy_modal.py
```

### **Run Tests:**
```bash
cd tests/
python run_tests.py
```

### **Start API Server:**
```bash
python run_api.py
```

## 📝 Import Paths

When running scripts from different folders, use these import paths:

- From `tests/` folder: `../core/modal_deployment.py`
- From `deployment/` folder: `core.modal_deployment`
- From root folder: `core.modal_deployment`

## 🔧 Maintenance

- **Adding new tests**: Add to `tests/` folder
- **Adding new schemas**: Add to `schemas/` folder
- **Core changes**: Modify files in `core/` folder
- **Deployment changes**: Modify files in `deployment/` folder
