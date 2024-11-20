# Partially taken from: https://docs.ultralytics.com/guides/raspberry-pi/
#Author: Ultralytics
#License: AGPL-3.0
#The following lines are taken from the above reference:
#12-17

import cv2
import os
import time
from picamera2 import Picamera2

picam2 = Picamera2()
picam2.preview_configuration.main.size = (1280, 720)
picam2.preview_configuration.main.format = "RGB888"
picam2.preview_configuration.align()
picam2.configure("preview")
picam2.start()

desktop_path = os.path.expanduser("~/Desktop")
folder_name = "Images"

folder_path = os.path.join(desktop_path, folder_name)
if not os.path.exists(folder_path):
    os.makedirs(folder_path)

interval = 3
num_pics = 50
last_time = time.time()
picture_count = 0

while picture_count < num_pics:
    
    frame = picam2.capture_array()

    cv2.imshow("Camera View", frame)

    current_time = time.time()
    if current_time - last_time >= interval:

        filename = os.path.join(folder_path, f"Object_{picture_count}.jpg")
        cv2.imwrite(filename, frame)
        print(f"Picture {picture_count + 1} saved")
        
        picture_count += 1
        
        last_time = current_time

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

picam2.stop()
cv2.destroyAllWindows()