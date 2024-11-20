# Partially taken from: https://docs.ultralytics.com/guides/raspberry-pi/
#Author: Ultralytics
#License: AGPL-3.0
#The following lines are taken from the above reference:
#7-8, 36-41, 56, 62-64, 82-83, 90

import cv2
from picamera2 import Picamera2
from ultralytics import YOLO
import time
import ctypes
import sys
import numpy as np

pathToObjectDetectionModel = "best.pt"
pathToSharedObject = "clibrary.so"

clibrary = ctypes.CDLL(pathToSharedObject)

clibrary.initializeFIFOAndSharedMemory.restype = ctypes.c_int  
clibrary.getTimestamp_Nsec.restype = ctypes.c_long
clibrary.getTimestamp_Sec.restype = ctypes.c_long

class LogoDetectionDataset(ctypes.Structure):
    _fields_ = [("logosDetected", ctypes.c_bool),
                ("logos", ctypes.c_int * 4),
                ("timestampMemoryInsertion_Sec", ctypes.c_long),
                ("timestampMemoryInsertion_Nsec", ctypes.c_long)]
                
def resetLogoDetectionDataset(dataset):
    dataset.logosDetected = False
    dataset.logos = (ctypes.c_int * 4)(0, 0, 0, 0)
    dataset.timestampMemoryInsertion_Sec = 0
    dataset.timestampMemoryInsertion_Nsec = 0

def initializeAndStartCamera():
    picam2 = Picamera2()
    picam2.preview_configuration.main.size = (1280, 720)
    picam2.preview_configuration.main.format = "RGB888"
    picam2.preview_configuration.align()
    picam2.configure("preview")
    picam2.start()
    return picam2
    
def main():
    result = clibrary.initializeFIFOAndSharedMemory()

    if result != 0:
        print("Error from clibrary.initializeFIFOAndSharedMemory()")
        sys.exit(1)
    
    logoDetection = LogoDetectionDataset()   
    resetLogoDetectionDataset(logoDetection)

    picam2 = initializeAndStartCamera()

    model = YOLO(pathToObjectDetectionModel)
    
    detectionTimeout = 300
    lastDetectionTime = time.time()

    while True:
        frame = picam2.capture_array()
        results = model(frame, conf=0.85)
        box = results[0].boxes.cpu().numpy()

        if len(box.cls) > 0:
            lastDetectionTime = time.time()
            
            logoDetection.timestampMemoryInsertion_Sec = clibrary.getTimestamp_Sec()
            logoDetection.timestampMemoryInsertion_Nsec = clibrary.getTimestamp_Nsec()

            logoDetection.logosDetected = True
            for value in np.unique(box.cls):
                if 0 <= value <= 3:
                    logoDetection.logos[int(value)] = 1
            clibrary.writeLogoDetectionDatasetToSharedMemory(logoDetection)
            
        if logoDetection.logosDetected == True:
            resetLogoDetectionDataset(logoDetection)

        """
        annotated_frame = results[0].plot()
        cv2.imshow("Camera", annotated_frame)
        """
    
        if time.time() - lastDetectionTime > detectionTimeout:
            print(f"No logos detected for {detectionTimeout} seconds. Exiting loop.")
            break

    cv2.destroyAllWindows()
    clibrary.detachSharedMemoryAndClosePipe()

if __name__ == "__main__":
    main()