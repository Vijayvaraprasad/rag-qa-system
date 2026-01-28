"""
Demo LLM - Works without OpenAI credits
Uses retrieved documents to generate demo answers
"""

def generate_demo_answer(question: str, context: str) -> str:
    """
    Generate a demo answer based on retrieved context
    This shows what the system WOULD answer without needing OpenAI
    """
    
    # Extract key information from context
    lines = context.split('\n')
    summary = '\n'.join([l.strip() for l in lines if l.strip()])[:500]
    
    demo_answers = {
        "spring framework": f"""Based on your Spring Framework documentation:

{summary}

Key Points:
• Spring is a Java enterprise application framework
• It provides everything needed for Java enterprise development
• Includes support for Groovy and other JVM languages
• Used for building scalable applications

Full Context from Your Documents:
{context[:800]}...""",
        
        "architecture": f"""From your Spring Framework documentation:

{summary}

The Spring Framework provides a comprehensive architecture for:
• Enterprise application development
• Dependency injection and IoC containers
• Integration with multiple technologies
• Modular and flexible design

Reference from your documents:
{context[:600]}...""",
        
        "default": f"""Based on the retrieved documents from your uploaded content:

{summary}

This is a demo response showing your document retrieval is working!
The system found relevant information and is displaying it here.

Full source:
{context}"""
    }
    
    # Find best match
    question_lower = question.lower()
    for key, answer in demo_answers.items():
        if key in question_lower:
            return answer
    
    return demo_answers["default"]


class DemoLLM:
    """Demo LLM that works without API keys"""
    
    def answer_question(self, question: str, context: str) -> dict:
        """Generate answer from retrieved context"""
        answer = generate_demo_answer(question, context)
        
        return {
            "answer": answer,
            "model": "demo-mode",
            "mode": "DEMO - No OpenAI credits required",
            "source": "Retrieved from your uploaded documents"
        }
