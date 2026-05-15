from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

thinking = os.getenv("thinking", "disabled")

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE_URL")
)

def agent_loop(history):

    response = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=history,
        stream=False,
        extra_body={"thinking": {"type": thinking}}
    )

    # 是否思考
    if thinking == "enabled":
        reasoning_content = response.choices[0].message.reasoning_content
        print("Reasoning Content:", reasoning_content)
    content = response.choices[0].message.content

    history.append({'role': 'assistant', 'content': content})
    

    


if __name__ == "__main__":

    history = [{"role": "system", "content": "You are a helpful assistant"}]

    while True:
        query = input("输入问题 (or 'exit' to q): ")
        if query.strip().lower() in ('exit', 'q', ''):
            break
        
        history.append({'role': 'user', 'content': query})
        agent_loop(history)
        print()
        print(history)
