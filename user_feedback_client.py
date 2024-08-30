import os
import json
from config import *
from vertexai.generative_models import GenerativeModel
import vertexai.preview.generative_models as generative_models
import vertexai
import utils

class UserFeedbackClient:
    def __init__(self):
        """Initializes the UserFeedbackClient with the Gemini model."""
        self.config = load_activity_config()
        self.schema = load_activity_config_schema()
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        self.model = GenerativeModel(os.getenv("GEMINI_MODEL"),
            system_instruction="""You are an expert in generating helpful feedback and co-design for users configuring a project. Your task is to create a conversational response that summarizes changes to a configuration the word 'we' to to refer to work both of you have done so far, then provide prompts to guide further changes."""
        )

    def get_feedback(self, previous_config, modified_config, user_input):
        """Generates feedback for the user based on the previous and modified configurations.

        Args:
            original_config: The original (template) configuration.
            extracted_config: The configuration extracted from user input.

        Returns:
            A string containing the feedback message for the user.
        """

        payload = {
            "original_config": previous_config,
            "extracted_config": modified_config,
            "schema": self.schema,
            "user_input": user_input
        }

        json_payload = json.dumps(payload, indent=2)
        prompt = (
            "The following is a JSON object containing the previous configuration, the modified configuration that you and the user contributed, and the configuration schema:\n\n"
            f"{json_payload}\n\n"
            "Create a conversational response for the user. In your response, do the following:\n"
            "1. If the 'user_input' contains any questions related the configuration:\n"
            "    - Provide an answer to the 'user_input' question, but only answer questions about this project configuration; if unrelated, state that you are an AI only able to assist with project configurations.\n"
            "2. If the extracted configuration contains any changes compared to the original configuration:\n"
            "    - Briefly report the types of changes made.\n"
            "    - If a project name and at least one phase, board, and group were provided, state 'Everything looks good!'; if one is missing, state 'To complete the configuration...' followed by a clear and concise prompt to provide one of those missing items.\n"
            "    - Do not use any JSON in your response.\n\n"
        )

        # Call the model to predict and get results in string format
        generation_config = {
            "max_output_tokens": 1024,
            "temperature": 0.2,
            "top_p": 0.95,
            "top_k": 40
        }

        safety_settings = {
            generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }
        
        # Call the model to predict and get results in string format
        response = self.model.generate_content(prompt, generation_config=generation_config, safety_settings=safety_settings).text
        clean_response = utils.remove_json_markdown(response)

        return clean_response  
