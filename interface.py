import streamlit as st
from pandas import DataFrame
from get_questions import get_question
import random
import time
from sentence_transformers import SentenceTransformer, util
import re

# Initialize the model (this will be cached by Streamlit)
@st.cache_resource
def load_model():
    return SentenceTransformer('all-MiniLM-L6-v2')  # Small, fast model good for semantic similarity

def clean_answer(answer):
    # Remove content within square brackets that starts with 'prompt on'
    answer = re.sub(r'\[.*?prompt on.*?\]', '', answer)
    # Extract all alternatives within square brackets
    alternatives = re.findall(r'\[(.*?)\]', answer)
    # Split alternatives by 'or' and clean
    if alternatives:
        alt_list = []
        for alt in alternatives:
            alt_list.extend([a.strip() for a in alt.split('or')])
        # Remove the bracketed content from the main answer
        main_answer = re.sub(r'\[.*?\]', '', answer).strip()
        return [main_answer] + alt_list
    return [answer]

# Function to check answer similarity
def check_answer_similarity(user_answer, correct_answer, threshold=0.7):
    if not user_answer or not correct_answer:
        return False
        
    user_answer = user_answer.lower().strip()
    # Get all possible correct answers
    correct_variants = clean_answer(correct_answer)
    
    # First check for exact matches (case insensitive)
    for variant in correct_variants:
        if user_answer == variant.lower().strip():
            return True
            
    # Then check semantic similarity
    model = load_model()
    user_embedding = model.encode(user_answer, convert_to_tensor=True)
    
    # Check similarity with each variant
    for variant in correct_variants:
        variant = variant.lower().strip()
        correct_embedding = model.encode(variant, convert_to_tensor=True)
        similarity = float(util.pytorch_cos_sim(user_embedding, correct_embedding)[0][0])
        if similarity >= threshold:
            return True
            
    return False

# Custom CSS for vertical alignment and answer colors
st.markdown("""
    <style>
    div.row-widget.stButton > button {
        margin-top: 25px;
        height: 45px;
    }
    .question-text {
        font-size: 1.2em;
        line-height: 1.6;
    }
    .correct-answer {
        color: #28a745;
        padding: 0.75rem 1.25rem;
        margin-bottom: 1rem;
        border: 1px solid #28a745;
        border-radius: 0.25rem;
        background-color: #d4edda;
    }
    .incorrect-answer {
        color: #dc3545;
        padding: 0.75rem 1.25rem;
        margin-bottom: 1rem;
        border: 1px solid #dc3545;
        border-radius: 0.25rem;
        background-color: #f8d7da;
    }
    </style>
""", unsafe_allow_html=True)

st.title('Quick Packet Query')

# Add help text for comma-separated queries
st.text_input(
    "Your query (comma-separated terms, e.g., 'world war, france, napoleon')", 
    key="query",
    help="Enter multiple search terms separated by commas. Questions matching ANY term will be included."
)

st.toggle("Check Answer Line", key="check_answer_line", value=True)
st.toggle("Check Question Line", key="check_question_line")

# Create two columns for the sliders
col1, col2 = st.columns(2)

with col1:
    st.select_slider(
        "Select a range of difficulties",
        options=range(11),
        value=(0, 10),
        key="difficulty_range"
    )

with col2:
    reading_speed = st.slider(
        "Reading Speed",
        min_value=0.5,
        max_value=2.0,
        value=1.0,
        step=0.1,
        format="%.1fx"
    )

# Initialize session state variables
if 'query' not in st.session_state:
    st.session_state['query'] = None
    
if 'current_question' not in st.session_state:
    st.session_state['current_question'] = None
    
if 'current_answer' not in st.session_state:
    st.session_state['current_answer'] = None
    
if 'show_answer' not in st.session_state:
    st.session_state['show_answer'] = False
    
if 'key_counter' not in st.session_state:
    st.session_state['key_counter'] = 0
    
if 'word_index' not in st.session_state:
    st.session_state['word_index'] = 0
    
if 'last_update_time' not in st.session_state:
    st.session_state['last_update_time'] = time.time()
    
if 'has_buzzed' not in st.session_state:
    st.session_state['has_buzzed'] = False

if 'show_full_question' not in st.session_state:
    st.session_state['show_full_question'] = False

if 'user_answer' not in st.session_state:
    st.session_state['user_answer'] = ""

if 'questions' not in st.session_state:
    st.session_state['questions'] = None

if 'last_query' not in st.session_state:
    st.session_state['last_query'] = None

# Create feedback container at the top level
feedback_container = st.empty()
st.session_state['feedback_container'] = feedback_container

