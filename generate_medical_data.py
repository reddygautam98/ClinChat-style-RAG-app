"""
Medical Data Generator for ClinChat RAG Application
Generates realistic clinical data for testing and training purposes.
"""

import csv
import random
from datetime import datetime, timedelta
from faker import Faker
import pandas as pd

# Initialize Faker for generating realistic data
fake = Faker()

# Medical data lists for realistic generation
SYMPTOMS = [
    "Chest pain", "Shortness of breath", "Fatigue", "Headache", "Nausea", "Vomiting",
    "Dizziness", "Fever", "Cough", "Sore throat", "Back pain", "Joint pain",
    "Abdominal pain", "Diarrhea", "Constipation", "Weight loss", "Weight gain",
    "Anxiety", "Depression", "Insomnia", "Muscle weakness", "Numbness",
    "Blurred vision", "Rash", "Swelling", "Palpitations", "Loss of appetite",
    "Difficulty swallowing", "Urinary frequency", "Blood in urine", "Confusion",
    "Memory loss", "Seizures", "Tremor", "Stiffness", "Bruising", "Bleeding",
    "High blood pressure", "Low blood pressure", "Irregular heartbeat", "Sweating"
]

DIAGNOSES = [
    "Hypertension", "Diabetes Type 2", "Diabetes Type 1", "Coronary Artery Disease",
    "Myocardial Infarction", "Stroke", "Pneumonia", "Asthma", "COPD", "Bronchitis",
    "Upper Respiratory Infection", "Gastroenteritis", "Peptic Ulcer", "GERD",
    "Appendicitis", "Gallstones", "Kidney Stones", "UTI", "Depression", "Anxiety",
    "Migraine", "Tension Headache", "Arthritis", "Osteoporosis", "Fibromyalgia",
    "Thyroid Disorder", "Anemia", "High Cholesterol", "Obesity", "Sleep Apnea",
    "Allergic Reaction", "Dermatitis", "Psoriasis", "Influenza", "COVID-19",
    "Sinusitis", "Vertigo", "Cataracts", "Glaucoma", "Hearing Loss"
]

TREATMENTS = [
    "Medication therapy", "Physical therapy", "Surgery", "Rest and observation",
    "Dietary modification", "Exercise program", "Stress management", "Counseling",
    "Blood pressure monitoring", "Blood sugar monitoring", "Insulin therapy",
    "Antibiotic treatment", "Pain medication", "Anti-inflammatory drugs",
    "Cardiac catheterization", "Bypass surgery", "Stent placement", "Dialysis",
    "Chemotherapy", "Radiation therapy", "Immunotherapy", "Vaccination",
    "Breathing treatments", "Oxygen therapy", "IV fluids", "Blood transfusion",
    "Wound care", "Splinting", "Cast application", "Joint replacement",
    "Endoscopy", "Biopsy", "CT scan", "MRI", "X-ray", "Ultrasound",
    "ECG monitoring", "Blood tests", "Urinalysis", "Colonoscopy"
]

SPECIALTIES = [
    "Internal Medicine", "Cardiology", "Endocrinology", "Gastroenterology",
    "Pulmonology", "Nephrology", "Neurology", "Psychiatry", "Orthopedics",
    "Dermatology", "Ophthalmology", "Otolaryngology", "Urology", "Oncology",
    "Emergency Medicine", "Family Medicine", "Pediatrics", "Geriatrics",
    "Rheumatology", "Infectious Disease", "Hematology", "Radiology",
    "Pathology", "Anesthesiology", "Surgery", "Obstetrics", "Gynecology"
]

MEDICATIONS = [
    "Lisinopril", "Metformin", "Atorvastatin", "Levothyroxine", "Amlodipine",
    "Metoprolol", "Omeprazole", "Losartan", "Gabapentin", "Sertraline",
    "Ibuprofen", "Acetaminophen", "Aspirin", "Prednisone", "Amoxicillin",
    "Azithromycin", "Ciprofloxacin", "Warfarin", "Insulin", "Albuterol",
    "Furosemide", "Hydrochlorothiazide", "Clopidogrel", "Simvastatin",
    "Pantoprazole", "Escitalopram", "Tramadol", "Oxycodone", "Morphine",
    "Digoxin", "Diltiazem", "Spironolactone", "Rosuvastatin", "Fluoxetine"
]

def generate_clinical_note():
    """Generate a realistic clinical note"""
    templates = [
        f"Patient presents with {random.choice(SYMPTOMS).lower()} for {random.randint(1, 14)} days. Physical examination reveals {random.choice(['normal', 'abnormal', 'concerning'])} findings. Recommend {random.choice(TREATMENTS).lower()} and follow-up.",
        
        f"Follow-up visit for {random.choice(DIAGNOSES).lower()}. Patient reports {random.choice(['improvement', 'worsening', 'no change'])} in symptoms. Current medications include {random.choice(MEDICATIONS)}. Plan: continue current treatment.",
        
        f"New patient consultation for {random.choice(SYMPTOMS).lower()}. History significant for {random.choice(DIAGNOSES).lower()}. Ordered {random.choice(['blood tests', 'imaging studies', 'specialist referral'])}. Return in 2 weeks.",
        
        f"Emergency department visit for acute {random.choice(SYMPTOMS).lower()}. Differential diagnosis includes {random.choice(DIAGNOSES).lower()}. Administered {random.choice(TREATMENTS).lower()}. Discharged home with instructions."
    ]
    return random.choice(templates)

