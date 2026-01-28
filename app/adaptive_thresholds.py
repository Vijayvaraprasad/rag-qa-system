"""
Adaptive Thresholds: Smart cutoff values!

Problem: Same threshold (0.75) for all questions?
- Simple "What is X?" needs high threshold (strict)
- Complex "Explain how X relates to Y..." needs low threshold (relaxed)

Solution: Adapt threshold based on question complexity!
"""

from app.rate_limit import rate_limit
from app.llm_client import get_available_client

class AdaptiveThreshold:
    """
    Calculate appropriate similarity threshold based on question.
    """
    
    # Base thresholds
    BASE_SIMPLE = 0.80      # Simple questions need exact matches
    BASE_MODERATE = 0.70    # Moderate questions
    BASE_COMPLEX = 0.55     # Complex questions need more lenient matching
    
    @staticmethod
    def classify_question_complexity(question: str) -> tuple[str, float]:
        """
        Classify question as simple, moderate, or complex.
        Returns (complexity_level, confidence)
        
        Simple: What is X? How do you Y?
        Moderate: Compare X and Y. Why does X happen?
        Complex: Explain how X causes Y. What are implications of X?
        """
        
        # Count complexity indicators
        complexity_score = 0
        
        # Simple indicators
        simple_words = ["what", "who", "when", "where", "how do", "how many", "how much", "what is"]
        if any(word in question.lower() for word in simple_words):
            complexity_score -= 1
        
        # Moderate indicators
        moderate_words = ["compare", "contrast", "difference", "similarity", "why", "how does"]
        if any(word in question.lower() for word in moderate_words):
            complexity_score += 1
        
        # Complex indicators
        complex_words = ["explain", "relate", "implication", "consequence", "cause effect", 
                        "mechanism", "complex", "analyze", "relationship", "impact"]
        if any(word in question.lower() for word in complex_words):
            complexity_score += 2
        
        # Question length (longer = often more complex)
        word_count = len(question.split())
        if word_count > 20:
            complexity_score += 1
        if word_count > 30:
            complexity_score += 1
        
        # Determine level
        if complexity_score <= -0.5:
            return "simple", 0.85
        elif complexity_score <= 1.5:
            return "moderate", 0.70
        else:
            return "complex", 0.70
    
    @staticmethod
    def get_threshold_for_question(question: str) -> dict:
        """
        Get appropriate threshold for a question.
        
        Returns:
            {
                "complexity": "simple|moderate|complex",
                "threshold": 0.75,
                "reasoning": str,
                "retrieval_count": int (suggested number of results)
            }
        """
        complexity, confidence = AdaptiveThreshold.classify_question_complexity(question)
        
        if complexity == "simple":
            threshold = AdaptiveThreshold.BASE_SIMPLE
            retrieval_count = 5  # Fewer results needed
            reasoning = "Simple question needs exact matches, high threshold"
        
        elif complexity == "moderate":
            threshold = AdaptiveThreshold.BASE_MODERATE
            retrieval_count = 8  # Medium number of results
            reasoning = "Moderate complexity, balanced threshold"
        
        else:  # complex
            threshold = AdaptiveThreshold.BASE_COMPLEX
            retrieval_count = 12  # More results might be needed
            reasoning = "Complex question, relaxed threshold to capture context"
        
        return {
            "complexity": complexity,
            "threshold": threshold,
            "threshold_confidence": confidence,
            "retrieval_count": retrieval_count,
            "reasoning": reasoning
        }
    
    @staticmethod
    def adjust_threshold_by_context(base_threshold: float, context_size: int) -> float:
        """
        Adjust threshold based on context availability.
        
        If we have lots of context, we can afford to lower threshold
        If we have little context, we need higher threshold
        """
        
        if context_size < 3:
            # Very few results, lower threshold to get more
            return max(0.5, base_threshold - 0.15)
        
        elif context_size < 5:
            # Still few results
            return max(0.55, base_threshold - 0.10)
        
        elif context_size > 20:
            # Lots of results, can be stricter
            return min(0.95, base_threshold + 0.05)
        
        return base_threshold
    
    @staticmethod
    def adjust_threshold_by_confidence(base_threshold: float, retrieval_confidence: float) -> float:
        """
        Adjust based on how confident we are about retrieved results.
        
        Args:
            base_threshold: Original threshold
            retrieval_confidence: 0-1, how good are our results?
        
        Returns:
            Adjusted threshold
        """
        
        if retrieval_confidence < 0.5:
            # Poor results, be stricter to avoid garbage
            return min(0.95, base_threshold + 0.10)
        
        elif retrieval_confidence < 0.7:
            # Moderate confidence
            return base_threshold
        
        else:
            # High confidence, can relax
            return max(0.5, base_threshold - 0.05)
        
        return base_threshold


@rate_limit(max_calls=15, time_window=60)
def llm_suggest_threshold(question: str, candidate_chunks: list[str]) -> float:
    """
    Use LLM to intelligently suggest threshold based on actual content.
    
    This is more sophisticated but costs more (LLM call).
    Use occasionally to calibrate, not for every query.
    """
    
    prompt = f"""
Question: {question}

I have {len(candidate_chunks)} candidate documents. Should I:
1. Be STRICT (threshold 0.85): Only keep best matches
2. Be MODERATE (threshold 0.70): Keep good and decent matches
3. Be RELAXED (threshold 0.55): Keep all potentially relevant matches

Return ONLY one number: 0.85, 0.70, or 0.55
Base your answer on how specific/complex the question is.
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=10
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Extract number
        if "0.85" in response_text:
            return 0.85
        elif "0.55" in response_text:
            return 0.55
        else:
            return 0.70
    
    except:
        return 0.70  # Default to moderate


class DynamicThresholdManager:
    """
    Manage thresholds across multiple queries and learn from feedback.
    """
    
    def __init__(self):
        self.threshold_history = []
        self.feedback_data = {}
    
    def record_result(self, question: str, threshold_used: float, 
                     user_satisfied: bool, answer_quality: int):
        """
        Record how well a threshold worked for a question.
        """
        self.threshold_history.append({
            "question": question,
            "threshold": threshold_used,
            "worked_well": user_satisfied,
            "quality_score": answer_quality  # 1-5
        })
    
    def get_learned_threshold(self, question: str) -> float:
        """
        Suggest threshold based on what worked well for similar questions.
        """
        # Find similar questions in history
        good_results = [
            h["threshold"] for h in self.threshold_history
            if h["worked_well"] and h["quality_score"] >= 4
        ]
        
        if good_results:
            return sum(good_results) / len(good_results)
        
        # Fallback to adaptive
        threshold_info = AdaptiveThreshold.get_threshold_for_question(question)
        return threshold_info["threshold"]
