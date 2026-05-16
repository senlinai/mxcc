from openai import OpenAI
from dotenv import load_dotenv
import os
import json
from tools.base import BASH_TOOL, run_bash

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
        extra_body={"thinking": {"type": thinking}},
        tools=[BASH_TOOL],
        tool_choice="auto"
    )
    # print(response)

    # 是否思考
    if thinking == "enabled":
        reasoning_content = response.choices[0].message.reasoning_content
        # print("Reasoning Content:", reasoning_content)
    
    # 工具调用
    if response.choices[0].message.tool_calls:
        history.append(response.choices[0].message.model_dump())

        tool_calls = response.choices[0].message.tool_calls
        for tool_call in tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            # print(f"工具调用: {name} with arguments {args}")
            if name == "bash":
                command = args.get("command")
                tool_result = run_bash(command)
                history.append({
                    'role': 'tool', 
                    'content': tool_result,
                    'name': name, 
                    "tool_call_id": tool_call.id,
                })

        second_response = client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=history,
            stream=False,
            extra_body={"thinking": {"type": thinking}},
        )
        final_content = second_response.choices[0].message.content
        history.append({
            "role": "assistant",
            "content": final_content
        })
        print("助手:", final_content)
    # 正常回复
    else:
        content = response.choices[0].message.content
        history.append({'role': 'assistant', 'content': content})
        print("助手:", content)
        

if __name__ == "__main__":
    SYSTEM = f"You are a helpful agent at {os.getcwd()}. Use bash to solve tasks. Act, don't explain."
    
    history = [{"role": "system", "content": SYSTEM}]

    while True:

        query = input("用户:")
        if query.strip().lower() in ('exit', 'q', ''):
            break
        
        history.append({'role': 'user', 'content': query})
        agent_loop(history)
    