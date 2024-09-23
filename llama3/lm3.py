import os
import requests
import re
import json
from openai import OpenAI
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer, util
import torch
from serpapi import GoogleSearch #pip install google-search-results
from bs4 import BeautifulSoup

load_dotenv()
mailgun_api_key = "your_mailgun_api_key"
serpapi_api_key = 'your_serpapi_api_key'
client = OpenAI(base_url='http://localhost:11434/v1', api_key='llama3:8b')#ollama服务默认端口
model = SentenceTransformer("your_path")#手动下载
#https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/tree/main

# 设置颜色
PINK = '\033[95m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
NEON_GREEN = '\033[92m'
RESET_COLOR = '\033[0m'

def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()

def get_relevant_context(user_input, vault_embeddings, vault_content, model, top_k=7): #adjust your top_k here
    if vault_embeddings.nelement() == 0:
        return []
    input_embedding = model.encode([user_input])
    cos_scores = util.cos_sim(input_embedding, vault_embeddings)[0]
    top_k = min(top_k, len(cos_scores))
    top_indices = torch.topk(cos_scores, k=top_k)[1].tolist()
    relevant_context = [vault_content[idx].strip() for idx in top_indices]
    return relevant_context
    
def write_to_notes(note_content):
    with open("notes.txt", "a", encoding="utf-8") as notes_file:
        notes_file.write(note_content + "\n")
    print(CYAN + "Note written to notes.txt" + RESET_COLOR)



def send_email(recipient, subject, body, attachment=None):
    data = {
        "from": "xxx@gmail.com", #set your from mail address here
        "to": recipient,
        "subject": subject,
        "text": body,
    }
    files = {'attachment': (os.path.basename(attachment), open(attachment, 'rb'))} if attachment else None
    response = requests.post(
        "https://api.mailgun.net/v3/sandbox000e649976434b279945a954878ef16a.mailgun.org/messages",
        auth=("api", mailgun_api_key),
        data=data,
        files=files
    )
    response.raise_for_status()
    print(CYAN + "Email sent successfully." + RESET_COLOR)

##发邮件技能,我这个用语聚AI配置的,也可以自己看各个邮箱API配置
def send_email2(recipient, subject, body, attachment=None):
    """
    Send email content to specified email address.

    Parameters:
    input_text (str): The specific content of the email.

    Returns:
    str: Is the program executed successfully.
    """
    body = '邮件收件人地址：'+recipient + '，邮件标题：'+subject+',邮件内容：'+body
    print(body)
    try:#https://chat.jijyun.cn/v1/openapi/exposed/%7Baction_id%7D/execute/
        url = "https://chat.jijyun.cn/v1/openapi/exposed/101544_1524_jjyibotID_afb0ac23709645cbae2edc7d293b4165/execute/?apiKey=McqK2D0aWAeuvzTxxt1765xn1705900572"

        payload = json.dumps({
            "instructions": body,
            "preview_only": False
        })
        headers = {
            'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'Host': 'chat.jijyun.cn',
            'Connection': 'keep-alive',
            'Cookie': 'acw_tc=0a099d3a17059056833806961eefbe4e0508c1110fd2e13a5467422f347a16'
        }

        response = requests.request("POST", url,headers=headers, data=payload)
        response.raise_for_status()
        print(CYAN + "Email sent successfully." + RESET_COLOR)
        #print(response.text)


    except Exception as e:
    # Return the error message in case of an exception
        print(e)
        return f"An error occurred: {str(e)}"

