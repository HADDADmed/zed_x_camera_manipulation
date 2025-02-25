from abc import ABC, abstractmethod

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
