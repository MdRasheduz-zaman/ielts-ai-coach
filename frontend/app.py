import streamlit as st
import requests
import time
import logging
import base64
from typing import Optional
from PIL import Image
import io
from datetime import datetime

# --- Configuration ---
st.set_page_config(
    page_title="IELTS AI Writing Coach",
    page_icon="✍️",
    layout="wide"
)

BACKEND_URL = "http://127.0.0.1:8000"
REQUEST_TIMEOUT = 300

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Session State Initialization ---
def initialize_session_state():
    """Initialize session state variables."""
    defaults = {
        'timer_start': None,
        'time_remaining': None,
        'evaluation_report': "",
        'essay_submitted': False,
        'last_timer_update': None,
        'uploaded_image': None,
        'current_question_id': None,
        'question_source': 'new',
        'save_evaluation': False,
        'current_essay_text': "",
        'current_word_count': 0,
        'show_history': False,
        'selected_task_type': None,
        'prompt_text': "",
        'module_type': "Academic",
        'task_num': "Task 1",
        'loaded_image_base64': None,
        'loaded_image_name': None,
        'question_just_loaded': False  # NEW: Track if question was just loaded
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

# --- API Helper Functions ---
def api_call(method: str, endpoint: str, data=None, timeout=30):
    """Generic API call wrapper."""
    try:
        url = f"{BACKEND_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=timeout)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=timeout)
        elif method == "DELETE":
            response = requests.delete(url, timeout=timeout)
        
        response.raise_for_status()
        return True, response.json()
    except Exception as e:
        logger.error(f"API call failed: {e}")
        return False, str(e)

def save_question_to_bank(task_type: str, prompt_text: str, image_base64: Optional[str] = None):
    """Save question to question bank."""
    success, result = api_call("POST", "/questions/save", {
        "task_type": task_type,
        "prompt_text": prompt_text,
        "image_data": image_base64
    })
    
    if success:
        return result.get("question_id")
    return None

def load_questions_from_bank(task_type: Optional[str] = None):
    """Load questions from bank."""
    success, result = api_call("GET", f"/questions/list{'?task_type=' + task_type if task_type else ''}")
    if success:
        return result.get("questions", [])
    return []

def load_question_details(question_id: str):
    """Load specific question details."""
    success, result = api_call("GET", f"/questions/{question_id}")
    if success:
        return result
    return None

def save_evaluation_to_history(question_id: str, essay_text: str, report: str, word_count: int):
    """Save evaluation to history."""
    success, result = api_call("POST", "/evaluations/save", {
        "question_id": question_id,
        "essay_text": essay_text,
        "evaluation_report": report,
        "word_count": word_count
    })
    return success

def load_evaluation_history(question_id: str):
    """Load evaluation history for a question."""
    success, result = api_call("GET", f"/evaluations/history/{question_id}")
    if success:
        return result.get("history", [])
    return []

def delete_question_from_bank(question_id: str):
    """Delete question and all evaluations."""
    success, result = api_call("DELETE", f"/questions/{question_id}")
    return success

def delete_evaluation(evaluation_id: str):
    """Delete specific evaluation."""
    success, result = api_call("DELETE", f"/evaluations/{evaluation_id}")
    return success

# --- Image Processing ---
def process_uploaded_image(uploaded_file) -> tuple[str, str]:
    """Process uploaded image and convert to base64."""
    try:
        image = Image.open(uploaded_file)
        if image.mode in ('RGBA', 'LA', 'P'):
            image = image.convert('RGB')
        
        max_size = 1024
        if max(image.size) > max_size:
            ratio = max_size / max(image.size)
            new_size = tuple(int(dim * ratio) for dim in image.size)
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=85)
        img_bytes = buffer.getvalue()
        img_base64 = base64.b64encode(img_bytes).decode()
        
        file_info = f"Image: {uploaded_file.name} ({image.size[0]}x{image.size[1]})"
        return img_base64, file_info
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        raise ValueError(f"Failed to process image: {str(e)}")

