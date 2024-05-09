import os
import uuid
from flask import Flask
from flask import render_template, request, redirect, url_for, jsonify, session
from dotenv import load_dotenv
from flask_dropzone import Dropzone
from flask_executor import Executor
from conversation import *
from waitress import serve

basedir = os.path.abspath(os.path.dirname(__file__))


app = Flask(__name__)   # run program: flask --app ./app/demo.py run --debug
app.secret_key = os.urandom(24).hex()
app.config.update(
    UPLOADED_PATH= os.path.join(basedir,'documents'),   # Random secret key
    DROPZONE_ALLOWED_FILE_CUSTOM = True,
    DROPZONE_ALLOWED_FILE_TYPE = '.pdf',
    DROPZONE_MAX_FILES = 1,
    DROPZONE_DEFAULT_MESSAGE = "<img class=\"logo\" src=\"/static/svg/pdf_icon.svg\" alt=\"pdf icon\">Drop files here to upload"
    DROPZONE_MAX_FILE_SIZE = 30
)
dropzone = Dropzone(app)
executor = Executor(app)

client = None
assistant = None

# dictionary that stores all converation objects.   cid : Conversation
convs = {}
convs_files = {}

def empty_documents_folder():
    print("LOG:empty folder")
    folder_path = app.config['UPLOADED_PATH']
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")

def get_env_variable(var_name: str) -> str:
    value = os.getenv(var_name)
    if value is not None:
        return value
    else:
        print(f"{var_name} is not set.")
        exit(1)

def conv_length(cid):
    c = convs[cid]
    if c is None:
        return -1
    messages = list(c.client.beta.threads.messages.list(
            thread_id= c.thread.id
        ))
    # print("conv_length:")
    # print(messages)
    return len(messages)


def processMsgList(msgList):
    result = {"data":[],"status":"good"}
    for i in range(1,len(msgList)):
        # print(f"i = {i}")
        # print(msgList[i])
        temp = {"role":None,"content":[]}
        temp["role"] = msgList[i].role
        temp["content"].append({
            "type":"text",
            "text":{
                "value":msgList[i].content[0].text.value,
                "annotations" : []
            }
        })
        result["data"].append(temp)

    # print(result)
    return result

def getKeys():
    return list(convs.keys())


"""
    Home Page. Wait for user to upload file.
    Once file uploaded, save the file and create new Conversation instance.
    Generate a unique id and return this id to frontend
"""
@app.route("/", methods = ['POST', 'GET'])
def home():
    # print("Log: HOME")
    print(f"client:{client is None},assistant:{assistant is None}")
    if request.method == "POST":
        # print("Log: got POST")
        file = request.files.get('file')
        print(file)
        if file:
            # print("LOG: file received")
            filepath = os.path.join(app.config['UPLOADED_PATH'],file.filename)
            file.save(filepath)
            cid = str(uuid.uuid4()) # Unique conversation id
            convs[cid] = Conversation(client,assistant)
            convs_files[cid] = file.filename
            convs[cid].upload([filepath])
            executor.submit_stored(cid,process_file,cid)
            return jsonify({"cid" : cid})
            # return redirect(url_for('conversation',filename = file.filename))
        else:
            return render_template('home.html',h_list = getKeys())
    else:
        return render_template('home.html',h_list = getKeys())
       


@app.route("/conversation/<cid>", methods = ['POST','GET'])
def conversation(cid):
    # TODO: check if cid exist
    # If Get, then user is either just uploaded a new file or it's visiting an existing conversation
    if request.method == "GET":
        c = convs.get(cid)
        if c is None:
            return render_template('404.html',h_list = getKeys())
        messages = c.client.beta.threads.messages.list(
            thread_id= c.thread.id,
            order = "asc"
        )
        messages_list = list(messages)
        # print(messages_list)
        if len(messages_list) <= 1:    # User just uploaded a new document
            response = {
                "data" : [
                    {
                        "role" : "assistant",
                        "content" : [
                            {
                                "type": "text",
                                "text": {
                                    "value": "Processing...",
                                    "annotations": []
                                }
                            }
                        ]
                    }
                ],
                'status' : None
            }
            return render_template('conversation.html', h_list = getKeys() ,data=response)
        else: # Revisit existing conversation, return all history messages
            # print("====================")
            result = processMsgList(messages_list)
            # print(result)
            return render_template('conversation.html', h_list = getKeys() ,data=result)
    else:
        user_message = request.json.get('message')
        cid = request.json.get('cid')
        # print("User msg:" + user_message)
        # print("cid:" + str(cid))
        answer = convs[cid].talk(user_message)
        response = {
            "data" : [
                {
                    "role" : "assistant",
                    "content" : [
                        {
                            "type": "text",
                            "text": {
                                "value": answer,
                                "annotations": []
                            }
                        }
                    ]
                }
            ],
            'status' : None
        }
        return response


@app.route("/check_task_result", methods=['POST'])
def check_task_result():
    cid = request.json.get('cid')
    if not executor.futures.done(cid):
        return jsonify({'status' : None})
    future = executor.futures.pop(cid)
    return jsonify(future.result())
    # return jsonify({'task_result': task_result})


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html",h_list = getKeys()), 404


def process_file(cid):
    # Process the file and store the result in session
    message = convs[cid].talk()
    # print("process_file: message=" + message)
    result = {
                "data" : [
                    {
                        "role" : "assistant",
                        "content" : [
                            {
                                "type": "text",
                                "text": {
                                    "value": message,
                                    "annotations": []
                                }
                            }
                        ]
                    }
                ],
                'status' : "good"
            }
    # print("process_file: complete")
    return result


if __name__ == "__main__":
    empty_documents_folder()

    load = load_dotenv()
    model = "gpt-4-turbo"
    api_key = get_env_variable("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)
    assistant = client.beta.assistants.create(
        name="Document Summarize Assistant",
        instructions="You are an expert at analyzing and summarizing scientific papers. Please assist the user in summarizing the document and answering any questions they may have.",
        model=model,
        tools=[{"type": "file_search"}],
    )

    serve(app,host="0.0.0.0", port = 8000)