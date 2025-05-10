from langchain_google_vertexai import ChatVertexAI
from typing import Dict, List
import os

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./my-gemini-key.json"

class ResponseEvaluator:
    def __init__(self, model_name: str = "gemini-1.5-pro"):
        self.llm = ChatVertexAI(model_name=model_name, temperature=0.0)
        
    def evaluate(self, query: str, response: Dict, sources: List[Dict]) -> Dict:
        """
        Evaluate the quality of RAG response
        
        Args:
            query: User question
            response: RAG response containing answer and sources
            sources: Retrieved source documents
            
        Returns:
            Evaluation results with scores and detailed feedback
        """
        evaluation_prompt = f"""
        Please evaluate the quality of the following RAG system response. Rate each dimension (1-5) and provide detailed feedback:

        1. Relevance: How well does the answer address the question?
        2. Accuracy: How accurate is the information based on the source documents?
        3. Completeness: How completely does the answer solve the problem?
        4. Fluency: How natural and easy to understand is the response?
        5. Usefulness: How helpful is the answer to the user?

        User Question: {query}

        RAG Response: {response['answer']}

        Source Documents:
        {self._format_sources(sources)}

        Please provide your evaluation in the following format:
        1. Relevance: [score]/5
        Feedback: [detailed feedback]

        2. Accuracy: [score]/5
        Feedback: [detailed feedback]

        3. Completeness: [score]/5
        Feedback: [detailed feedback]

        4. Fluency: [score]/5
        Feedback: [detailed feedback]

        5. Usefulness: [score]/5
        Feedback: [detailed feedback]

        Overall Assessment: [summary feedback]
        """
        
        evaluation = self.llm.invoke(evaluation_prompt)
        return self._parse_evaluation(evaluation.content)
    
    def _format_sources(self, sources: List[Dict]) -> str:
        """Format source documents"""
        formatted = []
        for i, source in enumerate(sources, 1):
            formatted.append(f"Document {i}:")
            formatted.append(f"Title: {source.get('title', 'N/A')}")
            formatted.append(f"Content: {source.get('content', 'N/A')[:200]}...")
            formatted.append("---")
        return "\n".join(formatted)
    
    def _parse_evaluation(self, evaluation_text: str) -> Dict:
        """Parse evaluation results"""
        return {
            "raw_evaluation": evaluation_text,
            "parsed_scores": self._extract_scores(evaluation_text)
        }
    
    def _extract_scores(self, text: str) -> Dict:
        """Extract scores from evaluation text"""
        scores = {}
        for line in text.split('\n'):
            if ':' in line and '/5' in line:
                metric, score = line.split(':')
                metric = metric.strip()
                score = score.strip().split('/')[0].strip()
                try:
                    scores[metric] = float(score)
                except ValueError:
                    continue
        return scores

def main():
    # Example usage
    evaluator = ResponseEvaluator()
    
    # Test evaluation
    query = "How to make steamed dumplings?"
    response = {
        "answer": "Steps to make steamed dumplings: 1. Prepare filling 2. Make dough 3. Wrap dumplings 4. Steam",
        "sources": [
            {
                "title": "Steamed Dumpling Guide",
                "content": "Detailed guide on making steamed dumplings, including filling preparation, dough making techniques, wrapping methods, and steaming time."
            }
        ]
    }
    
    evaluation = evaluator.evaluate(query, response, response["sources"])
    print("Evaluation Results:")
    print(evaluation["raw_evaluation"])
    print("\nScore Summary:")
    print(evaluation["parsed_scores"])

if __name__ == "__main__":
    main() 