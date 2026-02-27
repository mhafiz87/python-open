# ruff: noqa: F401
import re
import time
import traceback
from enum import StrEnum

from rapidfuzz import fuzz, process
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from logger import logger
from src.config import (
    get_medias,
    get_obs_path,
    get_root_output_dir,
    get_section_to_focus,
    get_section_to_stop,
)


class Element(StrEnum):
    CourseTitle = r'//h1[@data-purpose = "course-header-title"]'
    BuyNowButton = r"//button[@data-purpose='buy-now-button'][.//*[contains(text(), 'Enroll now') or contains(text(), 'Go to course')]]"
    Title = r'//section[@class = "lecture-view--container--mrZSm"]'
    ProgressDisplay = r'//div[@data-purpose = "progress-display"]'
    CurrentTime = r'span[@data-purpose = "current-time"]'
    Duration = r'span[@data-purpose = "duration"]'
    Section = r'//span[@class = "ud-accordion-panel-title"]'
    Lecture = (
        r'//span[@class = "curriculum-item-link--curriculum-item-title-content--S-urg"]'
    )
    LectureProgress = r'//input[@data-purpose = "progress-toggle-button"]'
    PauseButton = r'//button[@data-purpose = "pause-button"]'
    PlayButton = r'//button[@data-purpose = "play-button"]'
    CancelButton = r'//button[@data-purpose = "cancel-button"]'
    GoToNextButton = r'//div[@data-purpose = "go-to-next-button"]'
    GoToNextRightButton = r'//div[@data-purpose = "go-to-next"]'
    RewindButton = r'//button[@data-purpose = "rewind-skip-button"]'
    VideoClass = r'//video[@class = "video-player--video-player--HiAnq"]'
    FullscreenButton = r'//button[@class = "ud-btn ud-btn-small ud-btn-ghost ud-btn-text-sm control-bar-dropdown--trigger--FnmP- control-bar-dropdown--trigger-dark--ZK26r control-bar-dropdown--trigger-small--ogRJ4 "]'
    FullscreenSVG = (
        r"//*[name()='svg'][@aria-label='Fullscreen' or @aria-label='Exit fullscreen']"
    )
    TextViewerClass = (
        r'//div[@data-purpose = "safely-set-inner-html:rich-text-viewer:html"]'
    )
    LastLesson = r'//h2[@data-purpose = "primary-message"]'
    ProgressBar = r'//div[@data-purpose="video-progress-buffer"]'


