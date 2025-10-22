"""
Create sample PDF documents for testing ClinChat RAG system
"""

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import os


def create_diabetes_guide_pdf(filename="data/pdfs/diabetes_guide.pdf"):
    """Create a PDF about diabetes management"""
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    doc = SimpleDocTemplate(filename, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    story.append(Paragraph("Comprehensive Guide to Diabetes Management", title_style))
    story.append(Spacer(1, 12))
    
    # Content
    content = [
        ("Introduction", """
        Diabetes mellitus is a chronic metabolic disorder characterized by elevated blood glucose levels. 
        It affects millions of people worldwide and requires careful management to prevent complications.
        This guide provides comprehensive information about diabetes types, symptoms, and management strategies.
        """),
        
        ("Types of Diabetes", """
        Type 1 Diabetes: An autoimmune condition where the pancreas produces little to no insulin. 
        It typically develops in childhood or adolescence and requires lifelong insulin therapy.
        
        Type 2 Diabetes: The most common form, characterized by insulin resistance and relative insulin deficiency. 
        It often develops in adults over 40 and can sometimes be managed with lifestyle changes and oral medications.
        
        Gestational Diabetes: Occurs during pregnancy and usually resolves after delivery, but increases 
        the risk of developing Type 2 diabetes later in life.
        """),
        
        ("Symptoms and Diagnosis", """
        Common symptoms of diabetes include excessive thirst, frequent urination, unexplained weight loss, 
        fatigue, blurred vision, and slow-healing wounds. Diagnosis is typically made through blood tests 
        including fasting glucose, oral glucose tolerance test, or HbA1c levels.
        
        Early detection is crucial for preventing complications and maintaining good health outcomes.
        """),
        
        ("Treatment and Management", """
        Medication Management: Type 1 diabetes requires insulin therapy through injections or insulin pumps. 
        Type 2 diabetes may be treated with oral medications like metformin, sulfonylureas, or newer 
        classes like SGLT-2 inhibitors and GLP-1 receptor agonists.
        
        Dietary Interventions: Focus on carbohydrate counting, portion control, and choosing foods with 
        low glycemic index. A balanced diet with regular meal timing helps maintain stable blood glucose levels.
        
        Physical Activity: Regular exercise improves insulin sensitivity and helps control blood glucose levels. 
        Aim for at least 150 minutes of moderate-intensity aerobic activity per week.
        """),
        
        ("Monitoring and Complications", """
        Blood Glucose Monitoring: Regular self-monitoring using glucometers or continuous glucose monitors 
        is essential for optimal diabetes management. Target ranges vary by individual but generally 
        aim for 80-130 mg/dL before meals and less than 180 mg/dL two hours after meals.
        
        Long-term Complications: Diabetes can lead to cardiovascular disease, nephropathy (kidney damage), 
        retinopathy (eye damage), and neuropathy (nerve damage). Regular screening and preventive care 
        can help reduce the risk of these complications.
        """),
        
        ("Conclusion", """
        Effective diabetes management requires a comprehensive approach including proper medication, 
        diet, exercise, and regular monitoring. Healthcare providers should work closely with patients 
        to develop individualized treatment plans that consider lifestyle, preferences, and health goals.
        
        With proper management, people with diabetes can lead healthy, active lives and prevent or 
        delay the onset of complications.
        """)
    ]
    
    for section_title, section_content in content:
        # Section title
        story.append(Paragraph(section_title, styles['Heading2']))
        story.append(Spacer(1, 12))
        
        # Section content
        story.append(Paragraph(section_content.strip(), styles['Normal']))
        story.append(Spacer(1, 20))
    
    doc.build(story)
    print(f"Created diabetes guide PDF: {filename}")


def create_hypertension_pdf(filename="data/pdfs/hypertension_management.pdf"):
    """Create a PDF about hypertension management"""
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    doc = SimpleDocTemplate(filename, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1
    )
    story.append(Paragraph("Hypertension: Prevention and Management", title_style))
    story.append(Spacer(1, 12))
    
    content = [
        ("Understanding Hypertension", """
        Hypertension, commonly known as high blood pressure, is a chronic medical condition where 
        blood pressure in the arteries is persistently elevated. It is often called the "silent killer" 
        because it typically has no symptoms but can lead to serious health complications.
        """),
        
        ("Blood Pressure Classifications", """
        Normal: Less than 120/80 mmHg
        Elevated: Systolic 120-129 and diastolic less than 80
        Stage 1 Hypertension: Systolic 130-139 or diastolic 80-89
        Stage 2 Hypertension: Systolic 140 or higher or diastolic 90 or higher
        Hypertensive Crisis: Systolic higher than 180 and/or diastolic higher than 120
        """),
        
        ("Risk Factors", """
        Non-modifiable risk factors include age, family history, race, and gender. 
        Modifiable risk factors include obesity, physical inactivity, smoking, excessive alcohol 
        consumption, high sodium intake, stress, and certain chronic conditions like diabetes.
        """),
        
        ("Treatment Approaches", """
        Lifestyle Modifications: Weight management, regular physical activity, dietary changes 
        (DASH diet), sodium reduction, limited alcohol consumption, and stress management.
        
        Medications: ACE inhibitors, ARBs, calcium channel blockers, diuretics, and beta-blockers 
        are commonly prescribed. The choice depends on individual patient factors and comorbidities.
        """),
        
        ("Monitoring and Prevention", """
        Regular blood pressure monitoring at home and during healthcare visits is essential. 
        Prevention strategies include maintaining healthy weight, regular exercise, balanced diet, 
        limiting sodium and alcohol, not smoking, and managing stress effectively.
        
        Complications of untreated hypertension include heart attack, stroke, kidney disease, 
        and vision problems.
        """)
    ]
    
    for section_title, section_content in content:
        story.append(Paragraph(section_title, styles['Heading2']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(section_content.strip(), styles['Normal']))
        story.append(Spacer(1, 20))
    
    doc.build(story)
    print(f"Created hypertension PDF: {filename}")


def create_cardiac_care_pdf(filename="data/pdfs/cardiac_care.pdf"):
    """Create a PDF about cardiac care"""
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    doc = SimpleDocTemplate(filename, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1
    )
    story.append(Paragraph("Cardiac Care and Heart Health", title_style))
    story.append(Spacer(1, 12))
    
    content = [
        ("Heart Disease Overview", """
        Cardiovascular disease remains the leading cause of death worldwide. It encompasses various 
        conditions affecting the heart and blood vessels, including coronary artery disease, 
        heart failure, arrhythmias, and valvular heart disease.
        """),
        
        ("Common Cardiac Conditions", """
        Coronary Artery Disease: Narrowing of coronary arteries due to plaque buildup, leading to 
        reduced blood flow to the heart muscle.
        
        Heart Failure: Condition where the heart cannot pump blood effectively to meet the body's needs.
        
        Arrhythmias: Abnormal heart rhythms that can be too fast, too slow, or irregular.
        
        Myocardial Infarction: Heart attack caused by blocked blood flow to part of the heart muscle.
        """),
        
        ("Symptoms and Warning Signs", """
        Chest pain or discomfort, shortness of breath, fatigue, swelling in legs or abdomen, 
        palpitations, dizziness, and fainting are common cardiac symptoms. Seek immediate medical 
        attention for severe chest pain, especially if accompanied by nausea, sweating, or 
        pain radiating to arms or jaw.
        """),
        
        ("Prevention and Treatment", """
        Lifestyle modifications include regular exercise, heart-healthy diet, maintaining healthy 
        weight, not smoking, limiting alcohol, and managing stress. Medical treatments may include 
        medications like statins, ACE inhibitors, beta-blockers, and antiplatelet agents.
        
        Advanced treatments include angioplasty, stent placement, bypass surgery, and implantable devices.
        """),
        
        ("Emergency Response", """
        Learn CPR and recognize signs of heart attack and stroke. Call emergency services immediately 
        if someone experiences severe chest pain, difficulty breathing, or loss of consciousness. 
        Early intervention can save lives and prevent permanent damage.
        """)
    ]
    
    for section_title, section_content in content:
        story.append(Paragraph(section_title, styles['Heading2']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(section_content.strip(), styles['Normal']))
        story.append(Spacer(1, 20))
    
    doc.build(story)
    print(f"Created cardiac care PDF: {filename}")


def create_all_test_pdfs():
    """Create all test PDFs"""
    print("Creating test PDFs for ClinChat RAG system...")
    
    create_diabetes_guide_pdf()
    create_hypertension_pdf() 
    create_cardiac_care_pdf()
    
    print("✅ All test PDFs created successfully!")


if __name__ == "__main__":
    create_all_test_pdfs()