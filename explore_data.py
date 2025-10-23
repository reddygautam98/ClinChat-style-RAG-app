"""
Data Explorer for HealthAI RAG Medical Dataset
Provides analysis and insights into the generated medical data.
"""

import pandas as pd
import numpy as np

def explore_medical_data(csv_file_path):
    """Explore and analyze the medical dataset"""
    
    print("🔍 Loading and analyzing medical dataset...")
    
    # Load the data
    df = pd.read_csv(csv_file_path)
    
    print(f"\n📊 DATASET OVERVIEW")
    print("=" * 50)
    print(f"Total Records: {len(df):,}")
    print(f"Total Columns: {len(df.columns)}")
    print(f"Date Range: {df['visit_date'].min()} to {df['visit_date'].max()}")
    print(f"Memory Usage: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
    
    print(f"\n📋 COLUMN INFORMATION")
    print("=" * 50)
    for col in df.columns:
        non_null = df[col].notna().sum()
        print(f"{col:20} | Non-null: {non_null:4,} ({non_null/len(df)*100:.1f}%)")
    
    print(f"\n👥 PATIENT DEMOGRAPHICS")
    print("=" * 50)
    print(f"Age Statistics:")
    print(f"  Mean Age: {df['age'].mean():.1f} years")
    print(f"  Age Range: {df['age'].min()} - {df['age'].max()} years")
    print(f"  Median Age: {df['age'].median():.1f} years")
    
    print(f"\nGender Distribution:")
    gender_counts = df['gender'].value_counts()
    for gender, count in gender_counts.items():
        percentage = (count / len(df)) * 100
        print(f"  {gender}: {count:,} ({percentage:.1f}%)")
    
    print(f"\n🏥 VISIT INFORMATION")
    print("=" * 50)
    print("Visit Types:")
    visit_counts = df['visit_type'].value_counts()
    for visit_type, count in visit_counts.head().items():
        percentage = (count / len(df)) * 100
        print(f"  {visit_type}: {count:,} ({percentage:.1f}%)")
    
    print(f"\n🩺 CLINICAL DATA")
    print("=" * 50)
    print("Top 10 Most Common Diagnoses:")
    diagnosis_counts = df['diagnosis'].value_counts()
    for i, (diagnosis, count) in enumerate(diagnosis_counts.head(10).items(), 1):
        percentage = (count / len(df)) * 100
        print(f"  {i:2}. {diagnosis}: {count} ({percentage:.1f}%)")
    
    print(f"\nTop 10 Most Common Primary Symptoms:")
    symptom_counts = df['primary_symptom'].value_counts()
    for i, (symptom, count) in enumerate(symptom_counts.head(10).items(), 1):
        percentage = (count / len(df)) * 100
        print(f"  {i:2}. {symptom}: {count} ({percentage:.1f}%)")
    
    print(f"\nMost Common Specialties:")
    specialty_counts = df['specialty'].value_counts()
    for i, (specialty, count) in enumerate(specialty_counts.head(8).items(), 1):
        percentage = (count / len(df)) * 100
        print(f"  {i:2}. {specialty}: {count} ({percentage:.1f}%)")
    
    print(f"\n💊 VITAL SIGNS ANALYSIS")
    print("=" * 50)
    vital_signs = ['systolic_bp', 'diastolic_bp', 'heart_rate', 'temperature', 'respiratory_rate', 'oxygen_saturation']
    
    for vital in vital_signs:
        mean_val = df[vital].mean()
        std_val = df[vital].std()
        min_val = df[vital].min()
        max_val = df[vital].max()
        print(f"{vital.replace('_', ' ').title()}: {mean_val:.1f} ± {std_val:.1f} (range: {min_val}-{max_val})")
    
    print(f"\n🧪 LAB VALUES")
    print("=" * 50)
    lab_values = ['glucose', 'cholesterol', 'hemoglobin']
    
    for lab in lab_values:
        non_null = df[lab].notna().sum()
        if non_null > 0:
            mean_val = df[lab].mean()
            std_val = df[lab].std()
            min_val = df[lab].min()
            max_val = df[lab].max()
            print(f"{lab.title()}: {mean_val:.1f} ± {std_val:.1f} (range: {min_val:.1f}-{max_val:.1f}) | Available in {non_null:,} records")
    
    print(f"\n📈 OUTCOMES")
    print("=" * 50)
    outcome_counts = df['outcome'].value_counts()
    for outcome, count in outcome_counts.items():
        percentage = (count / len(df)) * 100
        print(f"  {outcome}: {count:,} ({percentage:.1f}%)")
    
    print(f"\n⚠️  RISK FACTORS ANALYSIS")
    print("=" * 50)
    # Count risk factors
    all_risk_factors = []
    for risk_factors_str in df['risk_factors'].dropna():
        if risk_factors_str:
            factors = [factor.strip() for factor in risk_factors_str.split(';')]
            all_risk_factors.extend(factors)
    
    from collections import Counter
    risk_factor_counts = Counter(all_risk_factors)
    
    print("Most Common Risk Factors:")
    for i, (factor, count) in enumerate(risk_factor_counts.most_common(10), 1):
        percentage = (count / len(df)) * 100
        print(f"  {i:2}. {factor}: {count:,} ({percentage:.1f}%)")
    
    return df

def show_sample_records(df, n=5):
    """Display sample records"""
    print(f"\n📋 SAMPLE RECORDS ({n} random records)")
    print("=" * 50)
    
    sample_df = df.sample(n=n)
    
    for i, (_, row) in enumerate(sample_df.iterrows(), 1):
        print(f"\n--- RECORD {i} ---")
        print(f"Patient ID: {row['patient_id']}")
        print(f"Date: {row['visit_date']} | Age: {row['age']} | Gender: {row['gender']}")
        print(f"Visit Type: {row['visit_type']} | Specialty: {row['specialty']}")
        print(f"Primary Symptom: {row['primary_symptom']}")
        print(f"All Symptoms: {row['all_symptoms']}")
        print(f"Diagnosis: {row['diagnosis']}")
        print(f"Treatment: {row['treatment']}")
        print(f"Vital Signs: BP {row['systolic_bp']}/{row['diastolic_bp']}, HR {row['heart_rate']}, Temp {row['temperature']}°F")
        print(f"Outcome: {row['outcome']}")
        print(f"Clinical Note: {row['clinical_note'][:100]}...")
        if row['risk_factors']:
            print(f"Risk Factors: {row['risk_factors']}")

if __name__ == "__main__":
    # Explore the generated dataset
    df = explore_medical_data("data/clinical_data_5000.csv")
    
    # Show sample records
    show_sample_records(df, 3)
    
    print(f"\n✅ Data exploration completed!")
    print(f"💡 This dataset is ready for use in your HealthAI RAG application")
    print(f"🔬 Use this data for testing queries, training embeddings, and RAG evaluation")