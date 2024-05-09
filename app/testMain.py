import os
from dotenv import load_dotenv
from openai import OpenAI
from app import get_env_variable
from conversation import *


if __name__ == "__main__":
    basedir = os.path.abspath(os.path.dirname(__file__))
    upload_path = os.path.join(basedir,'documents')

    load = load_dotenv()
    model = "gpt-4-turbo"
    api_key = get_env_variable("OPENAI_API_KEY")

    client = OpenAI(api_key=api_key)
    # List of assistants with different openai model
    conv_list = []
    assistant = client.beta.assistants.create(
        name="Document Summarize Assistant",
        instructions="You are an expert at analyzing and summarizing scientific papers. Please assist the user in summarizing the document and answering any questions they may have.",
        model=model,
        tools=[{"type": "file_search"}],
    )

    # User provide a file. For testing, hard code the file name here
    filename = "file.pdf"
    file_path = os.path.join(upload_path, filename)
    # Start a new conversation

    conv = Conversation(client,assistant)
    conv.upload([file_path])
    conv.talk()
    while(True):
        user_input = input("User > ")
        if user_input == "q":
            exit(0)
        conv.talk(user_input)
        
    