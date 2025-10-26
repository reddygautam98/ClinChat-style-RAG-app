"""
Enhanced input validation for healthcare AI applications
HIPAA-compliant validation with medical context awareness
"""
import re
import json
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, field_validator, Field
from dataclasses import dataclass
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of input validation"""
    is_valid: bool
    sanitized_input: str
    violations: List[str]
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    pii_detected: List[str]
    medical_context_score: float

class MedicalInputValidator:
    """Enhanced input validation for medical queries"""
    
    def __init__(self):
        # HIPAA-defined PII patterns
        self.pii_patterns = {
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b|\b\d{9}\b',
            'phone': r'\b\d{3}-\d{3}-\d{4}\b|\(\d{3}\)\s*\d{3}-\d{4}',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'medical_record': r'\b(MRN|MR|Medical Record)[\s#:]*\d+\b',
            'patient_id': r'\b(Patient|PT|ID)[\s#:]*\d+\b',
            'date_of_birth': r'\b\d{1,2}/\d{1,2}/\d{4}\b|\b\d{4}-\d{1,2}-\d{1,2}\b',
            'address': r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd)\b'
        }
        
        # Prompt injection patterns
        self.injection_patterns = [
            r'ignore\s+previous\s+instructions',
            r'forget\s+everything\s+above',
            r'system\s*:\s*you\s+are',
            r'assistant\s*:\s*i\s+will',
            r'\\n\\n(human|assistant|system)\\s*:',
            r'jailbreak|bypass|override',
            r'pretend\s+you\s+are\s+not\s+an?\s+ai',
            r'roleplay\s+as'
        ]
        
        # Medical terminology indicators
        self.medical_keywords = {
            'symptoms': ['pain', 'fever', 'nausea', 'headache', 'fatigue', 'cough', 'dizziness'],
            'conditions': ['diabetes', 'hypertension', 'asthma', 'cancer', 'infection', 'disease'],
            'medications': ['medication', 'drug', 'prescription', 'treatment', 'therapy', 'dose'],
            'anatomy': ['heart', 'lung', 'brain', 'liver', 'kidney', 'blood', 'bone'],
            'procedures': ['surgery', 'procedure', 'test', 'scan', 'biopsy', 'examination']
        }
        
        # Dangerous medical advice patterns
        self.dangerous_patterns = [
            r'stop\s+taking\s+(medication|medicine)',
            r'increase\s+dose',
            r'ignore\s+doctor',
            r'self\s*-?\s*diagnose',
            r'emergency\s+situation'
        ]

    def validate_medical_query(self, query: str, user_context: Dict[str, Any] = None) -> ValidationResult:
        """
        Comprehensive validation of medical queries
        
        Args:
            query: The input query to validate
            user_context: Additional context about the user/session
            
        Returns:
            ValidationResult with validation status and details
        """
        violations = []
        risk_level = "LOW"
        pii_detected = []
        
        # Basic input validation
        if not query or not query.strip():
            violations.append("Empty query")
            return ValidationResult(False, "", violations, "CRITICAL", [], 0.0)
        
        # Length validation
        if len(query) > 4000:
            violations.append("Query exceeds maximum length (4000 characters)")
            risk_level = "HIGH"
        
        # PII Detection
        pii_found = self._detect_pii(query)
        if pii_found:
            pii_detected = pii_found
            violations.append(f"PII detected: {', '.join(pii_found)}")
            risk_level = "CRITICAL"
        
        # Prompt injection detection
        injection_detected = self._detect_injection(query)
        if injection_detected:
            violations.append("Potential prompt injection detected")
            risk_level = "HIGH"
        
        # Medical context analysis
        medical_score = self._analyze_medical_context(query)
        
        # Dangerous advice pattern detection
        dangerous_detected = self._detect_dangerous_patterns(query)
        if dangerous_detected:
            violations.append("Potentially dangerous medical advice request detected")
            risk_level = "HIGH"
        
        # Content sanitization
        sanitized_query = self._sanitize_input(query, pii_detected)
        
        # Risk level assessment
        final_risk = self._assess_risk_level(violations, medical_score, user_context)
        
        is_valid = len(violations) == 0 or (final_risk in ["LOW", "MEDIUM"] and not pii_detected)
        
        # Log validation attempt for audit
        self._log_validation_attempt(query, is_valid, violations, final_risk)
        
        return ValidationResult(
            is_valid=is_valid,
            sanitized_input=sanitized_query,
            violations=violations,
            risk_level=final_risk,
            pii_detected=pii_detected,
            medical_context_score=medical_score
        )

    def _detect_pii(self, text: str) -> List[str]:
        """Detect PII in the input text"""
        detected = []
        
        for pii_type, pattern in self.pii_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                detected.append(pii_type)
        
        return detected

    def _detect_injection(self, text: str) -> bool:
        """Detect potential prompt injection attempts"""
        for pattern in self.injection_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _analyze_medical_context(self, text: str) -> float:
        """Analyze how medical-focused the query is"""
        text_lower = text.lower()
        medical_word_count = 0
        total_categories = 0
        
        for category, keywords in self.medical_keywords.items():
            category_matches = sum(1 for keyword in keywords if keyword in text_lower)
            if category_matches > 0:
                total_categories += 1
                medical_word_count += category_matches
        
        # Calculate score based on medical keyword density and category coverage
        word_density = medical_word_count / max(len(text.split()), 1)
        category_coverage = total_categories / len(self.medical_keywords)
        
        return min(1.0, (word_density * 10) + (category_coverage * 0.5))

    def _detect_dangerous_patterns(self, text: str) -> bool:
        """Detect potentially dangerous medical advice requests"""
        for pattern in self.dangerous_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _sanitize_input(self, text: str, pii_types: List[str]) -> str:
        """Sanitize input by removing or masking PII"""
        sanitized = text
        
        # Replace detected PII with masked versions
        for pii_type in pii_types:
            if pii_type in self.pii_patterns:
                pattern = self.pii_patterns[pii_type]
                sanitized = re.sub(pattern, f'[{pii_type.upper()}_REDACTED]', sanitized, flags=re.IGNORECASE)
        
        # Remove excessive whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        return sanitized

    def _assess_risk_level(self, violations: List[str], medical_score: float, user_context: Dict[str, Any]) -> str:
        """Assess overall risk level based on various factors"""
        if any('PII detected' in v for v in violations):
            return "CRITICAL"
        
        if any('injection' in v.lower() for v in violations):
            return "HIGH"
        
        if any('dangerous' in v.lower() for v in violations):
            return "HIGH"
        
        if len(violations) > 2:
            return "HIGH"
        
        if medical_score > 0.7 and len(violations) > 0:
            return "MEDIUM"
        
        if len(violations) > 0:
            return "MEDIUM"
        
        return "LOW"

    def _log_validation_attempt(self, query: str, is_valid: bool, violations: List[str], risk_level: str):
        """Log validation attempt for HIPAA audit trail"""
        # Hash query for privacy-compliant logging
        query_hash = hashlib.sha256(query.encode()).hexdigest()[:16]
        
        audit_data = {
            "timestamp": "2024-10-24T00:00:00Z",  # This would be actual timestamp
            "query_hash": query_hash,
            "is_valid": is_valid,
            "violations": violations,
            "risk_level": risk_level,
            "event_type": "INPUT_VALIDATION",
            "query_length": len(query)
        }
        
        logger.info(f"Input validation: {json.dumps(audit_data)}")

class EnhancedMedicalQuery(BaseModel):
    """Enhanced medical query model with validation"""
    
    question: str = Field(..., min_length=5, max_length=4000)
    use_fusion: bool = True
    model_preference: str = Field(default="auto", pattern="^(auto|gemini|groq)$")
    patient_context: Optional[str] = Field(default=None, max_length=500)
    urgency_level: str = Field(default="routine", pattern="^(routine|urgent|emergency)$")
    
    @field_validator('question')
    @classmethod
    def validate_question(cls, v: str) -> str:
        """Validate medical question input"""
        validator = MedicalInputValidator()
        result = validator.validate_medical_query(v)
        
        if not result.is_valid:
            raise ValueError(f"Invalid medical query: {'; '.join(result.violations)}")
        
        return result.sanitized_input
    
    @field_validator('patient_context')
    @classmethod
    def validate_patient_context(cls, v: Optional[str]) -> Optional[str]:
        """Validate patient context for PII"""
        if v is None:
            return v
            
        validator = MedicalInputValidator()
        result = validator.validate_medical_query(v)
        
        if result.pii_detected:
            raise ValueError("Patient context cannot contain PII")
        
        return result.sanitized_input