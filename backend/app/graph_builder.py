import logging
from langgraph.graph import StateGraph, END
from .graph_state import GraphState
from . import graph_nodes

logger = logging.getLogger(__name__)

def should_evaluate_task_1_or_2(state: GraphState) -> str:
    """
    Router function to decide which task achievement/response node to use.
    
    Returns the name of the next node to execute based on task type.
    """
    task_type = state.get("task_type", "").lower()
    
    logger.info(f"Routing based on task_type: {task_type}")
    
    if "task 1" in task_type:
        return "evaluate_task_achievement_t1"
    elif "task 2" in task_type:
        return "evaluate_task_response_t2"
    else:
        # Route to error handler instead of ending abruptly
        logger.error(f"Invalid task type specified: {task_type}")
        return "handle_error"

def handle_error_node(state: GraphState) -> dict:
    """
    Handle errors that occur during graph execution.
    
    This node ensures graceful error handling and provides meaningful feedback.
    """
    logger.error("Error node activated")
    
    # Check if there's already an error message, otherwise set a default
    error_message = state.get('error', 'An unknown error occurred during evaluation.')
    
    return {
        "error": error_message,
        "final_report": f"**Evaluation Error**\n\n{error_message}\n\nPlease check your inputs and try again."
    }

def create_graph() -> StateGraph:
    """
    Build and compile the LangGraph agent for IELTS evaluation.
    
    Returns:
        Compiled StateGraph ready for execution
    """
    logger.info("Creating IELTS evaluation graph...")
    
    try:
        # Initialize the workflow
        workflow = StateGraph(GraphState)

        # Add all evaluation nodes
        workflow.add_node("evaluate_task_achievement_t1", graph_nodes.evaluate_task_achievement_t1)
        workflow.add_node("evaluate_task_response_t2", graph_nodes.evaluate_task_response_t2)
        workflow.add_node("evaluate_coherence_cohesion", graph_nodes.evaluate_coherence_cohesion)
        workflow.add_node("evaluate_lexical_resource", graph_nodes.evaluate_lexical_resource)
        workflow.add_node("evaluate_grammatical_range", graph_nodes.evaluate_grammatical_range)
        workflow.add_node("synthesizer", graph_nodes.synthesizer_node)
        
        # Add error handling node
        workflow.add_node("handle_error", handle_error_node)

        # Set up the conditional entry point with error handling
        workflow.add_conditional_edges(
            "__start__",
            should_evaluate_task_1_or_2,
            {
                "evaluate_task_achievement_t1": "evaluate_task_achievement_t1",
                "evaluate_task_response_t2": "evaluate_task_response_t2",
                "handle_error": "handle_error"
            },
        )

        # Define the main evaluation flow
        # After initial task-specific evaluation, flow to coherence & cohesion
        workflow.add_edge("evaluate_task_achievement_t1", "evaluate_coherence_cohesion")
        workflow.add_edge("evaluate_task_response_t2", "evaluate_coherence_cohesion")
        
        # Sequential evaluation flow (could be parallelized in advanced setup)
        workflow.add_edge("evaluate_coherence_cohesion", "evaluate_lexical_resource")
        workflow.add_edge("evaluate_lexical_resource", "evaluate_grammatical_range")
        workflow.add_edge("evaluate_grammatical_range", "synthesizer")
        
        # Terminal edges
        workflow.add_edge("synthesizer", END)
        workflow.add_edge("handle_error", END)

        # Compile the graph
        app = workflow.compile()
        
        logger.info("Graph created and compiled successfully")
        return app
        
    except Exception as e:
        logger.error(f"Failed to create graph: {e}")
        raise

# Factory function for creating graph instances
def get_graph_instance() -> StateGraph:
    """
    Factory function to get a graph instance.
    
    This allows for better testing and potential future optimizations
    like graph pooling or caching.
    """
    return create_graph()