import os
import json
import curses
from curses import textpad
from config import load_activity_config, ACTIVITY_CONFIG_SCHEMA_FILE
from extract_config_client import ExtractConfigClient
from user_feedback_client import UserFeedbackClient
from jsonschema import validate
from gtts import gTTS 
from pydub import AudioSegment
from pydub.playback import play


def draw_classroom(stdscr, extracted_config):
    stdscr.clear()
    height, width = stdscr.getmaxyx()

    # Define the classroom boundaries (adjust these values as needed)
    classroom_top = 2
    classroom_bottom = height - 4  # Leave space for feedback or other elements
    classroom_left = 2
    classroom_right = width - 2

    # Draw the classroom border
    textpad.rectangle(stdscr, classroom_top, classroom_left, classroom_bottom, classroom_right)

    # Check if there are any phases defined
    if not extracted_config.get("phases"):
        stdscr.addstr(height // 2, width // 2 - 10, "No phases defined yet.")
        stdscr.refresh()
        stdscr.getch()
        return  # Exit the function if no phases
    
    # Check if there are any boards defined
    if not extracted_config.get("boards"):
        stdscr.addstr(height // 2, width // 2 - 9, "No boards defined yet.")
        stdscr.refresh()
        stdscr.getch()
        return

    # Get the current phase from extracted_config (assuming the first phase is shown initially)
    current_phase_index = 0 
    current_phase = extracted_config["phases"][current_phase_index]["name"]

    # Draw the classroom display at the top
    display_width = width - 4
    display_height = 5
    display_start_y = 1
    display_start_x = 2
    textpad.rectangle(stdscr, display_start_y, display_start_x, display_start_y + display_height, display_start_x + display_width)
    stdscr.addstr(display_start_y + 2, display_start_x + display_width // 2 - len(current_phase) // 2, current_phase)

    # Draw teacher icons
    if not extracted_config["accounts"]["teachers"]:
        stdscr.addstr(height - 3, 2, "Error: No teachers defined yet.")
    else:
        for teacher_name, details in extracted_config["accounts"]["teachers"].items():
            teacher_x = details["x"]
            teacher_y = details["y"]

            teacher_x = max(len(teacher_name), min(teacher_x, width - 2 - len(teacher_name)))  # Clamp x between 0 and max_x - 2 (leave space for icon)
            teacher_y = max(0, min(teacher_y, height - 1))  # Clamp y between 0 and max_y - 1
            stdscr.addstr(teacher_y, teacher_x, "👩‍🏫") 

            # Display teacher name above or below the icon
            name_y = teacher_y - 1  # Display above by default
            if name_y < 0: 
                name_y = teacher_y + 1  # If above is out of bounds, display below

            # Adjust x-coordinate to ensure the name stays within bounds
            name_x = teacher_x - len(teacher_name) // 2
            if name_x < 0:
                name_x = 0
            elif name_x + len(teacher_name) > width:
                name_x = width - len(teacher_name)

            stdscr.addstr(name_y, teacher_x - len(teacher_name) // 2, teacher_name)

    # Draw student icons
    if not extracted_config["accounts"]["students"]:
        stdscr.addstr(height - 3, 2, "Error: No students defined yet.")
    else:
        for student_name, details in extracted_config["accounts"]["students"].items():
            student_x = details["x"]
            student_y = details["y"]

            student_x = max(len(student_name), min(student_x, width - 2 - len(student_name)))  # Clamp x between 0 and max_x - 2 (leave space for name)
            student_y = max(0, min(student_y, height - 1))  # Clamp y between 0 and max_y - 1

            stdscr.addstr(student_y, student_x, "👩") 

            # Display teacher name above or below the icon
            name_y = student_y - 1  # Display above by default
            if name_y < 0: 
                name_y = student_y + 1  # If above is out of bounds, display below

            # Adjust x-coordinate to ensure the name stays within bounds
            name_x = student_x - len(student_name) // 2
            if name_x < 0:
                name_x = 0
            elif name_x + len(student_name) > width:
                name_x = width - len(student_name)

            stdscr.addstr(name_y, student_x - len(student_name) // 2, student_name)

    # Draw devices icons
    if extracted_config["accounts"]["devices"]:
        for device_name, details in extracted_config["accounts"]["devices"].items():
            device_x = details["x"]
            device_y = details["y"]

            device_x = max(len(device_name), min(device_x, width - 2 - len(device_name)))  # Clamp x between 0 and max_x - 2 (leave space for icon)
            device_y = max(0, min(device_y, height - 1))  # Clamp y between 0 and max_y - 1
            stdscr.addstr(device_y, device_x, "💻") 

            # Display teacher name above or below the icon
            name_y = device_y - 1  # Display above by default
            if name_y < 0: 
                name_y = device_y + 1  # If above is out of bounds, display below

            # Adjust x-coordinate to ensure the name stays within bounds
            name_x = teacher_x - len(device_name) // 2
            if name_x < 0:
                name_x = 0
            elif name_x + len(device_name) > width:
                name_x = width - len(device_name)

            stdscr.addstr(name_y, device_x - len(device_name) // 2, device_name)
    
    # Display resource visibility based on extracted_config
    resource_y = height // 2 + 4
    for resource_name in ["canvas", "bucket_view", "monitor_view", "todo", "workspace"]:
        stdscr.addstr(resource_y, 2, f"{resource_name.capitalize()}: ")
        
        # Check if the resource exists for the first board
        if resource_name not in extracted_config["boards"][0]:
            stdscr.addstr("Resource not defined yet.", curses.color_pair(1))  # You can customize the color
        else:
            for group in extracted_config['groups']:
                if group in extracted_config["boards"][0][resource_name].get(current_phase, []):
                    color_pair = extracted_config["groups"].index(group) + 1
                    stdscr.addstr(group + " ", curses.color_pair(color_pair))
        
        resource_y += 1

    stdscr.refresh()
    stdscr.getch()

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
    ai_text = ("""Hello there!\n""")
# I'm your new AI assistant, designed to help you streamline the process of setting up new SCORE projects. 
# Ready to get started? Use plain language to tell me about the activity. Or describe the specific project phases or CK Board components you would like us to use or modify. We'll work together to ensure your project is complete and accurate. What SCORE activity should we build?\n\n""")

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
    prev_system_response = ai_text

    text_input = input("Teacher response: ")
    
    # 4. Extraction and feedback loop
    while True:
        # 4a. Extract configuration values
        extracted_config = extractor.extract_values(prev_system_response, text_input, extracted_config)
        print("\nExtracted Configuration:")  #Optional Print Statement
        print(json.dumps(extracted_config, indent=2)+"\nAnalyzing for feedback...\n\n")
            
        # Display first phase using curses
        curses.wrapper(draw_classroom, extracted_config)

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
        prev_system_response = feedback

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
