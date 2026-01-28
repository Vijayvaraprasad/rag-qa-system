"""
Knowledge Graph: Connect ideas together!

Example:
Entities: "Isaac Newton", "Calculus", "Physics", "Apple"
Relations:
  Isaac Newton --invented--> Calculus
  Isaac Newton --discovered--> Laws of Motion
  Laws of Motion --part-of--> Physics
  Apple --falling--> Laws of Motion

Why? When you search for Newton, you get all related concepts!
"""

import json
from pathlib import Path
from typing import Dict, List
from app.rate_limit import rate_limit
from app.llm_client import get_available_client

class KnowledgeGraph:
    """
    Build and query knowledge graphs from documents.
    """
    
    def __init__(self, graph_file: str = "data/knowledge_graph.json"):
        self.graph_file = Path(graph_file)
        self.graph_file.parent.mkdir(parents=True, exist_ok=True)
        self.entities = {}  # {entity: [related entities]}
        self.relations = []  # [(entity1, relation, entity2)]
        self._load_graph()
    
    def _load_graph(self):
        """Load existing knowledge graph."""
        if self.graph_file.exists():
            with open(self.graph_file, 'r') as f:
                data = json.load(f)
                self.entities = data.get("entities", {})
                self.relations = data.get("relations", [])
    
    def _save_graph(self):
        """Save knowledge graph to file."""
        with open(self.graph_file, 'w') as f:
            json.dump({
                "entities": self.entities,
                "relations": self.relations
            }, f, indent=2)
    
    @rate_limit(max_calls=15, time_window=60)
    def extract_entities_and_relations(self, text: str) -> Dict:
        """
        Extract entities and their relationships from text using LLM.
        
        Example text: "Isaac Newton invented calculus in the 1600s"
        Returns:
            {
                "entities": ["Isaac Newton", "calculus"],
                "relations": [
                    {"entity1": "Isaac Newton", "relation": "invented", "entity2": "calculus"}
                ]
            }
        """
        
        prompt = f"""
Extract all named entities and their relationships from this text.

Text: {text}

For ENTITIES: List important names, concepts, places (e.g., "Isaac Newton", "Calculus")
For RELATIONS: List how entities are connected (e.g., "invented", "discovered", "caused")

Format your response as JSON:
{{
    "entities": ["entity1", "entity2", ...],
    "relations": [
        {{"entity1": "...", "relation": "...", "entity2": "..."}}
    ]
}}

Return ONLY the JSON, nothing else.
"""
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=300
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Parse JSON
            try:
                data = json.loads(response_text)
                return data
            except json.JSONDecodeError:
                # Try to extract JSON from response
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                return {"entities": [], "relations": []}
        
        except Exception as e:
            print(f"Error extracting entities: {e}")
            return {"entities": [], "relations": []}
    
    def add_document(self, text: str, source: str = "unknown"):
        """
        Add document to knowledge graph by extracting and storing entities/relations.
        """
        extracted = self.extract_entities_and_relations(text)
        
        # Add entities
        for entity in extracted.get("entities", []):
            if entity not in self.entities:
                self.entities[entity] = {
                    "sources": [source],
                    "occurrences": 1
                }
            else:
                if source not in self.entities[entity]["sources"]:
                    self.entities[entity]["sources"].append(source)
                self.entities[entity]["occurrences"] += 1
        
        # Add relations
        for relation in extracted.get("relations", []):
            relation["source"] = source
            self.relations.append(relation)
        
        self._save_graph()
        
        return {
            "entities_added": len(extracted.get("entities", [])),
            "relations_added": len(extracted.get("relations", []))
        }
    
    def find_related_entities(self, entity: str, max_distance: int = 2) -> Dict:
        """
        Find all entities related to a given entity.
        
        Args:
            entity: Starting entity
            max_distance: How many hops away to search (1=direct, 2=2 hops, etc.)
        
        Returns:
            {
                "entity": "Isaac Newton",
                "direct_relations": [...],
                "related_entities": ["Calculus", "Physics", ...]
            }
        """
        
        if entity not in self.entities:
            return {"entity": entity, "found": False}
        
        # Find direct relations
        direct_relations = [
            r for r in self.relations
            if r.get("entity1") == entity or r.get("entity2") == entity
        ]
        
        # Find related entities
        related = set()
        for relation in direct_relations:
            if relation.get("entity1") == entity:
                related.add(relation.get("entity2"))
            else:
                related.add(relation.get("entity1"))
        
        # Find second-level relations if max_distance > 1
        if max_distance > 1:
            for related_entity in list(related):
                for relation in self.relations:
                    if relation.get("entity1") == related_entity:
                        related.add(relation.get("entity2"))
                    elif relation.get("entity2") == related_entity:
                        related.add(relation.get("entity1"))
        
        return {
            "entity": entity,
            "found": True,
            "direct_relations": direct_relations,
            "related_entities": list(related),
            "sources": self.entities.get(entity, {}).get("sources", [])
        }
    
    def find_path_between_entities(self, entity1: str, entity2: str) -> List:
        """
        Find shortest path between two entities in the knowledge graph.
        
        Example:
            entity1: "Isaac Newton"
            entity2: "Gravity"
            Returns: ["Isaac Newton", "--discovered-->", "Laws of Motion", 
                     "--explains-->", "Gravity"]
        """
        # Simple BFS path finding
        from collections import deque
        
        visited = set()
        queue = deque([(entity1, [entity1])])
        
        while queue:
            current, path = queue.popleft()
            
            if current == entity2:
                return path
            
            if current in visited:
                continue
            visited.add(current)
            
            # Find neighbors
            for relation in self.relations:
                if relation.get("entity1") == current:
                    neighbor = relation.get("entity2")
                    if neighbor not in visited:
                        queue.append((neighbor, path + [relation.get("relation"), neighbor]))
                
                elif relation.get("entity2") == current:
                    neighbor = relation.get("entity1")
                    if neighbor not in visited:
                        queue.append((neighbor, path + [relation.get("relation"), neighbor]))
        
        return []  # No path found
    
    def query_by_entity(self, entity: str) -> Dict:
        """
        Get all information about an entity from the knowledge graph.
        """
        return self.find_related_entities(entity)
    
    def get_graph_summary(self) -> Dict:
        """Get statistics about the knowledge graph."""
        return {
            "total_entities": len(self.entities),
            "total_relations": len(self.relations),
            "top_entities": sorted(
                self.entities.items(),
                key=lambda x: x[1].get("occurrences", 0),
                reverse=True
            )[:10]
        }