def generate_medical_record():
    """Generate a single medical record"""
    # Patient demographics
    patient_id = fake.uuid4()
    age = random.randint(18, 95)
    gender = random.choice(['Male', 'Female', 'Other'])
    
    # Visit information
    visit_date = fake.date_between(start_date='-2y', end_date='today')
    visit_type = random.choice(['Outpatient', 'Inpatient', 'Emergency', 'Telehealth', 'Follow-up'])
    
    # Clinical data
    primary_symptom = random.choice(SYMPTOMS)
    secondary_symptoms = random.sample(SYMPTOMS, random.randint(0, 3))
    all_symptoms = [primary_symptom] + secondary_symptoms
    
    diagnosis = random.choice(DIAGNOSES)
    treatment = random.choice(TREATMENTS)
    specialty = random.choice(SPECIALTIES)
    
    # Vital signs
    systolic_bp = random.randint(90, 180)
    diastolic_bp = random.randint(60, 120)
    heart_rate = random.randint(60, 120)
    temperature = round(random.uniform(97.0, 103.0), 1)
    respiratory_rate = random.randint(12, 24)
    oxygen_saturation = random.randint(88, 100)
    
    # Lab values (some may be None/empty)
    glucose = random.randint(70, 300) if random.random() > 0.3 else None
    cholesterol = random.randint(120, 350) if random.random() > 0.5 else None
    hemoglobin = round(random.uniform(8.0, 18.0), 1) if random.random() > 0.4 else None
    
    # Clinical notes
    clinical_note = generate_clinical_note()
    
    # Outcome
    outcome = random.choice(['Improved', 'Stable', 'Worsened', 'Resolved', 'Referred', 'Hospitalized'])
    
    # Risk factors
    risk_factors = random.sample([
        'Smoking', 'Obesity', 'Diabetes', 'Hypertension', 'High Cholesterol', 
        'Family History', 'Sedentary Lifestyle', 'Alcohol Use', 'Age', 'Stress'
    ], random.randint(0, 4))
    
    return {
        'patient_id': patient_id,
        'visit_date': visit_date,
        'age': age,
        'gender': gender,
        'visit_type': visit_type,
        'primary_symptom': primary_symptom,
        'all_symptoms': '; '.join(all_symptoms),
        'diagnosis': diagnosis,
        'treatment': treatment,
        'specialty': specialty,
        'systolic_bp': systolic_bp,
        'diastolic_bp': diastolic_bp,
        'heart_rate': heart_rate,
        'temperature': temperature,
        'respiratory_rate': respiratory_rate,
        'oxygen_saturation': oxygen_saturation,
        'glucose': glucose,
        'cholesterol': cholesterol,
        'hemoglobin': hemoglobin,
        'clinical_note': clinical_note,
        'outcome': outcome,
        'risk_factors': '; '.join(risk_factors),
        'created_at': datetime.now().isoformat()
    }

def generate_medical_dataset(num_records=5000):
    """Generate a dataset of medical records"""
    print(f"Generating {num_records} medical records...")
    
    records = []
    for i in range(num_records):
        if (i + 1) % 500 == 0:
            print(f"Generated {i + 1} records...")
        
        record = generate_medical_record()
        records.append(record)
    
    return records

def save_to_csv(records, filename):
    """Save records to CSV file"""
    df = pd.DataFrame(records)
    df.to_csv(filename, index=False)
    print(f"Saved {len(records)} records to {filename}")
    
    # Display summary statistics
    print("\nDataset Summary:")
    print(f"Total Records: {len(records)}")
    print(f"Date Range: {df['visit_date'].min()} to {df['visit_date'].max()}")
    print(f"Age Range: {df['age'].min()} to {df['age'].max()}")
    print(f"Gender Distribution:")
    print(df['gender'].value_counts())
    print(f"\nTop 10 Diagnoses:")
    print(df['diagnosis'].value_counts().head(10))

if __name__ == "__main__":
    # Generate the dataset
    medical_records = generate_medical_dataset(5000)
    
    # Save to CSV
    save_to_csv(medical_records, "data/clinical_data_5000.csv")
    
    print("\n✅ Medical dataset generation completed successfully!")
    print("📊 Dataset includes: Patient demographics, symptoms, diagnoses, treatments, vital signs, lab values, and clinical notes")
    print("🏥 Ready for use in ClinChat RAG application for testing and training purposes")