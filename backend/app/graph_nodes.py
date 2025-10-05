import json
import os
import logging
import time
from typing import Dict, Any, Optional
from pathlib import Path

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.exceptions import OutputParserException
from .graph_state import GraphState
from .llm_config import UniversalLLMConfig

# Configure logging
logger = logging.getLogger(__name__)

# Initialize LLM and parser using Universal Config
llm = UniversalLLMConfig.get_llm()
json_parser = JsonOutputParser()

# --- Utility Functions ---
def load_rubric(filename: str) -> Dict[str, Any]:
    """
    Load and validate rubric file.
    
    Args:
        filename: Name of the rubric file
        
    Returns:
        Parsed rubric as dictionary
        
    Raises:
        FileNotFoundError: If rubric file doesn't exist
        json.JSONDecodeError: If rubric file is malformed
    """
    rubric_path = Path(__file__).parent.parent / 'rubrics' / filename
    
    try:
        with open(rubric_path, 'r', encoding='utf-8') as f:
            rubric = json.load(f)
        
        # Validate rubric structure
        required_keys = ['category', 'criteria_to_evaluate', 'output_format']
        if not all(key in rubric for key in required_keys):
            raise ValueError(f"Invalid rubric structure in {filename}")
        
        logger.debug(f"Successfully loaded rubric: {filename}")
        return rubric
        
    except FileNotFoundError:
        logger.error(f"Rubric file not found: {filename}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in rubric file {filename}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error loading rubric {filename}: {e}")
        raise

def prepare_rubric_with_word_count(rubric_data: Dict[str, Any], word_count: int) -> str:
    """
    Prepare rubric string with word count injected where needed.
    
    Args:
        rubric_data: The loaded rubric dictionary
        word_count: Current essay word count
        
    Returns:
        Formatted rubric string ready for prompt
    """
    # Convert to JSON string first
    rubric_str = json.dumps(rubric_data, indent=2)
    
    # Only replace {word_count} if it exists in the string
    if '{word_count}' in rubric_str:
        rubric_str = rubric_str.replace('{word_count}', str(word_count))
    
    return rubric_str

def sanitize_text(text: str) -> str:
    """
    Sanitize text input for safe processing.
    
    Args:
        text: Input text to sanitize
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove excessive whitespace and normalize
    text = ' '.join(text.split())
    
    # Basic length check
    if len(text) > 15000:  # Reasonable limit for essays
        logger.warning("Text truncated due to length")
        text = text[:15000] + "... [truncated]"
    
    return text

def validate_json_output(result: Any, expected_keys: list) -> bool:
    """
    Validate JSON output from LLM.
    
    Args:
        result: LLM output to validate
        expected_keys: Required keys in the output
        
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(result, dict):
        return False
    
    return all(key in result for key in expected_keys)

def format_previous_attempts(previous_attempts: list) -> str:
    """
    Format previous attempts for inclusion in evaluation prompts.
    
    Args:
        previous_attempts: List of previous attempt dictionaries
        
    Returns:
        Formatted string describing previous attempts
    """
    if not previous_attempts:
        return ""
    
    formatted = "\n\n--- PREVIOUS ATTEMPTS FOR COMPARISON ---\n"
    formatted += f"This is attempt #{len(previous_attempts) + 1} for this question.\n\n"
    
    for i, attempt in enumerate(previous_attempts, 1):
        formatted += f"ATTEMPT #{i}:\n"
        formatted += f"Word Count: {attempt.get('word_count', 'N/A')}\n"
        formatted += f"Date: {attempt.get('timestamp', 'N/A')[:10]}\n"
        formatted += f"Essay Excerpt: {attempt.get('essay_text', 'N/A')}\n"
        formatted += f"Previous Evaluation Summary: {attempt.get('evaluation_summary', 'N/A')}\n"
        formatted += "\n"
    
    formatted += "INSTRUCTION: When evaluating, note any improvements or regressions compared to previous attempts. "
    formatted += "Provide specific feedback on how this submission compares to earlier ones.\n"
    formatted += "--- END PREVIOUS ATTEMPTS ---\n\n"
    
    return formatted

