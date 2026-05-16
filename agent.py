from openai import AsyncOpenAI
from dotenv import load_dotenv
import os
import json
import asyncio
from tools.base import BASH_TOOL, run_bash

load_dotenv()

thinking = os.getenv("thinking", "disabled")

client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE_URL")
)

class MXCC:
    def __init__(self, client):
        self.client = client
        self.system_prompt = f"You are a helpful agent at {os.getcwd()}. Use bash to solve tasks. Act, don't explain."  
        self.history = [{"role": "system", "content": self.system_prompt}]
        self.main_model = 'deepseek-v4-pro'
        self.sub_mmodel = 'deepseek-v4-flash'

    def get_base_tools(self):
        return [BASH_TOOL]

    async def agent_loop(self, query):
        # 1.添加用户输入到上下文中
        self.history.append({'role': 'user', 'content': query})

        # 2.添加工具到上下文中
        all_tools = self.get_base_tools()

        # 3.调用模型，获取回复
        response = await self.client.chat.completions.create(
            model=self.sub_mmodel,
            messages=self.history,
            stream=False,
            extra_body={"thinking": {"type": thinking}},
            tools=all_tools,
            tool_choice="auto"
        )
        # print(response)

        # 4.是否思考
        if thinking == "enabled":
            reasoning_content = response.choices[0].message.reasoning_content
            # print("Reasoning Content:", reasoning_content)
        
        # 5.1.工具调用
        if response.choices[0].message.tool_calls:
            self.history.append(response.choices[0].message.model_dump())

            tool_calls = response.choices[0].message.tool_calls
            for tool_call in tool_calls:
                name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                # print(f"工具调用: {name} with arguments {args}")
                if name == "bash":
                    command = args.get("command")
                    tool_result = run_bash(command)
                    self.history.append({
                        'role': 'tool', 
                        'content': tool_result,
                        'name': name, 
                        "tool_call_id": tool_call.id,
                    })

            second_response = await self.client.chat.completions.create(
                model=self.sub_mmodel,
                messages=self.history,
                stream=False,
                extra_body={"thinking": {"type": thinking}},
            )
            final_content = second_response.choices[0].message.content
            self.history.append({
                "role": "assistant",
                "content": final_content
            })
        # 5.2.正常回复
        else:
            content = response.choices[0].message.content
            self.history.append({'role': 'assistant', 'content': content})
            
        
async def main():
    agent = MXCC(client)

    while True:

        query = input("用户:")
        if query.strip().lower() in ('exit', 'q', ''):
            break
        await agent.agent_loop(query)

        if agent.history[-1]['role'] == 'assistant' and agent.history[-1]['content'].strip():
             print("助手:", agent.history[-1]['content'])
        
if __name__ == "__main__":
    
    asyncio.run(main())