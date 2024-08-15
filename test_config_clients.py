import unittest
from unittest.mock import patch
from extract_config_client import ExtractConfigClient
from user_feedback_client import UserFeedbackClient
from config import load_activity_config, load_activity_config_schema
import json

@unittest.skip("Temp")
class TestExtractConfigClient(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config_structure = load_activity_config()
        cls.schema = load_activity_config_schema()
        cls.client = ExtractConfigClient()

    def test_extract_values_valid_input(self):
        text = """The project name is 'Awesome Project'. We have three phases: Planning, Development, and Testing. 
                   The main board is called 'Development Board'.  During the Planning phase, the canvas and todo 
                   should be visible to the Managers and Developers. In the Development phase, the bucket view and 
                   workspace should be visible to Developers only. Finally, in Testing, the monitor should be visible 
                   to the QA Team. We will use four buckets: To Do, In Progress, Review, and Done."""
        extracted_config = self.client.extract_values(text, self.config_structure)

        # Assertions
        self.assertEqual(extracted_config["project_name"], "Awesome Project")
        self.assertEqual(extracted_config["phases"], ["Planning", "Development", "Testing"])
        self.assertEqual(len(extracted_config["boards"]), 1) 
        self.assertEqual(extracted_config["boards"][0]["board_name"], "Development Board")
        self.assertEqual(extracted_config["boards"][0]["canvas"]["Planning"], ["Managers", "Developers"])
        self.assertEqual(extracted_config["boards"][0]["todo"]["Planning"], ["Managers", "Developers"])
        self.assertEqual(extracted_config["boards"][0]["bucket_view"]["Development"], ["Developers"])
        self.assertEqual(extracted_config["boards"][0]["workspace"]["Development"], ["Developers"])
        self.assertEqual(extracted_config["boards"][0]["monitor_view"]["Testing"], ["QA Team"])
        self.assertEqual(extracted_config["boards"][0]["buckets"], ["To Do", "In Progress", "Review", "Done"])

    def test_extract_values_invalid_input(self):
        """Test with invalid input that should result in an empty configuration."""
        text = "This is some random text with no relevant information."

        extracted_config = self.client.extract_values(text, self.config_structure)

        # Assertions: Check if key fields are empty or have default values
        self.assertEqual(extracted_config["project_name"], "")  
        self.assertEqual(extracted_config["phases"], [])  
        self.assertEqual(extracted_config["boards"], []) 
        self.assertEqual(extracted_config["groups"], []) 

    def test_extract_values_partial_input(self):
        text = "The project has a board called 'Marketing Board'. There's a 'Marketing' group."

        extracted_config = self.client.extract_values(text, self.config_structure)
        
        # Assertions: Check that default values are used when information is missing
        self.assertEqual(len(extracted_config["phases"]), 0)  # Should be empty
        self.assertEqual(len(extracted_config["boards"]), 1) 
        self.assertEqual(extracted_config["boards"][0]["board_name"], "Marketing Board")
        # Check that all resource visibility settings are empty for the "Marketing Board"
        for resource_name in ["canvas", "bucket_view", "monitor_view", "todo", "workspace"]:
            for phase in self.config_structure["phases"]:
                self.assertEqual(extracted_config["boards"][0][resource_name].get(phase, []), [])
        #Check that buckets are empty
        self.assertEqual(extracted_config["boards"][0]["buckets"], [])

    def test_extract_values_ambiguous_input(self):
        # You'll need to add assertions based on the expected LLM behavior for ambiguous inputs
        pass

    @patch('vertexai.generative_models.GenerativeModel.generate_content')
    def test_extract_values_model_error(self, mock_generate_content):
        mock_generate_content.side_effect = Exception("Simulated model error")
        with self.assertRaises(Exception):
            self.client.extract_values("Some text", self.config_structure)


class TestUserFeedbackClient(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.config_structure = load_activity_config()
        cls.schema = load_activity_config_schema()
        cls.client = UserFeedbackClient()

    def test_get_feedback_complete_config(self):
        """Test with a fully completed configuration - expect 'Everything looks good so far!'."""

        # Load a fully completed config (you'll need to create this)
        with open("activity_config_example.json", "r") as f:
            complete_config = json.load(f)

        feedback = self.client.get_feedback(self.config_structure, complete_config)

        # Assertion
        self.assertIn("everything looks good so far!", feedback.lower())  # Case-insensitive check

    def test_get_feedback_missing_fields(self):
        """Test with missing fields - expect prompts for those fields."""

        # Create a config with some missing fields
        incomplete_config = {
            "project_name": "",
            "phases": ["Planning", "Execution"],
            "boards": [
                {
                    "board_name": "Board 1"
                    # Missing other resources and their visibility settings
                }
            ],
            "groups": ["Managers", "Developers"]
        }

        feedback = self.client.get_feedback(self.config_structure, incomplete_config)

        # Assertions
        self.assertIn("to complete the configuration", feedback.lower())


    @patch('vertexai.generative_models.GenerativeModel.generate_content')
    def test_get_feedback_model_error(self, mock_generate_content):
        """Simulate an error from the Gemini model."""
        mock_generate_content.side_effect = Exception("Simulated model error")

        with self.assertRaises(Exception):
            self.client.get_feedback(self.config_structure, {})  # Empty config to trigger feedback generation


if __name__ == '__main__':
    unittest.main()
