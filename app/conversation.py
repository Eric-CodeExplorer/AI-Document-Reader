from openai import OpenAI

class Conversation():

    def __init__(self,client,assistant) -> None:
        self.client = client
        self.assistant = assistant
        self.vector_store = client.beta.vector_stores.create(name="Documents")
        self.thread = client.beta.threads.create()
    
    
    def upload(self,files:list[str]) -> None:
        file_streams = [open(path, "rb") for path in files]
        file_batch = self.client.beta.vector_stores.file_batches.upload_and_poll(
            vector_store_id= self.vector_store.id, 
            files= file_streams
        )

        print(f"file_batch.status:{file_batch.status}")
        print(f"file_batch.file_counts:{file_batch.file_counts}")

        # Update the assistant to use the new Vector Store
        self.client.beta.assistants.update(
            assistant_id= self.assistant.id,
            tool_resources={"file_search": {"vector_store_ids": [self.vector_store.id]}},
        )
    

    def talk(self,input_msg:str=None):
        if input_msg is None:
            input_msg = "Briefly summarize the document by listing the main topic and all important points."
        
        # Create a new message instance for user's input and add it to the thread
        self.client.beta.threads.messages.create(
            self.thread.id,
            role="user",
            content=input_msg,
        )

        # Create a run
        run = self.client.beta.threads.runs.create_and_poll(
            thread_id= self.thread.id, 
            assistant_id= self.assistant.id
        )

        # print status and result
        while(run.status != "completed"):
            print(run.status)
        
        messages = list(self.client.beta.threads.messages.list(
            thread_id= self.thread.id
        ))
        output = messages[0].content[0].text.value
        print("Assistant > ", end="\t")
        print(output)
        return output