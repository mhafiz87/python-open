# ruff: noqa: F401
import threading
import time
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image

from auto import Automate, MediaType
from config import get_root_output_dir
from logger import log_file_handler, logger
from obs_client import ObsClient

ROOT_OUTPUT_DIR = get_root_output_dir()
FRAME_CHECK_INTERVAL = 5
IMAGE_1_NAME = Path(ROOT_OUTPUT_DIR / "debug_screenshot_1.png").as_posix()
IMAGE_2_NAME = Path(ROOT_OUTPUT_DIR / "debug_screenshot_2.png").as_posix()
frame_counter: int = 1
media_stop_event = threading.Event()
media_stop_event.clear()


def handle_frame_freeze(obs: ObsClient, media: str) -> None:
    global frame_counter
    if frame_counter % 2 == 1:
        obs.get_obs_screenshot((ROOT_OUTPUT_DIR / IMAGE_1_NAME).as_posix())
        frame_counter = 2
    else:
        obs.get_obs_screenshot((ROOT_OUTPUT_DIR / IMAGE_2_NAME).as_posix())
        frame_counter = 1
    img1 = Image.open(IMAGE_1_NAME)
    img2 = Image.open(IMAGE_2_NAME)
    img1_array = np.array(img1)
    img2_array = np.array(img2)
    freeze = np.array_equal(img1_array, img2_array)
    if freeze:
        logger.warning("Frame freeze detected in OBS.")
        logger.warning(f"Stopping {media} due to freeze.")
        logger.warning("Stopping process.")
        obs.stop_record()
        exit(1)


def check_time_and_frame(
    obs: ObsClient,
    automate: Automate,
    new_media: bool,
    section: str,
    lecture: str,
) -> None:
    obs.get_obs_screenshot(IMAGE_2_NAME)
    frame_check_initial_time: float = time.monotonic()
    current_time, duration = automate.show_time_position(clear_line=not new_media)
    if current_time == duration:
        logger.warning(
            "Current time equals duration, media might have ended or paused."
        )
        logger.warning(f"Stopping media: {section}/{lecture}")
    frame_check_time = time.monotonic()
    if frame_check_time - frame_check_initial_time >= FRAME_CHECK_INTERVAL:
        handle_frame_freeze(obs, f"{section}/{lecture}")
        frame_check_initial_time = frame_check_time


if __name__ == "__main__":
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file_handler.write_header(f"Web Parser: Start At {timestamp}")
    automate = Automate()
    obs = ObsClient()
    obs.connect()
    # There's a possibility that course name is too long and causes OBS
    # recording error, so set output dir to root dir first, then manually copy
    # and paste to course dir after recording is done
    obs.create_output_dir(ROOT_OUTPUT_DIR.as_posix())
    obs.set_output_dir(ROOT_OUTPUT_DIR.as_posix())

    automate.attach_driver()
    # TODO: [ ] open url in config, handle go to course page and open first section
    course_name = automate.get_course_name()
    automate.open_all_sections()
    while True:
        if not automate.is_fullscreen():
            automate.toggle_fullscreen()
        # TODO: [ ] handle focus
        section, lecture = automate.get_current_media_info()
        obs.set_output_filename(f"{section}/{lecture}")
        current_media_type = automate.get_current_media_type()
        if current_media_type == MediaType.ARTICLE:
            automate.save_text_content(
                output=Path(ROOT_OUTPUT_DIR / section / f"{lecture}.txt").as_posix()
            )
        elif current_media_type == MediaType.VIDEO:
            for _ in range(5):
                if automate.is_media_paused():
                    automate.send_spacebar()
                else:
                    break
                time.sleep(1)
            else:
                logger.error("Unable to play the video.")
                raise Exception("Unable to play the video.")
            for _ in range(5):
                if automate.is_ui_visible():
                    automate.make_video_ui_invisible()
                else:
                    break
            else:
                logger.error("Unable to hide the video UI.")
                raise Exception("Unable to hide the video UI.")
            automate.restart_media()
            obs.start_record()
            obs.get_obs_screenshot(IMAGE_2_NAME)
            new_media = True
            while True:
                if automate.is_media_ended():
                    logger.info(f"Media ended: {section}/{lecture}")
                    break
                check_time_and_frame(obs, automate, new_media, section, lecture)
                new_media = False
                time.sleep(1)
            obs.stop_record()
        if not automate.go_to_next_media():
            break
