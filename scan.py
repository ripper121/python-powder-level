import cv2
import numpy as np
import winsound

# Define the target color with tolerance
color = 90  # 0-255 Gray is mostly 3 times the same Color Value like 90,90,90
target_color = np.array([color, color, color])
tolerance = 0.6  # 0.0-2.0
start_of_scan = 70
end_of_scan = 350
scan_line_length = 40  # in px
min_matches = 25
low_level_px=248
high_level_px=151
percent_alarm = 120

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

# Capture video from the default webcam
cap = cv2.VideoCapture(1)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to capture video.")
        break

    # Process the current frame
    scan_image_with_line_and_draw(frame, scan_line_length, target_color, tolerance, start_of_scan, end_of_scan, min_matches,low_level_px, high_level_px, percent_alarm)

    # Display the modified frame
    cv2.imshow("Webcam - Color Match Indicator", frame)

    # Break the loop when 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the capture and close any open windows
cap.release()
cv2.destroyAllWindows()
