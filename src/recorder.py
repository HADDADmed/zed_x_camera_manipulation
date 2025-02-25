import pyzed.sl as sl  # 🎥 ZED SDK for camera operations
import threading       # 🧵 For concurrent camera grabbing threads
import time            # ⏱️ For sleep/delay
import os              # 📁 For file system operations
from datetime import datetime  # 📆 For timestamping sessions
from abc import ABC, abstractmethod  # 🛠️ For defining interfaces

# ============================================================
# Interface: ICameraRecorder (ISP, DIP)
# ============================================================
class ICameraRecorder(ABC):
    @abstractmethod
    def open_camera(self) -> bool:
        """Opens the camera device."""
        pass

    @abstractmethod
    def start_recording(self) -> bool:
        """Starts recording to a file."""
        pass

    @abstractmethod
    def start_grabbing(self) -> None:
        """Starts grabbing frames in a separate thread."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Signals the grabbing thread to stop."""
        pass

    @abstractmethod
    def join(self) -> None:
        """Waits for the grabbing thread to finish."""
        pass

# ============================================================
# Implementation: ZEDCameraRecorder (SRP, LSP)
# ============================================================
class ZEDCameraRecorder(ICameraRecorder):
    def __init__(self, camera_info: sl.CameraInformation, init_params: sl.InitParameters, session_dir: str):
        """
        Initializes the ZED camera recorder.
        :param camera_info: The camera's information (serial number, etc.)
        :param init_params: Initialization parameters for the camera
        :param session_dir: Directory to store the recording file
        """
        self.camera_info = camera_info
        self.init_params = init_params
        self.session_dir = session_dir
        self.camera = sl.Camera()
        self.thread = None
        self._stop = False

    def open_camera(self) -> bool:
        # 🔧 Set camera parameters based on the serial number and open it
        self.init_params.set_from_serial_number(self.camera_info.serial_number)
        status = self.camera.open(self.init_params)
        if status != sl.ERROR_CODE.SUCCESS:
            print(f"❌ Error opening camera {self.camera_info.serial_number}: {repr(status)}")
            return False
        return True

    def start_recording(self) -> bool:
        # 💾 Define a unique SVO file name and enable recording
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
        # 🔄 Continuously grab frames until signaled to stop
        runtime = sl.RuntimeParameters()
        while not self._stop:
            err = self.camera.grab(runtime)
            if err != sl.ERROR_CODE.SUCCESS:
                print(f"⚠️ Camera {self.camera_info.serial_number} grab error: {err}")
            time.sleep(0.001)  # 💤 Short sleep to avoid CPU overload
        self.camera.close()
        print(f"🛑 Camera {self.camera_info.serial_number} stopped.")

    def start_grabbing(self) -> None:
        # 🚀 Start the grabbing thread for this camera
        self.thread = threading.Thread(target=self._grab_run)
        self.thread.start()

    def stop(self) -> None:
        # 🛑 Signal the thread to stop
        self._stop = True

    def join(self) -> None:
        # 🔗 Wait for the thread to finish
        if self.thread is not None:
            self.thread.join()

# ============================================================
# Session Manager: RecordingSessionManager (SRP)
# ============================================================
class RecordingSessionManager:
    def __init__(self, base_dir: str = None):
        """
        Manages the recording session directory.
        :param base_dir: Base directory where session folders are created.
        """
        if base_dir is None:
            base_dir = os.path.join(os.getcwd(), "results")
        self.base_dir = base_dir
        self.session_dir = self._create_session_directory()

    def _create_session_directory(self) -> str:
        # 📁 Ensure the base directory exists, then create a unique session folder
        if not os.path.exists(self.base_dir):
            os.mkdir(self.base_dir)
        timestamp_folder = datetime.now().strftime("recording_%Y%m%d_%H%M%S")
        session_dir = os.path.join(self.base_dir, timestamp_folder)
        os.mkdir(session_dir)
        print(f"📁 Recording session folder created at: {session_dir}")
        return session_dir

    def get_session_directory(self) -> str:
        return self.session_dir

# ============================================================
# Controller: RecordingController (SRP, DIP)
# ============================================================
class RecordingController:
    def __init__(self):
        """
        Orchestrates the entire recording process.
        """
        self.camera_recorders = []  # List[ICameraRecorder]
        self.session_manager = RecordingSessionManager()
        self.init_params = self._setup_init_params()

    def _setup_init_params(self) -> sl.InitParameters:
        # ⚙️ Set up common initialization parameters for all cameras
        init_params = sl.InitParameters()
        init_params.camera_resolution = sl.RESOLUTION.HD1200
        init_params.camera_fps = 30
        # Optionally enable real-time SVO mode if needed:
        # init_params.svo_real_time_mode = True
        return init_params

    def discover_and_setup_cameras(self):
        # 🔍 Discover available ZED cameras
        cameras_info = sl.Camera.get_device_list()
        if len(cameras_info) == 0:
            print("❌ No ZED cameras detected.")
            return

        # For each detected camera, create and configure a recorder
        for cam_info in cameras_info:
            recorder = ZEDCameraRecorder(cam_info, self.init_params, self.session_manager.get_session_directory())
            if recorder.open_camera() and recorder.start_recording():
                self.camera_recorders.append(recorder)

        if not self.camera_recorders:
            print("❌ No cameras were successfully opened for recording.")

    def start_recording(self):
        # ▶️ Start grabbing frames on all configured cameras
        for recorder in self.camera_recorders:
            recorder.start_grabbing()
        print("🎥 Recording started. Press Enter to stop recording...")

    def stop_recording(self):
        # 🛑 Signal all recorders to stop and wait for their threads to finish
        for recorder in self.camera_recorders:
            recorder.stop()
        for recorder in self.camera_recorders:
            recorder.join()
        print("🛑 Recording stopped.")
        print("💾 SVO files saved in:", self.session_manager.get_session_directory())

    def run(self):
        # 🚀 Main entry point: discover, start, wait for input, then stop recording
        self.discover_and_setup_cameras()
        if not self.camera_recorders:
            return
        self.start_recording()
        input()  # ⌨️ Wait for the user to press Enter to stop
        self.stop_recording()

# ============================================================
# Program Entry Point
# ============================================================
if __name__ == "__main__":
    controller = RecordingController()
    controller.run()
