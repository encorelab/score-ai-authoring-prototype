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

    # Check if there are any phases defined
    if not extracted_config.get("phases"):
        stdscr.addstr(height // 2, width // 2 - 10, "No phases defined yet.")
        stdscr.refresh()
        return

    # Check if there are any boards defined
    if not extracted_config.get("boards"):
        stdscr.addstr(height // 2, width // 2 - 9, "No boards defined yet.")
        stdscr.refresh()
        return

    # Get the current phase and its associated board
    current_phase_index = 0
    current_phase = extracted_config["phases"][current_phase_index]["name"]
    current_board_name = extracted_config["phases"][current_phase_index]["board"]

    # Find the board object based on the current_board_name
    current_board = next((board for board in extracted_config["boards"] if board["board_name"] == current_board_name), None)
    if current_board is None:
        stdscr.addstr(height // 2, width // 2 - 12, "Board not found for this phase.")
        stdscr.refresh()
        return

    # Draw the classroom display at the top
    display_width = width - 4
    display_height = 3  # Adjust height as needed
    display_start_y = 0  # Start at the top of the screen
    display_start_x = 2
    textpad.rectangle(stdscr, display_start_y, display_start_x, display_start_y + display_height, display_start_x + display_width)
    stdscr.addstr(display_start_y + 1, display_start_x + display_width // 2 - len(current_phase) // 2, current_phase)

    # Define the classroom boundaries, considering the display height
    classroom_top = display_start_y + display_height + 2
    classroom_bottom = height - 4
    classroom_left = 2
    classroom_right = width - 2

    # Draw the classroom border
    textpad.rectangle(stdscr, classroom_top, classroom_left, classroom_bottom, classroom_right)

    # Initialize color pairs for groups (up to 6 groups)
    group_colors = [
        curses.COLOR_RED,     # Group 1
        curses.COLOR_GREEN,   # Group 2
        curses.COLOR_BLUE,    # Group 3
        curses.COLOR_YELLOW,  # Group 4
        curses.COLOR_MAGENTA, # Group 5
        curses.COLOR_CYAN     # Group 6
    ]

    for i, group in enumerate(extracted_config["groups"]):
        if i < len(group_colors):
            curses.init_pair(i + 1, group_colors[i], curses.COLOR_BLACK)
        else:
            # If you have more than 6 groups, you'll need to handle this case
            # For example, you could cycle through colors again or use a different scheme
            pass

    # Draw teacher icons and names 
    if not extracted_config["accounts"]["teachers"]:
        stdscr.addstr(height - 3, 2, "Error: No teachers defined yet.")
    else:
        for teacher_name, details in extracted_config["accounts"]["teachers"].items():
            # Get teacher's location for the current phase
            if current_phase in details["locations"]:
                teacher_x = details["locations"][current_phase]["x"]
                teacher_y = details["locations"][current_phase]["y"]

                # Ensure teacher is within classroom bounds
                teacher_x = max(classroom_left + 1, min(teacher_x, classroom_right - 2))
                teacher_y = max(classroom_top + 1, min(teacher_y, classroom_bottom - 1))

                # Get the teacher's group and its color pair
                group = details["groups"][0] 
                color_pair = extracted_config["groups"].index(group) + 1

                stdscr.addstr(teacher_y, teacher_x, "👩‍🏫", curses.color_pair(color_pair)) 

                # Display teacher name 
                name_y = teacher_y - 1 
                if name_y < 0: 
                    name_y = teacher_y + 1 

                name_x = teacher_x - len(teacher_name) // 2
                if name_x < 0:
                    name_x = 0
                elif name_x + len(teacher_name) > width:
                    name_x = width - len(teacher_name)

                stdscr.addstr(name_y, name_x, teacher_name, curses.color_pair(color_pair))

    # Draw student and device icons
    for account_type in ["students", "devices"]:
        if not extracted_config["accounts"][account_type]:
            stdscr.addstr(height - 3, 2, f"Error: No {account_type} defined yet.")
        else:
            for name, details in extracted_config["accounts"][account_type].items():
                # Get student/device location for the current phase
                if current_phase in details["locations"]:
                    x = details["locations"][current_phase]["x"]
                    y = details["locations"][current_phase]["y"]

                    # Ensure student/device is within classroom bounds
                    x = max(classroom_left + 1, min(x, classroom_right - 2))
                    y = max(classroom_top + 1, min(y, classroom_bottom - 1))

                    # Get the first group the account belongs to and its color pair
                    group = details["groups"][0]
                    color_pair = extracted_config["groups"].index(group) + 1

                    icon = "👩" if account_type == "students" else "💻"
                    stdscr.addstr(y, x, icon, curses.color_pair(color_pair))

                    # Display name above or below the icon
                    name_y = y - 1 
                    if name_y < 0: 
                        name_y = y + 1

                    name_x = x - len(name) // 2
                    if name_x < 0:
                        name_x = 0
                    elif name_x + len(name) > width:
                        name_x = width - len(name)

                    stdscr.addstr(name_y, name_x, name, curses.color_pair(color_pair))


    # Display resource visibility based on extracted_config and the current board
    resource_y = height // 2 + 4
    for resource_name in ["canvas", "bucket_view", "monitor_view", "todo", "workspace"]:
        assigned_groups = ""
        stdscr.addstr(resource_y, 2, f"{resource_name.capitalize()}: ")

        if resource_name not in current_board:
            stdscr.addstr("Resource not defined yet.", curses.color_pair(1))
        else:
            for group in extracted_config['groups']:
                if group in current_board[resource_name].get(current_phase, []):
                    assigned_groups += group + ", "

        stdscr.addstr(resource_y, 4 + len(resource_name), assigned_groups[:-2])
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
