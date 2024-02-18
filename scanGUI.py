import cv2
import numpy as np
import winsound
import tkinter as tk
from tkinter import simpledialog
from threading import Thread, Event
import configparser
from PIL import Image, ImageTk

camera = 0
color = 90  # 0-255 Gray is mostly 3 times the same Color Value like 90,90,90
target_color = np.array([color, color, color])
tolerance = 0.6  # 0.0-2.0
start_of_scan = 50
end_of_scan = 360
scan_line_length = 40  # in px
min_matches = 20
low_level_px=248
high_level_px=151
percent_alarm = 120

# Use an Event for better thread control
stop_event = Event()

def translate(value, leftMin, leftMax, rightMin, rightMax):
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin
    valueScaled = float(value - leftMin) / float(leftSpan)
    return rightMin + (valueScaled * rightSpan)

def is_color_within_tolerance(color, target_color, tolerance):
    lower_bound = target_color * (1 - tolerance)
    upper_bound = target_color * (1 + tolerance)
    return np.all(color >= lower_bound) and np.all(color <= upper_bound)

def scan_image_with_line_and_draw(image, _scan_line_length, _target_color, _tolerance, _start_of_scan, _end_of_scan, _min_matches,_low_level_px,_high_level_px, _percent_alarm):
    height, width, _ = image.shape
    scan_line_length = min(_scan_line_length, width)
    center_x = width // 2
    center_y = height // 2
    x_start = max(center_x - scan_line_length // 2, 0)
    x_end = min(center_x + scan_line_length // 2, width)
    match_counter = 0



    for y in range(_start_of_scan, _end_of_scan):
        line = image[y, x_start:x_end]
        average_color = line.mean(axis=0).astype(np.uint8)

        if is_color_within_tolerance(average_color, _target_color, _tolerance):
            match_counter += 1
            cv2.line(image, (x_start, y), (x_end, y), (0, 255, 0), 1)
        else:
            match_counter = 0
            cv2.line(image, (x_start, y), (x_end, y), (0, 255, 255), 1)
        
        if match_counter > _min_matches:
            #print(f"Fill {y-_min_matches}")
            #print(f"{round(translate(y-_min_matches, _low_level_px, _high_level_px, 0, 100),2)} %")
            cv2.line(image, (x_start-10, y-_min_matches), (x_end+10, y-_min_matches), (0, 255, 0), 5)
            percent =  round(translate(y-_min_matches, _low_level_px, _high_level_px, 0, 100),2)
            if percent < 0:
                percent = 0
            if percent >= _percent_alarm:
                cv2.putText(image, '!!!ALARM!!!', (center_x-150,center_y), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255) , 3, cv2.LINE_AA)
                winsound.Beep(2500,100)
                break
            cv2.putText(image, f"{percent} %", (x_end+20, y-_min_matches+10), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0) , 2, cv2.LINE_AA)
            break

    cv2.line(image, (x_start-20, _start_of_scan), (x_end+20, _start_of_scan), (0, 0, 0), 5)
    cv2.line(image, (x_start-20, _end_of_scan), (x_end+20, _end_of_scan), (0, 0, 0), 5)

def save_variables_to_ini():
    """Save the current variables to an INI file."""
    config = configparser.ConfigParser()
    
    # Section for variables
    config['Variables'] = {
        'camera': camera,
        'color': color,
        'tolerance': tolerance,
        'start_of_scan': start_of_scan,
        'end_of_scan': end_of_scan,
        'scan_line_length': scan_line_length,
        'min_matches': min_matches,
        'low_level_px': low_level_px,
        'high_level_px': high_level_px,
        'percent_alarm': percent_alarm
    }
    
    # Write to an INI file
    with open('settings.ini', 'w') as configfile:
        config.write(configfile)

def load_variables_from_ini():
    """Load variables from an INI file."""
    # Create a ConfigParser object
    config = configparser.ConfigParser()
    try:        
        # Read the INI file
        config.read('settings.ini')
        global camera, color, target_color, tolerance, start_of_scan, end_of_scan, scan_line_length, min_matches, low_level_px, high_level_px, percent_alarm
        camera = int(config['Variables']['camera'])
        color = int(config['Variables']['color'])
        tolerance = float(config['Variables']['tolerance'])
        start_of_scan = int(config['Variables']['start_of_scan'])
        end_of_scan = int(config['Variables']['end_of_scan'])
        scan_line_length = int(config['Variables']['scan_line_length'])
        min_matches = int(config['Variables']['min_matches'])
        low_level_px = int(config['Variables']['low_level_px'])
        high_level_px = int(config['Variables']['high_level_px'])
        percent_alarm = int(config['Variables']['percent_alarm'])

    except configparser.NoSectionError:
        # Handle the case where the 'Variables' section is missing
        print("Error: Section 'Variables' not found in the INI file.")
    except configparser.Error as e:
        # Handle other configparser errors
        print(f"ConfigParser error: {e}")
        variables = {}  # Consider setting default values here
    except Exception as e:
        # Handle unexpected errors
        print(f"Unexpected error: {e}")

