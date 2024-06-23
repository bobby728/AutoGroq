
import datetime
import importlib
import os
import re
import sqlite3
import streamlit as st
import uuid

from configs.config import FRAMEWORK_DB_PATH
from models.tool_base_model import ToolBaseModel
from prompts import get_generate_tool_prompt
from utils.api_utils import get_api_key
from utils.db_utils import sql_to_db
from utils.file_utils import regenerate_zip_files
from utils.ui_utils import get_llm_provider


def create_tool_data(python_code):
    # Extract the function name from the Python code
    function_name_match = re.search(r"def\s+(\w+)\(", python_code)
    if function_name_match:
        function_name = function_name_match.group(1)    
    else:
        function_name = "unnamed_function"

    # Extract the tool description from the docstring
    docstring_match = re.search(r'"""(.*?)"""', python_code, re.DOTALL)
    if docstring_match:
        tool_description = docstring_match.group(1).strip()
    else:
        tool_description = "No description available"

    # Get the current timestamp
    current_timestamp = datetime.datetime.now().isoformat()

    # Update st.session_state.tool_model with the tool data
    st.session_state.tool_model.name = function_name
    st.session_state.tool_model.description = tool_description
    st.session_state.tool_model.title = function_name
    st.session_state.tool_model.file_name = f"{function_name}.py"
    st.session_state.tool_model.content = python_code
    st.session_state.tool_model.user_id = "default"
    st.session_state.tool_model.timestamp = current_timestamp


def export_tool_as_skill(tool_name: str, edited_skill: str):
    print(f"Exporting skill '{tool_name}'...")
    try:
        create_tool_data(edited_skill)
        print(f"Skill data: {st.session_state.tool_model.dict()}")  # Use dict() to get the dictionary representation
        skill_tuple = (
            str(uuid.uuid4()),  # Generate a unique ID for the skill
            'default',  # Set the user ID to 'default'
            datetime.datetime.now().isoformat(),
            edited_skill,
            st.session_state.tool_model.title,
            st.session_state.tool_model.file_name
        )
        print(f"Inserting skill data: {skill_tuple}")
        sql = "INSERT INTO skills (id, user_id, timestamp, content, title, file_name) VALUES (?, ?, ?, ?, ?, ?)"
        sql_to_db(sql, skill_tuple)
        st.success(f"Skill '{tool_name}' exported tool successfully!")
        st.experimental_rerun()
    except sqlite3.Error as e:
        st.error(f"Error exporting skill: {str(e)}")
        print(f"Error exporting skill: {str(e)}")


def generate_tool(rephrased_tool_request):  
    temperature_value = st.session_state.get('temperature', 0.1)
    max_tokens_value = st.session_state.get('max_tokens', 100)
    top_p_value = st.session_state.get('top_p', 1)
    llm_request_data = {
        "model": st.session_state.model,
        "temperature": st.session_state.temperature,
        "max_tokens": max_tokens_value,
        "top_p": top_p_value,
        "stop": "TERMINATE",
        "messages": [
            {
                "role": "user",
                "content": get_generate_tool_prompt(rephrased_tool_request)
            }
        ]
    }
    api_key = get_api_key()
    llm_provider = get_llm_provider(api_key=api_key)
    response = llm_provider.send_request(llm_request_data)
    if response.status_code == 200:
        response_data = llm_provider.process_response(response)
        print(f"Response data: {response_data}")
        if "choices" in response_data and response_data["choices"]:
            proposed_tool = response_data["choices"][0]["message"]["content"].strip()
            match = re.search(r"def\s+(\w+)\(", proposed_tool)
            if match:
                tool_name = match.group(1)
                
                # Update the st.session_state.tool_model with the proposed tool data
                create_tool_data(proposed_tool)
                
                return proposed_tool, tool_name
            else:
                print("Error: Failed to extract tool name from the proposed tool.")
                return None, None
    return None, None


