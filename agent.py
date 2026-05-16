from openai import AsyncOpenAI
from dotenv import load_dotenv
import os
import json
import asyncio
import re
from tools.base import BASE_TOOLS, run_bash, read_file, write_file, edit_file

# --- 颜色定义 (ANSI Escape Codes) ---
COLOR_USER = "\033[96m"      # 青色
COLOR_TOOL = "\033[93m"      # 黄色
COLOR_ASSISTANT = "\033[92m" # 绿色
COLOR_RESET = "\033[0m"      # 重置颜色

load_dotenv()
source = os.getenv('SOURCE', 'ALI')
thinking = os.getenv("thinking", "disabled")

client = AsyncOpenAI(
    api_key=os.getenv("ALI_OPENAI_API_KEY") if source == 'ALI' else os.getenv("DEEPSEEK_OPENAI_API_KEY"),
    base_url=os.getenv("ALI_API_BASE_URL") if source == 'ALI' else os.getenv("DEEPSEEK_API_BASE_URL")
)

class MXCC:
    def __init__(self, client):
        self.WORKDIR = os.getcwd()
        self.client = client
        self.system_prompt = f"You are a helpful agent at {self.WORKDIR}. Use bash to solve tasks. Act, don't explain."  
        self.history = [{"role": "system", "content": self.system_prompt}]
        self.main_model = os.getenv('ALI_MAIN_MODEL_NAME') if source == 'ALI' else os.getenv('DEEPSEEK_MAIN_MODEL_NAME')
        self.sub_model = os.getenv('ALI_SUB_MODEL_NAME') if source == 'ALI' else os.getenv('DEEPSEEK_SUB_MODEL_NAME')

        self.all_tools = BASE_TOOLS
        self.tool_map = {
            "bash": run_bash,
            "read_file": read_file,
            "write_file": write_file,
            "edit_file": edit_file
        }

    def clean_dsml_tags(self, text):
        if not text:
            return text
        # 修改为双竖线 \|\|，并使用 .*? 进行非贪婪匹配，以兼容跨行标签
        pattern = r'<｜｜DSML｜｜.*?>'
        cleaned = re.sub(pattern, '', text, flags=re.DOTALL)
        # 清理空行
        lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
        return '\n'.join(lines)

    async def agent_loop(self, query):
        # 1.添加用户输入到上下文中
        self.history.append({'role': 'user', 'content': query})

        # 3.调用模型，获取回复
        response = await self.client.chat.completions.create(
            model=self.sub_model,
            messages=self.history,
            stream=False,
            extra_body={"thinking": {"type": thinking}},
            # extra_body={"thinking": {"type": thinking} if source == 'ALI' else {"type": thinking}},
            tools=self.all_tools,
            tool_choice="auto"
        )
        # print(response)

        # 4.是否思考
        if thinking == "enabled":
            reasoning_content = response.choices[0].message.reasoning_content
            print("思考内容:", reasoning_content)
        
        # 5.1.工具调用
        if response.choices[0].message.tool_calls:
            self.history.append(response.choices[0].message.model_dump())

            tool_calls = response.choices[0].message.tool_calls
            for tool_call in tool_calls:
                name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                print(f"{COLOR_TOOL}工具调用: {name} 参数: {args}{COLOR_RESET}")
                if name in self.tool_map:
                    tool_func = self.tool_map[name]
                    tool_result = tool_func(** args)
                else:
                    tool_result = f"未知工具: {name}"

                self.history.append({
                    'role': 'tool', 
                    'content': tool_result,
                    'name': name, 
                    "tool_call_id": tool_call.id,
                })

            second_response = await self.client.chat.completions.create(
                model=self.sub_model,
                messages=self.history,
                stream=False,
                extra_body={"thinking": {"type": thinking}},
                tools=None,
                tool_choice="none"
            )
            final_content = second_response.choices[0].message.content
            
        # 5.2.正常回复
        else:
            final_content = response.choices[0].message.content
        final_content = self.clean_dsml_tags(final_content)
        self.history.append({'role': 'assistant', 'content': final_content})

async def main():
    agent = MXCC(client)

    while True:
        query = input(f"{COLOR_USER}用户: {COLOR_RESET}")
        if query.strip().lower() in ('exit', 'q', ''):
            print("\n👋 再见！")
            break
        await agent.agent_loop(query)

        if agent.history[-1]['role'] == 'assistant' and agent.history[-1]['content'].strip():
            print(f"{COLOR_ASSISTANT}助手: {agent.history[-1]['content']}{COLOR_RESET}")
            
        
if __name__ == "__main__":
    
    asyncio.run(main())