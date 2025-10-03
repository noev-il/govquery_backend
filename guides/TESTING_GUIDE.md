# GovQuery Mass Testing Guide

## 🎯 **Overview**

This guide provides multiple approaches for testing your GovQuery system with mass questions to validate performance, accuracy, and reliability.

## 🚀 **Quick Start**

### **1. Simple Batch Test (Recommended for beginners)**
```bash
python batch_test.py
```
- Tests 15 questions across different tables
- Sequential execution
- Good for basic validation

### **2. Comprehensive Mass Test**
```bash
python mass_test.py
```
- Interactive menu with multiple test types
- Tests across all categories and models
- Detailed reporting and JSON output

### **3. Parallel Testing (Advanced)**
```bash
python parallel_test.py
```
- Runs multiple queries simultaneously
- Faster execution
- Good for performance testing

## 📊 **Test Categories**

### **Population Demographics (B01001)**
- Total population by state
- Gender distribution
- Age group analysis
- Geographic comparisons

### **Income & Economics (B19013, B19001)**
- Median household income
- Income distribution
- Economic indicators
- Regional comparisons

### **Education (B15003)**
- Educational attainment levels
- Degree distribution
- Regional education patterns
- Demographics by education

### **Employment (B23025)**
- Unemployment rates
- Labor force participation
- Employment status
- Regional employment patterns

### **Race & Ethnicity (B02001)**
- Population by race
- Ethnic distribution
- Regional demographics
- Diversity metrics

### **Housing (B19001)**
- Home values
- Ownership rates
- Rental statistics
- Housing affordability

## 🔧 **Test Types**

### **1. Quick Test**
- **Questions**: 12 (2 from each category)
- **Models**: Auto selection
- **Duration**: ~10-15 minutes
- **Use case**: Basic validation

### **2. Full Test**
- **Questions**: 60+ (all categories)
- **Models**: Auto, T5, SQLCoder
- **Duration**: ~60-90 minutes
- **Use case**: Comprehensive validation

### **3. Model Comparison**
- **Questions**: 4 representative questions
- **Models**: All three models
- **Duration**: ~20-30 minutes
- **Use case**: Model performance comparison

### **4. Parallel Test**
- **Questions**: 6 questions
- **Workers**: 3 parallel processes
- **Duration**: ~15-20 minutes
- **Use case**: Performance testing

## 📈 **Expected Results**

### **Success Metrics**
- **Success Rate**: >90% for basic queries
- **Response Time**: 30-90 seconds per query
- **Geography Accuracy**: Correct state FIPS codes
- **SQL Quality**: Valid, executable SQL

### **Common Issues**
- **Timeout**: First run takes longer (model loading)
- **Geography**: Ensure correct state mapping
- **Model Selection**: Auto vs manual model choice
- **Schema**: Table code and column validation

## 🎯 **Testing Strategies**

### **1. Progressive Testing**
```bash
# Start with quick test
python batch_test.py

# Then comprehensive test
python mass_test.py

# Finally parallel test
python parallel_test.py
```

### **2. Model-Specific Testing**
```bash
# Test T5 model
modal run modal_deployment.py::query --table-code B01001 --question "What is the total population in Texas?" --force-model t5

# Test SQLCoder model
modal run modal_deployment.py::query --table-code B01001 --question "What is the total population in Texas?" --force-model sqlcoder
```

### **3. Category-Specific Testing**
```bash
# Test only population questions
python mass_test.py
# Select option 4 (Custom Test)
# Enter "population_demographics"
# Enter "auto"
```

## 📊 **Results Analysis**

### **JSON Output**
All tests save results to JSON files with:
- Success/failure status
- Response times
- Generated SQL
- Error messages
- Model used

### **Key Metrics to Monitor**
1. **Success Rate**: Percentage of successful queries
2. **Response Time**: Average time per query
3. **Geography Accuracy**: Correct state FIPS codes
4. **SQL Quality**: Valid, executable SQL queries
5. **Model Performance**: T5 vs SQLCoder comparison

## 🔧 **Troubleshooting**

### **Common Issues**

#### **Timeout Errors**
- **Cause**: Models loading slowly
- **Solution**: Wait longer or increase timeout
- **Prevention**: Run tests during off-peak hours

#### **Geography Errors**
- **Cause**: Incorrect state mapping
- **Solution**: Check geography extraction logic
- **Prevention**: Validate state names in questions

#### **Model Errors**
- **Cause**: Model loading issues
- **Solution**: Check Modal app status
- **Prevention**: Ensure proper authentication

#### **SQL Errors**
- **Cause**: Invalid SQL generation
- **Solution**: Check schema and column mapping
- **Prevention**: Validate table codes and columns

### **Performance Optimization**

#### **Faster Testing**
1. **Use Parallel Testing**: Run multiple queries simultaneously
2. **Model Caching**: Keep models loaded between queries
3. **Batch Processing**: Group similar queries together
4. **Off-Peak Hours**: Run during low-usage periods

#### **Resource Management**
1. **Monitor Modal Usage**: Check app limits and quotas
2. **Optimize Timeouts**: Balance speed vs reliability
3. **Error Handling**: Implement retry logic
4. **Logging**: Track performance metrics

## 📋 **Test Checklist**

### **Before Testing**
- [ ] Modal authentication configured
- [ ] Models deployed and accessible
- [ ] Test questions prepared
- [ ] Expected results defined

### **During Testing**
- [ ] Monitor success rates
- [ ] Track response times
- [ ] Validate geography accuracy
- [ ] Check SQL quality

### **After Testing**
- [ ] Analyze results
- [ ] Identify issues
- [ ] Document findings
- [ ] Plan improvements

## 🎉 **Success Criteria**

### **Basic Validation**
- [ ] >90% success rate
- [ ] <2 minutes average response time
- [ ] Correct geography mapping
- [ ] Valid SQL generation

### **Advanced Validation**
- [ ] Model comparison results
- [ ] Performance benchmarks
- [ ] Error rate analysis
- [ ] Scalability testing

## 🚀 **Next Steps**

1. **Run Quick Test**: Validate basic functionality
2. **Analyze Results**: Identify any issues
3. **Run Full Test**: Comprehensive validation
4. **Optimize Performance**: Based on results
5. **Document Findings**: For future reference

## 📞 **Support**

If you encounter issues:
1. Check the troubleshooting section
2. Review error logs
3. Validate Modal app status
4. Test with simpler queries first
5. Check authentication and permissions

---

**Happy Testing!** 🎯
