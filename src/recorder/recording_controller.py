import pyzed.sl as sl
from .zed_camera_recorder import ZEDCameraRecorder
from .gnss_recorder import GNSSRecorder
from .recording_session_manager import RecordingSessionManager

class RecordingController:
    def __init__(self, config: dict = None):
        """
        Orchestrates the entire recording process.
        :param config: Dictionary containing configuration parameters.
        """
        # Default configuration parameters.
        default_config = {
            "camera_resolution": sl.RESOLUTION.HD1200,
            "camera_fps": 30,
            "gnss_port": "COM3",
            "gnss_baudrate": 9600
        }
        if config is not None:
            default_config.update(config)
        self.config = default_config

        self.camera_recorders = []  # List to hold camera recorder instances.
        self.gnss_recorder = None   # GNSS sensor recorder.
        self.session_manager = RecordingSessionManager()
        self.init_params = self._setup_init_params()

    def _setup_init_params(self) -> sl.InitParameters:
        init_params = sl.InitParameters()
        init_params.camera_resolution = self.config["camera_resolution"]
        init_params.camera_fps = self.config["camera_fps"]
        # Optionally enable real-time SVO mode if needed:
        # init_params.svo_real_time_mode = True
        return init_params

    def discover_and_setup_devices(self):
        # Discover available ZED cameras.
        cameras_info = sl.Camera.get_device_list()
        if len(cameras_info) == 0:
            print("❌ No ZED cameras detected.")
        else:
            for cam_info in cameras_info:
                recorder = ZEDCameraRecorder(
                    cam_info,
                    self.init_params,
                    self.session_manager.get_svo2_directory()  # SVO files go in the svo2 folder.
                )
                if recorder.open_camera() and recorder.start_recording():
                    self.camera_recorders.append(recorder)
            if not self.camera_recorders:
                print("❌ No cameras were successfully opened for recording.")

        # Set up the GNSS sensor recorder.
        self.gnss_recorder = GNSSRecorder(
            session_dir=self.session_manager.get_gnss_directory(),  # GNSS JSON data goes in the gnss folder.
            port=self.config["gnss_port"],
            baudrate=self.config["gnss_baudrate"]
        )
        if self.gnss_recorder.open_sensor() and self.gnss_recorder.start_recording():
            print("✅ GNSS sensor is set up and recording.")
        else:
            print("❌ GNSS sensor failed to start recording.")

    def start_recording(self):
        for recorder in self.camera_recorders:
            recorder.start_grabbing()
        if self.gnss_recorder:
            self.gnss_recorder.start_logging()
        print("🎥 Recording started. Press Enter to stop recording...")

    def stop_recording(self):
        for recorder in self.camera_recorders:
            recorder.stop()
        for recorder in self.camera_recorders:
            recorder.join()
        if self.gnss_recorder:
            self.gnss_recorder.stop()
            self.gnss_recorder.join()
        print("🛑 Recording stopped.")
        print("💾 SVO files saved in:", self.session_manager.get_svo2_directory())
        print("💾 GNSS data saved in:", self.session_manager.get_gnss_directory())

    def run(self):
        self.discover_and_setup_devices()
        if not self.camera_recorders and not self.gnss_recorder:
            return
        self.start_recording()
        input()  # Wait for user input to stop.
        self.stop_recording()