# Function to update global variables
def update_variables():
    global camera, color, target_color, tolerance, start_of_scan, end_of_scan, scan_line_length, min_matches, low_level_px, high_level_px, percent_alarm
    camera = int(camera_var.get())
    color = int(color_var.get())
    target_color = np.array([color, color, color])
    tolerance = float(tolerance_var.get())
    start_of_scan = int(start_of_scan_var.get())
    end_of_scan = int(end_of_scan_var.get())
    scan_line_length = int(scan_line_length_var.get())
    min_matches = int(min_matches_var.get())
    low_level_px = int(low_level_px_var.get())
    high_level_px = int(high_level_px_var.get())
    percent_alarm = int(percent_alarm_var.get())
    save_variables_to_ini()

# Function that encapsulates your existing code for processing and displaying the video
def process_video(root, image_label):
    global camera, target_color, tolerance, start_of_scan, end_of_scan, scan_line_length, min_matches, low_level_px, high_level_px, percent_alarm
    cap = cv2.VideoCapture(camera)

    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture video.")
            break

        scan_image_with_line_and_draw(frame, scan_line_length, target_color, tolerance, start_of_scan, end_of_scan, min_matches, low_level_px, high_level_px, percent_alarm)

        # Convert the image to RGB (from BGR)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Convert the image to PIL format
        img = Image.fromarray(frame)
        # Convert the image for Tkinter
        imgtk = ImageTk.PhotoImage(image=img)
        # Update the image_label with the new image
        image_label.configure(image=imgtk)
        image_label.image = imgtk

        # This replaces cv2.waitKey, tkinter doesn't need an explicit wait function for updates
        root.update_idletasks()
        root.update()

    cap.release()

def start_video():
    stop_event.clear()
    update_variables()
    video_thread = Thread(target=lambda: process_video(root, image_label), daemon=True)
    video_thread.start()

def stop_video():
    stop_event.set()


# Load variables and print them to verify
load_variables_from_ini()

# GUI setup
root = tk.Tk()
root.title("Powder Level Alarm")
root.geometry("657x795")
#root.resizable(False, False)

# Configure the grid to use all available space in columns
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)

# Adding the first two centered labels
tk.Label(root, text="Powder Level Alarm (1.0) by ripper121").grid(row=0, column=0, columnspan=2, sticky=tk.EW)
tk.Label(root, text="https://strenuous.dev").grid(row=1, column=0, columnspan=2, sticky=tk.EW)


# Variables for GUI
camera_var = tk.StringVar(value=str(camera))
color_var = tk.StringVar(value=str(color))
tolerance_var = tk.StringVar(value=str(tolerance))
start_of_scan_var = tk.StringVar(value=str(start_of_scan))
end_of_scan_var = tk.StringVar(value=str(end_of_scan))
scan_line_length_var = tk.StringVar(value=str(scan_line_length))
min_matches_var = tk.StringVar(value=str(min_matches))
low_level_px_var = tk.StringVar(value=str(low_level_px))
high_level_px_var = tk.StringVar(value=str(high_level_px))
percent_alarm_var = tk.StringVar(value=str(percent_alarm))

# GUI Layout
labels_and_vars = [("Camera (ID)", camera_var), ("Gray Lum (0-255)", color_var), ("Tolerance (0.0-2.0)", tolerance_var), ("Start of Scan (Px)", start_of_scan_var), ("End of Scan (Px)", end_of_scan_var), ("Scan Line Length (Px)", scan_line_length_var), ("Min Matches", min_matches_var), ("Low Level (Px)", low_level_px_var), ("High Level (Px)", high_level_px_var), ("Percent Alarm", percent_alarm_var)]


# Dynamically add labels and entries based on labels_and_vars content
for i, (label_text, var) in enumerate(labels_and_vars, start=2):  # Start at row 2
    tk.Label(root, text=label_text).grid(row=i, column=0, sticky=tk.W)  # Align labels to the west (left)
    tk.Entry(root, textvariable=var).grid(row=i, column=1, sticky=tk.EW)  # Entry fills cell

# Start and Stop buttons
tk.Button(root, text="Start", command=start_video).grid(row=len(labels_and_vars) + 3, column=0)
tk.Button(root, text="Stop", command=stop_video).grid(row=len(labels_and_vars) + 3, column=1)

# Create an image label to display the video
image_label = tk.Label(root)
image_label.grid(row=len(labels_and_vars) + 4, column=0, columnspan=2)  # Adjust grid positioning as needed


root.mainloop()