def display_image_preview(uploaded_file):
    """Display preview of uploaded image."""
    try:
        image = Image.open(uploaded_file)
        st.image(image, caption=f"📊 {uploaded_file.name}", use_column_width=True)
    except Exception as e:
        st.error(f"Cannot preview image: {e}")

# --- Essay Submission ---
def submit_essay_for_evaluation(task_type: str, prompt_text: str, essay_text: str, 
                              image_base64: Optional[str] = None) -> tuple[bool, str]:
    """Submit essay to backend."""
    payload = {
        "task_type": task_type,
        "prompt_text": prompt_text,
        "essay_text": essay_text
    }
    
    if image_base64:
        payload["image_data"] = image_base64
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/evaluate",
            json=payload,
            timeout=REQUEST_TIMEOUT,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        
        result = response.json()
        if "report" in result:
            return True, result["report"]
        else:
            error_msg = result.get('error', 'Unknown error occurred')
            return False, f"Evaluation error: {error_msg}"
    except Exception as e:
        return False, f"Error: {str(e)}"

# --- Timer Functions ---
def update_timer(time_limit: int) -> bool:
    """Update timer."""
    current_time = time.time()
    
    if (st.session_state.last_timer_update is None or 
        current_time - st.session_state.last_timer_update >= 1.0):
        
        elapsed_time = current_time - st.session_state.timer_start
        st.session_state.time_remaining = max(0, time_limit - elapsed_time)
        st.session_state.last_timer_update = current_time
        
        return st.session_state.time_remaining > 0
    
    return st.session_state.time_remaining > 0

# --- UI Components ---
def render_question_bank_sidebar():
    """Render question bank management in sidebar."""
    with st.sidebar:
        st.title("📚 Question Bank")
        
        # Load questions
        questions = load_questions_from_bank()
        
        if questions:
            st.write(f"**{len(questions)} saved questions**")
            
            # Filter by task type
            filter_task = st.selectbox(
                "Filter by task:",
                ["All", "Academic Task 1", "Academic Task 2", 
                 "General Training Task 1", "General Training Task 2"],
                key="filter_task_type"
            )
            
            # Filter questions
            if filter_task != "All":
                filtered = [q for q in questions if q["task_type"] == filter_task]
            else:
                filtered = questions
            
            # Display questions
            for i, q in enumerate(filtered):
                # Create display text - use prompt if available, otherwise indicate image-only
                display_text = q['prompt_text'][:30] if q['prompt_text'] and q['prompt_text'].strip() else "[Image only]"
                with st.expander(f"{q['task_type'][:15]}... - {display_text}..."):
                    st.write(f"**ID:** {q['question_id']}")
                    st.write(f"**Task:** {q['task_type']}")
                    st.write(f"**Created:** {q.get('created_at', 'N/A')[:10]}")
                    st.write(f"**Has Image:** {'Yes' if q.get('has_image') else 'No'}")
                    if q['prompt_text'] and q['prompt_text'].strip():
                        st.write(f"**Text:** {q['prompt_text'][:50]}...")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("Load", key=f"load_{i}"):
                            load_question_from_bank(q['question_id'])
                    
                    with col2:
                        if st.button("History", key=f"history_{i}"):
                            show_question_history(q['question_id'])
                    
                    with col3:
                        if st.button("Delete", key=f"delete_{i}"):
                            if delete_question_from_bank(q['question_id']):
                                st.success("Deleted!")
                                st.rerun()
        else:
            st.info("No saved questions yet. Start practicing to build your question bank!")

