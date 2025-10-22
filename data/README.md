# ClinChat RAG Medical Dataset

## Overview
This dataset contains **5,000 synthetic medical records** generated for testing and training the ClinChat RAG application. The data includes realistic clinical information while being completely artificial and HIPAA-compliant.

## Dataset Details

### 📊 **Dataset Statistics**
- **Total Records:** 5,000
- **Date Range:** October 2023 - October 2025
- **File Size:** ~5MB
- **Format:** CSV

### 📋 **Column Schema**

| Column | Type | Description | Coverage |
|--------|------|-------------|----------|
| `patient_id` | String | Unique patient identifier (UUID) | 100% |
| `visit_date` | Date | Date of medical visit | 100% |
| `age` | Integer | Patient age (18-95 years) | 100% |
| `gender` | String | Patient gender (Male/Female/Other) | 100% |
| `visit_type` | String | Type of visit (Outpatient/Inpatient/Emergency/Telehealth/Follow-up) | 100% |
| `primary_symptom` | String | Main presenting symptom | 100% |
| `all_symptoms` | String | All symptoms (semicolon-separated) | 100% |
| `diagnosis` | String | Primary diagnosis | 100% |
| `treatment` | String | Treatment recommendation | 100% |
| `specialty` | String | Medical specialty | 100% |
| `systolic_bp` | Integer | Systolic blood pressure (90-180) | 100% |
| `diastolic_bp` | Integer | Diastolic blood pressure (60-120) | 100% |
| `heart_rate` | Integer | Heart rate (60-120 bpm) | 100% |
| `temperature` | Float | Body temperature (97.0-103.0°F) | 100% |
| `respiratory_rate` | Integer | Respiratory rate (12-24/min) | 100% |
| `oxygen_saturation` | Integer | Oxygen saturation (88-100%) | 100% |
| `glucose` | Integer | Blood glucose level (70-300 mg/dL) | 69.9% |
| `cholesterol` | Integer | Cholesterol level (120-350 mg/dL) | 50.1% |
| `hemoglobin` | Float | Hemoglobin level (8.0-18.0 g/dL) | 59.7% |
| `clinical_note` | String | Detailed clinical narrative | 100% |
| `outcome` | String | Visit outcome | 100% |
| `risk_factors` | String | Risk factors (semicolon-separated) | 79.8% |
| `created_at` | DateTime | Record creation timestamp | 100% |

## 🏥 **Medical Content Coverage**

### **Top Diagnoses** (Most Common)
1. GERD (2.8%)
2. Diabetes Type 2 (2.8%)
3. Influenza (2.8%)
4. Allergic Reaction (2.7%)
5. COVID-19 (2.7%)
6. Asthma (2.7%)
7. Hypertension (2.6%)
8. Migraine (2.7%)

### **Common Symptoms**
- Chest pain, Shortness of breath, Fatigue
- Headache, Nausea, Dizziness
- Fever, Cough, Sore throat
- Back pain, Joint pain, Abdominal pain
- And 30+ more realistic symptoms

### **Medical Specialties Covered**
- Internal Medicine, Cardiology, Endocrinology
- Gastroenterology, Pulmonology, Neurology
- Emergency Medicine, Family Medicine
- And 20+ other specialties

### **Risk Factors**
- High Cholesterol (21.2%)
- Hypertension (20.4%)
- Smoking (20.3%)
- Diabetes (19.9%)
- Obesity (19.8%)

## 📁 **Files Generated**

```
data/
├── clinical_data_5000.csv          # Main dataset (5,000 records)
├── generate_medical_data.py        # Data generation script
└── explore_data.py                 # Data analysis script
```

## 🚀 **Usage in ClinChat RAG**

### **1. Loading the Data**
```python
import pandas as pd

# Load the dataset
df = pd.read_csv('data/clinical_data_5000.csv')

# Basic exploration
print(f"Dataset shape: {df.shape}")
print(f"Columns: {list(df.columns)}")
```

### **2. RAG Use Cases**

#### **Document Indexing**
```python
# Create documents for RAG from clinical notes
documents = []
for _, row in df.iterrows():
    doc_text = f"""
    Patient: {row['age']} year old {row['gender']}
    Date: {row['visit_date']}
    Symptoms: {row['all_symptoms']}
    Diagnosis: {row['diagnosis']}
    Treatment: {row['treatment']}
    Clinical Note: {row['clinical_note']}
    Outcome: {row['outcome']}
    """
    documents.append(doc_text)
```

#### **Query Examples**
Test your RAG system with these queries:
- "What are the symptoms of diabetes?"
- "How is hypertension typically treated?"
- "What vital signs indicate emergency care?"
- "What risk factors are associated with heart disease?"
- "Show me cases with chest pain and shortness of breath"

#### **Embeddings Training**
```python
# Use clinical notes for embedding training
clinical_texts = df['clinical_note'].tolist()
diagnosis_texts = df['diagnosis'].tolist()
symptom_texts = df['all_symptoms'].tolist()

# Combine for comprehensive medical text corpus
medical_corpus = clinical_texts + diagnosis_texts + symptom_texts
```

## 🔍 **Data Quality Features**

### **Realistic Patterns**
- ✅ Age-appropriate conditions
- ✅ Correlated symptoms and diagnoses  
- ✅ Realistic vital sign ranges
- ✅ Appropriate specialty referrals
- ✅ Logical treatment recommendations

### **Data Completeness**
- ✅ 100% coverage for core fields
- ✅ Realistic missing data patterns for lab values
- ✅ Varied symptom combinations
- ✅ Comprehensive clinical notes

### **Privacy Compliant**
- ✅ Completely synthetic data
- ✅ No real patient information
- ✅ HIPAA-compliant
- ✅ Safe for development/testing

## 🔧 **Regenerating Data**

To generate new data or modify the dataset:

```bash
# Generate new dataset
python generate_medical_data.py

# Explore the data
python explore_data.py

# Modify parameters in generate_medical_data.py:
# - Change number of records
# - Add new medical conditions
# - Adjust data distributions
# - Customize clinical note templates
```

## 📊 **Dataset Statistics Summary**

| Metric | Value |
|--------|-------|
| **Records** | 5,000 |
| **Patients** | 5,000 unique |
| **Date Range** | 2 years |
| **Age Range** | 18-95 years |
| **Conditions** | 40+ diagnoses |
| **Symptoms** | 40+ symptoms |
| **Specialties** | 25+ medical specialties |
| **Completeness** | 90%+ for most fields |

## 🎯 **Perfect For**

- ✅ **RAG System Testing** - Query and retrieval evaluation
- ✅ **Embedding Training** - Medical text embeddings
- ✅ **Search Evaluation** - Semantic search testing  
- ✅ **API Development** - Backend testing with realistic data
- ✅ **Demo Purposes** - Showcasing medical AI capabilities
- ✅ **Performance Testing** - Load testing with large datasets

This dataset provides a robust foundation for developing and testing your ClinChat RAG application with realistic medical scenarios while maintaining complete privacy compliance.