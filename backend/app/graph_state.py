from typing import TypedDict, Dict, Any, List

class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        task_type: The type of IELTS task (e.g., "Academic Task 1").
        prompt_text: The text of the question/prompt.
        essay_text: The user's essay.
        word_count: The number of words in the essay.
        previous_attempts: List of previous evaluation attempts for this question.
        evaluations: A dictionary to store the results from each evaluation node.
        final_report: The final compiled feedback for the user.
        error: A string to hold any error messages.
    """
    task_type: str
    prompt_text: str
    essay_text: str
    word_count: int
    previous_attempts: List[Dict[str, Any]]
    evaluations: Dict[str, Any]
    final_report: str
    error: str