# --- Enhanced Evaluator Factory ---
def create_evaluator_node(criterion_name: str, rubric_filename: str):
    """
    Factory function to create an evaluation node with enhanced error handling.
    
    Args:
        criterion_name: Name of the evaluation criterion
        rubric_filename: Filename of the rubric to use
        
    Returns:
        Configured evaluator function
    """
    
    # Load rubric at creation time for early validation
    try:
        rubric_data = load_rubric(rubric_filename)
        expected_output_keys = list(rubric_data['output_format'].keys())
    except Exception as e:
        logger.error(f"Failed to load rubric for {criterion_name}: {e}")
        raise
    
    def evaluator_node(state: GraphState) -> Dict[str, Any]:
        """
        Evaluate essay based on specific criterion.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated evaluation results or error information
        """
        logger.info(f"Starting evaluation: {criterion_name}")
        start_time = time.time()
        
        try:
            # Validate input state
            if not state.get('essay_text'):
                raise ValueError("No essay text provided")
            
            # Sanitize inputs
            essay_text = sanitize_text(state['essay_text'])
            word_count = state.get('word_count', len(essay_text.split()))
            
            # Prepare rubric with word count
            filled_rubric = prepare_rubric_with_word_count(rubric_data, word_count)
            
            # Check if this is Task 1 (needs prompt/visual data context)
            is_task_1 = "task 1" in state.get('task_type', '').lower()
            prompt_text = state.get('prompt_text', '')
            
            # Get previous attempts for comparison
            previous_attempts = state.get('previous_attempts', [])
            previous_context = format_previous_attempts(previous_attempts)
            
            # Create prompt with conditional visual data context AND previous attempts
            if is_task_1 and prompt_text:
                prompt = PromptTemplate(
                    template="""You are a specialist IELTS examiner for {criterion}.
Evaluate the following Task 1 essay based *only* on the rubric provided.
Provide your final evaluation strictly in the JSON format specified in `output_format`.

Be objective, fair, and specific in your evaluation. Use concrete examples from the text.

VISUAL DATA / TASK DESCRIPTION:
---
{visual_data}
---

{previous_context}

CURRENT ESSAY TO EVALUATE:
---
{essay}
---

JSON RUBRIC:
---
{rubric}
---

IMPORTANT for Task 1: 
1. Evaluate how well the essay describes the visual data provided above.
2. Check if the essay accurately reports key features, trends, and figures from the visual data.
3. If there are previous attempts, comment on improvements or areas that still need work compared to earlier submissions.

Remember: Your response must be valid JSON matching the output_format exactly.
""",
                    input_variables=["criterion", "visual_data", "previous_context", "essay", "rubric"],
                )
            else:
                prompt = PromptTemplate(
                    template="""You are a specialist IELTS examiner for {criterion}.
Evaluate the following essay based *only* on the rubric provided.
Provide your final evaluation strictly in the JSON format specified in `output_format`.

Be objective, fair, and specific in your evaluation. Use concrete examples from the text.

{previous_context}

CURRENT ESSAY TO EVALUATE:
---
{essay}
---

JSON RUBRIC:
---
{rubric}
---

{comparison_instruction}

Remember: Your response must be valid JSON matching the output_format exactly.
""",
                    input_variables=["criterion", "previous_context", "essay", "rubric", "comparison_instruction"],
                )

            # Execute chain with retry logic
            for attempt in range(UniversalLLMConfig.MAX_RETRIES):
                try:
                    chain = prompt | llm | json_parser
                    
                    # Prepare invoke parameters based on whether visual data is needed
                    invoke_params = {
                        "criterion": criterion_name,
                        "essay": essay_text,
                        "rubric": filled_rubric,
                        "previous_context": previous_context
                    }
                    
                    if is_task_1 and prompt_text:
                        invoke_params["visual_data"] = prompt_text
                    else:
                        # Add comparison instruction for Task 2
                        comparison_instruction = ""
                        if previous_attempts:
                            comparison_instruction = "IMPORTANT: If there are previous attempts shown above, comment on improvements or areas that still need work compared to earlier submissions."
                        invoke_params["comparison_instruction"] = comparison_instruction
                    
                    result = chain.invoke(invoke_params)
                    
                    # Validate output
                    if validate_json_output(result, expected_output_keys):
                        processing_time = time.time() - start_time
                        logger.info(f"Successfully evaluated {criterion_name} in {processing_time:.2f}s")
                        
                        # Update state
                        current_evaluations = state.get('evaluations', {})
                        current_evaluations[criterion_name] = result
                        
                        return {"evaluations": current_evaluations}
                    else:
                        logger.warning(f"Invalid output format from LLM for {criterion_name}, attempt {attempt + 1}")
                        if attempt == UniversalLLMConfig.MAX_RETRIES - 1:
                            raise ValueError("LLM returned invalid output format")
                        
                except OutputParserException as e:
                    logger.warning(f"JSON parsing error for {criterion_name}, attempt {attempt + 1}: {e}")
                    if attempt == UniversalLLMConfig.MAX_RETRIES - 1:
                        raise
                    
                except Exception as e:
                    logger.error(f"LLM invocation error for {criterion_name}, attempt {attempt + 1}: {e}")
                    if attempt == UniversalLLMConfig.MAX_RETRIES - 1:
                        raise
                
                # Wait before retry
                time.sleep(2 ** attempt)  # Exponential backoff
                
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Failed to evaluate {criterion_name} after {processing_time:.2f}s: {e}")
            return {"error": f"Failed during {criterion_name} evaluation: {str(e)}"}

    return evaluator_node

