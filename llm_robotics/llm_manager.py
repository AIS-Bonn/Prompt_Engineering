from openai import OpenAI
from mistralai.client import MistralClient


# ANSI escape codes for text color
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
RESET = "\033[0m"  # Reset text color to default
PRINT_COLOR_DICT = {
    "user" : GREEN,
    "assistant": CYAN,
    "system": MAGENTA,
    "function": YELLOW
}

class LLMManager:
    
    def __init__(self, config_dict) -> None:
        self.cofig_dict = config_dict
        
        self.client = config_dict["client"]
        if isinstance(self.client, MistralClient):
            self.chat = self.client.chat
        else:
            self.chat = self.client.chat.completions.create


        self.model = config_dict["model"]
        self.temperature = config_dict["temperature"]
        self.message_history = []
        self.tmp_msgs = []
        self.functions = None
        self.no_color_print = not config_dict["color_print"]
        
        
    def create_message(self, role, content):
        message = {"role": role, "content": content}
        self.add_message(message)
        
    def add_message(self, message):
        self.message_history.append(message)
        self.print_message(message)
        
    def add_tmp_message(self, message):
        self.tmp_msgs.append(message)
        self.print_message(message)
        
    def print_message(self, message):
        if type(message) is dict:
            color = PRINT_COLOR_DICT.get(message["role"], RESET)
            reset = RESET
            if self.no_color_print:
                color = ""
                reset = ""
            
            if message.get("tool_calls", None) != None:
                print("\n" + color + message["role"] + ":\n" + reset + message["tool_calls"][0]["function"]["name"]
                    + "\n" + message["tool_calls"][0]["function"]["arguments"] + "\n")
            else: 
                print("\n" + color + message["role"] + ":\n" + reset + message["content"] + "\n")

        else:
            color = PRINT_COLOR_DICT.get(message.role, RESET)
            reset = RESET
            if self.no_color_print:
                color = ""
                reset = ""
            
            if message.tool_calls != None:
                print("\n" + color + message.role + ":\n" + reset + message.tool_calls[0].function.name
                    + "\n" + message.tool_calls[0].function.arguments + "\n")
            else: 
                print("\n" + color + message.role + ":\n" + reset + message.content + "\n")
        
    def print_message_history(self):
        for message in self.message_history:
            self.print_message(message)
    
    def update_funtions(self, new_functions):
        self.functions = new_functions
    
    def get_model_response(self, function_call="auto"):
        if function_call == "any" and not isinstance(self.client, MistralClient):
            function_call = "auto"
        if self.functions != None: 
            llm_response = self.chat(
                model = self.model,
                messages = self.message_history + self.tmp_msgs,
                tools = self.functions,
                tool_choice =  function_call, # "none" '{"name":\ "my_function"}'
                temperature = self.temperature, # [0, 2] higher means more random
            )
        else:
            llm_response = self.chat(
                model = self.model,
                messages = self.message_history + self.tmp_msgs,
                temperature = self.temperatur, # [0, 2] higher means more random
            )
        llm_response 
        llm_message = llm_response.choices[0].message
        if llm_message.tool_calls != None:
            tool_calls = [llm_message.tool_calls[0]]
            llm_message.tool_calls = tool_calls


        self.tmp_msgs = []
        self.message_history.append(llm_response.choices[0].message)
        self.print_message(llm_response.choices[0].message)
        return llm_response



if __name__ == "__main__":
    llm = LLMManager("<your key>")
    llm.create_message("system", "you are a comedian.")
    llm.create_message("user", "tell me a joke")
    response = llm.get_model_response()
    llm.create_message("user", "tell me one about engineers")
    response = llm.get_model_response()
    
    print("--------------------")
    llm.print_message_history
    