"""
Few-Shot Prompting: Teach LLM your style!

Instead of just "Answer the question", show examples first:

Standard:
"Answer: What is Python?"

Few-Shot:
"Examples:
Q: What is Java?
A: Java is a compiled, object-oriented programming language...

Q: What is JavaScript?
A: JavaScript is an interpreted, dynamic programming language...

Now answer:
Q: What is Python?
A: ..."

Result: LLM follows your format, style, and tone!
"""

from typing import List, Dict
from app.llm_client import get_available_client

class FewShotExamples:
    """
    Manage few-shot examples for different question types.
    """
    
    # Definition questions examples
    DEFINITION_EXAMPLES = [
        {
            "question": "What is machine learning?",
            "answer": "Machine learning is a subset of artificial intelligence that enables computers to learn from data and improve their performance without being explicitly programmed."
        },
        {
            "question": "What is a neural network?",
            "answer": "A neural network is a computing system inspired by biological neural networks found in animal brains. It consists of interconnected nodes (neurons) that work together to process information."
        }
    ]
    
    # Explanation questions examples
    EXPLANATION_EXAMPLES = [
        {
            "question": "How does photosynthesis work?",
            "answer": "Photosynthesis is a process where plants convert light energy into chemical energy. It occurs in two stages: the light-dependent reactions (in thylakoids) where light is captured, and the light-independent reactions (Calvin cycle) where CO2 is converted into glucose."
        },
        {
            "question": "How do neural networks learn?",
            "answer": "Neural networks learn through a process called backpropagation. During training, the network makes predictions, calculates the error, and then adjusts the weights of connections between neurons to minimize that error. This iterative process continues until the network achieves good accuracy."
        }
    ]
    
    # Comparison questions examples
    COMPARISON_EXAMPLES = [
        {
            "question": "What's the difference between supervised and unsupervised learning?",
            "answer": "Supervised learning uses labeled data where correct answers are provided during training, while unsupervised learning finds patterns in unlabeled data. Supervised is better for classification tasks, unsupervised is better for discovering hidden patterns."
        }
    ]
    
    # Summary examples
    SUMMARY_EXAMPLES = [
        {
            "question": "Summarize the key points about climate change",
            "answer": "Key points: 1) Global temperatures are rising due to greenhouse gas emissions, 2) Main causes are fossil fuel burning and deforestation, 3) Effects include polar ice melting and extreme weather, 4) Solutions include renewable energy and carbon reduction."
        }
    ]
    
    @staticmethod
    def classify_question_type(question: str) -> str:
        """
        Classify question into type: definition, explanation, comparison, summary, etc.
        """
        question_lower = question.lower()
        
        if question_lower.startswith("what is"):
            return "definition"
        elif question_lower.startswith(("how does", "how do", "explain")):
            return "explanation"
        elif any(word in question_lower for word in ["compare", "difference", "vs", "versus"]):
            return "comparison"
        elif any(word in question_lower for word in ["summarize", "summary", "overview", "key points"]):
            return "summary"
        else:
            return "general"
    
    @staticmethod
    def get_examples_for_question(question: str) -> List[Dict]:
        """
        Get relevant few-shot examples based on question type.
        """
        question_type = FewShotExamples.classify_question_type(question)
        
        if question_type == "definition":
            return FewShotExamples.DEFINITION_EXAMPLES
        elif question_type == "explanation":
            return FewShotExamples.EXPLANATION_EXAMPLES
        elif question_type == "comparison":
            return FewShotExamples.COMPARISON_EXAMPLES
        elif question_type == "summary":
            return FewShotExamples.SUMMARY_EXAMPLES
        else:
            # Return general examples mixing styles
            return FewShotExamples.DEFINITION_EXAMPLES[:1] + FewShotExamples.EXPLANATION_EXAMPLES[:1]


def build_few_shot_prompt(question: str, context: str, 
                         num_examples: int = 2) -> str:
    """
    Build a prompt with few-shot examples.
    
    Args:
        question: User's question
        context: Retrieved context
        num_examples: How many examples to include
    
    Returns:
        Complete prompt with examples
    """
    
    # Get relevant examples
    examples = FewShotExamples.get_examples_for_question(question)
    examples = examples[:num_examples]
    
    # Build prompt
    prompt = "You are a helpful AI assistant. Learn from these examples and answer similarly:\n\n"
    
    # Add examples
    for i, example in enumerate(examples, 1):
        prompt += f"Example {i}:\n"
        prompt += f"Question: {example['question']}\n"
        prompt += f"Answer: {example['answer']}\n\n"
    
    # Add context and question
    prompt += "Now, using the context below, answer the user's question in a similar style.\n"
    prompt += f"Context: {context}\n\n"
    prompt += f"Question: {question}\n"
    prompt += "Answer: "
    
    return prompt


def generate_answer_few_shot(context: str, question: str, 
                            num_examples: int = 2,
                            temperature: float = 0.2) -> str:
    """
    Generate answer using few-shot prompting.
    
    Args:
        context: Retrieved context
        question: User question
        num_examples: How many examples to show
        temperature: Creativity level (0.2 for factual)
    
    Returns:
        Generated answer
    """
    
    prompt = build_few_shot_prompt(question, context, num_examples)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=500
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        print(f"Error generating answer: {e}")
        return ""


class CustomFewShotExamples:
    """
    Allow users to add their own few-shot examples.
    """
    
    def __init__(self, examples_file: str = "data/custom_examples.json"):
        import json
        from pathlib import Path
        
        self.examples_file = Path(examples_file)
        self.examples_file.parent.mkdir(parents=True, exist_ok=True)
        self.examples = self._load_examples()
    
    def _load_examples(self) -> Dict:
        """Load custom examples."""
        import json
        
        if self.examples_file.exists():
            with open(self.examples_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_examples(self):
        """Save custom examples."""
        import json
        
        with open(self.examples_file, 'w') as f:
            json.dump(self.examples, f, indent=2)
    
    def add_example(self, category: str, question: str, answer: str):
        """
        Add a custom few-shot example.
        
        Args:
            category: "technical", "medical", "legal", etc.
            question: Example question
            answer: Example answer (good model answer)
        """
        if category not in self.examples:
            self.examples[category] = []
        
        self.examples[category].append({
            "question": question,
            "answer": answer
        })
        
        self._save_examples()
    
    def get_examples_for_category(self, category: str) -> List[Dict]:
        """Get examples for a specific category."""
        return self.examples.get(category, [])
    
    def build_custom_prompt(self, category: str, question: str, 
                           context: str, num_examples: int = 2) -> str:
        """
        Build prompt using custom examples from a category.
        """
        examples = self.get_examples_for_category(category)
        examples = examples[:num_examples]
        
        if not examples:
            # Fall back to standard few-shot
            return build_few_shot_prompt(question, context, num_examples)
        
        # Build prompt with custom examples
        prompt = f"You are answering {category} questions. Learn from these examples:\n\n"
        
        for i, example in enumerate(examples, 1):
            prompt += f"Example {i}:\n"
            prompt += f"Q: {example['question']}\n"
            prompt += f"A: {example['answer']}\n\n"
        
        prompt += f"Context: {context}\n\n"
        prompt += f"Question: {question}\n"
        prompt += "Answer: "
        
        return prompt
