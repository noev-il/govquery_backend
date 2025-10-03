# 🚀 GovQuery Smart API Guide

## 🎯 Overview

The Smart API automatically handles Modal app deployment and cold starts, making your system much more robust and user-friendly.

## ✨ Smart Features

### **1. Automatic App Detection**
- ✅ Checks if Modal app is running
- ✅ Detects when app is not available
- ✅ Provides real-time status information

### **2. Automatic Deployment**
- 🚀 Deploys Modal app when needed
- 🔄 Retries queries after deployment
- ⚡ No manual intervention required

### **3. Cold Start Fallback**
- 🎯 Tries existing app first
- 🔄 Falls back to cold start if needed
- 📊 Provides detailed status information

### **4. Smart Error Recovery**
- 🛡️ Handles deployment failures gracefully
- 📝 Provides clear error messages
- 🔧 Suggests next steps

## 🛠️ Setup

### **Start the Smart API Server**
```bash
python run_smart_api.py
```

The server will be available at: `http://localhost:8000`

### **Import Smart Postman Collection**
1. Open Postman
2. Import: `Smart_GovQuery_Postman_Collection.json`
3. All requests are pre-configured with smart features

## 📮 Available Endpoints

### **🔍 Enhanced Health Check**
- **URL**: `GET http://localhost:8000/health`
- **Features**: Shows Modal app status, deployment history, smart features
- **Response**:
```json
{
  "status": "healthy",
  "schemas_loaded": 12,
  "modal_app_running": false,
  "modal_app_name": "govquery-nl2sql-main",
  "deployment_attempted": false,
  "features": {
    "auto_deployment": true,
    "cold_start_fallback": true,
    "smart_error_recovery": true
  }
}
```

### **🚀 Smart Query (Auto-Deploy)**
- **URL**: `POST http://localhost:8000/query`
- **Features**: Automatically deploys Modal app if needed
- **Request**:
```json
{
  "query": "What is the total population in Texas?",
  "table_codes": ["B01001"],
  "model_choice": "auto"
}
```
- **Response**:
```json
{
  "sql_query": "SELECT total_population FROM b01001 WHERE geography_id = '04000US48' AND year = 2022;",
  "confidence": 0.95,
  "model_used": "t5",
  "deployment_status": "deployed"
}
```

### **⚡ Simple Query (Fallback)**
- **URL**: `POST http://localhost:8000/query/simple`
- **Features**: Uses simple query method with fallback
- **Request**: Same as smart query
- **Response**: Simplified format with deployment info

### **🔧 Manual Deploy**
- **URL**: `POST http://localhost:8000/deploy`
- **Features**: Manually trigger Modal app deployment
- **Response**:
```json
{
  "status": "deployed",
  "message": "Modal app deployed successfully",
  "app_name": "govquery-nl2sql-main"
}
```

## 🎯 Usage Scenarios

### **Scenario 1: First Time User**
1. Start Smart API: `python run_smart_api.py`
2. Make a query in Postman
3. API automatically detects no Modal app
4. API automatically deploys Modal app
5. Query executes successfully

### **Scenario 2: App Stopped**
1. Modal app stops running (timeout, error, etc.)
2. User makes a query
3. API detects app is not running
4. API automatically redeploys app
5. Query executes successfully

### **Scenario 3: Manual Control**
1. Check app status: `GET /health`
2. Manually deploy: `POST /deploy`
3. Make queries with confidence

## 📊 Response Status Codes

### **Deployment Status**
- `"existing"` - Used existing running app
- `"deployed"` - Deployed app for this query
- `"failed"` - Deployment failed

### **Error Handling**
- Clear error messages
- Suggested next steps
- Fallback options

## 🧪 Testing Workflow

### **1. Health Check**
```bash
GET http://localhost:8000/health
```
Should show: `"modal_app_running": false` initially

### **2. Smart Query (Auto-Deploy)**
```bash
POST http://localhost:8000/query
{
  "query": "What is the total population in Texas?",
  "table_codes": ["B01001"]
}
```
Should automatically deploy and return SQL

### **3. Verify Deployment**
```bash
GET http://localhost:8000/health
```
Should show: `"modal_app_running": true`

### **4. Subsequent Queries**
All subsequent queries should use the existing app (faster)

## 🚨 Troubleshooting

### **Deployment Fails**
- Check Modal credentials are set
- Verify deployment script exists
- Check network connectivity

### **App Not Found**
- Smart API will attempt deployment
- Check Modal app name configuration
- Verify app was deployed successfully

### **Query Still Fails**
- Check schema files exist
- Verify table codes are valid
- Check Modal app logs

## 🎉 Benefits

### **For Users**
- ✅ No manual deployment needed
- ✅ Automatic error recovery
- ✅ Clear status information
- ✅ Faster subsequent queries

### **For Developers**
- ✅ Robust error handling
- ✅ Automatic fallback mechanisms
- ✅ Detailed logging and status
- ✅ Easy testing and debugging

## 🔄 Comparison: Regular vs Smart API

| Feature | Regular API | Smart API |
|---------|-------------|-----------|
| App Detection | Manual | Automatic |
| Deployment | Manual | Automatic |
| Error Recovery | Basic | Advanced |
| Status Info | Limited | Comprehensive |
| User Experience | Requires setup | Plug-and-play |

## 🚀 Next Steps

1. **Start Smart API**: `python run_smart_api.py`
2. **Import Postman Collection**: `Smart_GovQuery_Postman_Collection.json`
3. **Test Health Check**: Verify smart features
4. **Make Smart Query**: Watch automatic deployment
5. **Enjoy**: Seamless NL2SQL experience!

The Smart API makes your GovQuery system truly production-ready with automatic deployment and intelligent error handling! 🎯
