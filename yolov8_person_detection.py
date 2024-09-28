import sys
import subprocess
import time
import os
from datetime import datetime
import io
import contextlib

def install_package(package):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", package],
                              stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print(f"\033[91mError installing {package}\033[0m")

def ensure_package(package):
    try:
        __import__(package)
    except ImportError:
        print(f"\033[90m{package} not found. Installing...\033[0m")
        install_package(package)

# Ensure required packages are installed
required_packages = ['opencv-python', 'ultralytics', 'torch', 'torchvision', 'tqdm', 'colorama', 'playsound']
for package in required_packages:
    ensure_package(package)

# Now that we've ensured the packages are installed, we can import them
try:
    import cv2
    from ultralytics import YOLO
    import torch
    from tqdm import tqdm
    import colorama
    from playsound import playsound
    colorama.init(autoreset=True)
    from colorama import Fore, Back, Style
    
    print(f"{Fore.LIGHTBLACK_EX}PyTorch version: {torch.__version__}")
    print(f"{Fore.LIGHTBLACK_EX}CUDA available: {torch.cuda.is_available()}")
except Exception as e:
    print(f"{Fore.RED}Error importing required packages: {e}")
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

def draw_colored_boxes(img, results):
    for r in results:
        boxes = r.boxes
        for box in boxes:
            b = box.xyxy[0]
            c = box.cls
            conf = box.conf[0]
            label = f"{results[0].names[int(c)]} {conf:.2f}"
            color = (0, 0, 255) if results[0].names[int(c)] == "person" else (128, 128, 128)
            cv2.rectangle(img, (int(b[0]), int(b[1])), (int(b[2]), int(b[3])), color, 2)
            
            # Improve label readability
            text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
            cv2.rectangle(img, (int(b[0]), int(b[1]) - text_size[1] - 10), (int(b[0]) + text_size[0], int(b[1])), color, -1)
            cv2.putText(img, label, (int(b[0]), int(b[1]) - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    return img

def main():
    try:
        print(f"{Fore.LIGHTBLACK_EX}Loading YOLO model...")
        model = YOLO('yolov8n.pt')
        print(f"{Fore.LIGHTBLACK_EX}YOLO model loaded successfully.")

        cap = cv2.VideoCapture(0)
        cv2.namedWindow("Object Detection", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Object Detection", 800, 600)

        detection_count = 0

        while cap.isOpened():
            success, frame = cap.read()

            if success:
                # Suppress print output from YOLO
                with contextlib.redirect_stdout(io.StringIO()):
                    results = model(frame)
                
                annotated_frame = draw_colored_boxes(frame, results)

                person_detected = any(results[0].names[int(box.cls)] == "person" and box.conf[0] >= 0.5 for box in results[0].boxes)
                if person_detected:
                    detection_count += 1
                    save_screenshot(frame, detection_count)
                    try:
                         # Construct the full path to the alert.mp3 file in the data folder
                        sound_path = os.path.join(os.path.dirname(__file__), 'data', 'alert.mp3')
                        playsound(sound_path)
                    except Exception as e:
                        print(f"{Fore.RED}Error playing sound: {e}")

                detection_info = f"{results[0].speed['inference']:.1f}ms inference"
                status_text = "Person Detected!" if person_detected else "Scanning..."
                status_color = (0, 0, 255) if person_detected else (255, 0, 0)

                cv2.putText(annotated_frame, detection_info, (10, frame.shape[0] - 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                cv2.putText(annotated_frame, status_text, (10, frame.shape[0] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)

                cv2.imshow("Object Detection", annotated_frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                print("Failed to capture frame. Retrying...")
                time.sleep(1)
                cap.release()
                cap = cv2.VideoCapture(0)

        cap.release()
        cv2.destroyAllWindows()

    except Exception as e:
        print(f"{Fore.RED}An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    for i in tqdm(range(100), desc="Initializing", bar_format="{l_bar}%s{bar}%s{r_bar}" % (Fore.BLUE, Fore.RESET)):
        time.sleep(0.02)
    print(f"{Fore.LIGHTBLACK_EX}Initialization complete.")
    
    main()
