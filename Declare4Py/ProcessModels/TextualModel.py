from abc import ABC
from Declare4Py.ProcessModels.DeclareModel import DeclareModel
from Declare4Py.Utils.Declare.DeclarePrompts import DeclarePrompts
from Declare4Py.ProcessModels.AbstractModel import ProcessModel
from typing import List, Optional
from groq import Groq, GroqError
import re


class TextualModel(ProcessModel, ABC):
    def __init__(self, textual_description: str = ""):
        super().__init__()
        self.textual_description = textual_description
        
        # Load prompts for the LLM   
        self.prompt_instructions: str = DeclarePrompts.INSTRUCTIONS_AND_TEMPLATES
        self.prompt_instructions = self.prompt_instructions + DeclarePrompts.ADDITIONAL_TEMPLATES
        self.prompt_meta_constraints: str = DeclarePrompts.META_CONSTRAINTS
        self.prompt_formatting_information: str = DeclarePrompts.DESCRIPTION_AND_FORMATTING_INFORMATION
        
        
    def parse_form_file (self, model_path: str, **kwargs):
        # Load the process description from a textual file
        self.textual_description = TextualModel.read_file(model_path)


    @staticmethod
    def get_available_models(client: Groq) -> List[str]:
        """Retrieve the model identifiers currently available from Groq."""
        response = client.models.list()
        models = response.get("data", []) if isinstance(response, dict) else response.data

        model_ids = []
        for model in models:
            model_id = model.get("id") if isinstance(model, dict) else model.id
            if model_id:
                model_ids.append(model_id)

        return sorted(model_ids)

    @staticmethod
    def select_best_model(available_models: List[str]) -> str:
        """Select the strongest general-purpose text model from the available IDs."""
        if not available_models:
            raise ValueError("Groq did not return any available models.")

        excluded_terms = (
            "guard",
            "whisper",
            "distil-whisper",
            "speech",
            "tts",
        )
        text_models = [
            model_id
            for model_id in available_models
            if not any(term in model_id.lower() for term in excluded_terms)
        ]
        candidates = text_models or available_models

        def model_score(model_id: str):
            normalized_id = model_id.lower()
            parameter_sizes = [
                float(size)
                for size in re.findall(r"(\d+(?:\.\d+)?)b(?:\W|$)", normalized_id)
            ]
            parameter_size = max(parameter_sizes, default=0)
            return (
                parameter_size,
                "instruct" in normalized_id or "versatile" in normalized_id,
                "instant" not in normalized_id,
                normalized_id,
            )

        return max(candidates, key=model_score)

    def to_decl (self, api_key, interactive : bool = False, llm_model : Optional[str] = None, **kwargs) -> DeclareModel:
        """
        This method handles, with a LLM, the textual description of the process to extract the declarative constraints,
        then represents it as an instance of DeclareModel and returns it.

        If llm_model is not provided, the strongest general-purpose text model
        returned by the Groq API is selected automatically.
        """
        # if interactive is not a boolean, set it to its default value False
        if not isinstance(interactive, bool):
            interactive = False
        
        # Format the prompt with the textual description and interaction status
        interaction_statuses = ["Consider this text and extract highly reliable declarative constraints. No interaction with the user will be available, so please be as precise as possible in your response.", "Consider this text and, if you find it necessary, ask me questions to clary whatever may be unclear and the extract highly reliable declarative constraints."]
        if interactive:
            formatted_prompt_formatting_information = self.prompt_formatting_information.format(textual_description=self.textual_description, interaction_status=interaction_statuses[1])
        else:
            formatted_prompt_formatting_information = self.prompt_formatting_information.format(textual_description=self.textual_description, interaction_status=interaction_statuses[0])

        # Load pre-set promt into the conversation
        conversation = []
        conversation.append(
            {'role': 'system',
            'content': self.prompt_instructions})
        conversation.append(
            {'role': 'system',
            'content': self.prompt_meta_constraints})
        conversation.append(
            {'role': 'system',
            'content': formatted_prompt_formatting_information})
    

        try:
            # Initialize client for Groq API using the API key
            client = Groq(api_key=api_key)
            available_models = TextualModel.get_available_models(client)
            if llm_model is None:
                llm_model = TextualModel.select_best_model(available_models)
            elif llm_model not in available_models:
                raise ValueError(
                    f"The model {llm_model} is not available. "
                    f"Available models: {available_models}."
                )

            # Since the user is available to interact with the LLM we start a cmd line chat
            if interactive:
                # Introduce chat
                print(
                    f"This is a new chat with Groq model {llm_model}.\n"
                    "Once you are satisfied with the results, type 'exit' to close the chat."
                )

                # While loop to handle interactions user-LLM
                while True:
                    # Retrive LLM's reply
                    response = client.chat.completions.create(
                        model=llm_model,
                        messages=conversation.copy()
                    )

                    # Extract and display model's reply
                    response_dict = dict(response)
                    choices = response_dict.get("choices", [])

                    reply = "The model did not return a valid response."
                    if choices:
                        reply = choices[0].message.content
                    
                    # print result
                    print(f"\n\n   AI: {reply}")

                    # Add model's response to the conversation
                    conversation.append({'role': 'assistant', 'content': reply})

                    user_input = input("\n\n   You: ")

                    if user_input.strip().lower() == 'exit':
                        last_reply = reply
                        break

                    conversation.append({'role': 'user', 'content': user_input})

            # Without interactions the LLM result should be directly saved into the model 
            else: 
                # Retrive AI's reply
                response = client.chat.completions.create(
                    model=llm_model,
                    messages=conversation.copy()
                )

                # Extract and display model's reply
                response_dict = dict(response)
                choices = response_dict.get("choices", [])

                reply = "The model did not return a valid response."
                if choices:
                    reply = choices[0].message.content

                # Add model's response to the conversation
                conversation.append({'role': 'assistant', 'content': reply})

            # Save the last LLM reply
            last_reply = conversation[-1]['content']

            # Parse the LLM result to extract activities and constraints, then format them following syntax rules
            parsed_content = TextualModel.parse_llm_result(last_reply)

            # Generate model from parsed string
            model = DeclareModel().parse_from_string(parsed_content)

            return model
        
        except GroqError as e:
            print(f" Invalid API key or connection issue: {e}")

    # Support method to parse results of the LLM
    def parse_llm_result (response: str) -> str:
        # Extract constraints from the LLM response
        constraints = TextualModel.parse_response_constraints(response)

        # From the full LLM response find the activities
        activities = TextualModel.parse_response_activities(response)

        # If activities are not found, try to parse them from constraints
        str = "No activities found in the LLM reply."
        if activities == [str]:
            activities = TextualModel.parse_activities(constraints)
        
        # Combine activities and constraints into a parsed string compatible with .decl syntax
        parsed_content = TextualModel.parse_string_to_decl(constraints, activities)
        
        return parsed_content

    # Support method: finds constraints in the LLM response
    def parse_response_constraints (llm_reply: str) -> List[str]:
        import re
        constraints = []
        str = "Final Formal Declarative Constraints"

        # Split the string after the last instace of "Final Formal Declarative Constraints:"
        index = llm_reply.rfind(str)
        if index == -1:
            return ["No constraints found in the AI reply."]
        else:
            # Split the string so that it contains only the constraints
            split_string = llm_reply[index + len(str):].strip()

            # Define all available regex to find constraints
            # Unary constraints
            at_most_regex = re.compile(
                r"at-most\s*\(\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )
            existence_regex = re.compile(
                r"existence\s*\(\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )
            init_regex = re.compile(
                r"init\s*\(\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )

            # Binary constraints with exclusions
            response_regex = re.compile(
                r"(?<!not-)(?<!chain-)(?<!alternate-)response\s*\(\s*([\w\s\-]+?)\s*,\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )
            precedence_regex = re.compile(
                r"(?<!not-)(?<!chain-)(?<!alternate-)precedence\s*\(\s*([\w\s\-]+?)\s*,\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )
            succession_regex = re.compile(
                r"(?<!not-)(?<!chain-)(?<!alternate-)succession\s*\(\s*([\w\s\-]+?)\s*,\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )
            choice_regex = re.compile(
                r"(?<!exclusive-)choice\s*\(\s*([\w\s\-]+?)\s*,\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )
            chain_succession_regex = re.compile(
                r"(?<!not-)chain-succession\s*\(\s*([\w\s\-]+?)\s*,\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )
            chain_response_regex = re.compile(
                r"(?<!not-)chain-response\s*\(\s*([\w\s\-]+?)\s*,\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )
            chain_precedence_regex = re.compile(
                r"(?<!not-)chain-precedence\s*\(\s*([\w\s\-]+?)\s*,\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )
            co_existence_regex = re.compile(
                r"(?<!not-)co-existence\s*\(\s*([\w\s\-]+?)\s*,\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )
            exclusive_choice_regex = re.compile(
                r"(?<!not-)exclusive-choice\s*\(\s*([\w\s\-]+?)\s*,\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )
            responded_existence_regex = re.compile(
                r"(?<!not-)responded-existence\s*\(\s*([\w\s\-]+?)\s*,\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )

            # Binary constraints with no exclusions
            alternate_response_regex = re.compile(
                r"alternate-response\s*\(\s*([\w\s\-]+?)\s*,\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )
            alternate_precedence_regex = re.compile(
                r"alternate-precedence\s*\(\s*([\w\s\-]+?)\s*,\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )
            alternate_succession_regex = re.compile(
                r"alternate-succession\s*\(\s*([\w\s\-]+?)\s*,\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )


            # Negative constraints
            not_response_regex = re.compile(
                r"not-response\s*\(\s*([\w\s\-]+?)\s*,\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )
            not_precedence_regex = re.compile(
                r"not-precedence\s*\(\s*([\w\s\-]+?)\s*,\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )
            not_chain_response_regex = re.compile(
                r"not-chain-response\s*\(\s*([\w\s\-]+?)\s*,\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )
            not_chain_precedence_regex = re.compile(
                r"not-chain-precedence\s*\(\s*([\w\s\-]+?)\s*,\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )
            not_chain_succession_regex = re.compile(
                r"not-chain-succession\s*\(\s*([\w\s\-]+?)\s*,\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )
            not_co_existence_regex = re.compile(
                r"not-co-existence\s*\(\s*([\w\s\-]+?)\s*,\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )
            not_exclusive_choice_regex = re.compile(
                r"not-exclusive-choice\s*\(\s*([\w\s\-]+?)\s*,\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )
            not_responded_existence_regex = re.compile(
                r"not-responded-existence\s*\(\s*([\w\s\-]+?)\s*,\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )
            not_succession_regex = re.compile(
                r"not-succession\s*\(\s*([A-Za-z_ ]+)\s*,\s*([A-Za-z_ ]+)\s*\)", re.IGNORECASE)


            regexes = [at_most_regex, existence_regex, response_regex, precedence_regex, co_existence_regex, not_co_existence_regex, not_succession_regex, responded_existence_regex, alternate_succession_regex, init_regex, not_responded_existence_regex, not_response_regex, not_precedence_regex, not_chain_response_regex, not_chain_precedence_regex, succession_regex, choice_regex, exclusive_choice_regex, not_exclusive_choice_regex, not_chain_succession_regex, chain_succession_regex, chain_response_regex, chain_precedence_regex, alternate_response_regex, alternate_precedence_regex]
            constraints = ["at-most", "existence", "response", "precedence", "co-existence", "not-co-existence", "not-succession", "responded-existence", "alternate-succession", "Init", "not-responded-existence", "not-response", "not-precedence", "not-chain-response", "not-chain-precedence", "succession", "choice", "exclusive-choice", "not-exclusive-choice", "not-chain-succession", "chain-succession", "chain-response", "chain-precedence", "alternate-response", "alternate-precedence"]

            found_constraints = []
            for i in range(len(regexes)):
                regex = regexes[i]
                matches = re.findall(regex, split_string)
                # if there are no matches for this regex, continue to the next one
                if not matches:
                    continue
                for match in matches:
                    # If the match is a tuple (for existence_pair), format it accordingly
                    if isinstance(match, tuple):
                        formatted_match = constraints[i] + "(" + ", ".join(match) + ")"
                    else:
                        formatted_match = constraints[i] + "(" + match + ")"
                    
                    found_constraints.append(formatted_match)
                    formatted_match=""

            return found_constraints

    # Support method: parses activities from constraints - used if parse_response_activities is unable to find activities in the LLM response
    def parse_activities (constraints: List[str]) -> List[str]:
        activities = []
        for constraint in constraints:
            # Remove the constraint type and parentheses 
            # Be careful with the order of replacements, not-template should be done before template, symilarly co-template and template
            constraint  = constraint.replace("at-most(", "").replace("Init(", "").replace("not-responded-existence(", "").replace("responded-existence(", "").replace("not-co-existence(", "").replace("co-existence(", "").replace("existence(", "").replace("alternate-response(", "").replace("not-chain-response(", "").replace("chain-response(", "").replace("not-response(", "").replace("response(", "").replace("alternate-precedence(", "").replace("not-chain-precedence(", "").replace("chain-precedence(", "").replace("not-precedence(", "").replace("precedence(", "").replace("alternate-succession(", "").replace("not-chain-succession(", "").replace("chain-succession(", "").replace("not-succession(", "").replace("succession(", "").replace("not-exclusive-choice(", "").replace("exclusive-choice(", "").replace("choice(", "").replace(")", "").replace(" ", "")

            # Split process based on whether the constraint is unary or binary
            if "," in constraint:
                # Binary constraint
                parts = constraint.split(",")
                activities.append(parts[0])
                activities.append(parts[1])
            else:
                # Unary constraint
                activities.append(constraint)
        
        return list(set(activities))

    # Support method: finds activities in the LLM response
    def parse_response_activities(llm_reply):
        activities = []
        str = "Activities: "

        # Split the string after the last instace of "Final Formal Declarative Constraints:"
        index = llm_reply.rfind(str)
        if index == -1:
            return ["No activities found in the LLM reply."]
        else:
            # Extract the line containing the activities
            lines = llm_reply[index:].split('\n')
            if lines:
                activity_line = lines[0]
                # Remove the "Activities: " part
                activity_line = activity_line.replace(str, "").strip()
                # Split by comma and strip whitespace
                activities = [act.strip() for act in activity_line.split(",") if act.strip()]    
        return activities

    # Support method: converts constraints and activities into a parsed strinc compaible with .decl syntax for model analysis
    def parse_string_to_decl(constrains: List[str], activities: List[str]) -> str:
        parsed_content = ""

        for activity in activities:
            parsed_content += f"activity {activity}\n"

        for constraint in constrains:
            # Replace () with [] to follow .decl syntax
            constraint = constraint.replace("(", "[").replace(")", "]")
            # Split process based on whether the constraint is unary or binary
            if "," in constraint:
                # Binary constraint
                parsed_content += f"{constraint} | | |\n"
                
            else:
                # Unary constraint
                parsed_content += f"{constraint} | |\n"
                
        return parsed_content
        
    # Support method: reads a file and return its content
    def read_file(filename):
        with open(filename, "r", encoding="utf8", errors='ignore') as file:
            content = file.read()
        return content
