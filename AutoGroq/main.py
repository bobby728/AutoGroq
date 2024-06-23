# main.py

import streamlit as st 

from agent_management import display_agents
from utils.api_utils import get_api_key
from utils.auth_utils import display_api_key_input
from utils.session_utils import initialize_session_variables
from utils.tool_utils import load_tool_functions, populate_tool_models, show_tools
from utils.ui_utils import (
    display_goal, display_reset_and_upload_buttons, 
    display_user_request_input, handle_user_request, 
    select_model, select_provider, set_css, 
    set_temperature, show_interfaces
)

def main():
    if 'warning_placeholder' not in st.session_state:
        st.session_state.warning_placeholder = st.empty()
    st.title("AutoGroq™")

    set_css()
    initialize_session_variables()
    load_tool_functions()

    # Check for API key
    api_key = get_api_key()
    if api_key is None:
        display_api_key_input()

    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        select_provider()
    
    with col2:
        select_model()

    with col3:
        set_temperature()
        
    with st.sidebar:
        display_agents()
        if "agents" in st.session_state and st.session_state.agents:
            display_goal()
            populate_tool_models()
            show_tools()
        else:
            st.empty()  

    with st.container():
        if st.session_state.get("rephrased_request", "") == "":
            user_request = st.text_input("Enter your request:", key="user_request", value=st.session_state.get("user_request", ""), on_change=handle_user_request, args=(st.session_state,))
            display_user_request_input()
        if "agents" in st.session_state and st.session_state.agents:
            show_interfaces()
            display_reset_and_upload_buttons()

if __name__ == "__main__":
    main()