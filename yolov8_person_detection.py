import sys
import subprocess
import time
import os
from datetime import datetime
import io
import contextlib
import numpy as np
import traceback

def install_package(package):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", package],
                              stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL)
        print(f"Successfully installed {package}")
    except subprocess.CalledProcessError:
        print(f"\033[91mError installing {package}\033[0m")

def ensure_packages(packages):
    missing_packages = [pkg for pkg in packages if pkg not in sys.modules]
    if missing_packages:
        print("\033[90mInstalling missing dependencies...", end="", flush=True)
        for _ in range(10):
            time.sleep(0.2)
            print(".", end="", flush=True)
        print("\033[0m")
        for package in missing_packages:
            install_package(package)

# Ensure required packages are installed
required_packages = ['opencv-python', 'ultralytics', 'torch', 'torchvision', 'tqdm', 'colorama', 'playsound']
ensure_packages(required_packages)

# Now that we've ensured the packages are installed, we can import them
try:
    import cv2
    print("OpenCV version:", cv2.__version__)
    
    from ultralytics import YOLO
    print("Ultralytics imported successfully")
    
    import torch
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    
    from tqdm import tqdm
    print("tqdm imported successfully")
    
    import colorama
    colorama.init(autoreset=True)
    from colorama import Fore, Back, Style
    print("Colorama initialized successfully")
    
    from playsound import playsound
    print("Playsound imported successfully")
    
except Exception as e:
    print(f"\033[91mError importing required packages: {e}\033[0m")
    print("Please check your Python environment and try again.")
    input("Press Enter to exit...")
    sys.exit(1)

def save_screenshot(frame, detection_count):
    now = datetime.now()
    date_str = now.strftime("%m-%d-%Y")
    time_str = now.strftime("%I.%M%p").lower()
    
    main_folder = "logged_detections"
    os.makedirs(main_folder, exist_ok=True)
    
    sub_folder = f"Logged-Images_{date_str}"
    folder_path = os.path.join(main_folder, sub_folder)
    os.makedirs(folder_path, exist_ok=True)
    
    filename = f"{date_str}_{time_str}_image-{detection_count:03d}.jpg"
    filepath = os.path.join(folder_path, filename)
    
    cv2.imwrite(filepath, frame)
    print(f"{Fore.LIGHTBLACK_EX}Screenshot saved: {filepath}")

def draw_colored_boxes(img, results, motion_boxes):
    for r in results:
        boxes = r.boxes
        for box in boxes:
            b = box.xyxy[0]
            c = box.cls
            conf = box.conf[0]
            label = f"{results[0].names[int(c)]} {conf:.2f}"
            if results[0].names[int(c)] == "person":
                color = (0, 0, 255)  # Red color for person
                cv2.rectangle(img, (int(b[0]), int(b[1])), (int(b[2]), int(b[3])), color, 2)
                
                # Calculate text size and position for centered label
                text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
                text_x = int(b[0] + (b[2] - b[0]) / 2 - text_size[0] / 2)
                text_y = int(b[1] - 5)
                
                # Draw background rectangle for text
                cv2.rectangle(img, (text_x - 2, text_y - text_size[1] - 2),
                              (text_x + text_size[0] + 2, text_y + 2), color, -1)
                
                # Draw centered text
                cv2.putText(img, label, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # Draw motion boxes
    for box in motion_boxes:
        x, y, w, h = box
        cv2.rectangle(img, (x, y), (x + w, y + h), (128, 128, 128), 2)  # Grey color for motion
        cv2.putText(img, "motion", (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (128, 128, 128), 1)
    
    return img

def detect_motion(frame, prev_frame, threshold=30):
    if prev_frame is None:
        return []
    
    frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    prev_frame_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    
    frame_diff = cv2.absdiff(frame_gray, prev_frame_gray)
    _, thresh = cv2.threshold(frame_diff, threshold, 255, cv2.THRESH_BINARY)
    
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    motion_boxes = []
    for contour in contours:
        if cv2.contourArea(contour) > 100:  # Adjust this value to change sensitivity
            x, y, w, h = cv2.boundingRect(contour)
            motion_boxes.append((x, y, w, h))
    
    return motion_boxes

def log_error(error_message):
    now = datetime.now()
    date_str = now.strftime("%m-%d-%Y")
    log_folder = "traceback logs"
    os.makedirs(log_folder, exist_ok=True)
    
    log_file = os.path.join(log_folder, f"log_{date_str}.txt")
    
    with open(log_file, "a") as f:
        f.write(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] {error_message}\n")
        f.write(traceback.format_exc())
        f.write("\n\n")

def set_window_icon(window_name):
    icon_path = os.path.join(os.path.dirname(__file__), 'data', 'Icon.ico')
    if os.path.exists(icon_path):
        try:
            import win32gui
            import win32con
            import win32api
            hwnd = win32gui.FindWindow(None, window_name)
            icon_handle = win32gui.LoadImage(0, icon_path, win32con.IMAGE_ICON, 0, 0, win32con.LR_LOADFROMFILE)
            win32api.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_SMALL, icon_handle)
            win32api.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_BIG, icon_handle)
            print(f"{Fore.LIGHTBLACK_EX}Window icon set successfully.")
        except ImportError:
            print(f"{Fore.YELLOW}Warning: Unable to set window icon. 'pywin32' module not found.")
        except Exception as e:
            print(f"{Fore.YELLOW}Warning: Failed to set window icon. Error: {e}")
    else:
        print(f"{Fore.YELLOW}Warning: Icon file not found at {icon_path}")

