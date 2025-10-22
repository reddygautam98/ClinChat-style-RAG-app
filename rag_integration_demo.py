"""
RAG Integration Example for ClinChat Medical Dataset
Shows how to use the generated medical data in your RAG application.
"""

import pandas as pd
import json
from typing import List, Dict, Any

def load_medical_data(csv_path: str = "data/clinical_data_5000.csv") -> pd.DataFrame:
    """Load the medical dataset"""
    print(f"📊 Loading medical dataset from {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"✅ Loaded {len(df):,} medical records")
    return df

def create_rag_documents(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Convert medical records into RAG-ready documents"""
    print("🔄 Converting medical records to RAG documents...")
    
    documents = []
    
    for idx, row in df.iterrows():
        # Create comprehensive document text
        doc_text = f"""
MEDICAL RECORD - {row['visit_date']}

PATIENT INFORMATION:
- Age: {row['age']} years
- Gender: {row['gender']}
- Visit Type: {row['visit_type']}

CLINICAL PRESENTATION:
- Primary Symptom: {row['primary_symptom']}
- All Symptoms: {row['all_symptoms']}
- Diagnosis: {row['diagnosis']}
- Specialty: {row['specialty']}

VITAL SIGNS:
- Blood Pressure: {row['systolic_bp']}/{row['diastolic_bp']} mmHg
- Heart Rate: {row['heart_rate']} bpm
- Temperature: {row['temperature']}°F
- Respiratory Rate: {row['respiratory_rate']}/min
- Oxygen Saturation: {row['oxygen_saturation']}%

LABORATORY VALUES:
- Glucose: {row['glucose'] if pd.notna(row['glucose']) else 'Not measured'} mg/dL
- Cholesterol: {row['cholesterol'] if pd.notna(row['cholesterol']) else 'Not measured'} mg/dL
- Hemoglobin: {row['hemoglobin'] if pd.notna(row['hemoglobin']) else 'Not measured'} g/dL

TREATMENT & OUTCOME:
- Treatment: {row['treatment']}
- Outcome: {row['outcome']}
- Risk Factors: {row['risk_factors'] if pd.notna(row['risk_factors']) else 'None documented'}

CLINICAL NOTES:
{row['clinical_note']}
        """.strip()
        
        # Create document metadata
        document = {
            "id": f"med_record_{idx}",
            "patient_id": row['patient_id'],
            "content": doc_text,
            "metadata": {
                "visit_date": row['visit_date'],
                "age": row['age'],
                "gender": row['gender'],
                "diagnosis": row['diagnosis'],
                "specialty": row['specialty'],
                "primary_symptom": row['primary_symptom'],
                "outcome": row['outcome']
            }
        }
        
        documents.append(document)
        
        if (idx + 1) % 1000 == 0:
            print(f"  Processed {idx + 1:,} records...")
    
    print(f"✅ Created {len(documents):,} RAG documents")
    return documents

def create_knowledge_base_queries() -> List[Dict[str, Any]]:
    """Create sample queries for testing RAG system"""
    
    test_queries = [
        {
            "query": "What are the symptoms of diabetes?",
            "category": "symptoms",
            "expected_topics": ["diabetes", "symptoms", "glucose"]
        },
        {
            "query": "How is hypertension typically treated?",
            "category": "treatment", 
            "expected_topics": ["hypertension", "blood pressure", "treatment"]
        },
        {
            "query": "What vital signs indicate emergency care?",
            "category": "emergency",
            "expected_topics": ["vital signs", "emergency", "critical values"]
        },
        {
            "query": "What are common risk factors for heart disease?",
            "category": "risk_factors",
            "expected_topics": ["heart disease", "risk factors", "cardiovascular"]
        },
        {
            "query": "Show me cases with chest pain and shortness of breath",
            "category": "symptom_search",
            "expected_topics": ["chest pain", "shortness of breath", "cardiac"]
        },
        {
            "query": "What medications are commonly prescribed for anxiety?",
            "category": "medications",
            "expected_topics": ["anxiety", "medications", "treatment"]
        },
        {
            "query": "What are normal ranges for blood pressure?",
            "category": "normal_values",
            "expected_topics": ["blood pressure", "normal", "ranges"]
        },
        {
            "query": "How do you diagnose sleep apnea?",
            "category": "diagnosis",
            "expected_topics": ["sleep apnea", "diagnosis", "symptoms"]
        },
        {
            "query": "What are the side effects of insulin therapy?",
            "category": "side_effects",
            "expected_topics": ["insulin", "side effects", "diabetes"]
        },
        {
            "query": "When should someone see a cardiologist?",
            "category": "referral",
            "expected_topics": ["cardiology", "heart", "referral"]
        }
    ]
    
    return test_queries

def filter_documents_by_condition(documents: List[Dict], condition: str) -> List[Dict]:
    """Filter documents by medical condition"""
    filtered = [
        doc for doc in documents 
        if condition.lower() in doc['metadata']['diagnosis'].lower()
    ]
    print(f"📋 Found {len(filtered)} documents related to '{condition}'")
    return filtered

def get_documents_by_symptom(documents: List[Dict], symptom: str) -> List[Dict]:
    """Get documents by primary symptom"""
    filtered = [
        doc for doc in documents 
        if symptom.lower() in doc['metadata']['primary_symptom'].lower()
    ]
    print(f"🩺 Found {len(filtered)} documents with symptom '{symptom}'")
    return filtered

def save_rag_documents(documents: List[Dict], output_file: str = "data/rag_documents.json"):
    """Save RAG documents to JSON file"""
    print(f"💾 Saving RAG documents to {output_file}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(documents, f, indent=2, default=str)
    
    print(f"✅ Saved {len(documents):,} documents")

def demonstrate_rag_integration():
    """Demonstrate how to integrate the medical data with RAG"""
    
    print("🏥 ClinChat RAG Integration Demo")
    print("=" * 50)
    
    # 1. Load medical data
    df = load_medical_data()
    
    # 2. Create RAG documents
    documents = create_rag_documents(df)
    
    # 3. Save documents for RAG system
    save_rag_documents(documents)
    
    # 4. Demonstrate filtering
    print("\n🔍 Document Filtering Examples:")
    filter_documents_by_condition(documents, "Diabetes")
    get_documents_by_symptom(documents, "Chest pain")
    
    # 5. Show sample queries
    print("\n❓ Sample RAG Test Queries:")
    test_queries = create_knowledge_base_queries()
    
    for i, query in enumerate(test_queries, 1):
        print(f"{i:2}. {query['query']} ({query['category']})")
    
    # 6. Display statistics
    print("\n📊 RAG Integration Summary:")
    print(f"   Total Documents: {len(documents):,}")
    print(f"   Average Document Length: {sum(len(doc['content']) for doc in documents) // len(documents):,} characters")
    print(f"   Unique Diagnoses: {df['diagnosis'].nunique()}")
    print(f"   Unique Symptoms: {df['primary_symptom'].nunique()}")
    print(f"   Date Range: {df['visit_date'].min()} to {df['visit_date'].max()}")
    
    print("\n✅ RAG integration demo completed!")
    print("💡 Use 'data/rag_documents.json' to load into your RAG system")
    print("🔬 Test with the provided sample queries for evaluation")

if __name__ == "__main__":
    demonstrate_rag_integration()