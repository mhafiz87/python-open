# ruff: noqa: F401
# TODO: Save current media for if stuck in loading, auto reload current course then navigate to current media
# TODO: Config; if `medias` 1st element is empty string, assume already in course page.
# TODO: Config; if `medias` element is not empty string, load course name, then navigate to media
# TODO: handle if video took too long to load
# TODO: Wait for play button to appear after lecture page loads, in fail reload page
# TODO: After saving caption, check if it's valid. If has `thumb-sprites`, not valid, retry again
# TODO: Make a table of database to store progress an/or issues

import threading
import time
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image

from auto import Automate, MediaType
from config import get_medias, get_root_output_dir
from logger import log_file_handler, logger
from obs_client import ObsClient

MAX_ATTEMPTS = 5
course_ended = 0
ROOT_OUTPUT_DIR = get_root_output_dir()
FRAME_CHECK_INTERVAL = 60 * 3
IMAGE_1_NAME = Path(ROOT_OUTPUT_DIR / "debug_screenshot_1.png").as_posix()
IMAGE_2_NAME = Path(ROOT_OUTPUT_DIR / "debug_screenshot_2.png").as_posix()
frame_counter: int = 1
media_stop_event = threading.Event()
media_stop_event.clear()


def handle_frame_freeze(obs: ObsClient, media: str) -> bool:
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
    return freeze


def check_frame_freeze(obs: ObsClient, check_time: float, media: str) -> bool:
    frame_check_time = time.monotonic()
    if frame_check_time - check_time >= FRAME_CHECK_INTERVAL:
        if handle_frame_freeze(obs, media):
            exit(1)
        return False
    return True


def check_time(obs: ObsClient, automate: Automate, new_media: bool, media: str) -> bool:
    obs.get_obs_screenshot(IMAGE_2_NAME)
    current_time, duration = automate.show_time_position(clear_line=not new_media)
    if current_time == duration:
        logger.warning(
            "Current time equals duration, media might have ended or paused."
        )
        logger.warning(f"Stopping media: {media}")
        return False
    return True


def reload_current_page() -> None:
    logger.error("Unable to play the video.")
    logger.info("Reloading current page...")
    url = automate.driver.current_url.split("lecture")[0]
    automate.driver.get(url)
    time.sleep(7)


def record_video_content(automate: Automate, section: str, lecture: str) -> int:
    automate.get_caption(
        filename=Path(ROOT_OUTPUT_DIR / section / f"{lecture}.vtt").as_posix()
    )
    # exit(1)
    automate.download_resources(section, lecture)
    # return 0

    # ---TEMP---
    # if not automate.is_fullscreen():
    #     automate.toggle_fullscreen()
    # for _ in range(5):
    #     if automate.is_media_paused():
    #         automate.send_spacebar()
    #     else:
    #         break
    #     time.sleep(1)
    # else:
    #     reload_current_page()
    #     return 1
    #     # raise Exception("Unable to play the video.")

    automate.send_f()
    time.sleep(3)
    automate.send_spacebar()
    time.sleep(3)

    for _ in range(5):
        if automate.is_ui_visible():
            automate.make_video_ui_invisible()
        else:
            break
    else:
        reload_current_page()
        return 2
        # raise Exception("Unable to hide the video UI.")

    automate.toggle_hide_inactivity(True)

    automate.restart_media()
    obs.start_record()
    obs.get_obs_screenshot(IMAGE_2_NAME)
    frame_check_time: float = time.monotonic()
    new_media = True
    while True:
        if automate.is_media_ended():
            logger.info(f"Media ended: {section}/{lecture}")
            break
        if not check_frame_freeze(obs, frame_check_time, f"{section}/{lecture}"):
            frame_check_time = time.monotonic()
        if not check_time(obs, automate, new_media, f"{section}/{lecture}"):
            break
        new_media = False
        time.sleep(1)
    obs.stop_record()

    automate.toggle_hide_inactivity(False)

    return 0


def record_course_content(automate: Automate, obs: ObsClient) -> None:
    global course_ended
    course_name = automate.get_course_name()
    (ROOT_OUTPUT_DIR / course_name).mkdir(parents=True, exist_ok=True)
    # automate.open_all_sections()
    attempt = 0
    while course_ended != 1:
        section = ""
        lecture = ""
        automate.driver.execute_script("window.scrollTo(0, 0);")
        while attempt < MAX_ATTEMPTS:
            current_url = automate.driver.current_url.split("#overview")[0]
            try:
                automate.get_course_name()
            except Exception as error:
                logger.error(f"{type(error).__name__}")
                logger.error("Unable to get current media info.")
                status = automate.go_to_next_media()
                if status == 0:
                    continue
                logger.info(f"Reloading current page: {current_url}")
                automate.driver.get(current_url)
                time.sleep(15)
                attempt += 1
                continue
            if automate.is_fullscreen():
                automate.toggle_fullscreen()
            # TODO: [ ] handle focus
            section, lecture = automate.get_current_media_info()
            (ROOT_OUTPUT_DIR / section).mkdir(parents=True, exist_ok=True)
            obs.set_output_filename(f"{section}/{lecture}")
            if "quiz" in current_url:
                logger.info("Skipping quiz.")
                current_media_type = MediaType.QUIZ
            else:
                current_media_type = automate.get_current_media_type()
            if current_media_type == MediaType.ARTICLE:
                automate.save_text_content(
                    output=Path(ROOT_OUTPUT_DIR / section / f"{lecture}.txt").as_posix()
                )
                automate.download_resources(section, lecture)
            elif current_media_type == MediaType.VIDEO:
                automate.driver.execute_script("window.scrollTo(0, 0);")
                if automate.is_fullscreen():
                    automate.toggle_fullscreen()
                if record_video_content(automate, section, lecture) > 0:
                    attempt += 1
                    continue
            course_ended = automate.go_to_next_media()
            if course_ended > 0:
                break
        else:
            logger.warning(
                f"Failed to play media {section}/{lecture} "
                f"after {MAX_ATTEMPTS} attempts."
            )
            logger.warning("Stopping process.")
            exit(1)
    logger.info(f"Course {course_name} ended.")


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
    reload_current_page()
    courses = get_medias()
    logger.info(f"{courses}")
    for index, course in enumerate(courses):
        logger.info(f"Processing {course}...")
        if index > 0 and not course:
            logger.warning(
                "Config Error: `medias` should only have one empty string, and"
                " it's the first element. Continue next element."
            )
            continue
        elif course:
            automate.driver.get(course)
            course_button_exists, course_button = automate.is_buy_now_button_exist()
            if course_button_exists:
                course_button.click()
                time.sleep(30)  # Wait for navigation to course page
        record_course_content(automate, obs)
        if index < len(courses) - 1:
            course_ended = 0
        else:
            course_ended = 1
    else:
        logger.info("Done...")

    automate.driver.quit()
    obs.obs_client.disconnect()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file_handler.write_header(f"Web Parser: End At {timestamp}")
