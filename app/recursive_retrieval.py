"""
Recursive Retrieval: Ask follow-up questions to refine results!

Example:
Question: "What's the capital of France?"
Initial retrieval: Gets some results

If answer not confident:
Follow-up: "What is the capital city of France?"
New retrieval: Gets better results

This iterates until confident or max tries reached.
"""

from app.embeddings import embed_texts
from app.vectordb import query_chunks
from app.llm import generate_answer
from app.answer_verification import verify_answer
from app.llm_client import get_available_client

class RecursiveRetriever:
    def __init__(self, max_iterations: int = 3, threshold: float = 0.6):
        self.max_iterations = max_iterations
        self.threshold = threshold
        self.iteration_history = []
    
    def refine_question(self, original_question: str, last_answer: str, 
                       iteration: int) -> str:
        """
        Generate a refined follow-up question based on previous attempt.
        
        Args:
            original_question: Original user question
            last_answer: Answer from previous iteration
            iteration: Which iteration we're on
        
        Returns:
            Refined question
        """
        if iteration == 1:
            return original_question
        
        prompt = f"""
The user originally asked: "{original_question}"

Our first attempt retrieved answer: "{last_answer[:300]}..."

This answer was not satisfactory. Generate a refined, more specific search query to find better information.
The query should be:
1. More specific than the original
2. Use different keywords
3. Target missing information

Return ONLY the refined query, nothing else.
"""
        
        try:
            client = get_available_client()
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=100
            )
            
            refined = response.choices[0].message.content.strip()
            return refined
        except:
            return original_question
    
    def retrieve_with_refined_query(self, question: str, top_k: int = 8) -> list[str]:
        """
        Retrieve using a question.
        
        Returns:
            List of relevant chunks
        """
        query_embedding = embed_texts([question])[0]
        results = query_chunks(query_embedding, top_k=top_k)
        
        chunks = results["documents"][0] if results["documents"] else []
        return chunks
    
    def recursive_retrieve(self, original_question: str, context_processor=None) -> dict:
        """
        Recursively refine retrieval until confident answer found or max iterations reached.
        
        Args:
            original_question: User's question
            context_processor: Optional function to process context between iterations
        
        Returns:
            {
                "final_answer": str,
                "final_chunks": [list of chunks],
                "iterations": 2,
                "confidence": 0.85,
                "history": [details of each iteration]
            }
        """
        self.iteration_history = []
        current_question = original_question
        best_chunks = []
        best_answer = ""
        best_confidence = 0
        
        for iteration in range(1, self.max_iterations + 1):
            # Retrieve with current question
            chunks = self.retrieve_with_refined_query(current_question)
            
            if not chunks:
                break
            
            # Generate answer from chunks
            context = "\n".join(chunks)
            answer = generate_answer(context, original_question)
            
            # Verify answer
            verification = verify_answer(answer, context, original_question)
            confidence = verification["confidence"]
            
            # Store iteration details
            iteration_info = {
                "iteration": iteration,
                "question_used": current_question,
                "chunks_found": len(chunks),
                "answer": answer[:200],
                "confidence": confidence,
                "is_grounded": verification["is_grounded"]
            }
            self.iteration_history.append(iteration_info)
            
            # Update best if this is better
            if confidence > best_confidence:
                best_confidence = confidence
                best_answer = answer
                best_chunks = chunks
            
            # Check if satisfied
            if verification["is_grounded"] and confidence >= self.threshold:
                break
            
            # Refine question for next iteration
            if iteration < self.max_iterations:
                current_question = self.refine_question(
                    original_question, answer, iteration + 1
                )
        
        return {
            "final_answer": best_answer,
            "final_chunks": best_chunks,
            "iterations": len(self.iteration_history),
            "confidence": best_confidence,
            "converged": best_confidence >= self.threshold,
            "history": self.iteration_history
        }
    
    def get_iteration_summary(self) -> str:
        """
        Pretty print the recursive retrieval process.
        """
        output = "Recursive Retrieval Summary:\n"
        output += "=" * 60 + "\n"
        
        for info in self.iteration_history:
            output += f"\n Iteration {info['iteration']}:\n"
            output += f"   Question: {info['question_used']}\n"
            output += f"   Chunks found: {info['chunks_found']}\n"
            output += f"   Confidence: {info['confidence']:.2f}\n"
            output += f"   Grounded: {'✓' if info['is_grounded'] else '✗'}\n"
            output += f"   Answer: {info['answer'][:100]}...\n"
        
        return output
