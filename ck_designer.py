import os
import json
from config import load_activity_config, ACTIVITY_CONFIG_SCHEMA_FILE
from extract_config_client import ExtractConfigClient
from user_feedback_client import UserFeedbackClient
from jsonschema import validate
from gtts import gTTS 
from pydub import AudioSegment
from pydub.playback import play

def main():
    # 1. Load configuration template and schema
    extracted_config = load_activity_config()
    previous_config = extracted_config
    with open(ACTIVITY_CONFIG_SCHEMA_FILE, "r") as f:
        schema = json.load(f)

    # 2. Initialize clients
    extractor = ExtractConfigClient()
    feedback_client = UserFeedbackClient()

    # 3. Get initial text input from the user
    ai_text = ("""Hello there!\n
I'm your new AI assistant, designed to help you streamline the process of setting up new SCORE projects. 
Ready to get started? Use plain language to tell me about the activity. Or describe the specific project phases or CK Board components you would like us to use or modify.
We'll work together to ensure your project is complete and accurate. What SCORE activity should we build?\n\n""")

    print(ai_text + "\nInitiating AI voice...")

    # Convert feedback to speech using gTTS
    tts = gTTS(text=ai_text, lang='en')  # You can change 'en' to a different language code if needed
    tts.save("feedback.mp3")
    # Speed up the audio using pydub
    sound = AudioSegment.from_mp3("feedback.mp3")
    faster_sound = sound.speedup(playback_speed=3)  # Adjust to your desired speed
    faster_sound.export("feedback_faster.mp3", format="mp3")

    # Play the feedback audio (you might need to install an audio player library like playsound)
    os.system("afplay feedback.mp3")

    text_input = input("Teacher response: ")
    
    # 4. Extraction and feedback loop
    while True:
        # 4a. Extract configuration values
        extracted_config = extractor.extract_values(text_input, extracted_config)
        print("\nExtracted Configuration:")  #Optional Print Statement
        print(json.dumps(extracted_config, indent=2)+"\nAnalyzing for feedback...\n\n")
            
        # 4b. Get user feedback
        feedback = feedback_client.get_feedback(previous_config, extracted_config, text_input)
        print(feedback)
        print("Initiating AI voice...")

        # Convert feedback to speech using gTTS
        tts = gTTS(text=feedback, lang='en')  # You can change 'en' to a different language code if needed
        tts.save("feedback.mp3")

        # Speed up the audio using pydub
        sound = AudioSegment.from_mp3("feedback.mp3")
        faster_sound = sound.speedup(playback_speed=3)  # Adjust to your desired speed
        faster_sound.export("feedback_faster.mp3", format="mp3")

        # Play the feedback audio (you might need to install an audio player library like playsound)
        os.system("afplay feedback.mp3")

        # 4c. Get additional input
        text_input = input("Teacher response (Enter 'exit' to save and quit): ")

        if text_input == "exit":
            break

        previous_config = extracted_config

    # 5. Final configuration output
    print("\nFinal Configuration:")
    print(json.dumps(extracted_config, indent=2))

if __name__ == "__main__":
    main()
