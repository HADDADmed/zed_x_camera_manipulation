import os
import time
import threading
import json
import pyzed.sl as sl
from .gpsd_reader import GPSDReader

class GNSSRecorder:
    def __init__(self, session_dir: str, port: str = "COM3", baudrate: int = 9600):
        """
        Initializes the GNSS sensor recorder.
        :param session_dir: Directory to store GNSS JSON data (should be the gnss folder).
        :param port: Port for the GNSS sensor.
        :param baudrate: Baud rate for the GNSS sensor.
        """
        self.session_dir = session_dir
        self.port = port
        self.baudrate = baudrate
        self._stop = False
        self.thread = None
        self.file_path = os.path.join(session_dir, "gnss_data.json")
        self.file = None
        # Create an instance of GPSDReader to interface with the GNSS sensor.
        self.gpsd_reader = GPSDReader()

    def open_sensor(self) -> bool:
        """
        Opens and initializes the GNSS sensor via the GPSDReader.
        :return: True if successful, False otherwise.
        """
        print(f"🔧 Opening GNSS sensor on port {self.port} at {self.baudrate} baud.")
        if self.gpsd_reader.initialize() == -1:
            print("❌ Failed to initialize GPSDReader.")
            return False
        return True

    def start_recording(self) -> bool:
        """
        Opens the output file for GNSS data.
        :return: True if the file was opened successfully, False otherwise.
        """
        try:
            self.file = open(self.file_path, "w")
        except Exception as e:
            print(f"❌ Failed to open GNSS data file: {e}")
            return False
        print(f"✅ GNSS sensor recording to {self.file_path}")
        return True

    def _log_data(self):
        """
        Continuously grabs GNSS data using GPSDReader and writes each record in JSON format.
        """
        while not self._stop:
            status, input_gnss = self.gpsd_reader.grab()
            if status == sl.ERROR_CODE.SUCCESS:
                record = {
                    "timestamp": time.time(),
                    "latitude": None,
                    "longitude": None,
                    "altitude": None
                }
                try:
                    # Retrieve coordinates; adjust the 'False' parameter as needed.
                    latitude, longitude, altitude = input_gnss.get_coordinates(False)
                    record["latitude"] = round(latitude, 6)
                    record["longitude"] = round(longitude, 6)
                    record["altitude"] = round(altitude, 2)
                except Exception as e:
                    print("⚠️ Error reading GNSS coordinates:", e)
                json_record = json.dumps(record)
                self.file.write(json_record + "\n")
                self.file.flush()
            time.sleep(1)  # Adjust this delay to match the GNSS sensor's update rate if necessary.
        self.file.close()
        print("🛑 GNSS sensor recording stopped.")

    def start_logging(self) -> None:
        """
        Starts the GNSS logging in a separate thread.
        """
        self.thread = threading.Thread(target=self._log_data)
        self.thread.start()

    def stop(self) -> None:
        """
        Signals the logging thread to stop.
        """
        self._stop = True

    def join(self) -> None:
        """
        Waits for the logging thread to finish.
        """
        if self.thread is not None:
            self.thread.join()
