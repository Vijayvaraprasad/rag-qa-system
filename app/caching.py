"""
Caching & Feedback: Remember what works!

Caching:
- Same question asked twice? Return cached answer instantly
- Saves API calls, faster response

Feedback:
- Did user like the answer? Track it
- Learn which questions get good vs bad answers
- Improve over time
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

class AnswerCache:
    """
    Simple caching system for Q&A pairs.
    """
    
    def __init__(self, cache_file: str = "data/answer_cache.json"):
        self.cache_file = Path(cache_file)
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """Load existing cache from file."""
        if self.cache_file.exists():
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_cache(self):
        """Save cache to file."""
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def _hash_question(self, question: str) -> str:
        """Create unique hash for a question."""
        # Normalize question (lowercase, remove extra spaces)
        normalized = " ".join(question.lower().split())
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def get(self, question: str) -> Optional[Dict]:
        """
        Get cached answer if exists.
        
        Returns:
            {"answer": str, "cached_at": timestamp, "hit_count": int}
            or None if not cached
        """
        question_hash = self._hash_question(question)
        
        if question_hash in self.cache:
            # Update hit count
            self.cache[question_hash]["hit_count"] += 1
            self.cache[question_hash]["last_accessed"] = datetime.now().isoformat()
            self._save_cache()
            return self.cache[question_hash]
        
        return None
    
    def set(self, question: str, answer: str, metadata: Dict = None):
        """
        Cache an answer.
        
        Args:
            question: User's question
            answer: Generated answer
            metadata: Optional extra info {"chunks_count": 3, "confidence": 0.95}
        """
        question_hash = self._hash_question(question)
        
        self.cache[question_hash] = {
            "question": question,
            "answer": answer,
            "cached_at": datetime.now().isoformat(),
            "hit_count": 0,
            "metadata": metadata or {},
            "feedback": None
        }
        
        self._save_cache()
    
    def get_cache_stats(self) -> Dict:
        """
        Get statistics about cache usage.
        """
        total_cached = len(self.cache)
        total_hits = sum(item.get("hit_count", 0) for item in self.cache.values())
        
        return {
            "total_cached_questions": total_cached,
            "total_cache_hits": total_hits,
            "avg_hits_per_question": total_hits / total_cached if total_cached > 0 else 0,
            "cache_file": str(self.cache_file)
        }
    
    def clear_cache(self):
        """Clear all cached answers."""
        self.cache = {}
        self._save_cache()


class FeedbackTracker:
    """
    Track user feedback on answers to improve over time.
    """
    
    def __init__(self, feedback_file: str = "data/answer_feedback.json"):
        self.feedback_file = Path(feedback_file)
        self.feedback_file.parent.mkdir(parents=True, exist_ok=True)
        self.feedback_data = self._load_feedback()
    
    def _load_feedback(self) -> Dict:
        """Load feedback history."""
        if self.feedback_file.exists():
            with open(self.feedback_file, 'r') as f:
                return json.load(f)
        return {"feedbacks": [], "stats": {}}
    
    def _save_feedback(self):
        """Save feedback to file."""
        with open(self.feedback_file, 'w') as f:
            json.dump(self.feedback_data, f, indent=2)
    
    def add_feedback(self, question: str, answer: str, rating: int, 
                     comment: str = None):
        """
        Record user feedback.
        
        Args:
            question: User's question
            answer: System's answer
            rating: 1-5 star rating (1=bad, 5=excellent)
            comment: Optional user comment
        """
        feedback_entry = {
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "answer": answer[:200],  # Store first 200 chars
            "rating": rating,
            "comment": comment
        }
        
        self.feedback_data["feedbacks"].append(feedback_entry)
        self._save_feedback()
    
    def get_feedback_summary(self) -> Dict:
        """
        Get aggregate feedback statistics.
        """
        feedbacks = self.feedback_data.get("feedbacks", [])
        
        if not feedbacks:
            return {
                "total_feedback": 0,
                "avg_rating": 0,
                "rating_distribution": {}
            }
        
        ratings = [f.get("rating", 0) for f in feedbacks]
        
        rating_dist = {}
        for rating in ratings:
            rating_dist[rating] = rating_dist.get(rating, 0) + 1
        
        return {
            "total_feedback": len(feedbacks),
            "avg_rating": sum(ratings) / len(ratings),
            "rating_distribution": rating_dist,
            "excellent": rating_dist.get(5, 0),
            "good": rating_dist.get(4, 0),
            "okay": rating_dist.get(3, 0),
            "poor": rating_dist.get(2, 0),
            "terrible": rating_dist.get(1, 0)
        }
    
    def get_low_rated_answers(self, threshold: int = 2) -> list:
        """
        Get answers rated below threshold (to improve).
        """
        feedbacks = self.feedback_data.get("feedbacks", [])
        low_rated = [f for f in feedbacks if f.get("rating", 0) <= threshold]
        return low_rated
    
    def get_high_rated_answers(self, threshold: int = 4) -> list:
        """
        Get answers rated above threshold (what works well).
        """
        feedbacks = self.feedback_data.get("feedbacks", [])
        high_rated = [f for f in feedbacks if f.get("rating", 0) >= threshold]
        return high_rated


class SmartCache:
    """
    Combine caching with feedback for smart decision making.
    """
    
    def __init__(self):
        self.cache = AnswerCache()
        self.feedback = FeedbackTracker()
    
    def should_use_cached_answer(self, question: str) -> bool:
        """
        Check if we should use cached answer.
        
        Don't use cache if it was rated poorly in feedback.
        """
        cached = self.cache.get(question)
        if not cached:
            return False
        
        # Check if this cached answer had negative feedback
        feedbacks = self.feedback.feedback_data.get("feedbacks", [])
        answer_key = cached["answer"][:50]  # Use start of answer as key
        
        for feedback in feedbacks:
            if feedback.get("answer", "")[:50] == answer_key:
                if feedback.get("rating", 0) <= 2:
                    return False  # Don't use poorly-rated cached answer
        
        return True
    
    def get_answer_with_cache(self, question: str):
        """
        Get answer from cache if available and good quality.
        """
        if self.should_use_cached_answer(question):
            return self.cache.get(question)
        return None
    
    def save_answer_with_feedback_prep(self, question: str, answer: str):
        """
        Cache answer and prepare for feedback collection.
        """
        self.cache.set(question, answer)
        return {
            "answer": answer,
            "feedback_ready": True,
            "from_cache": False
        }
