import os
from datetime import datetime

class RecordingSessionManager:
    def __init__(self, base_dir: str = None):
        """
        Manages the recording session directories.
        :param base_dir: Base directory where session folders are created.
        """
        if base_dir is None:
            base_dir = os.path.join(os.getcwd(), "results")
        self.base_dir = base_dir
        self.session_dir = self._create_session_directory()
        self.svo2_dir = self._create_subdirectory("svo2")
        self.gnss_dir = self._create_subdirectory("gnss")

    def _create_session_directory(self) -> str:
        # Ensure the base directory exists, then create a unique session folder.
        if not os.path.exists(self.base_dir):
            os.mkdir(self.base_dir)
        timestamp_folder = datetime.now().strftime("recording_%Y%m%d_%H%M%S")
        session_dir = os.path.join(self.base_dir, timestamp_folder)
        os.mkdir(session_dir)
        print(f"📁 Recording session folder created at: {session_dir}")
        return session_dir

    def _create_subdirectory(self, subdirname: str) -> str:
        subdirectory = os.path.join(self.session_dir, subdirname)
        if not os.path.exists(subdirectory):
            os.mkdir(subdirectory)
            print(f"📁 Subdirectory '{subdirname}' created at: {subdirectory}")
        return subdirectory

    def get_session_directory(self) -> str:
        return self.session_dir

    def get_svo2_directory(self) -> str:
        return self.svo2_dir

    def get_gnss_directory(self) -> str:
        return self.gnss_dir
