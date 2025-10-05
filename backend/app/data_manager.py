"""
Data Manager for IELTS AI Coach
Handles question bank and evaluation history persistence
FIXED VERSION: Stores images in proper format
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import hashlib
import logging
import base64

logger = logging.getLogger(__name__)

class DataManager:
    """Manages question bank and evaluation history."""
    
    def __init__(self, base_dir: str = None):
        """Initialize data manager with base directory."""
        if base_dir is None:
            base_dir = Path(__file__).parent.parent.parent / "data"
        
        self.base_dir = Path(base_dir)
        self.question_bank_dir = self.base_dir / "question_bank"
        self.evaluation_history_dir = self.base_dir / "evaluation_history"
        
        # Ensure directories exist
        self.question_bank_dir.mkdir(parents=True, exist_ok=True)
        self.evaluation_history_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"DataManager initialized at {self.base_dir}")
    
    def _generate_question_id(self, task_type: str, prompt_text: str) -> str:
        """Generate a unique ID for a question based on content."""
        content = f"{task_type}:{prompt_text}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _get_image_extension(self, base64_data: str) -> str:
        """Detect image format from base64 data."""
        # Check the header of base64 data
        if base64_data.startswith('/9j/'):
            return '.jpg'
        elif base64_data.startswith('iVBORw0KGgo'):
            return '.png'
        elif base64_data.startswith('R0lGOD'):
            return '.gif'
        elif base64_data.startswith('JVBERi0'):
            return '.pdf'
        else:
            # Default to jpg if unknown
            return '.jpg'
    
    def save_question(self, task_type: str, prompt_text: str, 
                     image_data: Optional[str] = None) -> str:
        """
        Save a question to the question bank.
        FIX: Stores images in proper format (jpg, png, etc.)
        
        Returns:
            question_id: Unique identifier for the question
        """
        question_id = self._generate_question_id(task_type, prompt_text)
        
        question_data = {
            "question_id": question_id,
            "task_type": task_type,
            "prompt_text": prompt_text,
            "has_image": image_data is not None,
            "created_at": datetime.now().isoformat(),
            "last_used": datetime.now().isoformat()
        }
        
        # Save image in proper format
        if image_data:
            # Detect format from base64 data
            extension = self._get_image_extension(image_data)
            image_path = self.question_bank_dir / f"{question_id}_image{extension}"
            
            # Save as binary file (not text!)
            try:
                image_bytes = base64.b64decode(image_data)
                with open(image_path, 'wb') as f:
                    f.write(image_bytes)
                question_data["image_filename"] = f"{question_id}_image{extension}"
                logger.info(f"Image saved as {image_path}")
            except Exception as e:
                logger.error(f"Failed to save image: {e}")
                question_data["has_image"] = False
        
        # Save question metadata
        question_path = self.question_bank_dir / f"{question_id}.json"
        with open(question_path, 'w') as f:
            json.dump(question_data, f, indent=2)
        
        logger.info(f"Question saved with ID: {question_id}")
        return question_id
    
    def get_question(self, question_id: str) -> Optional[Dict]:
        """Retrieve a question by ID."""
        question_path = self.question_bank_dir / f"{question_id}.json"
        
        if not question_path.exists():
            logger.warning(f"Question not found: {question_id}")
            return None
        
        with open(question_path, 'r') as f:
            question_data = json.load(f)
        
        # Load image if exists
        if question_data.get("has_image"):
            image_filename = question_data.get("image_filename", f"{question_id}_image.jpg")
            image_path = self.question_bank_dir / image_filename
            
            if image_path.exists():
                # Read as binary and convert to base64
                with open(image_path, 'rb') as f:
                    image_bytes = f.read()
                    question_data["image_data"] = base64.b64encode(image_bytes).decode()
                    question_data["image_format"] = image_path.suffix  # .jpg, .png, etc.
            else:
                # Try legacy .txt format
                legacy_path = self.question_bank_dir / f"{question_id}_image.txt"
                if legacy_path.exists():
                    with open(legacy_path, 'r') as f:
                        question_data["image_data"] = f.read()
                        question_data["image_format"] = ".jpg"  # Assume jpg for legacy
        
        # Update last used timestamp
        question_data["last_used"] = datetime.now().isoformat()
        with open(question_path, 'w') as f:
            json.dump(question_data, f, indent=2)
        
        return question_data
    
    def list_questions(self, task_type: Optional[str] = None) -> List[Dict]:
        """
        List all saved questions, optionally filtered by task type.
        
        Returns:
            List of question metadata (without full image data)
        """
        questions = []
        
        for file_path in self.question_bank_dir.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    question_data = json.load(f)
                
                # Filter by task type if specified
                if task_type and question_data.get("task_type") != task_type:
                    continue
                
                # Don't include image data in list view
                questions.append({
                    "question_id": question_data["question_id"],
                    "task_type": question_data["task_type"],
                    "prompt_text": question_data["prompt_text"][:100] + "..." if len(question_data["prompt_text"]) > 100 else question_data["prompt_text"],
                    "has_image": question_data.get("has_image", False),
                    "created_at": question_data.get("created_at"),
                    "last_used": question_data.get("last_used")
                })
            except Exception as e:
                logger.error(f"Error reading question file {file_path}: {e}")
        
        # Sort by last used (most recent first)
        questions.sort(key=lambda x: x.get("last_used", ""), reverse=True)
        return questions
    
    def delete_question(self, question_id: str) -> bool:
        """Delete a question and its associated evaluations."""
        try:
            # Delete question file
            question_path = self.question_bank_dir / f"{question_id}.json"
            if question_path.exists():
                question_path.unlink()
            
            # Delete associated images (all possible formats)
            for ext in ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.txt']:
                image_path = self.question_bank_dir / f"{question_id}_image{ext}"
                if image_path.exists():
                    image_path.unlink()
            
            # Delete associated evaluations
            for eval_file in self.evaluation_history_dir.glob(f"{question_id}_*.json"):
                eval_file.unlink()
            
            logger.info(f"Question and associated data deleted: {question_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting question {question_id}: {e}")
            return False
    
    def save_evaluation(self, question_id: str, essay_text: str, 
                       evaluation_report: str, word_count: int) -> str:
        """
        Save an evaluation result.
        
        Returns:
            evaluation_id: Unique identifier for the evaluation
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        evaluation_id = f"{question_id}_{timestamp}"
        
        evaluation_data = {
            "evaluation_id": evaluation_id,
            "question_id": question_id,
            "essay_text": essay_text,
            "evaluation_report": evaluation_report,
            "word_count": word_count,
            "timestamp": datetime.now().isoformat()
        }
        
        evaluation_path = self.evaluation_history_dir / f"{evaluation_id}.json"
        with open(evaluation_path, 'w') as f:
            json.dump(evaluation_data, f, indent=2)
        
        logger.info(f"Evaluation saved with ID: {evaluation_id}")
        return evaluation_id
    
    def get_evaluation_history(self, question_id: str) -> List[Dict]:
        """
        Get all evaluations for a specific question.
        
        Returns:
            List of evaluation data sorted by timestamp (oldest first)
        """
        evaluations = []
        
        for file_path in self.evaluation_history_dir.glob(f"{question_id}_*.json"):
            try:
                with open(file_path, 'r') as f:
                    eval_data = json.load(f)
                evaluations.append(eval_data)
            except Exception as e:
                logger.error(f"Error reading evaluation file {file_path}: {e}")
        
        # Sort by timestamp (oldest first for progression tracking)
        evaluations.sort(key=lambda x: x.get("timestamp", ""))
        return evaluations
    
    def delete_evaluation(self, evaluation_id: str) -> bool:
        """Delete a specific evaluation."""
        try:
            evaluation_path = self.evaluation_history_dir / f"{evaluation_id}.json"
            if evaluation_path.exists():
                evaluation_path.unlink()
                logger.info(f"Evaluation deleted: {evaluation_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting evaluation {evaluation_id}: {e}")
            return False
    
    def delete_all_evaluations_for_question(self, question_id: str) -> int:
        """
        Delete all evaluations for a question.
        
        Returns:
            Number of evaluations deleted
        """
        count = 0
        for eval_file in self.evaluation_history_dir.glob(f"{question_id}_*.json"):
            try:
                eval_file.unlink()
                count += 1
            except Exception as e:
                logger.error(f"Error deleting evaluation {eval_file}: {e}")
        
        logger.info(f"Deleted {count} evaluations for question {question_id}")
        return count
    
    def generate_comparison_report(self, question_id: str, 
                                   current_essay: str, 
                                   current_report: str) -> str:
        """
        Generate a comparison report between current and previous attempts.
        
        Returns:
            Comparison report as markdown string
        """
        history = self.get_evaluation_history(question_id)
        
        if not history:
            return current_report
        
        # Build comparison section
        comparison = "\n\n---\n\n## 📊 Progress Comparison\n\n"
        comparison += f"**Attempt #{len(history) + 1}**\n\n"
        
        comparison += "### Previous Attempts:\n\n"
        for i, prev_eval in enumerate(history, 1):
            prev_date = datetime.fromisoformat(prev_eval["timestamp"]).strftime("%Y-%m-%d %H:%M")
            prev_word_count = prev_eval.get("word_count", "N/A")
            comparison += f"- **Attempt {i}** ({prev_date}): {prev_word_count} words\n"
        
        comparison += f"\n**Current Attempt**: {len(current_essay.split())} words\n\n"
        
        # Add improvement suggestions based on history
        comparison += "### 💡 Based on Your Learning Journey:\n\n"
        comparison += "You've practiced this question before! "
        comparison += "Review your previous feedback carefully and focus on addressing "
        comparison += "the areas that needed improvement.\n\n"
        
        # Combine with current report
        full_report = current_report + comparison
        
        return full_report


# Global instance
data_manager = DataManager()