# --- Create Specific Evaluator Nodes ---
try:
    evaluate_task_achievement_t1 = create_evaluator_node("task_achievement", "1_task_achievement_t1.json")
    evaluate_task_response_t2 = create_evaluator_node("task_response", "2_task_response_t2.json")
    evaluate_coherence_cohesion = create_evaluator_node("coherence_cohesion", "3_coherence_cohesion.json")
    evaluate_lexical_resource = create_evaluator_node("lexical_resource", "4_lexical_resource.json")
    evaluate_grammatical_range = create_evaluator_node("grammatical_range", "5_grammatical_range_accuracy.json")
    
    logger.info("All evaluator nodes created successfully")
    
except Exception as e:
    logger.error(f"Failed to create evaluator nodes: {e}")
    raise

# --- Enhanced Synthesizer Node ---
def synthesizer_node(state: GraphState) -> Dict[str, Any]:
    """
    Compile all evaluations into a comprehensive final report.
    
    Args:
        state: Current graph state with all evaluations
        
    Returns:
        Final report or error information
    """
    logger.info("Starting report synthesis")
    start_time = time.time()
    
    try:
        # Check for errors in previous evaluations
        if state.get('error'):
            logger.warning(f"Previous error detected: {state['error']}")
            return {
                "final_report": "**Evaluation Error**\n\nAn error occurred during the evaluation process. Please try again.",
                "error": state['error']
            }

        # Validate evaluations exist
        evaluations = state.get('evaluations', {})
        if not evaluations:
            raise ValueError("No evaluation results found")
        
        # Check that we have all expected evaluations
        task_type = state.get('task_type', '').lower()
        expected_evaluations = ['coherence_cohesion', 'lexical_resource', 'grammatical_range']
        
        if 'task 1' in task_type:
            expected_evaluations.append('task_achievement')
        elif 'task 2' in task_type:
            expected_evaluations.append('task_response')
        
        missing_evaluations = [eval_type for eval_type in expected_evaluations if eval_type not in evaluations]
        if missing_evaluations:
            logger.warning(f"Missing evaluations: {missing_evaluations}")
        
        # Prepare data for synthesis
        evaluations_json = json.dumps(evaluations, indent=2)
        
        # Get previous attempts info
        previous_attempts = state.get('previous_attempts', [])
        has_previous = len(previous_attempts) > 0
        attempt_number = len(previous_attempts) + 1
        
        # Prepare previous attempts context for synthesis
        previous_context = ""
        if has_previous:
            previous_context = f"""
CONTEXT: This is attempt #{attempt_number} for this question. The student has previously attempted this {len(previous_attempts)} time(s).

Previous Attempts Summary:
"""
            for i, attempt in enumerate(previous_attempts, 1):
                previous_context += f"\nAttempt #{i} ({attempt.get('timestamp', 'N/A')[:10]}):\n"
                previous_context += f"- Word count: {attempt.get('word_count', 'N/A')}\n"
                previous_context += f"- Previous feedback summary: {attempt.get('evaluation_summary', 'N/A')[:300]}...\n"
            
            previous_context += "\nIMPORTANT: Provide comparative feedback showing how this attempt compares to previous ones. Highlight improvements and persistent issues.\n"
        
        # Enhanced synthesis prompt - PERSONAL COACHING STYLE with comparative feedback
        prompt = PromptTemplate(
            template="""
ROLE: You are an expert IELTS examiner and personal writing coach providing direct, personalized feedback to a student.

CONTEXT: You have evaluated an IELTS {task_type} essay using structured criteria and now need to provide encouraging, direct feedback.

{previous_context}

INPUT DATA:
---
{evaluations}
---

TASK:
Create a warm, personal feedback report in Markdown format. Address the student directly using "you" and "your" throughout. Structure as follows:

1.  **🎯 Your Overall Band Score:** Calculate the final band score using the average of all individual scores, rounded to the nearest half-band (e.g., 6.25 → 6.5, 6.1 → 6.0, 6.8 → 7.0). Present it encouragingly.
    {attempt_info}

2.  **📝 How You Did:** A warm 2-3 sentence summary of your performance, highlighting what you did well and what needs attention.
    {comparison_note}

3.  **🔍 Detailed Feedback:** For each criterion evaluated:
    * State the criterion and your score (e.g., "**Task Response: 6.5**")
    * Write a supportive paragraph about your strengths and areas to improve
    * Quote specific examples from your essay when relevant
    * {comparison_instruction}

4.  **📐 Your Essay Structure:** Comment directly on how you organized your essay.

5.  **🚀 What to Focus on Next:** 2-3 specific, actionable steps for you to improve.
    {improvement_focus}

6.  **📚 Recommended Practice:** Suggest specific activities you should try.

TONE & STYLE:
- Write as if you're speaking directly to the student
- Use "you", "your", "you've written" instead of "the student", "the writer"
- Be encouraging and supportive like a personal tutor
- Make it feel like personalized coaching, not generic assessment
- Include motivational language while being honest about areas for improvement

EXAMPLES OF GOOD PHRASING:
✅ "You've demonstrated good understanding..."
✅ "Your essay shows strong organization..."
✅ "In your introduction, you clearly state..."
✅ "You could improve by..."
✅ "Compared to your last attempt, you've improved significantly in..."
✅ "You're still struggling with..., just like in your previous attempt"

AVOID:
❌ "The student demonstrates..."
❌ "The writer shows..."
❌ "This essay contains..."
""",
            input_variables=["task_type", "previous_context", "evaluations", "attempt_info", 
                           "comparison_note", "comparison_instruction", "improvement_focus"],
        )

        # Prepare conditional content based on whether there are previous attempts
        if has_previous:
            attempt_info = f"    *This is your attempt #{attempt_number} at this question.*"
            comparison_note = "    *Include a brief comparison with your previous attempt(s).*"
            comparison_instruction = "If applicable, note improvements or ongoing issues compared to previous attempts"
            improvement_focus = "    *Especially focus on areas you struggled with in previous attempts.*"
        else:
            attempt_info = ""
            comparison_note = ""
            comparison_instruction = ""
            improvement_focus = ""

        # Generate report with retry logic
        for attempt in range(UniversalLLMConfig.MAX_RETRIES):
            try:
                chain = prompt | llm
                
                result = chain.invoke({
                    "task_type": state.get('task_type', 'IELTS Writing Task'),
                    "previous_context": previous_context,
                    "evaluations": evaluations_json,
                    "attempt_info": attempt_info,
                    "comparison_note": comparison_note,
                    "comparison_instruction": comparison_instruction,
                    "improvement_focus": improvement_focus
                })
                
                processing_time = time.time() - start_time
                logger.info(f"Report synthesis completed in {processing_time:.2f}s")
                
                return {"final_report": result.content}
                
            except Exception as e:
                logger.warning(f"Synthesis attempt {attempt + 1} failed: {e}")
                if attempt == UniversalLLMConfig.MAX_RETRIES - 1:
                    raise
                time.sleep(2 ** attempt)
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Synthesis failed after {processing_time:.2f}s: {e}")
        
        # Generate fallback report
        fallback_report = """
**Evaluation Report**

An error occurred while generating your detailed feedback report. However, your essay has been processed.

**What you can do:**
- Check that your essay meets the minimum word requirements
- Ensure your essay directly addresses the prompt
- Review basic IELTS writing criteria: Task Achievement/Response, Coherence & Cohesion, Lexical Resource, and Grammatical Range & Accuracy

Please try submitting your essay again.
"""
        
        return {
            "final_report": fallback_report,
            "error": f"Synthesis error: {str(e)}"
        }
