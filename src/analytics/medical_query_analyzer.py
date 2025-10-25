"""
Medical Query Analytics System
Advanced analysis of medical queries and patterns for healthcare AI optimization
"""
import re
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import spacy
from collections import Counter, defaultdict
import boto3
from textblob import TextBlob

logger = logging.getLogger(__name__)

class MedicalDomain(Enum):
    """Medical domain categories"""
    SYMPTOMS = "symptoms"
    DIAGNOSIS = "diagnosis"
    TREATMENT = "treatment"
    MEDICATION = "medication"
    PREVENTION = "prevention"
    LIFESTYLE = "lifestyle"
    EMERGENCY = "emergency"
    MENTAL_HEALTH = "mental_health"
    PEDIATRICS = "pediatrics"
    GERIATRICS = "geriatrics"
    WOMEN_HEALTH = "women_health"
    MEN_HEALTH = "men_health"

class QueryComplexity(Enum):
    """Query complexity levels"""
    SIMPLE = "simple"          # Single symptom/condition
    MODERATE = "moderate"      # Multiple related symptoms
    COMPLEX = "complex"        # Multiple conditions/medications
    VERY_COMPLEX = "very_complex"  # Complex medical history

@dataclass
class MedicalQueryAnalysis:
    """Analysis results for a medical query"""
    query_id: str
    original_query: str
    medical_domains: List[MedicalDomain]
    complexity: QueryComplexity
    medical_entities: List[str]
    symptoms: List[str]
    conditions: List[str]
    medications: List[str]
    urgency_score: float
    confidence_score: float
    query_intent: str
    clinical_keywords: List[str]
    extracted_relationships: Dict[str, List[str]]