def extract_tool_description(proposed_tool):
    docstring_match = re.search(r'"""(.*?)"""', proposed_tool, re.DOTALL)
    if docstring_match:
        return docstring_match.group(1).strip()
    else:
        return "No description available"


def load_tool_functions():
    # Get the parent directory of the current script
    parent_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Define the path to the 'tools' folder in the parent directory
    tools_folder_path = os.path.join(parent_directory, 'tools')

    # List all files in the 'tools' folder
    tool_files = [f for f in os.listdir(tools_folder_path) if f.endswith('.py')]

    tool_functions = {}
    for tool_file in tool_files:
        tool_name = os.path.splitext(tool_file)[0]
        tool_module = importlib.import_module(f"tools.{tool_name}")
        if hasattr(tool_module, tool_name):
            tool_functions[tool_name] = getattr(tool_module, tool_name)

    st.session_state.tool_functions = tool_functions


def populate_tool_models():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tool_folder = os.path.join(project_root, "tools")
    tool_files = [f for f in os.listdir(tool_folder) if f.endswith(".py")]

    tool_models = []
    for tool_file in tool_files:
        tool_name = os.path.splitext(tool_file)[0]
        tool_file_path = os.path.join(tool_folder, tool_file)
        with open(tool_file_path, 'r') as file:
            tool_data = file.read()
            create_tool_data(tool_data)
            tool_model = ToolBaseModel(
                name=st.session_state.tool_model.name,
                description=st.session_state.tool_model.description,
                title=st.session_state.tool_model.title,
                file_name=st.session_state.tool_model.file_name,
                content=st.session_state.tool_model.content,
                id=len(tool_models) + 1,
                created_at=datetime.datetime.now().isoformat(),
                updated_at=datetime.datetime.now().isoformat(),
                user_id=st.session_state.tool_model.user_id,
                secrets=st.session_state.tool_model.secrets,
                libraries=st.session_state.tool_model.libraries,
                timestamp=st.session_state.tool_model.timestamp
            )
            tool_models.append(tool_model)

    st.session_state.tool_models = tool_models
    st.session_state.project_model.tools = tool_models
    

def process_tool_request():
    if st.session_state.tool_request and not st.session_state.get('tool_processed', False):
        tool_request = st.session_state.tool_request
        parent_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        tool_folder = os.path.join(parent_directory, "tools")
        print(f"Tool Request: {tool_request}")
        rephrased_tool_request = rephrase_tool(tool_request)
        if rephrased_tool_request:
            print(f"Generating proposed tool...")
            proposed_tool, tool_name = generate_tool(rephrased_tool_request)  # Unpack the tuple
            print(f"Proposed tool: {proposed_tool}")
            if proposed_tool:
                match = re.search(r"def\s+(\w+(?:_\w+)*)\(", proposed_tool)  # Updated regex pattern
                print(f"Match: {match}")
                if match:
                    tool_name = match.group(1)
                    st.write(f"Proposed tool: {tool_name}")
                    st.code(proposed_tool)

                    with st.form(key=f"export_form_{tool_name}"):
                        submit_export = st.form_submit_button("Export/Write")
                        if submit_export:
                            print(f"Exporting tool {tool_name}")
                            export_tool_as_skill(tool_name, proposed_tool)
                            st.success(f"tool {tool_name} exported to Autogen successfully!")
                            # Clear the tool_request input and hide the input field
                            st.session_state.show_tool_input = False
                            st.session_state.tool_request = ""
                            # Clear the 'proposed_tool' and 'tool_name' from the session state
                            st.session_state.proposed_tool = None
                            st.session_state.tool_name = None
                            st.session_state.tool_processed = True  # Set the flag to indicate processing is complete
                            st.experimental_rerun()
                            
                    with st.form(key=f"discard_form_{tool_name}"):
                        submit_discard = st.form_submit_button("Clear")
                        if submit_discard:
                            st.warning("tool discarded.")
                            # Clear the tool_request input and hide the input field
                            st.session_state.show_tool_input = False
                            st.session_state.tool_request = ""
                            # Clear the 'proposed_tool' and 'tool_name' from the session state
                            st.session_state.proposed_tool = None
                            st.session_state.tool_name = None
                            st.session_state.tool_processed = True  # Set the flag to indicate processing is complete
                            st.experimental_rerun()
                else:
                    st.error("Failed to extract tool name from the proposed tool.")
            else:
                st.error("No proposed tool generated.")


