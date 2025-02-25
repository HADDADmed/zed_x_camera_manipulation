# zed_x_camera_manipulation
# Project Structure Documentation

## 📁 Project Structure
```
zed_x_camera_manipulation/
│-- config/
│-- docs/
│-- results/
│-- src/
│   │-- main.py
│   │-- gui.py
│   │-- recorder/
│   │   │-- __init__.py
│   │   │-- gnss_recorder.py
│   │   │-- gpsd_reader.py
│   │   │-- icamera_recorder.py
│   │   │-- recording_controller.py
│   │   │-- recording_session_manager.py
│   │   │-- zed_camera_recorder.py
│-- README.md
```
---
## 📜 File Descriptions

### `src/main.py`
**Description:** Entry point of the application, responsible for initializing the recording process.
- **Inputs:** None (directly executed)
- **Outputs:** Controls camera and GNSS data recording
- **Called By:** User (via command line)
- **Calls:** `RecordingController` (from `recording_controller.py`)

### `src/recorder/recording_controller.py`
**Description:** Manages camera and GNSS synchronization, initializes devices, and controls recording.
- **Inputs:** None (instantiated in `main.py`)
- **Outputs:** Manages `GNSSRecorder`, `ZedCameraRecorder`, and `ICameraRecorder`
- **Called By:** `main.py`
- **Calls:** `GNSSRecorder`, `ZedCameraRecorder`, `ICameraRecorder`

### `src/recorder/gnss_recorder.py`
**Description:** Manages GNSS data collection and stores synchronized data with video frames.
- **Inputs:** GPSD connection
- **Outputs:** JSON file with GNSS timestamps and coordinates
- **Called By:** `RecordingController`
- **Calls:** `GPSDReader`

### `src/recorder/gpsd_reader.py`
**Description:** Reads GNSS data from the GPSD daemon.
- **Inputs:** GPSD socket connection
- **Outputs:** Latitude, longitude, altitude
- **Called By:** `GNSSRecorder`

### `src/recorder/icamera_recorder.py`
**Description:** Handles additional camera types apart from ZED, managing their initialization and recording.
- **Inputs:** Camera index, file paths
- **Outputs:** Video files stored in `results/`
- **Called By:** `RecordingController`

### `src/recorder/zed_camera_recorder.py`
**Description:** Manages ZED camera initialization and recording, handling `.svo` video storage.
- **Inputs:** Camera settings, file paths
- **Outputs:** `.svo` video files stored in `results/`
- **Called By:** `RecordingController`
- **Calls:** ZED SDK functions

### `src/recorder/recording_session_manager.py`
**Description:** Manages different recording sessions, ensuring proper file handling and organization.
- **Inputs:** Session details (timestamp, devices used)
- **Outputs:** Organized session files
- **Called By:** `RecordingController`

### `src/results/`
**Description:** Stores all generated `.svo` files, GNSS data, and GUI elements.
- **Outputs:**
  - `camera_X_output.svo` (video recordings from cameras)
  - `synchronized_gnss_data.json` (recorded GNSS data)
  - GUI-related files

### `src/results/gui.py`
**Description:** Contains GUI-related components for visualizing the recorded data.
- **Inputs:** Recorded data
- **Outputs:** Graphical representations of GNSS and video data
- **Called By:** Future GUI applications

---
## 💡 Future Development Notes
- New sensors can be integrated by adding separate recorder classes and modifying `RecordingController`.
- Ensure GNSS synchronization with cameras by adjusting timestamp handling.
- If using a different GPS module, modify `GPSDReader` accordingly.
- A dedicated GUI can be further developed in `gui.py`.

---
### 🚀 Running the Project
To start recording:
```bash
python src/main.py
```
Recorded files will be stored in `src/results/`.