class MedicalQueryAnalyzer:
    """Advanced medical query analysis and pattern recognition"""
    
    def __init__(self):
        # Load medical NLP model
        try:
            self.nlp = spacy.load("en_core_web_md")
        except OSError:
            logger.warning("Spacy model not found, using basic analysis")
            self.nlp = None
        
        # AWS services
        self.comprehend_medical = boto3.client('comprehendmedical')
        self.dynamodb = boto3.resource('dynamodb')
        
        # Medical knowledge bases
        self.medical_keywords = self._load_medical_keywords()
        self.symptom_patterns = self._load_symptom_patterns()
        self.medication_patterns = self._load_medication_patterns()
        self.urgency_indicators = self._load_urgency_indicators()
        
        # Analytics storage
        self.analytics_table = 'healthai-query-analytics'
    
    def analyze_query(self, 
                     query: str, 
                     user_context: Optional[Dict[str, Any]] = None) -> MedicalQueryAnalysis:
        """Comprehensive analysis of medical query"""
        
        query_id = f"qa_{int(datetime.now().timestamp())}_{hash(query) % 10000}"
        
        try:
            # Basic text analysis
            cleaned_query = self._clean_query_text(query)
            
            # Extract medical entities using AWS Comprehend Medical
            medical_entities = self._extract_medical_entities(cleaned_query)
            
            # Classify medical domains
            domains = self._classify_medical_domains(cleaned_query, medical_entities)
            
            # Determine complexity
            complexity = self._assess_query_complexity(cleaned_query, medical_entities)
            
            # Extract specific medical components
            symptoms = self._extract_symptoms(cleaned_query, medical_entities)
            conditions = self._extract_conditions(cleaned_query, medical_entities)
            medications = self._extract_medications(cleaned_query, medical_entities)
            
            # Calculate urgency and confidence scores
            urgency_score = self._calculate_urgency_score(cleaned_query, symptoms)
            confidence_score = self._calculate_confidence_score(medical_entities, domains)
            
            # Determine query intent
            intent = self._determine_query_intent(cleaned_query, domains)
            
            # Extract clinical keywords
            clinical_keywords = self._extract_clinical_keywords(cleaned_query)
            
            # Find relationships between medical entities
            relationships = self._extract_medical_relationships(
                cleaned_query, symptoms, conditions, medications
            )
            
            analysis = MedicalQueryAnalysis(
                query_id=query_id,
                original_query=query,
                medical_domains=domains,
                complexity=complexity,
                medical_entities=medical_entities,
                symptoms=symptoms,
                conditions=conditions,
                medications=medications,
                urgency_score=urgency_score,
                confidence_score=confidence_score,
                query_intent=intent,
                clinical_keywords=clinical_keywords,
                extracted_relationships=relationships
            )
            
            # Store analysis for pattern recognition
            self._store_query_analysis(analysis, user_context)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Query analysis failed: {e}")
            # Return minimal analysis
            return MedicalQueryAnalysis(
                query_id=query_id,
                original_query=query,
                medical_domains=[MedicalDomain.SYMPTOMS],
                complexity=QueryComplexity.SIMPLE,
                medical_entities=[],
                symptoms=[],
                conditions=[],
                medications=[],
                urgency_score=0.5,
                confidence_score=0.0,
                query_intent="information_request",
                clinical_keywords=[],
                extracted_relationships={}
            )
    
    def get_query_patterns(self, 
                          start_date: datetime, 
                          end_date: datetime) -> Dict[str, Any]:
        """Get medical query patterns and trends"""
        
        try:
            patterns = {
                'domain_distribution': self._analyze_domain_patterns(start_date, end_date),
                'complexity_trends': self._analyze_complexity_trends(start_date, end_date),
                'common_symptoms': self._analyze_symptom_patterns(start_date, end_date),
                'medication_queries': self._analyze_medication_patterns(start_date, end_date),
                'urgency_distribution': self._analyze_urgency_patterns(start_date, end_date),
                'clinical_insights': self._generate_clinical_insights(start_date, end_date),
                'query_intent_analysis': self._analyze_query_intents(start_date, end_date),
                'temporal_patterns': self._analyze_temporal_patterns(start_date, end_date)
            }
            
            return patterns
            
        except Exception as e:
            logger.error(f"Pattern analysis failed: {e}")
            return {}
    
    def _extract_medical_entities(self, query: str) -> List[str]:
        """Extract medical entities using AWS Comprehend Medical"""
        try:
            response = self.comprehend_medical.detect_entities_v2(Text=query)
            
            entities = []
            for entity in response.get('Entities', []):
                if entity['Score'] > 0.5:  # Confidence threshold
                    entities.append({
                        'text': entity['Text'],
                        'category': entity['Category'],
                        'type': entity['Type'],
                        'score': entity['Score']
                    })
            
            return entities
            
        except Exception as e:
            logger.error(f"Medical entity extraction failed: {e}")
            return self._fallback_entity_extraction(query)
    
    def _fallback_entity_extraction(self, query: str) -> List[str]:
        """Fallback medical entity extraction using patterns"""
        entities = []
        
        # Common medical terms patterns
        medical_patterns = [
            r'\b(pain|ache|hurt|sore|tender)\b',
            r'\b(fever|temperature|chills)\b',
            r'\b(nausea|vomiting|dizzy|headache)\b',
            r'\b(diabetes|hypertension|asthma|arthritis)\b',
            r'\b(medication|medicine|drug|pill|tablet)\b'
        ]
        
        for pattern in medical_patterns:
            matches = re.findall(pattern, query.lower())
            entities.extend(matches)
        
        return list(set(entities))
    
    def _classify_medical_domains(self, 
                                query: str, 
                                entities: List[str]) -> List[MedicalDomain]:
        """Classify query into medical domains"""
        domains = []
        
        domain_keywords = {
            MedicalDomain.SYMPTOMS: ['symptom', 'feel', 'pain', 'ache', 'hurt', 'dizzy', 'nausea'],
            MedicalDomain.DIAGNOSIS: ['diagnosis', 'condition', 'disease', 'disorder', 'syndrome'],
            MedicalDomain.TREATMENT: ['treatment', 'therapy', 'cure', 'heal', 'surgery'],
            MedicalDomain.MEDICATION: ['medication', 'medicine', 'drug', 'pill', 'dose'],
            MedicalDomain.PREVENTION: ['prevent', 'avoid', 'reduce risk', 'healthy'],
            MedicalDomain.EMERGENCY: ['emergency', 'urgent', 'severe', 'immediate', 'critical']
        }
        
        query_lower = query.lower()
        
        for domain, keywords in domain_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                domains.append(domain)
        
        return domains if domains else [MedicalDomain.SYMPTOMS]
    
    def _assess_query_complexity(self, 
                               query: str, 
                               entities: List[str]) -> QueryComplexity:
        """Assess query complexity based on multiple factors"""
        
        # Count medical entities
        entity_count = len(entities)
        
        # Count sentences
        sentence_count = len(query.split('.'))
        
        # Count medical conditions mentioned
        condition_indicators = ['and', 'also', 'plus', 'additionally', 'furthermore']
        condition_count = sum(1 for indicator in condition_indicators if indicator in query.lower())
        
        # Calculate complexity score
        complexity_score = entity_count + sentence_count + condition_count
        
        if complexity_score <= 2:
            return QueryComplexity.SIMPLE
        elif complexity_score <= 4:
            return QueryComplexity.MODERATE
        elif complexity_score <= 7:
            return QueryComplexity.COMPLEX
        else:
            return QueryComplexity.VERY_COMPLEX
    
    def _extract_symptoms(self, query: str, entities: List[str]) -> List[str]:
        """Extract symptoms from query"""
        symptoms = []
        
        symptom_patterns = [
            r'\b(pain|ache|hurt|sore|tender|burning|throbbing)\b',
            r'\b(nausea|vomiting|dizzy|lightheaded|weak|tired)\b',
            r'\b(fever|chills|sweating|hot|cold)\b',
            r'\b(cough|sneeze|runny nose|congestion)\b',
            r'\b(headache|migraine|pressure)\b'
        ]
        
        for pattern in symptom_patterns:
            matches = re.findall(pattern, query.lower())
            symptoms.extend(matches)
        
        return list(set(symptoms))
    
    def _extract_conditions(self, query: str, entities: List[str]) -> List[str]:
        """Extract medical conditions from query"""
        conditions = []
        
        condition_patterns = [
            r'\b(diabetes|hypertension|asthma|arthritis|cancer)\b',
            r'\b(depression|anxiety|bipolar|schizophrenia)\b',
            r'\b(heart disease|stroke|kidney disease)\b'
        ]
        
        for pattern in condition_patterns:
            matches = re.findall(pattern, query.lower())
            conditions.extend(matches)
        
        return list(set(conditions))
    
    def _extract_medications(self, query: str, entities: List[str]) -> List[str]:
        """Extract medications from query"""
        medications = []
        
        # Common medication patterns
        med_patterns = [
            r'\b(aspirin|ibuprofen|acetaminophen|tylenol)\b',
            r'\b(insulin|metformin|lisinopril|atorvastatin)\b',
            r'\b(amoxicillin|azithromycin|ciprofloxacin)\b'
        ]
        
        for pattern in med_patterns:
            matches = re.findall(pattern, query.lower())
            medications.extend(matches)
        
        return list(set(medications))
    
    def _calculate_urgency_score(self, query: str, symptoms: List[str]) -> float:
        """Calculate urgency score based on symptoms and language"""
        
        urgency_keywords = {
            'high': ['emergency', 'urgent', 'severe', 'critical', 'immediate', 'chest pain'],
            'medium': ['painful', 'concern', 'worry', 'problem', 'issue'],
            'low': ['mild', 'slight', 'occasional', 'sometimes']
        }
        
        query_lower = query.lower()
        score = 0.5  # baseline
        
        # Check for high urgency indicators
        if any(keyword in query_lower for keyword in urgency_keywords['high']):
            score += 0.4
        
        # Check for medium urgency indicators  
        elif any(keyword in query_lower for keyword in urgency_keywords['medium']):
            score += 0.2
        
        # Check for low urgency indicators
        elif any(keyword in query_lower for keyword in urgency_keywords['low']):
            score -= 0.2
        
        return max(0.0, min(1.0, score))
    
    def _calculate_confidence_score(self, 
                                  entities: List[str], 
                                  domains: List[MedicalDomain]) -> float:
        """Calculate confidence in query analysis"""
        
        # Base confidence
        confidence = 0.5
        
        # Increase confidence based on number of medical entities
        confidence += min(0.3, len(entities) * 0.1)
        
        # Increase confidence based on domain classification
        confidence += min(0.2, len(domains) * 0.1)
        
        return min(1.0, confidence)
    
    def _determine_query_intent(self, 
                              query: str, 
                              domains: List[MedicalDomain]) -> str:
        """Determine the intent of the medical query"""
        
        intent_patterns = {
            'information_request': ['what is', 'tell me about', 'explain', 'information'],
            'symptom_inquiry': ['symptoms of', 'signs of', 'how do I know'],
            'treatment_request': ['how to treat', 'treatment for', 'cure for'],
            'medication_inquiry': ['medication for', 'drugs for', 'prescribe'],
            'diagnosis_request': ['do I have', 'am I', 'could it be'],
            'prevention_inquiry': ['how to prevent', 'avoid', 'reduce risk']
        }
        
        query_lower = query.lower()
        
        for intent, patterns in intent_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                return intent
        
        return 'general_inquiry'
    
    def _extract_clinical_keywords(self, query: str) -> List[str]:
        """Extract clinical and medical keywords"""
        
        if self.nlp:
            doc = self.nlp(query)
            keywords = []
            
            for token in doc:
                if (token.pos_ in ['NOUN', 'ADJ'] and 
                    len(token.text) > 3 and 
                    not token.is_stop):
                    keywords.append(token.lemma_.lower())
            
            return list(set(keywords))
        
        # Fallback: simple keyword extraction
        words = re.findall(r'\b[a-zA-Z]{4,}\b', query.lower())
        return list(set(words))
    
    def _extract_medical_relationships(self, 
                                     query: str, 
                                     symptoms: List[str], 
                                     conditions: List[str], 
                                     medications: List[str]) -> Dict[str, List[str]]:
        """Extract relationships between medical entities"""
        
        relationships = {
            'symptom_condition': [],
            'condition_medication': [],
            'symptom_medication': []
        }
        
        # Simple relationship detection based on proximity
        query_lower = query.lower()
        
        for symptom in symptoms:
            for condition in conditions:
                if abs(query_lower.find(symptom) - query_lower.find(condition)) < 50:
                    relationships['symptom_condition'].append(f"{symptom} -> {condition}")
        
        return relationships
    
    def _store_query_analysis(self, 
                            analysis: MedicalQueryAnalysis, 
                            user_context: Optional[Dict[str, Any]]):
        """Store query analysis for pattern recognition"""
        try:
            table = self.dynamodb.Table(self.analytics_table)
            
            item = {
                'query_id': analysis.query_id,
                'timestamp': datetime.utcnow().isoformat(),
                'domains': [d.value for d in analysis.medical_domains],
                'complexity': analysis.complexity.value,
                'entity_count': len(analysis.medical_entities),
                'symptom_count': len(analysis.symptoms),
                'condition_count': len(analysis.conditions),
                'medication_count': len(analysis.medications),
                'urgency_score': analysis.urgency_score,
                'confidence_score': analysis.confidence_score,
                'query_intent': analysis.query_intent,
                'query_length': len(analysis.original_query),
                'ttl': int((datetime.utcnow() + timedelta(days=90)).timestamp())
            }
            
            if user_context:
                item.update({
                    'user_hash': user_context.get('user_hash', ''),
                    'session_id': user_context.get('session_id', ''),
                    'user_type': user_context.get('user_type', 'general')
                })
            
            table.put_item(Item=item)
            
        except Exception as e:
            logger.error(f"Failed to store query analysis: {e}")
    
    def _load_medical_keywords(self) -> Dict[str, List[str]]:
        """Load medical keywords from knowledge base"""
        # This would be loaded from a medical ontology or knowledge base
        return {
            'symptoms': ['pain', 'fever', 'nausea', 'headache', 'fatigue'],
            'conditions': ['diabetes', 'hypertension', 'asthma', 'arthritis'],
            'medications': ['aspirin', 'insulin', 'antibiotics', 'painkillers']
        }
    
    def _load_symptom_patterns(self) -> List[str]:
        """Load symptom recognition patterns"""
        return [
            r'\b(pain|ache|hurt|sore|tender)\b',
            r'\b(fever|temperature|chills)\b',
            r'\b(nausea|vomiting|dizzy)\b'
        ]
    
    def _load_medication_patterns(self) -> List[str]:
        """Load medication recognition patterns"""
        return [
            r'\b\w+cillin\b',  # Antibiotics ending in -cillin
            r'\b\w+pril\b',    # ACE inhibitors ending in -pril
            r'\b\w+statin\b'   # Statins ending in -statin
        ]
    
    def _load_urgency_indicators(self) -> Dict[str, List[str]]:
        """Load urgency indicator keywords"""
        return {
            'emergency': ['chest pain', 'difficulty breathing', 'unconscious'],
            'urgent': ['severe pain', 'high fever', 'bleeding'],
            'routine': ['mild', 'occasional', 'general question']
        }
    
    # Pattern analysis methods (placeholder implementations)
    def _analyze_domain_patterns(self, start_date: datetime, end_date: datetime) -> Dict:
        """Analyze medical domain distribution patterns"""
        # Implementation would query DynamoDB and analyze patterns
        return {'symptoms': 45, 'treatment': 30, 'medication': 25}
    
    def _analyze_complexity_trends(self, start_date: datetime, end_date: datetime) -> Dict:
        """Analyze query complexity trends over time"""
        return {'simple': 40, 'moderate': 35, 'complex': 20, 'very_complex': 5}
    
    def _analyze_symptom_patterns(self, start_date: datetime, end_date: datetime) -> Dict:
        """Analyze common symptom patterns"""
        return {'headache': 25, 'pain': 20, 'fever': 15, 'nausea': 10}
    
    def _analyze_medication_patterns(self, start_date: datetime, end_date: datetime) -> Dict:
        """Analyze medication query patterns"""
        return {'aspirin': 15, 'insulin': 12, 'antibiotics': 10}
    
    def _analyze_urgency_patterns(self, start_date: datetime, end_date: datetime) -> Dict:
        """Analyze urgency score distribution"""
        return {'low': 60, 'medium': 30, 'high': 10}
    
    def _generate_clinical_insights(self, start_date: datetime, end_date: datetime) -> Dict:
        """Generate clinical insights from query patterns"""
        return {
            'trending_conditions': ['diabetes', 'hypertension'],
            'seasonal_patterns': ['flu symptoms increased'],
            'medication_concerns': ['antibiotic resistance questions']
        }
    
    def _analyze_query_intents(self, start_date: datetime, end_date: datetime) -> Dict:
        """Analyze query intent distribution"""
        return {
            'information_request': 40,
            'symptom_inquiry': 25,
            'treatment_request': 20,
            'diagnosis_request': 15
        }
    
    def _analyze_temporal_patterns(self, start_date: datetime, end_date: datetime) -> Dict:
        """Analyze temporal patterns in queries"""
        return {
            'peak_hours': [9, 13, 17, 21],
            'busiest_days': ['Monday', 'Wednesday', 'Friday'],
            'seasonal_trends': 'flu_season_increase'
        }
    
    def _clean_query_text(self, query: str) -> str:
        """Clean and normalize query text"""
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', query.strip())
        
        # Remove non-medical special characters but keep medical notation
        cleaned = re.sub(r'[^\w\s\-./]', '', cleaned)
        
        return cleaned