def next_question():
    if 'questions' in st.session_state and st.session_state.questions:
        st.session_state.key_counter += 1
        random_idx = random.randint(0, len(st.session_state.questions) - 1)
        st.session_state.current_question = st.session_state.questions[random_idx][0]
        st.session_state.current_answer = st.session_state.questions[random_idx][1]
        st.session_state.show_answer = False  # Reset show_answer state
        st.session_state.show_full_question = False
        st.session_state.word_index = 0
        st.session_state.last_update_time = time.time()
        st.session_state.has_buzzed = False
        st.session_state.user_answer = ""  # Reset user answer
        st.rerun()  # Force a rerun to clear the UI

def handle_buzz():
    st.session_state.has_buzzed = True
    st.session_state.show_answer = False
    st.session_state.show_full_question = False
    st.session_state.user_answer = ""  # Reset user answer

def on_answer_submit():
    st.session_state.show_answer = True
    st.session_state.show_full_question = True
    
# Get query parameters
query = st.session_state.get('query', '')
check_answer = st.session_state.get('check_answer_line', True)
check_question = st.session_state.get('check_question_line', False)
min_difficulty = st.session_state.get('difficulty_range', (1, 10))[0]
max_difficulty = st.session_state.get('difficulty_range', (1, 10))[1]

# Only fetch new questions if query changes or questions not yet fetched
if query and (st.session_state.questions is None or query != st.session_state.get('last_query', '')):
    st.session_state.questions = get_question(
        query,
        check_answer,
        check_question,
        min_difficulty,
        max_difficulty,
        outputs=['Question', 'Answer', 'Difficulty']
    )
    st.session_state.last_query = query

# Display questions if available
if st.session_state.questions is not None and len(st.session_state.questions) > 0:
    if not st.session_state.current_question:
        next_question()
                
    # Create columns for the buzz button and next question button
    col1, col2 = st.columns([3, 1])
    
    with col1:
        answer_container = st.empty()
        if not st.session_state.has_buzzed:
            answer_container.button(
                "Buzz!", 
                key=f"buzz_{st.session_state.key_counter}", 
                on_click=handle_buzz,
                use_container_width=True
            )
        else:
            user_answer = answer_container.text_input(
                "Your answer:", 
                key=f"answer_{st.session_state.key_counter}", 
                on_change=on_answer_submit
            )
            st.session_state.user_answer = user_answer  # Store the user's answer
                
    with col2:
        if st.button("Next Question", key=f"next_{st.session_state.key_counter}", use_container_width=True):
            # Clear feedback before proceeding
            feedback_container.empty()
            st.session_state.show_answer = False
            next_question()
    
    st.subheader("Question:")
    
    # Word by word display
    if st.session_state.current_question:
        words = st.session_state.current_question.split()
        
        # Only update word_index if not buzzed
        if not st.session_state.has_buzzed:
            current_time = time.time()
            
            # Get the current word's length for dynamic delay
            if st.session_state.word_index < len(words):
                current_word = words[st.session_state.word_index - 1] if st.session_state.word_index > 0 else ""
                # Adjust delay based on reading speed
                base_delay = len(current_word) * 0.03 if current_word else 0.03  # Base delay
                delay = base_delay / reading_speed  # Adjust delay by reading speed
                
                if current_time - st.session_state.last_update_time >= delay:
                    st.session_state.word_index += 1
                    st.session_state.last_update_time = current_time
        
        # Display either partial or full question
        if st.session_state.show_full_question:
            displayed_text = st.session_state.current_question
        else:
            displayed_text = " ".join(words[:st.session_state.word_index])
        st.markdown(f'<p class="question-text">{displayed_text}</p>', unsafe_allow_html=True)
        
        # Only rerun if not buzzed and still have words to show
        if st.session_state.word_index < len(words) and not st.session_state.has_buzzed:
            current_word = words[st.session_state.word_index - 1] if st.session_state.word_index > 0 else ""
            base_sleep_delay = len(current_word) * 0.02 if current_word else 0.02
            sleep_delay = base_sleep_delay / reading_speed  # Adjust sleep delay by reading speed
            time.sleep(sleep_delay)
            st.rerun()
    
    # Use the persistent feedback container for answer feedback
    if st.session_state.show_answer:
        # Check if the answer is semantically correct
        is_correct = check_answer_similarity(st.session_state.user_answer, st.session_state.current_answer)
        if is_correct:
            feedback_container.markdown(f'<div class="correct-answer">{st.session_state.current_answer}</div>', unsafe_allow_html=True)
        else:
            feedback_container.markdown(f'<div class="incorrect-answer">{st.session_state.current_answer}</div>', unsafe_allow_html=True)
else:
    st.subheader(f'Nothing yet matches your query.')