# SCORE/CK Board Designer Feasibility MVP

This project demonstrates how to use the Vertex AI Gemini model to generate and refine CK Board configurations based on user input.  The configuration focuses on defining resource visibility across different project phases for various groups.

## Overview

This system uses a combination of:

- **Vertex AI Gemini:** A powerful generative AI model from Google to understand natural language input and generate structured JSON configurations.
- **JSON Schema:** A formal specification to define the valid structure and constraints of the configuration files.
- **Conversational Feedback:**  Gemini provides user-friendly feedback, guiding the user through the process and helping them complete the configuration.

## Features

- **Natural Language Input:**  Users can describe their project configuration in plain English.
- **Structured Output:**  The system generates a valid JSON configuration file that adheres to a predefined schema.
- **Iterative Refinement:** The user receives feedback and can iteratively add details to their configuration until it's complete.
- **Phase-Based Resource Visibility:**  The configuration allows you to control which resources (e.g., canvas, workspace) are visible to specific groups during different project phases.
- **Error Handling:**  Invalid input and model errors are handled gracefully.

## Project Structure

- ck_designer/
    - .env      # Environment variables (i.e., Gemini specifications: PROJECT_ID, LOCATION, GEMINI_MODEL)
    - config.py     # Configuration loader
    - activity_config_example.json   # Example CK Board project configuration
    - activity_config_schema.json       # JSON Schema for CK Board project configuration validation
    - activity_config_template.json     # Template for blank CK Board project configuration 
    - extract_config_client.py      # Client for extracting configuration values
    - user_feedback_client.py       # Client for generating user feedback
    - ck_designer.py        # Main script to run the configuration generation process
    - test_config_clients.py     # Test suite for Gemini configuration clients

## How to Use

1. **Prerequisites:**
   - Clone this repository.
   - **Install Dependencies:** `pip install -r requirements.txt`
   - **Environment Variables:** Create a `.env` file in the project root directory and add the following:
      ```
      PROJECT_ID=your-project-id
      LOCATION=your-project-location (e.g., us-central1)
      GEMINI_MODEL=text-bison@001
      ```
   - **Log in to Google Cloud:** 
      ```bash
      gcloud auth application-default login
      ```

2. **Run Tests**

```bash
python -m unittest discover tests
```

3. **Run Tool:**
   - From the project root directory, run `python ck_designer.py`.
   - Follow the prompts to describe your project configuration.
   - The system will generate a JSON configuration file based on your input.

# You'll be guided through defining your CK Board project