def load_question_from_bank(question_id: str):
    """Load a question from the bank - FIXED VERSION."""
    question = load_question_details(question_id)
    if question:
        # Parse the task type to set the dropdowns correctly
        task_parts = question['task_type'].split()
        if len(task_parts) >= 2:
            # Handle "Academic Task 1" or "General Training Task 2"
            if task_parts[0] == "General":
                module_type = "General Training"
                task_num = f"Task {task_parts[-1]}"
            else:
                module_type = task_parts[0]
                task_num = f"Task {task_parts[-1]}"
        else:
            module_type = "Academic"
            task_num = "Task 1"
        
        # Set all state in one go to avoid multiple reruns
        st.session_state.question_just_loaded = True
        st.session_state.question_source = 'bank'
        st.session_state.current_question_id = question_id
        st.session_state.selected_task_type = question['task_type']
        st.session_state.prompt_text = question['prompt_text']
        
        # Store the dropdown values persistently
        st.session_state.module_type = module_type
        st.session_state.task_num = task_num
        
        # Handle image if exists - store base64 data for later use
        if question.get('image_data'):
            st.session_state.loaded_image_base64 = question.get('image_data')
            st.session_state.loaded_image_name = f"Question_{question_id[:8]}.jpg"
            st.session_state.uploaded_image = None  # Clear any uploaded file
        else:
            st.session_state.loaded_image_base64 = None
            st.session_state.loaded_image_name = None
            st.session_state.uploaded_image = None
        
        st.success(f"✅ Question loaded: {question['task_type']}")
        st.rerun()

def show_question_history(question_id: str):
    """Show evaluation history for a question."""
    st.session_state.show_history = True
    st.session_state.current_question_id = question_id
    st.rerun()

def render_evaluation_history():
    """Render evaluation history view."""
    if not st.session_state.show_history or not st.session_state.current_question_id:
        return
    
    st.subheader("📊 Evaluation History")
    
    history = load_evaluation_history(st.session_state.current_question_id)
    
    if history:
        st.write(f"**Total Attempts:** {len(history)}")
        
        for i, eval_data in enumerate(history, 1):
            timestamp = datetime.fromisoformat(eval_data['timestamp']).strftime("%Y-%m-%d %H:%M")
            
            with st.expander(f"Attempt #{i} - {timestamp} ({eval_data['word_count']} words)"):
                st.markdown("**Essay:**")
                st.text_area("", eval_data['essay_text'], height=150, key=f"essay_hist_{i}", disabled=True)
                
                st.markdown("**Evaluation Report:**")
                st.markdown(eval_data['evaluation_report'])
                
                if st.button(f"Delete Attempt #{i}", key=f"del_eval_{i}"):
                    if delete_evaluation(eval_data['evaluation_id']):
                        st.success("Evaluation deleted!")
                        st.rerun()
    else:
        st.info("No evaluation history for this question yet.")
    
    if st.button("Close History"):
        st.session_state.show_history = False
        st.rerun()