def rephrase_tool(tool_request):
    print("Debug: Rephrasing tool: ", tool_request)
    temperature_value = st.session_state.get('temperature', 0.1)
    llm_request_data = {
        "model": st.session_state.model,
        "temperature": st.session_state.temperature,
        "max_tokens": st.session_state.max_tokens,
        "top_p": 1,
        "stop": "TERMINATE",
        "messages": [
            {
                "role": "user",
                "content": f"""
                Act as a professional tool creator and rephrase the following tool request into an optimized prompt:

                tool request: "{tool_request}"

                Rephrased:
                """
            }
        ]
    }
    api_key = get_api_key()
    llm_provider = get_llm_provider(api_key=api_key)
    response = llm_provider.send_request(llm_request_data)
    if response.status_code == 200:
        response_data = llm_provider.process_response(response)
        if "choices" in response_data and response_data["choices"]:
            rephrased = response_data["choices"][0]["message"]["content"].strip()
            print(f"Debug: Rephrased tool: {rephrased}")
            return rephrased
    return None                


def save_tool(tool_name, edited_tool):
    with open(f"{tool_name}.py", "w") as f:
        f.write(edited_tool)
    st.success(f"tool {tool_name} saved successfully!")


def show_tools():
    with st.expander("Tools"):
        selected_tools = []
        select_all = st.checkbox("Select All", key="select_all_tools")
        for idx, tool_model in enumerate(st.session_state.tool_models):
            tool_name = tool_model.name
            if select_all:
                tool_checkbox = st.checkbox(f"Add {tool_name} tool to all agents", value=True, key=f"tool_{tool_name}_{idx}")
            else:
                tool_checkbox = st.checkbox(f"Add {tool_name} tool to all agents", value=False, key=f"tool_{tool_name}_{idx}")
            if tool_checkbox:
                selected_tools.append(tool_name)

        if select_all:
            st.session_state.selected_tools = [tool_model.name for tool_model in st.session_state.tool_models]
        else:
            st.session_state.selected_tools = selected_tools

        # Update the 'Tools' property of each agent with the selected tools
        for agent in st.session_state.agents:
            agent['tools'] = [tool_model.name for tool_model in st.session_state.tool_models if tool_model.name in st.session_state.selected_tools]

        regenerate_zip_files()

        if st.button("Add tool", key="add_tool_button"):
            st.session_state.show_tool_input = True
            st.session_state.tool_request = ""
            st.session_state.tool_processed = False 

        if st.session_state.get('show_tool_input'):
            tool_request = st.text_input("Need a new tool? Describe what it should do:", key="tool_request_input")
            if tool_request:
                st.session_state.tool_request = tool_request  # Store in a separate session state variable
                process_tool_request()  # Pass the tool_request to the process_tool_request function

        if selected_tools or 'proposed_tool' in st.session_state:
            if st.button("Attempt to Export tool to Autogen (experimental)", key=f"export_button_{st.session_state.tool_name}"):
                tool_name = st.session_state.tool_name
                proposed_tool = st.session_state.proposed_tool
                print(f"Exporting tool {tool_name} to Autogen")
                export_tool_as_skill(tool_name, proposed_tool)
                st.success(f"tool {tool_name} exported to Autogen successfully!")
                # Clear the tool_request input and hide the input field
                st.session_state.show_tool_input = False
                st.session_state.tool_request = ""
                st.experimental_rerun()