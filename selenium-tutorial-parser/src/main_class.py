# ruff: noqa: F401
import time

from auto import Automate, MediaType
from logger import logger
from obs_client import ObsClient

if __name__ == "__main__":
    automate = Automate()
    # obs_client = ObsClient()

    automate.attach_driver()
    # TODO: [ ] open url in config, handle go to course page and open first section
    automate.open_all_sections()
    # TODO: [ ] handle focus
    current_media_type = automate.get_current_media_type()
    if current_media_type == MediaType.UNKNOWN:
        automate.go_to_next_media()
    elif current_media_type == MediaType.ARTICLE:
        pass
        # automate.save_text_content()
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
        # TODO: [ ] handle start and stop recording, handle focus