# --- Main Application ---
def main():
    initialize_session_state()
    
    # Render sidebar
    render_question_bank_sidebar()
    
    # Show history if requested
    if st.session_state.show_history:
        render_evaluation_history()
        return
    
    # Main UI
    st.title("✍️ IELTS AI Writing Coach")
    st.markdown("Practice your IELTS writing tasks with instant, AI-powered feedback.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("1. Test Setup")
        
        # Show info if a question was loaded from bank
        if st.session_state.question_source == 'bank' and st.session_state.current_question_id:
            st.info(f"📚 **Question loaded from bank** (ID: {st.session_state.current_question_id[:8]}...)")
        
        # Task selection - use session state values
        module_index = 0 if st.session_state.module_type == "Academic" else 1
        module_type = st.selectbox(
            "Select Module:", 
            ["Academic", "General Training"],
            index=module_index,
            key="module_selector"
        )
        
        task_index = 0 if st.session_state.task_num == "Task 1" else 1
        task_type_num = st.selectbox(
            "Select Task:", 
            ["Task 1", "Task 2"],
            index=task_index,
            key="task_selector"
        )
        
        task_type = f"{module_type} {task_type_num}"
        
        # Track previous task to detect changes
        if 'previous_task_type' not in st.session_state:
            st.session_state.previous_task_type = task_type
        
        # Only clear data if task changed AND question was NOT just loaded
        if (st.session_state.previous_task_type != task_type and 
            not st.session_state.question_just_loaded):
            st.session_state.prompt_text = ""
            st.session_state.uploaded_image = None
            st.session_state.loaded_image_base64 = None
            st.session_state.loaded_image_name = None
            st.session_state.current_question_id = None
            st.session_state.question_source = 'new'
        
        # Update session state with current selections
        st.session_state.module_type = module_type
        st.session_state.task_num = task_type_num
        st.session_state.previous_task_type = task_type
        st.session_state.selected_task_type = task_type
        
        # Reset the "just loaded" flag after processing
        if st.session_state.question_just_loaded:
            st.session_state.question_just_loaded = False

        # Task-specific input
        if task_type_num == "Task 1":
            st.markdown("### 📊 Task 1 Setup")
            
            # Initialize uploaded_file to None
            uploaded_file = None
            
            # Display loaded image from history if available
            if st.session_state.loaded_image_base64:
                st.success(f"✅ Image loaded: {st.session_state.loaded_image_name}")
                try:
                    # Decode and display the base64 image
                    image_bytes = base64.b64decode(st.session_state.loaded_image_base64)
                    image = Image.open(io.BytesIO(image_bytes))
                    st.image(image, caption=f"📊 {st.session_state.loaded_image_name}", use_column_width=True)
                except Exception as e:
                    st.error(f"Error displaying loaded image: {e}")
                    # If error, clear and allow upload
                    st.session_state.loaded_image_base64 = None
                    st.session_state.loaded_image_name = None
            
            # Only show file uploader if NO image is loaded from history
            if not st.session_state.loaded_image_base64:
                uploaded_file = st.file_uploader(
                    "Upload chart/graph/table image (recommended):",
                    type=["png", "jpg", "jpeg", "pdf"],
                    help="Upload the visual data you need to describe"
                )
                
                if uploaded_file:
                    if uploaded_file.type == "application/pdf":
                        st.info("📄 PDF uploaded. The AI will extract the visual content.")
                    else:
                        display_image_preview(uploaded_file)
                    
                    st.session_state.uploaded_image = uploaded_file
            else:
                # Clear uploaded_image when using loaded image
                st.session_state.uploaded_image = None
            
            # Use shared text area with unified key
            prompt_text = st.text_area(
                "Question text (optional if image contains the question):",
                value=st.session_state.prompt_text,
                height=100,
                placeholder="e.g., 'The chart shows the percentage of households...'",
                key="unified_prompt_input"
            )
            
            # Update session state
            st.session_state.prompt_text = prompt_text
            
            st.info("💡 **Task 1 Tip:** Describe the visual data accurately, provide an overview, and support with specific figures.")
            
        else:  # Task 2
            st.markdown("### 📝 Task 2 Setup")
            
            # Use shared text area with same unified key
            prompt_text = st.text_area(
                "Paste the question prompt here:",
                value=st.session_state.prompt_text,
                height=150,
                placeholder="e.g., 'Some people think that universities should...'",
                key="unified_prompt_input"
            )
            
            # Update session state
            st.session_state.prompt_text = prompt_text
            
            st.info("💡 **Task 2 Tip:** Address all parts, present a clear position, develop ideas with examples.")
        
        # Save question option - for Task 1, allow saving with just image; for Task 2, require text
        # Only show if NOT loaded from bank
        if st.session_state.question_source != 'bank':
            if task_type_num == "Task 1":
                # Task 1: Save if there's either text OR image
                can_save = prompt_text.strip() or uploaded_file or st.session_state.loaded_image_base64
            else:
                # Task 2: Require text
                can_save = prompt_text.strip()
            
            if can_save:
                save_question_checkbox = st.checkbox("💾 Save this question to my question bank", value=True)
            else:
                save_question_checkbox = False
        else:
            save_question_checkbox = False

        # Timer setup
        time_limit = 20 * 60 if task_type_num == "Task 1" else 40 * 60

        # Start button
        if st.button("Start Timed Writing Practice", type="primary"):
            if task_type_num == "Task 1":
                if not uploaded_file and not st.session_state.loaded_image_base64 and not prompt_text.strip():
                    st.error("For Task 1, please upload an image or provide the question text.")
                else:
                    # Determine if we should auto-save (even without explicit checkbox)
                    # For new questions with images, always create a question ID for tracking
                    should_save = save_question_checkbox or (st.session_state.question_source != 'bank' and 
                                                              (uploaded_file or st.session_state.loaded_image_base64))
                    
                    if should_save:
                        image_base64 = None
                        if uploaded_file:
                            try:
                                image_base64, _ = process_uploaded_image(uploaded_file)
                            except:
                                pass
                        elif st.session_state.loaded_image_base64:
                            # Use the loaded image if no new image uploaded
                            image_base64 = st.session_state.loaded_image_base64
                        
                        # Use empty string for prompt_text if not provided
                        save_prompt = prompt_text if prompt_text.strip() else "[Task 1 - Image only]"
                        q_id = save_question_to_bank(task_type, save_prompt, image_base64)
                        if q_id:
                            st.session_state.current_question_id = q_id
                            st.success("✅ Question saved to bank!")
                    
                    start_session()
            else:
                if not prompt_text.strip():
                    st.error("Please paste the question prompt before starting.")
                else:
                    # Save question if requested
                    if save_question_checkbox:
                        q_id = save_question_to_bank(task_type, prompt_text, None)
                        if q_id:
                            st.session_state.current_question_id = q_id
                            st.success("Question saved to bank!")
                    
                    start_session()

    with col2:
        st.subheader("2. Your Essay")
        
        if st.session_state.timer_start and not st.session_state.essay_submitted:
            # Timer display
            timer_active = update_timer(time_limit)
            
            minutes = int(st.session_state.time_remaining // 60)
            seconds = int(st.session_state.time_remaining % 60)
            
            if timer_active:
                st.markdown(f"**⏰ Time Remaining: `{minutes:02d}:{seconds:02d}`**")
            else:
                st.error("⏰ **Time's up!** Please submit your essay.")

            # Essay input
            essay_text = st.text_area(
                "Write your essay here:", 
                height=400, 
                key="essay_input",
                disabled=st.session_state.essay_submitted,
                placeholder="Start writing your IELTS essay here..."
            )
            
            # Word count
            word_count = len(essay_text.split()) if essay_text else 0
            min_words = 150 if task_type_num == "Task 1" else 250
            
            if word_count < min_words:
                st.warning(f"📝 Word Count: {word_count} (Target: {min_words}+ words)")
            else:
                st.success(f"📝 Word Count: {word_count} ✓")

            # Save evaluation option
            save_eval = st.checkbox("💾 Save this evaluation to history", value=True)

            # Submit button
            if st.button("Submit for Evaluation", type="primary", disabled=st.session_state.essay_submitted):
                if not essay_text.strip() or word_count < 50:
                    st.error("Please write a substantial essay before submitting.")
                else:
                    st.session_state.timer_start = None
                    st.session_state.essay_submitted = True
                    st.session_state.save_evaluation = save_eval
                    st.session_state.current_essay_text = essay_text
                    st.session_state.current_word_count = word_count
                    
                    with st.spinner("🤖 Evaluating your essay... Please wait."):
                        # Process image - either uploaded or loaded from history
                        image_base64 = None
                        if st.session_state.uploaded_image:
                            try:
                                image_base64, file_info = process_uploaded_image(st.session_state.uploaded_image)
                                st.info(f"✅ Processed: {file_info}")
                            except ValueError as e:
                                st.error(str(e))
                                st.session_state.essay_submitted = False
                                st.rerun()
                        elif st.session_state.loaded_image_base64:
                            # Use loaded image from history
                            image_base64 = st.session_state.loaded_image_base64
                            st.info(f"✅ Using loaded image: {st.session_state.loaded_image_name}")
                        
                        # Submit for evaluation
                        # Use placeholder text if prompt is empty for Task 1
                        eval_prompt = prompt_text if prompt_text.strip() else "[Describe the visual data shown in the image]"
                        success, result = submit_essay_for_evaluation(
                            task_type, eval_prompt, essay_text, image_base64
                        )
                        
                        if success:
                            st.session_state.evaluation_report = result
                            
                            # Save to history if requested and question exists
                            if save_eval and st.session_state.current_question_id:
                                save_success = save_evaluation_to_history(
                                    st.session_state.current_question_id,
                                    essay_text,
                                    result,
                                    word_count
                                )
                                if save_success:
                                    st.success("✅ Evaluation saved to history!")
                            
                            st.success("✅ Evaluation complete!")
                        else:
                            st.session_state.evaluation_report = f"❌ **Error:** {result}"
                    
                    st.rerun()

            # Auto-refresh for timer
            if timer_active and not st.session_state.essay_submitted:
                time.sleep(1)
                st.rerun()
                
        elif st.session_state.essay_submitted:
            st.success("✅ Essay submitted! Check your evaluation report below.")
            
        else:
            st.info("Complete the setup on the left and click 'Start Timed Writing Practice' to begin.")

    st.divider()

    # Display Report
    st.subheader("3. Evaluation Report")
    
    if st.session_state.evaluation_report:
        if st.session_state.evaluation_report.startswith("❌"):
            st.error(st.session_state.evaluation_report)
        else:
            # Show comparison if there's history
            if st.session_state.current_question_id:
                history = load_evaluation_history(st.session_state.current_question_id)
                if history:
                    st.info(f"📊 **Attempt #{len(history)}** for this question. "
                           f"[View previous attempts in the sidebar]")
            
            st.markdown(st.session_state.evaluation_report)
        
        # Action buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Start New Practice", type="secondary"):
                reset_session()
        
        with col2:
            if st.session_state.current_question_id:
                if st.button("View History", type="secondary"):
                    show_question_history(st.session_state.current_question_id)
    else:
        st.info("Your feedback report will appear here after you submit your essay.")

def start_session():
    """Start a new writing session."""
    st.session_state.timer_start = time.time()
    st.session_state.time_remaining = None
    st.session_state.evaluation_report = ""
    st.session_state.essay_submitted = False
    st.session_state.last_timer_update = None
    st.rerun()

def reset_session():
    """Reset session for a new practice."""
    keys_to_reset = [
        'timer_start', 'time_remaining', 'evaluation_report', 
        'essay_submitted', 'last_timer_update', 'uploaded_image',
        'current_question_id', 'save_evaluation', 'current_essay_text',
        'current_word_count', 'show_history', 'prompt_text',
        'loaded_image_base64', 'loaded_image_name', 'question_just_loaded'
    ]
    for key in keys_to_reset:
        if key in ['timer_start', 'time_remaining', 'last_timer_update', 
                   'uploaded_image', 'current_question_id', 
                   'loaded_image_base64', 'loaded_image_name']:
            st.session_state[key] = None
        elif key in ['evaluation_report', 'current_essay_text', 'prompt_text']:
            st.session_state[key] = ""
        elif key in ['current_word_count']:
            st.session_state[key] = 0
        elif key in ['question_just_loaded']:
            st.session_state[key] = False
        else:
            st.session_state[key] = False
    
    st.session_state.question_source = 'new'
    st.rerun()

if __name__ == "__main__":
    main()
