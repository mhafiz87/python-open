# ruff: noqa: F401
import base64
import os
import subprocess
import threading
import traceback
from pathlib import Path

import obsws_python as obs
import psutil
from PIL import Image

from logger import logger
from src.config import (
    get_medias,
    get_obs_path,
    get_root_output_dir,
    get_section_to_focus,
    get_section_to_stop,
)


class ObsClient:
    def __init__(self) -> None:
        self.obs_client = None
        self.root_output_dir: Path = get_root_output_dir()
        self.obs_path = get_obs_path()
        self.obs_process: psutil.Popen | None = None

    def connect(self):
        self.obs_client = obs.ReqClient(
            host="localhost",
            port=os.getenv("OBS_PORT"),
            password=os.getenv("OBS_PASSWORD"),
            timeout=3,
        )
        logger.info("Connected to OBS")

    def get_obs_screenshot(self, file_path: str, source_name: str = "chrome") -> None:
        screenshot = self.obs_client.get_source_screenshot(
            source_name, width=1920, height=1080, quality=100, img_format="png"
        )
        if screenshot:
            # Remove the base64 prefix ("data:image/png;base64,")
            base64_data = screenshot.image_data.split(",")[1]
            image_bytes = base64.b64decode(base64_data)

            with open(file_path, "wb") as f:
                f.write(image_bytes)
        else:
            logger.error("Failed to take screenshot")

    def create_output_dir(self, title: str = "") -> None:
        # obs_cl.set_profile_parameter("SimpleOutput", "FilePath", root_output_dir.as_posix())
        output = self.root_output_dir
        if title:
            output = self.root_output_dir / title
        if not output.is_dir():
            output.mkdir(parents=True, exist_ok=True)
        print(f"Created output directory: {output}")

    def set_output_dir(self, name: str) -> None:
        print(f"Setting output directory to: {name}")
        self.obs_client.set_profile_parameter("SimpleOutput", "FilePath", name)

    def set_output_filename(self, name: str) -> None:
        print(f"Setting output filename to: {name}")
        self.obs_client.set_profile_parameter("Output", "FilenameFormatting", name)

    def lauch_obs(self):
        cmd = [self.obs_path, "--multi"]
        try:
            self.obs_process = psutil.Popen(cmd, cwd=str(Path(get_obs_path()).parent))
            logger.info(f"Launched OBS with PID: {self.obs_process.pid}")
        except FileNotFoundError:
            logger.info(
                "Error: Command not found. Make sure 'OBS' is installed and "
                "in your PATH."
            )
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            traceback.print_exc()
            raise

    def start_record(self) -> None:
        try:
            self.obs_client.start_record()
            logger.info("Started recording")
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            traceback.print_exc()
            raise

    def stop_record(self) -> None:
        try:
            self.obs_client.stop_record()
            logger.info("Stopped recording")
        except Exception as e:
            logger.error(f"Failed to stop recording: {e}")
            traceback.print_exc()
            raise

    @staticmethod
    def find_pids_by_name(process_name: str = "obs64.exe") -> list[int]:
        """Return a list of PIDs matching the process name."""
        pids = []
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                if proc.info["name"] == process_name:
                    pids.append(proc.info["pid"])
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                logger.info("Unable to find OBS process.")
        logger.info(f"Found {len(pids)} OBS processes.")
        if pids:
            print(f"OBS processes: {pids}")
        return pids

    def close(self, pid: int):
        try:
            p = psutil.Process(pid)
            p.kill()
            psutil.wait_procs([p], timeout=60)
            logger.info(f"Closed OBS process with PID: {pid}")
        except psutil.NoSuchProcess:
            logger.warning(f"Error: No such process with PID {pid}")
        except psutil.AccessDenied:
            logger.error(
                "Error: Access denied. Try running the script as an"
                " administrator/superuser."
            )
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            raise


if __name__ == "__main__":
    obs = ObsClient()
    obs_pids = obs.find_pids_by_name("obs64.exe")
    if not obs_pids:
        obs.lauch_obs()
    else:
        for obs_pid in obs_pids:
            obs.close(obs_pid)
