import os
import logging
import time
import base64
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv

from .graph_builder import create_graph
from .image_processor import extract_image_description
from .data_manager import data_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Environment validation
def validate_environment():
    """Validate required environment variables."""
    required_vars = ["GOOGLE_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    # Optional LangSmith validation
    if os.getenv("LANGCHAIN_TRACING_V2") == "true" and not os.getenv("LANGCHAIN_API_KEY"):
        logger.warning("LangSmith tracing enabled but LANGCHAIN_API_KEY not found")

# Global variables
graph_instance = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global graph_instance
    
    # Startup
    logger.info("Starting IELTS AI Coach API...")
    validate_environment()
    
    try:
        graph_instance = create_graph()
        logger.info("LangGraph instance created successfully")
    except Exception as e:
        logger.error(f"Failed to create LangGraph instance: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down IELTS AI Coach API...")

# FastAPI app with lifespan
app = FastAPI(
    title="IELTS AI Coach API",
    description="API for evaluating IELTS writing tasks using a LangGraph agent with image support.",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],  # Streamlit default ports
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.herokuapp.com"]  # Add your production domains
)

# Request/Response Models
class EvaluationRequest(BaseModel):
    task_type: str = Field(..., description="IELTS task type (e.g., 'Academic Task 1')")
    prompt_text: str = Field(default="", description="The question/prompt text")
    essay_text: str = Field(..., min_length=50, max_length=10000, description="The student's essay")
    image_data: Optional[str] = Field(default=None, description="Base64 encoded image data for Task 1")
    question_id: Optional[str] = Field(default=None, description="Question ID for tracking previous attempts")
    
    @validator('task_type')
    def validate_task_type(cls, v):
        valid_types = [
            "Academic Task 1", "Academic Task 2", 
            "General Training Task 1", "General Training Task 2"
        ]
        if v not in valid_types:
            raise ValueError(f"Invalid task_type. Must be one of: {', '.join(valid_types)}")
        return v
    
    @validator('essay_text')
    def validate_essay_text(cls, v):
        # Remove excessive whitespace
        v = ' '.join(v.split())
        
        # Basic content validation
        if len(v.split()) < 50:
            raise ValueError("Essay must contain at least 50 words")
        
        return v
    
    @validator('image_data')
    def validate_image_data(cls, v, values):
        """Validate image data for Task 1."""
        task_type = values.get('task_type', '')
        prompt_text = values.get('prompt_text', '')
        
        # For Task 1, either image or prompt text should be provided
        if 'Task 1' in task_type:
            if not v and not prompt_text.strip():
                raise ValueError("For Task 1, either image_data or prompt_text must be provided")
        
        return v

class EvaluationResponse(BaseModel):
    report: Optional[str] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None
    word_count: Optional[int] = None
    image_description: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str

# Exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    logger.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": str(exc)}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error occurred"}
    )

# Routes
@app.get("/", response_model=dict)
async def read_root():
    """Root endpoint returning basic API information."""
    return {
        "message": "IELTS AI Coach API is running",
        "version": "1.0.0",
        "features": ["Task 1 & 2 evaluation", "Image analysis for Task 1", "Personalized feedback"],
        "endpoints": {
            "evaluate": "/evaluate",
            "health": "/health",
            "docs": "/docs"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        version="1.0.0"
    )

@app.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_essay(request: EvaluationRequest):
    """
    Evaluate an IELTS essay and return comprehensive feedback.
    
    For Task 1, this endpoint can process visual data (charts, graphs, tables)
    and extract relevant information to enhance the evaluation.
    """
    start_time = time.time()
    
    try:
        if graph_instance is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Evaluation service is not available"
            )
        
        # Calculate word count
        word_count = len(request.essay_text.split())
        logger.info(f"Processing essay evaluation: {request.task_type}, {word_count} words")
        
        # Process image if provided (Task 1)
        image_description = ""
        if request.image_data and 'Task 1' in request.task_type:
            logger.info("Processing uploaded image for Task 1")
            try:
                image_description = await extract_image_description(request.image_data)
                logger.info(f"Image description extracted: {len(image_description)} characters")
            except Exception as e:
                logger.warning(f"Failed to process image: {e}")
                image_description = "[Image uploaded but could not be processed]"
        
        # Prepare enhanced prompt text for Task 1
        enhanced_prompt = request.prompt_text
        if image_description and 'Task 1' in request.task_type:
            if enhanced_prompt.strip():
                enhanced_prompt += f"\n\nVisual Data Description:\n{image_description}"
            else:
                enhanced_prompt = f"Visual Data Description:\n{image_description}"
        
        # Fetch previous attempts if question_id provided
        previous_attempts = []
        if request.question_id:
            history = data_manager.get_evaluation_history(request.question_id)
            if history:
                logger.info(f"Found {len(history)} previous attempts for question {request.question_id}")
                previous_attempts = [
                    {
                        "attempt_number": i + 1,
                        "word_count": h.get("word_count", 0),
                        "timestamp": h.get("timestamp", ""),
                        "essay_text": h.get("essay_text", "")[:200] + "..." if len(h.get("essay_text", "")) > 200 else h.get("essay_text", ""),
                        "evaluation_summary": h.get("evaluation_report", "")[:500] + "..." if len(h.get("evaluation_report", "")) > 500 else h.get("evaluation_report", "")
                    }
                    for i, h in enumerate(history)
                ]
        
        # Prepare input for the graph
        inputs = {
            "task_type": request.task_type,
            "prompt_text": enhanced_prompt,
            "essay_text": request.essay_text,
            "word_count": word_count,
            "previous_attempts": previous_attempts,
            "evaluations": {},
            "final_report": "",
            "error": ""
        }
        
        # Process through the graph
        final_state = None
        try:
            # Collect all events from the stream
            events = []
            async for event in graph_instance.astream(inputs):
                events.append(event)
                logger.debug(f"Received event: {list(event.keys())}")
            
            # The final state should be in the last event
            if events:
                last_event = events[-1]
                # Try different ways to extract the final state
                if "__end__" in last_event:
                    final_state = last_event["__end__"]
                elif "synthesizer" in last_event:
                    final_state = last_event["synthesizer"]
                else:
                    # Get the last non-empty state
                    for event in reversed(events):
                        for node_name, node_state in event.items():
                            if isinstance(node_state, dict) and node_state.get("final_report"):
                                final_state = node_state
                                break
                        if final_state:
                            break
            
            logger.info(f"Final state extracted: {bool(final_state)}")
            if final_state:
                logger.debug(f"Final state keys: {list(final_state.keys())}")
                
        except Exception as e:
            logger.error(f"Graph processing error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Evaluation processing failed"
            )
        
        processing_time = time.time() - start_time
        
        # Handle results
        if final_state:
            if final_state.get('final_report') and not final_state.get('error'):
                logger.info(f"Evaluation completed successfully in {processing_time:.2f}s")
                return EvaluationResponse(
                    report=final_state.get("final_report"),
                    processing_time=processing_time,
                    word_count=word_count,
                    image_description=image_description if image_description else None
                )
            else:
                error_message = final_state.get('error', 'Evaluation completed but no report generated')
                logger.error(f"Evaluation failed: {error_message}")
                return EvaluationResponse(
                    error=error_message,
                    processing_time=processing_time,
                    word_count=word_count,
                    image_description=image_description if image_description else None
                )
        else:
            logger.error("No final state returned from graph")
            return EvaluationResponse(
                error="No evaluation result was generated",
                processing_time=processing_time,
                word_count=word_count
            )
            
    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Unexpected error during evaluation: {e}")
        return EvaluationResponse(
            error="An unexpected error occurred during evaluation",
            processing_time=processing_time
        )

