"""
Multi-Hop Retrieval: Chain retrievals for complex questions!

Example:
Question: "What did the inventor of calculus eat for breakfast?"

Hop 1: Retrieve "Isaac Newton invented calculus"
Hop 2: Retrieve "Isaac Newton's breakfast habits"
Result: Combine both to answer the full question!

Why? Some questions need multiple lookups to answer fully.
"""

from app.embeddings import embed_texts
from app.vectordb import query_chunks
from app.hybrid_search import HybridSearcher

class MultiHopRetriever:
    def __init__(self, max_hops: int = 3):
        self.max_hops = max_hops
        self.retrieval_chain = []
    
    def extract_entities(self, text: str) -> list[str]:
        """
        Extract important entities/nouns from text.
        Simple method: Look for capitalized words.
        
        Example:
            "Isaac Newton invented calculus"
            -> ["Isaac Newton", "calculus"]
        """
        import re
        
        # Find capitalized phrases
        entities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        return list(set(entities))  # Remove duplicates
    
    def first_hop_retrieval(self, question: str, top_k: int = 5) -> tuple[list[str], list[str]]:
        """
        First retrieval based on original question.
        
        Returns:
            (retrieved_chunks, extracted_entities)
        """
        query_embedding = embed_texts([question])[0]
        results = query_chunks(query_embedding, top_k=top_k)
        
        chunks = results["documents"][0] if results["documents"] else []
        
        # Extract entities from retrieved chunks for next hops
        all_entities = []
        for chunk in chunks:
            entities = self.extract_entities(chunk)
            all_entities.extend(entities)
        
        self.retrieval_chain.append({
            "hop": 1,
            "query": question,
            "chunks": chunks,
            "entities": list(set(all_entities))
        })
        
        return chunks, all_entities
    
    def subsequent_hop_retrieval(self, entities: list[str], hop_num: int, top_k: int = 3) -> list[str]:
        """
        Retrieve using entities from previous hop.
        
        This searches for documents related to the entities found earlier.
        """
        if not entities:
            return []
        
        # Create query from entities
        entity_query = " ".join(entities[:3])  # Use top 3 entities
        
        query_embedding = embed_texts([entity_query])[0]
        results = query_chunks(query_embedding, top_k=top_k)
        
        chunks = results["documents"][0] if results["documents"] else []
        
        # Extract new entities for next hop
        new_entities = []
        for chunk in chunks:
            entities = self.extract_entities(chunk)
            new_entities.extend(entities)
        
        self.retrieval_chain.append({
            "hop": hop_num,
            "query": entity_query,
            "chunks": chunks,
            "entities": list(set(new_entities))
        })
        
        return chunks, new_entities
    
    def multi_hop_retrieve(self, question: str, num_hops: int = 2, top_k_per_hop: int = 5) -> dict:
        """
        Perform multi-hop retrieval.
        
        Args:
            question: Original user question
            num_hops: How many hops to perform (2-3 recommended)
            top_k_per_hop: Results per hop
        
        Returns:
            {
                "all_chunks": [all retrieved chunks],
                "chain": [details of each hop],
                "summary": "Hop 1 found X, Hop 2 found Y, ..."
            }
        """
        self.retrieval_chain = []
        all_chunks = set()
        
        # First hop
        chunks, entities = self.first_hop_retrieval(question, top_k_per_hop)
        all_chunks.update(chunks)
        
        # Subsequent hops
        current_entities = entities
        for hop in range(2, min(num_hops + 1, self.max_hops + 1)):
            chunks, current_entities = self.subsequent_hop_retrieval(
                current_entities, hop, top_k_per_hop
            )
            all_chunks.update(chunks)
            
            if not current_entities:  # No new entities found
                break
        
        # Build summary
        summary_parts = []
        for hop_info in self.retrieval_chain:
            summary_parts.append(
                f"Hop {hop_info['hop']}: Found {len(hop_info['chunks'])} chunks, "
                f"extracted {len(hop_info['entities'])} entities"
            )
        
        return {
            "all_chunks": list(all_chunks),
            "total_chunks": len(all_chunks),
            "hops_performed": len(self.retrieval_chain),
            "chain": self.retrieval_chain,
            "summary": " | ".join(summary_parts)
        }
    
    def get_chain_visualization(self) -> str:
        """
        Pretty print the retrieval chain.
        """
        output = "Multi-Hop Retrieval Chain:\n"
        output += "=" * 50 + "\n"
        
        for hop_info in self.retrieval_chain:
            output += f"\n🔍 Hop {hop_info['hop']}:\n"
            output += f"   Query: {hop_info['query']}\n"
            output += f"   Chunks found: {len(hop_info['chunks'])}\n"
            output += f"   Entities extracted: {', '.join(hop_info['entities'][:5])}"
            if len(hop_info['entities']) > 5:
                output += f" ... +{len(hop_info['entities'])-5} more"
            output += "\n"
        
        return output
