import os
import time
import threading
import pyzed.sl as sl
from .icamera_recorder import ICameraRecorder

class ZEDCameraRecorder(ICameraRecorder):
    def __init__(self, camera_info: sl.CameraInformation, init_params: sl.InitParameters, session_dir: str):
        """
        Initializes the ZED camera recorder.
        :param camera_info: The camera's information (serial number, etc.)
        :param init_params: Initialization parameters for the camera.
        :param session_dir: Directory to store the SVO file (should be the svo2 folder).
        """
        self.camera_info = camera_info
        self.init_params = init_params
        self.session_dir = session_dir
        self.camera = sl.Camera()
        self.thread = None
        self._stop = False

    def open_camera(self) -> bool:
        # Set camera parameters based on the serial number and open it.
        self.init_params.set_from_serial_number(self.camera_info.serial_number)
        status = self.camera.open(self.init_params)
        if status != sl.ERROR_CODE.SUCCESS:
            print(f"❌ Error opening camera {self.camera_info.serial_number}: {repr(status)}")
            return False
        return True

    def start_recording(self) -> bool:
        # Define a unique SVO file name and enable recording.
        svo_filename = os.path.join(self.session_dir, f"camera_{self.camera_info.serial_number}.svo")
        recording_params = sl.RecordingParameters(svo_filename)
        err = self.camera.enable_recording(recording_params)
        if err != sl.ERROR_CODE.SUCCESS:
            print(f"❌ Error starting recording on camera {self.camera_info.serial_number}: {err}")
            self.camera.close()
            return False
        print(f"✅ Camera {self.camera_info.serial_number} is recording to {svo_filename}")
        return True

    def _grab_run(self):
        # Continuously grab frames until signaled to stop.
        runtime = sl.RuntimeParameters()
        while not self._stop:
            err = self.camera.grab(runtime)
            if err != sl.ERROR_CODE.SUCCESS:
                print(f"⚠️ Camera {self.camera_info.serial_number} grab error: {err}")
            time.sleep(0.001)  # Short sleep to avoid CPU overload.
        self.camera.close()
        print(f"🛑 Camera {self.camera_info.serial_number} stopped.")

    def start_grabbing(self) -> None:
        # Start the grabbing thread for this camera.
        self.thread = threading.Thread(target=self._grab_run)
        self.thread.start()

    def stop(self) -> None:
        # Signal the thread to stop.
        self._stop = True

    def join(self) -> None:
        # Wait for the thread to finish.
        if self.thread is not None:
            self.thread.join()