class Automate:
    def __init__(self) -> None:
        self.driver: WebDriver = None

    def attach_driver(self) -> None:
        options = Options()
        # options.add_argument("--remote-debugging-port=9222")
        # options.add_argument("user-data-dir=C:\\selenium\\ChromeProfile")
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        # options.add_experimental_option("detach", True)
        self.driver = webdriver.Chrome(options=options)
        logger.info(
            f"Attached to existing Chrome session. Current URL: "
            f"\033[4;34m{self.driver.current_url}\033[0m"
        )

    def get_course_name(self) -> str:
        element = WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.XPATH, Element.CourseTitle))
        )
        course = re.sub(r"[^\w\s-]", "", element.text.replace(": ", " - "))
        logger.info(f"Course name: {course}")
        return course

    def get_sections(self) -> list[str]:
        sections: list[str] = []
        elements = self.driver.find_elements(
            by=By.XPATH,
            value=Element.Section,
        )
        for element in elements:
            sections.append(element.text.replace(": ", " - "))
        return sections

    def open_all_sections(self) -> None:
        sections = WebDriverWait(self.driver, 30).until(
            EC.presence_of_all_elements_located((By.XPATH, Element.Section))
        )
        for section in sections:
            button = section.find_element(By.XPATH, "..")
            try:
                if button.get_attribute("aria-expanded") == "false":
                    logger.info(f"{section.text} is collapsed. Expanding...")
                    button.click()
                    logger.info(f"Opened section: {section.text}")
                    time.sleep(1)
                else:
                    logger.info(f"{section.text} is already expanded.")
            except Exception:
                logger.error(f"Failed to open section: {section.text}")
                traceback.print_exc()

    def get_current_media_info(self) -> tuple[str, str]:
        section = ""
        title = ""
        section_pattern = r"^(Section \d{1,3}.*), (Lecture \d{1,3}.*).*"
        try:
            element = WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located((By.XPATH, Element.Title))
            )
            info = element.get_attribute("aria-label")
            result = re.match(section_pattern, info)
            for index, item in enumerate(result.groups()):
                if index == 0:
                    section = re.sub(r"[^\w\s-]", "", item.replace(": ", " - "))
                elif index == 1:
                    title = re.sub(r"[^\w\s-]", "", item.replace(": ", " - "))
            logger.info(f"Current media info - Section: {section}, Title: {title}")
            return section, title
        except Exception:
            traceback.print_exc()
            logger.error("Unable to find media title.")
            return section, title

    def get_all_lectures(self) -> list[str]:
        lectures: list[str] = []
        elements = self.driver.find_elements(
            by=By.XPATH,
            value=Element.Lecture,
        )
        for element in elements:
            lectures.append(element.text.replace(": ", " - "))
        return lectures

    def is_lecture_completed(self, lecture: str) -> bool:
        try:
            lectures = self.driver.find_elements(
                by=By.XPATH,
                value=Element.Lecture,
            )
            target_lecture, score, index = process.extractOne(
                lecture,
                [lecture.text for lecture in lectures],
                scorer=fuzz.token_sort_ratio,
            )
            logger.info(
                f"Target lecture: {target_lecture}, Score: {score}, Index: {index}"
            )
            check_label = self.driver.find_element(
                By.XPATH,
                rf'//input[contains(@aria-label, "Mark lecture {target_lecture.split(". ")[1]}")]',
            )
            logger.info(check_label.get_attribute("aria-label"))
            if "incomplete" in check_label.get_attribute("aria-label").lower():
                logger.info(f"{lecture} is completed.")
                return True
            logger.info(f"{lecture} is not completed.")
            return False
        except Exception:
            traceback.print_exc()
            logger.error(f"Unable to determine {lecture} progress.")
            return False

    def is_current_page_video(self) -> bool:
        try:
            element = WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located((By.XPATH, Element.VideoClass))
            )
            # Move mouse to make UI invisible
            ActionChains(self.driver).move_to_element(element).perform()
            return True
        except Exception:
            return False

    def is_fullscreen(self) -> bool:
        try:
            element = WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located((By.XPATH, Element.FullscreenSVG))
            )
            aria_label = element.get_attribute("aria-label")
            if aria_label == "Fullscreen":
                logger.info("Currently not in fullscreen mode.")
                return False
            else:
                logger.info("Currently in fullscreen mode.")
                return True
        except Exception:
            traceback.print_exc()
            logger.error("Unable to determine fullscreen mode. Assuming in fullscreen.")
            return True

    def toggle_fullscreen(self) -> None:
        try:
            child = WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located((By.XPATH, Element.FullscreenSVG))
            )
            element = child.find_element(By.XPATH, "./..")
            element.click()
            logger.info("Toggled fullscreen mode.")
        except Exception:
            traceback.print_exc()
            logger.error("Unable to toggle fullscreen mode.")

    def is_next_right_button_exist(self) -> tuple[bool, WebElement | None]:
        try:
            element = WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located((By.XPATH, Element.GoToNextRightButton))
            )
            return True, element
        except Exception:
            return False, None

    def is_buy_now_button_exist(self) -> tuple[bool, WebElement | None]:
        try:
            element = WebDriverWait(self.driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, Element.BuyNowButton))
            )
            logger.info("Enroll Now / Go to course button found.")
            return True, element
        except Exception:
            return False, None

    def is_media_paused(self) -> bool:
        try:
            WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located((By.XPATH, Element.PlayButton))
            )
            print("Media is paused.")
            return True
        except Exception:
            print("Media is playing.")
            return False

    def is_media_playing(self) -> bool:
        try:
            WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located((By.XPATH, Element.PauseButton))
            )
            print("Media is playing.")
            return True
        except Exception:
            print("Media is paused.")
            return False

    def is_media_ended(self) -> bool:
        try:
            WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located((By.XPATH, Element.CancelButton))
            )
            logger.info("Media has ended.")
            return True
        except Exception:
            # print("Media is playing...")
            return False

    def is_last_screen(self) -> bool:
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, Element.LastLesson))
            )
            print("This is the last lesson screen.")
            return True
        except Exception:
            # print("This is not the last lesson screen.")
            return False

    def is_ui_visible(self) -> bool:
        try:
            element = WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located((By.XPATH, Element.ProgressBar))
            )
            logger.info(f"Progress bar visibility: {element.is_displayed()}")
            return element.is_displayed()
        except Exception:
            logger.info("Progress bar visibility: False")
            return False

    def make_video_ui_invisible(self) -> None:
        video_element = WebDriverWait(self.driver, 2).until(
            EC.presence_of_element_located((By.XPATH, Element.VideoClass))
        )
        logger.info("Moving mouse to make video UI invisible...")
        ActionChains(self.driver).move_to_element(video_element).perform()
        # ActionChains(self.driver).move_by_offset(200, 200).perform()
        time.sleep(5)

    def show_time_position(self, clear_line: bool = True) -> None:
        LINE_UP = "\033[1A"
        LINE_CLEAR = "\x1b[2K"
        try:
            times = self.get_media_time()
            if times is not None:
                current_time, duration = times
                if clear_line:
                    print(LINE_UP + LINE_CLEAR, end="")
                print(f"Current Time: {current_time} / Duration: {duration}")
        except Exception:
            logger.warning("Unable to get time position.")

    def get_media_time(self) -> tuple[str, str] | None:
        try:
            progress_display = WebDriverWait(automate.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, Element.ProgressDisplay))
            )
            times = progress_display.find_elements(By.XPATH, "./*")
            current_time = times[0].get_attribute("textContent")
            duration = times[2].get_attribute("textContent")
            return current_time, duration
        except Exception:
            logger.warning("Unable to get media time.")
            return None

    def send_spacebar(self) -> None:
        self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.SPACE)

    @staticmethod
    def seconds_to_time(seconds, precision=2):
        """
        Convert seconds to formatted HH:MM:SS string with customizable decimal precision.

        Args:
            seconds (float): Time in seconds
            precision (int): Number of decimal places (default: 6)

        Returns:
            str: Formatted time string in HH:MM:SS.xxxxxx format
        """
        hours = int(seconds // 3600)
        remaining = seconds % 3600
        minutes = int(remaining // 60)
        remaining_seconds = remaining % 60

        # Calculate width for seconds (2 digits + decimal point + precision)
        sec_width = 3 + precision if precision > 0 else 2

        if precision > 0:
            return f"{hours:02d}:{minutes:02d}:{remaining_seconds:0{sec_width}.{precision}f}"
        else:
            return f"{hours:02d}:{minutes:02d}:{int(remaining_seconds):02d}"


if __name__ == "__main__":
    automate = Automate()
    automate.attach_driver()
    automate.get_course_name()
    section, lecture = automate.get_current_media_info()
    print(lecture)
    # print(automate.get_all_lectures())
    automate.is_lecture_completed(lecture)
    automate.show_time_position()