#serpapi,需要注册下,但是我测试中文搜索不咋地
def search_google(query):
    params = {
        "q": query,
        "hl": "en",
        "gl": "us",
        "api_key": serpapi_api_key,
        "num": 3  # Retrieve the top 3 search results
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    organic_results = results.get("organic_results", [])
    if organic_results:
        urls = []
        for result in organic_results[:3]:  # Process the top 3 results
            url = result["link"]
            urls.append(url)
            
            # Scrape the content of the URL and add it to the vault
            response = requests.get(url)
            soup = BeautifulSoup(response.content, "html.parser")
            text = soup.get_text()
            
            # Normalize whitespace and clean up text
            text = re.sub(r'\s+', ' ', text).strip()
            
            # Split text into chunks by sentences, respecting a maximum chunk size
            sentences = re.split(r'(?<=[.!?]) +', text)
            chunks = []
            current_chunk = ""
            for sentence in sentences:
                if len(current_chunk) + len(sentence) + 1 < 1000: #adjust chunk length here
                    current_chunk += (sentence + " ").strip()
                else:
                    chunks.append(current_chunk)
                    current_chunk = sentence + " "
            if current_chunk:
                chunks.append(current_chunk)
            
            with open("vault.txt", "a", encoding="utf-8") as vault_file:
                for chunk in chunks:
                    vault_file.write(chunk.strip() + "\n\n")
        
        return "\n".join(urls)
    else:
        return "No relevant search results found."

def check_context(user_message):
    vault_content = []
    if os.path.exists("vault.txt"):
        with open("vault.txt", "r", encoding='utf-8') as vault_file:
            vault_content = vault_file.readlines()
    vault_embeddings = model.encode(vault_content) if vault_content else []
    vault_embeddings_tensor = torch.tensor(vault_embeddings)
    relevant_context = get_relevant_context(user_message, vault_embeddings_tensor, vault_content, model)
    if relevant_context:
        context_str = "\n".join(relevant_context)
        result = f"Relevant context:\n{context_str}\n\nUser's question: {user_message}"
        result2 = chat([{"role": "user", "content": result}])  # Pass a list of messages
        conversation_history.append({"role": "system", "content": result2})
        return result2
    else:
        result = f"No relevant context found.\n\nUser's question: {user_message}"
        result2 = chat([{"role": "user", "content": result}])  # Pass a list of messages
        conversation_history.append({"role": "system", "content": result2})
        return result2
#参考：https://platform.openai.com/docs/guides/function-calling
def convert_to_openai_function(func):
    return {
        "name": func.__name__,
        "description": func.__doc__,
        "parameters": {
            "type": "object",
            "properties": {
                "recipient": {"type": "string", "description": "Email address of the recipient"},
                "subject": {"type": "string", "description": "Subject of the email"},
                "body": {"type": "string", "description": "Body of the email"},
                "attachment": {"type": "string", "description": "Path to an attachment"},
                "query": {"type": "string", "description": "Query to search on Google"},
                "user_message": {"type": "string", "description": "Users provided message to compare to the context"},
                "note_content": {"type": "string", "description": "Content to be written to the notes.txt file"},
            },
            "required": ["recipient", "subject", "body"],
        },
    }

functions = [
    convert_to_openai_function(send_email2),
    convert_to_openai_function(search_google),
    convert_to_openai_function(check_context),
    convert_to_openai_function(write_to_notes)
]

def parse_function_call(input_str):
    match = re.search(r'<functioncall>(.*?)</functioncall>', input_str, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            return None
    return None

def chat(messages):
    system_message = f"""
    You are an AI Agent that is an expert in following instructions. You will engage in conversation and provide relevant information to the best of your knowledge. You have a set of functions you can use.
    You have access to these functions:
    {json.dumps(functions, indent=2)}
    
    If the user's input contains "send a mail" or similar, extract the necessary information (recipient, subject, body) from the input and generate a function call in the following format:
    <functioncall>{{"name": "send_email2","arguments": {{"recipient": "user_provided_email@example.com","subject": "User-provided subject","body": "User-provided email body"}}}}</functioncall>
    Make sure to replace the placeholders (user_provided_email@example.com, User-provided subject, User-provided email body) with the actual information provided by the user, and ensure that the entire function call is on a single line.
    After generating the function call, execute the function to send the email and inform the user that the email has been sent.
    
    Example: send a mail with information to users provided recipient
    
    If the user's input contains "check context" or similar, followed by a message or question, generate a function call in the following format:
    <functioncall>{{"name": "check_context","arguments": {{"user_message": "user_provided_message"}}}}</functioncall>
    Replace "user_provided_message" with the actual message or question provided by the user, and ensure that the entire function call is on a single line.
    After generating the function call, execute the function to retrieve the relevant context and include it in your response to answer the user's question.
    
    Example: user: check context user message
    
    If user's input contains "search google" or similar and some sort of questions or query, generate a function call in the following format:
    <functioncall>{{"name": "search_google","arguments": {{"query": "user_provided_query"}}}}</functioncall>
    Replace "user_provided_query" with the actual query provided by the user, and ensure that the entire function call is on a single line.
    After generating the function call, execute the function to search Google, scrape the content of the top 3 search result URLs, add them to the vault in chunks of 1000 characters, and return the URLs.
    
    Example: user: search google user query / question

    If the user's input contains "write note" or similar, followed by some content, generate a function call in the following format:
    <functioncall>{{"name": "write_to_notes","arguments": {{"note_content": "user_provided_note_content"}}}}</functioncall>
    Replace "user_provided_note_content" with the actual content provided by the user, and ensure that the entire function call is on a single line.
    After generating the function call, execute the function to write the content to the notes.txt file.

    Example: user: write note user note content 
 
"""
    
    messages.insert(0, {"role": "system", "content": system_message})
    response = client.chat.completions.create(model="llama3:8b", messages=messages, functions=functions, temperature=0)
    message_content = response.choices[0].message.content
    function_call = parse_function_call(message_content)
    if function_call:
        function_name = function_call["name"]
        function_arguments = function_call["arguments"]
        if function_name == "send_email2":
            send_email2(**function_arguments)
            return "Email sent successfully!"
        elif function_name == "search_google":
            search_result = search_google(**function_arguments)
            return f"Top search results:\n{search_result}\nContent added to the context."
        elif function_name == "check_context":
            vault_result = check_context(**function_arguments)
            return vault_result
        elif function_name == "write_to_notes":
            write_to_notes(**function_arguments)
            return "Note written to notes.txt"
        else:
            return f"Unknown function: {function_name}"
    return message_content

conversation_history = []
while True:
    user_input = input(NEON_GREEN + "User: " + RESET_COLOR)
    conversation_history = conversation_history[-1:] #change this if you want full history
    conversation_history.append({"role": "user", "content": user_input})
    response = chat(conversation_history)
    conversation_history.append({"role": "assistant", "content": response})
    print(YELLOW + "Assistant:" + RESET_COLOR, response)
