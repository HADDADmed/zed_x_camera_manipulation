from recorder.recording_controller import RecordingController

from pyzed.sl import RESOLUTION

def main():
    # Provide a valid resolution type from the ZED SDK.
    config = {
        "camera_resolution": RESOLUTION.HD1200,  # Use a valid RESOLUTION enum.
        "camera_fps": 30,
        "gnss_port": "COM3",
        "gnss_baudrate": 9600
    }
    controller = RecordingController(config=config)
    controller.run()

if __name__ == "__main__":
    main()

