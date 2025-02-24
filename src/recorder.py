import pyzed.sl as sl
import threading
import time
import os
from datetime import datetime

# Global lists to hold camera objects and threads
zed_list = []
thread_list = []
stop_signal = False

def grab_run(index):
    """
    Thread function for continuously grabbing frames from a ZED camera.
    With recording enabled, frames are saved automatically to the SVO file.
    """
    runtime = sl.RuntimeParameters()
    while not stop_signal:
        err = zed_list[index].grab(runtime)
        if err != sl.ERROR_CODE.SUCCESS:
            print(f"Camera {index} grab error: {err}")
        # Small sleep to avoid overloading the CPU
        time.sleep(0.001)
    zed_list[index].close()
	
def main():
    global stop_signal, zed_list, thread_list

    # ===============================
    # Create a results folder with a unique timestamp
    # ===============================
    base_results_dir = os.path.join(os.getcwd(), "results")
    if not os.path.exists(base_results_dir):
        os.mkdir(base_results_dir)
    
    # Create a unique subfolder for this recording session (e.g., "recording_20250302_142530")
    timestamp_folder = datetime.now().strftime("recording_%Y%m%d_%H%M%S")
    session_dir = os.path.join(base_results_dir, timestamp_folder)
    os.mkdir(session_dir)
    print("Recording session folder created at:", session_dir)

    # ===============================
    # Set up ZED camera initialization parameters
    # ===============================
    init_params = sl.InitParameters()
    init_params.camera_resolution = sl.RESOLUTION.HD720
    init_params.camera_fps = 30
    # (Optional) You can enable real-time SVO recording mode if needed:
    # init_params.svo_real_time_mode = True

    # ===============================
    # Open available ZED cameras and start recording
    # ===============================
    cameras = sl.Camera.get_device_list()
    if len(cameras) == 0:
        print("No ZED cameras detected.")
        return

    for i, cam in enumerate(cameras):
        # Set the initialization parameters for this camera using its serial number
        init_params.set_from_serial_number(cam.serial_number)
        zed = sl.Camera()
        status = zed.open(init_params)
        if status != sl.ERROR_CODE.SUCCESS:
            print(f"Error opening camera {cam.serial_number}: {repr(status)}")
            continue

        # Define a unique SVO file name for this camera inside the session folder
        svo_filename = os.path.join(session_dir, f"camera_{cam.serial_number}.svo")
        recording_params = sl.RecordingParameters(svo_filename)
        err = zed.start_recording(recording_params)
        if err != sl.ERROR_CODE.SUCCESS:
            print(f"Error starting recording on camera {cam.serial_number}: {err}")
            zed.close()
            continue

        print(f"Camera {cam.serial_number} is recording to {svo_filename}")
        zed_list.append(zed)
    
    if not zed_list:
        print("No cameras were successfully opened for recording.")
        return

    # ===============================
    # Start threads for each camera to continuously grab frames
    # ===============================
    for i in range(len(zed_list)):
        thread = threading.Thread(target=grab_run, args=(i,))
        thread.start()
        thread_list.append(thread)
    
    # ===============================
    # Wait for user input to stop recording
    # ===============================
    print("Recording started. Press Enter to stop recording...")
    input()  # Wait for the user to press Enter

    # Signal all threads to stop
    stop_signal = True

    # Wait for all threads to finish
    for thread in thread_list:
        thread.join()
    
    print("Recording stopped.")
    print("SVO files saved in:", session_dir)
    
if __name__ == "__main__":
    main()
