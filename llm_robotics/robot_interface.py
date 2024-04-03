import openai
import numpy as np
import json



#message_template = {"role": "tool", "content": results, "name": calling_message["function_call"]["name"]}

class FunctionManager:
    
    def __init__(self, robot, config_dict) -> None:
        self.config_dict = config_dict
        self.robot = robot
        self.use_speech_recognition = config_dict["use_speech_recognition"]
        self.task = None
        
        
        # state of the robot and the environment
        self.location_list = ["bedroom", "kitchen", "study", "parlor"] #["kitchen", "couch", "startLocation"]
        self.current_location = "parlor" #"startLocation"
        self.start_location = "parlor"
        self.known_objects = {x: {} for x in self.location_list}
        self.arms = {
            "left": None,
            "right": None,
        }
        return
    
    def get_available_functions(self, selective_mode=False):
        # add the get_description functions here
        function_descriptions = [
            self.get_description_drive_to_location,
            self.get_description_find_object,
            self.get_description_grasp_object,
            self.get_description_place_object,
            self.get_description_exit,
            #self.get_description_interact,
        ]
        
        functions = []
        for fn in function_descriptions:
            description = fn(selective_mode)
            if description != None:
                #print(description["name"])
                functions.append(description)
        return functions
    
    
    def handle_llm_response(self, llm_response):
        response_message = None 
        llm_message = llm_response.choices[0].message
        
        parallel_response = None
        if llm_message.tool_calls != None:
            response_message = self.execute_function(llm_message)
            if len(llm_message.tool_calls) > 1:
                parallel_response = []
                for i in range (1, len(llm_message.tool_calls)):
                    r = {"role": "tool", 
                            "content": f"Not executed. You may only use one function at a time.", 
                            "name": llm_message.tool_calls[i].function.name}
                    r["tool_call_id"] = llm_message.tool_calls[i].id
                    parallel_response.append

        else:
            response_message = self.get_user_interaction(llm_message)
        
        return response_message, parallel_response
    
    
    def execute_function(self, llm_message):
        function_call =  llm_message.tool_calls[0]
        print(f"Calling {function_call.function.name}")
        parsed_arguments = json.loads(function_call.function.arguments)
        if function_call.function.name == "drive_to_location":
            response_message = self.handle_drive_to_location(llm_message, parsed_arguments)
        elif function_call.function.name == "find_object":
            response_message = self.handle_find_object(llm_message, parsed_arguments)
        elif function_call.function.name == "grasp_object":
            response_message = self.handle_grasp_object(llm_message, parsed_arguments)
        elif function_call.function.name == "place_object":
            response_message = self.handle_place_object(llm_message, parsed_arguments)
        elif function_call.function.name == "exit":
            response_message = self.handle_exit(llm_message, parsed_arguments)
        elif function_call.function.name == "interact":
            response_message = self.handle_exit(llm_message, parsed_arguments)
        else:
            raise ValueError("Invalid name provided in function call.")
        
        if response_message != "exit":
            response_message["tool_call_id"] = function_call.id
        return response_message 
    
    def replay_llm_history(self, llm_history):
        verbose = self.config_dict["verbose_robot"]
        for message in llm_history:
            role = message["role"]
            if role == "assistant":
                print(message)
                if message.get("function_call"):
                    response_message = self.execute_function(message)
                elif verbose:
                    self.robot.speak(message["content"])
        
        
    def get_user_interaction(self, llm_message):
        content = llm_message.content
        
        reply = self.user_dialogue(content)
        
        response_message = {"role": "user", "content": reply}
        return response_message
    
    def user_dialogue(self, text):
        self.robot.speak(text)
        if self.use_speech_recognition:
            reply = self.robot.recognize_speech()
        else: 
            reply = input("User input: ")
        
        return reply
        
    def get_robot_state_description(self):
        
        state = [f"You are currently located in {self.current_location}.",
                 f"The user is located in the parlor.",
                 f"The user has given you the task: \"{self.task}\"",
        ]
        
        objects_str = "The following lists each location and the objects which are known to be located there:"
        new_string = ""
        for location in self.location_list:
            location_string = f"\n\nObjects present in the {location}:"
            item_string = ""
            for item, num in self.known_objects[location].items():
                if num == 0:
                    item_string += f"\n no {item},"
                else:
                    item_string += f"\n {num} {item}{'s' if num > 1 else ''},"

            if item_string != "":
                item_string = item_string[0:-1] + "."
                new_string += (location_string + item_string)
        
        if new_string != "":
            objects_str += new_string
            state.append(objects_str)
        
        if self.arms["left"] == None and self.arms["right"] == None:
            state.append(f"You are holding no objects.")
        elif self.arms["left"] == None and self.arms["right"] != None:
            state.append(f'You are holding a{"n" if self.arms["right"][0] in "aeiou" else ""} {self.arms["right"]}.')
        elif self.arms["left"] != None and self.arms["right"] == None:
            state.append(f'You are holding a{"n" if self.arms["left"][0] in "aeiou" else ""} {self.arms["left"]}.')
        elif self.arms["left"] != None and self.arms["right"] != None:
            state.append(f'You are holding a{"n" if self.arms["left"][0] in "aeiou" else ""} {self.arms["left"]} and a{"n" if self.arms["right"][0] in "aeiou" else ""} {self.arms["right"]}.')

        
        # missing join()
        response_message = {"role": "system", "content": "\n\n".join(state)}
        return response_message
    
    
    #====================================
    # Handling of the various function calls and creation of response messages
    # every function xyz() has a handle_xyz for the function call
    # and a get_description_xyz() to get the function call api
    #======================get_description==============
    
    
    #----------
    # drive_to_location
    #----------
    
    def handle_drive_to_location(self, llm_message, parsed_arguments):
        location = parsed_arguments['location']
        
        if location not in self.location_list:
            return {"role": "tool", 
                    "content": f"There is no location known to you by the name {location}.", 
                    "name": llm_message.tool_calls[0].function.name}
        
        
        success = self.robot.drive_to_location(location)
        
        
        response_message = {"role": "tool", 
                            "content": f"You successfully arrived in the new location {location}. This is now the current location.", 
                            "name": llm_message.tool_calls[0].function.name}
        self.current_location = location
        # failure state deleted due to error: TODO test for success
        return response_message
    
    def get_description_drive_to_location(self, selective_mode=True):
        description = {
            "type": "function",
            "function": {
            "name": "drive_to_location",
            "description": "Drive to the location specified in the parameter.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "enum": self.location_list,
                        "description": "The location of the house where to drive.",
                    },
                },
                "required": ["location"],
                # "result": {
                #         "type": "array",
                #         "items": {
                #             "type": "string"
                #         }
                # },
            }
            },
        }
        return description
    
    
    #----------l"
    # find_object
    #----------
    
    def handle_find_object(self, llm_message, parsed_arguments):
        object_name_list = parsed_arguments['object_name_list']
        detections = self.robot.find_object_detic(object_name_list)
        
        dict = {name : 0 for name in object_name_list}
        for detection in detections:
            dict[detection] = dict.get(detection, 0) + 1
            
        string = ""
        found_something = False
        for name in object_name_list:
            self.known_objects[self.current_location][name] = dict[name]
            if dict[name] > 1:
                string += f"\n{dict[name]} {name}s,"
                found_something = True
            elif  dict[name] == 1:
                string += f"\n{dict[name]} {name},"
                found_something = True
            else:
                string += f"\nno {name},"
        
        string = string[0:-1] + "."
        
        response_message = None
        response_message = {"role": "tool", 
                            #"content": f"The following items were found at the:{string}", 
                            "content": f"The following items were found in the {self.current_location}:{string}", 
                            "name": llm_message.tool_calls[0].function.name}
        return response_message
    
    def get_description_find_object(self, selective_mode=True):
        description = {
            "type": "function",
            "function": {
            "name": "find_object",
            "description": "Check if any of the specified objects are at the current location. If the object is located at another location within the house this function will not find it. This function also counts the number of objects present.",
            "parameters": {
                "type": "object",
                "properties": {
                    "object_name_list": {
                        "type": "array",
                        "items": {
                            "type" : "string",
                        },
                        "description": "Array of objects we want to search for. Object names should be given in the singular if possible.",
                    },
                },
                "required": ["object_name_list"]
            },
            },
        }
        return description
    
    
    #----------
    # grasp_object
    #----------
    
    def handle_grasp_object(self, llm_message, parsed_arguments):
        # handover_object(self, object_name: str, arm : str = "left", post_configuration="home", max_tries=3, attach_as_collision_object=True):
        object_name = parsed_arguments['object_name']
        
        used_arm = "left"
        if self.arms["left"] != None:
            used_arm = "right"
        
            
        success = self.robot.handover_object(object_name, arm=used_arm, attach_as_collision_object=False)
        
        response_message = None
        if success:
            if self.known_objects[self.current_location].get(object_name) != None:
                self.known_objects[self.current_location][object_name] -= 1
            response_message = {"role": "tool", 
                                "content": f"You successfully grasped the object {object_name}.", 
                                "name": llm_message.tool_calls[0].function.name}
            self.arms[used_arm] = object_name
        else:
            response_message = {"role": "tool", 
                                "content": f"You failed to grasp the object {object_name}.", 
                                "name": llm_message.tool_calls[0].function.name}
        return response_message
    
    def get_description_grasp_object(self, selective_mode=True):
        description = {
            "type": "function",
            "function": {
            "name": "grasp_object",
            "description": "Attempt to pick up an object located at the current location. Object needs to be detected with find_object before this function is called. The recipient will only receive the object if you are in the same location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "object_name": {
                        "type": "string",
                        #"enum": self.known_objects,
                        "description": "Name of the object which we want to pick up.",
                    },
                },
                "required": ["object_name"]
            },
            },
        }
        
        if selective_mode:
            if self.arms["left"] != None and self.arms["right"] != None:
                return None 
            
            current_known_items = self.known_objects[self.current_location]
            
            
            if self.arms["right"] != None and self.arms["left"] != None:
                return None
            items = []
            for item in current_known_items.keys():
                if current_known_items[item] > 0:
                    items.append(item)
            if items != []:
                description["function"]["parameters"]["properties"]["object_name"]["enum"] = items  
            else:
                return None
            
        return description
    
    
    #----------
    # place_object
    #----------
    
    def handle_place_object(self, llm_message, parsed_arguments):
        # let_customer_get_object(self, arm):
        object_name = parsed_arguments['object_name']
        
        arm = None
        if object_name == self.arms["left"]:
            arm = "left"
        elif object_name == self.arms["right"]:
            arm = "right"
        else:
            return {"role": "tool", 
                    "content": f"You are not holding the object {object_name}. Use grasp_object to first to pick the object up.", 
                    "name": llm_message.tool_calls[0].function.name}
        
        success = self.robot.let_customer_get_object(arm = arm)
        
        
        if success:
            if object_name in self.known_objects[self.current_location].keys():
                self.known_objects[self.current_location][object_name] += 1
            else:
                self.known_objects[self.current_location][object_name] = 1
                
            response_message = {"role": "tool", 
                                "content": f"You successfully placed the object {object_name}.", 
                                "name": llm_message.tool_calls[0].function.name}
        else:
            response_message = {"role": "tool", 
                                "content": f"You failed to placed the object {object_name}.", 
                                "name": llm_message.tool_calls[0].function.name}
        self.arms[arm] = None
        return response_message
    
    def get_description_place_object(self, selective_mode=True):
        held_objects = []
        if self.arms["left"] != None:
            held_objects.append(self.arms["left"])
        if self.arms["right"] != None:
            held_objects.append(self.arms["right"])
        
        description = {
            "type": "function",
            "function": {
            "name": "place_object",
            #"description": "Hands over an object to the user. The user needs to be in the current location and the object must have been picked up previously",
            "description": "Places an object at the current location. If the user is at the current location the item will be handed over to the user. An object needs to be grasped first before it can be placed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "object_name": {
                        "type": "string",
                        #"enum": held_objects,
                        "description": "Name of the object which you want to hand over.",
                    },
                },
                "required": ["object_name"]
            },
            },
        }
        
        if selective_mode:
            if held_objects != []:
                description["function"]["parameters"]["properties"]["object_name"]["enum"] = held_objects
            else:
                return None
            
        return description
    
    
    #----------
    # exit
    #----------
    
    def handle_exit(self, llm_message, parsed_arguments):
        # let_customer_get_object(self, arm):
        return "exit"
    
    def get_description_exit(self, selective_mode=True):
        
        description = {
            "type": "function",
            "function": {
            "name": "exit",
            #"description": "Only call this function if the user has no additional tasks for you. This function will finish the interaction with the user.",
            "description": "This function will finish the interaction with the user and should be called when the task is finished.",
            "parameters": {
                "type": "object",
                "properties": {
                    },
                },
            },
        }
        return description
    
    #----------
    # interact
    #----------
    
    def handle_interact(self, llm_message, parsed_arguments):
        text = parsed_arguments['text']

        reply = self.user_dialogue(text)
        
        response_message = {"role": "tool", 
                            "content": reply, 
                            "name": llm_message.tool_calls[0].function.name}
        return response_message
    
    def get_description_interact(self, selective_mode=True):
        
        description = {
            "type": "function",
            "function": {
            "name": "interact",
            "description": "This function interacts with a person or the user. Text will be spoken and the textual response of the dialogue partner will be returned.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text which will be said to the person or user.",
                    },
                },
                "required": ["object_name"]
            },
            },
        }
        return description
