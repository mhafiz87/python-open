# ruff: noqa: F401
import re
import traceback
from enum import StrEnum

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
            value=('//span[@class = "truncate-with-tooltip--ellipsis--YJw4N "]'),
        )
        for element in elements:
            sections.append(element.text.replace(": ", " - "))
        return sections

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
            return section, title
        except Exception:
            traceback.print_exc()
            print("Unable to find media title.")
            return section, title

    def send_spacebar(self) -> None:
        self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.SPACE)


if __name__ == "__main__":
    pass