def main():
    try:
        print(f"{Fore.LIGHTBLACK_EX}Loading YOLO model...")
        model = YOLO('yolov8n.pt')
        print(f"{Fore.LIGHTBLACK_EX}YOLO model loaded successfully.")

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("\033[91mError: Unable to open camera.\033[0m")
            return

        window_name = "Object Detection"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, 800, 600)
        
        # Set the window icon
        set_window_icon(window_name)

        detection_count = 0
        last_detection_time = 0
        sound_played = False
        prev_frame = None

        while cap.isOpened():
            success, frame = cap.read()

            if success:
                # Detect motion
                motion_boxes = detect_motion(frame, prev_frame)
                prev_frame = frame.copy()

                # Suppress print output from YOLO
                with contextlib.redirect_stdout(io.StringIO()):
                    results = model(frame)
                
                annotated_frame = draw_colored_boxes(frame, results, motion_boxes)

                current_time = time.time()
                person_detected = any(results[0].names[int(box.cls)] == "person" and box.conf[0] >= 0.30 for box in results[0].boxes)
                if person_detected and (current_time - last_detection_time) > 10:
                    detection_count += 1
                    save_screenshot(frame, detection_count)
                    last_detection_time = current_time
                    if not sound_played:
                        try:
                            sound_path = os.path.join(os.path.dirname(__file__), 'data', 'alert.mp3')
                            playsound(sound_path)
                            sound_played = True
                        except Exception as e:
                            print(f"{Fore.RED}Error playing sound: {e}")
                            log_error(f"Error playing sound: {e}")
                elif not person_detected:
                    sound_played = False

                detection_info = f"{results[0].speed['inference']:.1f}ms inference"
                if person_detected:
                    status_text = "Person Detected!"
                    status_color = (0, 0, 255)  # Red
                elif motion_boxes:
                    status_text = "Motion Detected!"
                    status_color = (128, 128, 128)  # Grey
                else:
                    status_text = "Scanning..."
                    status_color = (255, 0, 0)  # Blue

                cv2.putText(annotated_frame, detection_info, (10, frame.shape[0] - 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                cv2.putText(annotated_frame, status_text, (10, frame.shape[0] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)

                cv2.imshow(window_name, annotated_frame)

                if cv2.waitKey(1) & 0xFF == ord('q') or cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                    break
            else:
                print("Failed to capture frame. Retrying...")
                time.sleep(1)
                cap.release()
                cap = cv2.VideoCapture(0)

        cap.release()
        cv2.destroyAllWindows()
        os._exit(0)  # Force exit the program when the window is closed

    except Exception as e:
        error_message = f"An error occurred: {e}"
        print(f"{Fore.RED}{error_message}")
        log_error(error_message)
        input("Press Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    try:
        for i in tqdm(range(100), desc="Initializing", bar_format="{l_bar}%s{bar}%s{r_bar}" % (Fore.BLUE, Fore.RESET)):
            time.sleep(0.02)
        print(f"{Fore.LIGHTBLACK_EX}Initialization complete.")
        
        main()
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        print(f"{Fore.RED}{error_message}")
        log_error(error_message)
        input("Press Enter to exit...")
        sys.exit(1)
