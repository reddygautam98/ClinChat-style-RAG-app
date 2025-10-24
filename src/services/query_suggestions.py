"""
Query Auto-Suggestions System for HealthAI RAG
Provides intelligent medical query suggestions based on patterns and context
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import asyncio
from fuzzywuzzy import fuzz, process
import redis
from src.analytics.medical_query_analyzer import MedicalQueryAnalyzer

logger = logging.getLogger(__name__)

@dataclass
class QuerySuggestion:
    """Individual query suggestion"""
    text: str
    confidence: float
    category: str
    completion_type: str  # "completion", "related", "popular"
    medical_domain: Optional[str] = None
    popularity_score: float = 0.0

class MedicalQuerySuggestionEngine:
    """Advanced query suggestion system for medical queries"""
    
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379):
        """Initialize suggestion engine"""
        self.query_analyzer = MedicalQueryAnalyzer()
        
        # Redis for caching and pattern storage
        try:
            self.redis_client = redis.Redis(
                host=redis_host, 
                port=redis_port, 
                decode_responses=True,
                socket_connect_timeout=5
            )
            self.redis_client.ping()
            logger.info("✅ Redis connected for suggestions cache")
        except Exception as e:
            logger.warning(f"Redis not available: {e}, using in-memory cache")
            self.redis_client = None
        
        # Medical knowledge base for suggestions
        self.medical_templates = self._load_medical_templates()
        self.popular_queries = self._load_popular_queries()
        self.symptom_suggestions = self._load_symptom_suggestions()
        
        # Pattern cache
        self.query_patterns = defaultdict(list)
        self.entity_relationships = defaultdict(set)
        
    def get_suggestions(self, 
                       partial_query: str,
                       max_suggestions: int = 8,
                       user_context: Optional[Dict[str, Any]] = None) -> List[QuerySuggestion]:
        """
        Get intelligent suggestions for partial medical query
        
        Args:
            partial_query: User's partial input
            max_suggestions: Maximum suggestions to return
            user_context: Optional user context for personalization
            
        Returns:
            List of ranked suggestions
        """
        if not partial_query or len(partial_query.strip()) < 2:
            return self._get_default_suggestions()
        
        suggestions = []
        query_lower = partial_query.lower().strip()
        
        try:
            # 1. Auto-completion suggestions (highest priority)
            completion_suggestions = self._get_completion_suggestions(query_lower)
            suggestions.extend(completion_suggestions)
            
            # 2. Medical entity-based suggestions
            entity_suggestions = self._get_entity_based_suggestions(query_lower)
            suggestions.extend(entity_suggestions)
            
            # 3. Pattern-based suggestions from historical queries
            pattern_suggestions = self._get_pattern_based_suggestions(query_lower, user_context)
            suggestions.extend(pattern_suggestions)
            
            # 4. Popular query suggestions
            popular_suggestions = self._get_popular_query_suggestions(query_lower)
            suggestions.extend(popular_suggestions)
            
            # 5. Contextual medical suggestions
            if user_context:
                contextual_suggestions = self._get_contextual_suggestions(query_lower, user_context)
                suggestions.extend(contextual_suggestions)
            
            # Rank and deduplicate suggestions
            ranked_suggestions = self._rank_and_deduplicate(suggestions, partial_query)
            
            # Cache successful suggestions
            if self.redis_client and ranked_suggestions:
                self._cache_suggestions(partial_query, ranked_suggestions)
            
            return ranked_suggestions[:max_suggestions]
            
        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
            return self._get_fallback_suggestions(query_lower)
    
    def _get_completion_suggestions(self, partial_query: str) -> List[QuerySuggestion]:
        """Generate auto-completion suggestions"""
        suggestions = []
        
        # Medical condition completions
        medical_completions = [
            "What are the symptoms of diabetes?",
            "What causes high blood pressure?",
            "How is heart disease treated?",
            "What medications are used for anxiety?",
            "What are the signs of stroke?",
            "How can I prevent kidney stones?",
            "What tests diagnose cancer?",
            "When should I see a cardiologist?",
            "What foods help lower cholesterol?",
            "How is depression managed?"
        ]
        
        # Find matching completions using fuzzy matching
        matches = process.extract(partial_query, medical_completions, limit=5, scorer=fuzz.partial_ratio)
        
        for match, score in matches:
            if score > 60:  # Reasonable match threshold
                suggestions.append(QuerySuggestion(
                    text=match,
                    confidence=score / 100.0,
                    category="completion",
                    completion_type="completion",
                    popularity_score=0.8
                ))
        
        return suggestions
    
    def _get_entity_based_suggestions(self, partial_query: str) -> List[QuerySuggestion]:
        """Generate suggestions based on medical entities"""
        suggestions = []
        
        # Extract potential medical entities from partial query
        words = partial_query.split()
        if not words:
            return suggestions
        
        last_word = words[-1]
        
        # Symptom-based suggestions
        symptom_templates = [
            f"What causes {last_word} pain?",
            f"How to treat {last_word}?",
            f"When to see a doctor for {last_word}?",
            f"What medications help with {last_word}?"
        ]
        
        for template in symptom_templates:
            if len(template) > len(partial_query) and template.lower().startswith(partial_query):
                suggestions.append(QuerySuggestion(
                    text=template,
                    confidence=0.7,
                    category="symptom",
                    completion_type="related",
                    medical_domain="symptoms"
                ))
        
        return suggestions
    
    def _get_pattern_based_suggestions(self, 
                                     partial_query: str,
                                     user_context: Optional[Dict[str, Any]]) -> List[QuerySuggestion]:
        """Generate suggestions based on learned patterns"""
        suggestions = []
        
        # Check Redis cache for pattern-based suggestions
        if self.redis_client:
            cache_key = f"patterns:{hash(partial_query) % 1000}"
            cached = self.redis_client.get(cache_key)
            if cached:
                try:
                    cached_suggestions = json.loads(cached)
                    return [QuerySuggestion(**s) for s in cached_suggestions[:3]]
                except Exception:
                    pass
        
        # Pattern matching logic
        query_words = set(partial_query.lower().split())
        
        # Medical question patterns
        if any(word in query_words for word in ["what", "how", "when", "why"]):
            if "symptoms" in partial_query.lower():
                suggestions.extend([
                    QuerySuggestion(
                        text="What are the symptoms of type 2 diabetes?",
                        confidence=0.6,
                        category="symptoms",
                        completion_type="related"
                    ),
                    QuerySuggestion(
                        text="What are the early symptoms of heart disease?",
                        confidence=0.6,
                        category="symptoms", 
                        completion_type="related"
                    )
                ])
        
        return suggestions
    
    def _get_popular_query_suggestions(self, partial_query: str) -> List[QuerySuggestion]:
        """Get suggestions from popular queries"""
        suggestions = []
        
        popular_queries = [
            ("What is diabetes?", 0.9, "condition"),
            ("How to lower blood pressure?", 0.85, "treatment"),
            ("Signs of heart attack?", 0.8, "emergency"),
            ("What causes anxiety?", 0.75, "mental_health"),
            ("How to prevent stroke?", 0.7, "prevention")
        ]
        
        for query, popularity, category in popular_queries:
            if (partial_query in query.lower() or 
                any(word in query.lower() for word in partial_query.split())):
                
                suggestions.append(QuerySuggestion(
                    text=query,
                    confidence=popularity,
                    category=category,
                    completion_type="popular",
                    popularity_score=popularity
                ))
        
        return suggestions
    
    def _get_contextual_suggestions(self, 
                                  partial_query: str,
                                  user_context: Dict[str, Any]) -> List[QuerySuggestion]:
        """Generate contextual suggestions based on user history"""
        suggestions = []
        
        # Get user's recent queries or preferences
        user_age_group = user_context.get("age_group", "adult")
        
        # Age-appropriate suggestions
        if user_age_group == "pediatric":
            suggestions.append(QuerySuggestion(
                text="What vaccines does my child need?",
                confidence=0.6,
                category="pediatric",
                completion_type="contextual",
                medical_domain="pediatrics"
            ))
        elif user_age_group == "geriatric":
            suggestions.append(QuerySuggestion(
                text="How to manage arthritis in older adults?",
                confidence=0.6,
                category="geriatric",
                completion_type="contextual", 
                medical_domain="geriatrics"
            ))
        
        return suggestions
    
    def _rank_and_deduplicate(self, 
                            suggestions: List[QuerySuggestion],
                            original_query: str) -> List[QuerySuggestion]:
        """Rank suggestions by relevance and remove duplicates"""
        # Deduplicate by text
        seen_texts = set()
        unique_suggestions = []
        
        for suggestion in suggestions:
            if suggestion.text.lower() not in seen_texts:
                seen_texts.add(suggestion.text.lower())
                unique_suggestions.append(suggestion)
        
        # Calculate relevance scores
        for suggestion in unique_suggestions:
            relevance_score = self._calculate_relevance_score(suggestion, original_query)
            suggestion.confidence = (suggestion.confidence + relevance_score) / 2
        
        # Sort by confidence (descending)
        return sorted(unique_suggestions, key=lambda x: x.confidence, reverse=True)
    
    def _calculate_relevance_score(self, 
                                 suggestion: QuerySuggestion,
                                 original_query: str) -> float:
        """Calculate relevance score for suggestion"""
        score = 0.0
        
        # Text similarity bonus
        similarity = fuzz.partial_ratio(original_query.lower(), suggestion.text.lower()) / 100.0
        score += similarity * 0.5
        
        # Popularity bonus
        score += suggestion.popularity_score * 0.3
        
        # Completion type bonuses
        type_bonuses = {
            "completion": 0.4,
            "related": 0.3,
            "popular": 0.2,
            "contextual": 0.35
        }
        score += type_bonuses.get(suggestion.completion_type, 0.1)
        
        return min(score, 1.0)
    
    def _get_default_suggestions(self) -> List[QuerySuggestion]:
        """Get default suggestions for empty/short queries"""
        return [
            QuerySuggestion(
                text="What are the symptoms of...",
                confidence=0.8,
                category="prompt",
                completion_type="template"
            ),
            QuerySuggestion(
                text="How to treat...", 
                confidence=0.7,
                category="prompt",
                completion_type="template"
            ),
            QuerySuggestion(
                text="What causes...",
                confidence=0.6,
                category="prompt", 
                completion_type="template"
            )
        ]
    
    def _get_fallback_suggestions(self, query: str) -> List[QuerySuggestion]:
        """Fallback suggestions when main logic fails"""
        return [
            QuerySuggestion(
                text="What is diabetes?",
                confidence=0.5,
                category="fallback",
                completion_type="popular"
            ),
            QuerySuggestion(
                text="How to lower blood pressure?",
                confidence=0.4,
                category="fallback",
                completion_type="popular"
            )
        ]
    
    def learn_from_query(self, query: str, user_clicked: bool = False):
        """Learn from user queries to improve suggestions"""
        if not query or len(query.strip()) < 3:
            return
        
        try:
            # Analyze query for patterns
            analysis = self.query_analyzer.analyze_query(query)
            
            # Store patterns in Redis
            if self.redis_client:
                # Update query frequency
                self.redis_client.zincrby("popular_queries", 1 if not user_clicked else 2, query)
                
                # Store domain patterns
                for domain in analysis.medical_domains:
                    self.redis_client.sadd(f"domain_queries:{domain.value}", query)
                
                # Store entity relationships
                for entity in analysis.medical_entities:
                    self.redis_client.sadd(f"entity_queries:{entity}", query)
            
        except Exception as e:
            logger.error(f"Failed to learn from query: {e}")
    
    def _cache_suggestions(self, query: str, suggestions: List[QuerySuggestion]):
        """Cache suggestions for performance"""
        try:
            cache_key = f"suggestions:{hash(query) % 10000}"
            cache_data = [
                {
                    "text": s.text,
                    "confidence": s.confidence, 
                    "category": s.category,
                    "completion_type": s.completion_type,
                    "medical_domain": s.medical_domain,
                    "popularity_score": s.popularity_score
                }
                for s in suggestions
            ]
            
            self.redis_client.setex(
                cache_key, 
                3600,  # 1 hour cache
                json.dumps(cache_data)
            )
            
        except Exception as e:
            logger.error(f"Failed to cache suggestions: {e}")
    
    def _load_medical_templates(self) -> List[str]:
        """Load medical query templates"""
        return [
            "What are the symptoms of {condition}?",
            "How is {condition} treated?",
            "What causes {condition}?",
            "When should I see a doctor for {symptom}?",
            "What medications are used for {condition}?",
            "How can I prevent {condition}?",
            "What tests diagnose {condition}?",
            "What are the side effects of {medication}?",
            "Is {symptom} serious?",
            "What foods help with {condition}?"
        ]
    
    def _load_popular_queries(self) -> List[Tuple[str, float]]:
        """Load popular medical queries with scores"""
        return [
            ("What is diabetes?", 0.95),
            ("How to lower blood pressure?", 0.90),
            ("Signs of heart attack?", 0.88),
            ("What causes anxiety?", 0.85),
            ("How to prevent stroke?", 0.82),
            ("Symptoms of depression?", 0.80),
            ("What is high cholesterol?", 0.78),
            ("How to manage pain?", 0.75),
            ("When to see a doctor?", 0.72),
            ("What causes headaches?", 0.70)
        ]
    
    def _load_symptom_suggestions(self) -> Dict[str, List[str]]:
        """Load symptom-based suggestion mappings"""
        return {
            "pain": [
                "What causes chest pain?",
                "How to treat back pain?", 
                "When is abdominal pain serious?"
            ],
            "fever": [
                "What causes fever in adults?",
                "When to see a doctor for fever?",
                "How to reduce fever naturally?"
            ],
            "headache": [
                "What causes migraines?",
                "How to treat tension headaches?",
                "When are headaches serious?"
            ]
        }

# Async wrapper for API integration
class AsyncQuerySuggestionEngine:
    """Async wrapper for query suggestions in FastAPI"""
    
    def __init__(self):
        self.engine = MedicalQuerySuggestionEngine()
    
    async def get_suggestions_async(self, 
                                  partial_query: str,
                                  max_suggestions: int = 8,
                                  user_context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Async version of get_suggestions"""
        # Run synchronous operation in thread pool
        loop = asyncio.get_event_loop()
        suggestions = await loop.run_in_executor(
            None,
            self.engine.get_suggestions,
            partial_query,
            max_suggestions, 
            user_context
        )
        
        # Convert to API-friendly format
        return [
            {
                "text": s.text,
                "confidence": round(s.confidence, 3),
                "category": s.category,
                "type": s.completion_type,
                "domain": s.medical_domain,
                "popularity": round(s.popularity_score, 3)
            }
            for s in suggestions
        ]
    
    async def learn_from_query_async(self, query: str, user_clicked: bool = False):
        """Async version of learn_from_query"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.engine.learn_from_query, query, user_clicked)