# Additional utility endpoints for production monitoring
@app.get("/metrics")
async def get_metrics():
    """Basic metrics endpoint (extend as needed)."""
    return {
        "graph_status": "ready" if graph_instance else "not_ready",
        "features": ["image_processing", "task1_support", "task2_support", "question_bank", "evaluation_history"],
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    }

# Question Bank Endpoints
class QuestionRequest(BaseModel):
    task_type: str
    prompt_text: str
    image_data: Optional[str] = None

class QuestionResponse(BaseModel):
    question_id: str
    message: str

@app.post("/questions/save", response_model=QuestionResponse)
async def save_question(request: QuestionRequest):
    """Save a question to the question bank."""
    try:
        question_id = data_manager.save_question(
            task_type=request.task_type,
            prompt_text=request.prompt_text,
            image_data=request.image_data
        )
        return QuestionResponse(
            question_id=question_id,
            message="Question saved successfully"
        )
    except Exception as e:
        logger.error(f"Error saving question: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save question"
        )

@app.get("/questions/list")
async def list_questions(task_type: Optional[str] = None):
    """List all saved questions, optionally filtered by task type."""
    try:
        questions = data_manager.list_questions(task_type=task_type)
        return {"questions": questions, "count": len(questions)}
    except Exception as e:
        logger.error(f"Error listing questions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list questions"
        )

@app.get("/questions/{question_id}")
async def get_question(question_id: str):
    """Retrieve a specific question by ID."""
    question = data_manager.get_question(question_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    return question

@app.delete("/questions/{question_id}")
async def delete_question(question_id: str):
    """Delete a question and all associated evaluations."""
    success = data_manager.delete_question(question_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found or deletion failed"
        )
    return {"message": "Question and associated data deleted successfully"}

# Evaluation History Endpoints
class SaveEvaluationRequest(BaseModel):
    question_id: str
    essay_text: str
    evaluation_report: str
    word_count: int

@app.post("/evaluations/save")
async def save_evaluation_history(request: SaveEvaluationRequest):
    """Save an evaluation to history."""
    try:
        evaluation_id = data_manager.save_evaluation(
            question_id=request.question_id,
            essay_text=request.essay_text,
            evaluation_report=request.evaluation_report,
            word_count=request.word_count
        )
        return {
            "evaluation_id": evaluation_id,
            "message": "Evaluation saved successfully"
        }
    except Exception as e:
        logger.error(f"Error saving evaluation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save evaluation"
        )

@app.get("/evaluations/history/{question_id}")
async def get_evaluation_history(question_id: str):
    """Get evaluation history for a specific question."""
    try:
        history = data_manager.get_evaluation_history(question_id)
        return {"history": history, "count": len(history)}
    except Exception as e:
        logger.error(f"Error retrieving evaluation history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve evaluation history"
        )

@app.delete("/evaluations/{evaluation_id}")
async def delete_evaluation(evaluation_id: str):
    """Delete a specific evaluation."""
    success = data_manager.delete_evaluation(evaluation_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation not found"
        )
    return {"message": "Evaluation deleted successfully"}

@app.delete("/evaluations/question/{question_id}")
async def delete_all_evaluations(question_id: str):
    """Delete all evaluations for a specific question."""
    count = data_manager.delete_all_evaluations_for_question(question_id)
    return {
        "message": f"Deleted {count} evaluation(s)",
        "count": count
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)