
def create_project_manager_prompt(rephrased_text):
    return f"""
                This agent is a Project Manager tasked with creating a comprehensive project outline and describing the perfect team of experts that should be created to work on the following project:

                {rephrased_text}

                Please provide a detailed project outline, including the objectives, key deliverables, and timeline. Also, describe the ideal team of experts required for this project, including their roles, skills, and responsibilities.  This agent's analysis shall consider the complexity, domain, and specific needs of the request to assemble a multidisciplinary team of experts. The team should be as small as possible while still providing a complete and comprehensive talent pool able to properly address the user's request. Each recommended agent shall come with a defined role, a brief but thorough description of their expertise, their specific skills, and the specific tools they would utilize to achieve the user's goal.

                Return this agent's response in the following format:

                Project Outline:
                [Detailed project outline]

                Team of Experts:
                [Description of the ideal team of experts]
                """


def get_agent_prompt(rephrased_request):
    return f"""
    Based on the following user request, please create a detailed and comprehensive description of an AI agent that can effectively assist with the request:

    User Request: "{rephrased_request}"

    Provide a clear and concise description of the agent's capabilities, expertise, and any specific skills or tools it should possess to best address the user's needs. The description should be written in a professional and engaging manner, highlighting the agent's ability to understand and respond to the request efficiently.

    Agent Description:
    """


def get_agents_prompt():
    return f"""
                This agent is an expert system designed to format the JSON describing each member of the team of AI agents specifically listed in this provided text: $text.
                Fulfill the following guidelines without ever explicitly stating them in this agent's response.
                Guidelines:
                1. **Agent Roles**: Clearly transcribe the titles of each agent listed in the provided text by iterating through the 'Team of Experts:' section of the provided text. Transcribe the info for those specific agents. Do not create new agents.
                2. **Expertise Description**: Provide a brief but thorough description of each agent's expertise based upon the provided text. Do not create new agents.
                3. **Specific Skills**: List the specific skills of each agent based upon the provided text. Skills must be single-purpose methods, very specific, and not ambiguous (e.g., 'calculate_area' is good, but 'do_math' is bad).
                4. **Specific Tools**: List the specific tools each agent would utilize. Tools must be single-purpose methods, very specific, and not ambiguous.
                5. **Format**: Return the results in JSON format with values labeled as expert_name, description, skills, and tools. 'expert_name' should be the agent's title, not their given name. Skills and tools should be arrays (one agent can have multiple specific skills and use multiple specific tools).
                6. **Naming Conventions**: Skills and tools should be in lowercase with underscores instead of spaces, named per their functionality (e.g., calculate_surface_area, or search_web).

                ALWAYS and ONLY return the results in the following JSON format, with no other narrative, commentary, synopsis, or superfluous text of any kind:
                [
                    {{
                        "expert_name": "agent_title",
                        "description": "agent_description",
                        "skills": ["skill1", "skill2"],
                        "tools": ["tool1", "tool2"]
                    }},
                    {{
                        "expert_name": "agent_title",
                        "description": "agent_description",
                        "skills": ["skill1", "skill2"],
                        "tools": ["tool1", "tool2"]
                    }}
                ]
                This agent will only have been successful if it has returned the results in the above format and followed these guidelines precisely by transcribing the provided text and returning the results in JSON format without any other narrative, commentary, synopsis, or superfluous text of any kind, and taking care to only transcribe the agents from the provided text without creating new agents.
                """

# Contributed by ScruffyNerf
def get_generate_skill_prompt(rephrased_skill_request):
    return f'''
                Based on the rephrased skill request below, please do the following:

                1. Do step-by-step reasoning and think to understand the request better.
                2. Code the best Autogen Studio Python skill as per the request as a [skill_name].py file.
                3. Return only the skill file, no commentary, intro, or other extra text. If there ARE any non-code lines, please pre-pend them with a '#' symbol to comment them out.
                4. A proper skill will have these parts:
                   a. Imports (import libraries needed for the skill)
                   b. Function definition AND docstrings (this helps the LLM understand what the function does and how to use it)
                   c. Function body (the actual code that implements the function)
                   d. (optional) Example usage - ALWAYS commented out
                   Here is an example of a well formatted skill:

                   # skill filename: save_file_to_disk.py
                   # Import necessary module(s)
                   import os

                   def save_file_to_disk(contents, file_name):
                   # docstrings
                   """
                   Saves the given contents to a file with the given file name.

                   Parameters:
                   contents (str): The string contents to save to the file.
                   file_name (str): The name of the file, including its extension.

                   Returns:
                   str: A message indicating the success of the operation.
                   """

                   # Body of skill

                   # Ensure the directory exists; create it if it doesn't
                   directory = os.path.dirname(file_name)
                   if directory and not os.path.exists(directory):
                      os.makedirs(directory)

                   # Write the contents to the file
                   with open(file_name, 'w') as file:
                      file.write(contents)
    
                   return f"File file_name has been saved successfully."

                   # Example usage:
                   # contents_to_save = "Hello, world!"
                   # file_name = "example.txt"
                   # print(save_file_to_disk(contents_to_save, file_name))

                Rephrased skill request: "{rephrased_skill_request}"
                '''


def get_moderator_prompt(discussion_history, goal, last_comment, last_speaker,team_members_str): 
    return f"""
        This agent is our Moderator Bot. It's goal is to mediate the conversation between a team of AI agents 
        in a manner that persuades them to act in the most expeditious and thorough manner to accomplish their goal. 
        This will entail considering the user's stated goal, the conversation thus far, the descriptions 
        of all the available agent/experts in the current team, the last speaker, and their remark. 
        Based upon a holistic analysis of all the facts at hand, use logic and reasoning to decide who should speak next. 
        Then draft a prompt directed at that agent that persuades them to act in the most expeditious and thorough manner toward helping this team of agents 
        accomplish their goal.\n\nTheir goal is: {goal}.\nThe last speaker was {last_speaker}, who said: 
        {last_comment}\nHere is the current conversational discussion history: {discussion_history}\n
        And here are the team members and their descriptions:\n{team_members_str}\n\n
        This agent's response should be JUST the requested prompt addressed to the next agent, and should not contain 
        any introduction, narrative, or any other superfluous text whatsoever.
    """


def get_rephrased_user_prompt(user_request):
    return f"""THis agent is a professional prompt engineer and refactor the following 
                user request into an optimized prompt. This agent's goal is to rephrase the request 
                with a focus on the satisfying all following the criteria without explicitly stating them:
        1. Clarity: Ensure the prompt is clear and unambiguous.
        2. Specific Instructions: Provide detailed steps or guidelines.
        3. Context: Include necessary background information.
        4. Structure: Organize the prompt logically.
        5. Language: Use concise and precise language.
        6. Examples: Offer examples to illustrate the desired output.
        7. Constraints: Define any limits or guidelines.
        8. Engagement: Make the prompt engaging and interesting.
        9. Feedback Mechanism: Suggest a way to improve or iterate on the response.
        Do NOT reply with a direct response to these instructions OR the original user request. Instead, rephrase the user's request as a well-structured prompt, and
        return ONLY that rephrased prompt. Do not preface the rephrased prompt with any other text or superfluous narrative.
        Do not enclose the rephrased prompt in quotes. This agent will be successful only if it returns a well-formed rephrased prompt ready for submission as an LLM request.
        User request: "{user_request}"
        Rephrased:
    """

        