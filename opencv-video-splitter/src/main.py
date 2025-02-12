import concurrent.futures
import multiprocessing
import time
from datetime import timedelta
from pathlib import Path

import cv2
import imagehash
from PIL import Image

HAMMING_THRESHOLD = 5
VIDEO_PATH = Path(__file__).parent.joinpath("data", "video.mkv")
REF_IMG_PATH = Path(__file__).parent.joinpath("data", "ref.png")
STEPS = 15


def temp() -> None:
    ref_img_cv2 = cv2.imread(REF_IMG_PATH, cv2.COLOR_BGR2RGB)
    ref_img_cvt = Image.fromarray(ref_img_cv2)
    ref_img_hash = imagehash.average_hash(ref_img_cvt)
    print(f"{'Reference image hash': <20}: {ref_img_hash}")


def process_video(start_frame: int, end_frame: int, steps: int) -> list[list[int]]:
    marks: list[list[int]] = []
    video = cv2.VideoCapture(VIDEO_PATH)
    ref_img_hash = imagehash.average_hash(Image.open(REF_IMG_PATH))
    print(f"{'Reference image hash': <20}: {ref_img_hash}")
    print(f"{'Video frame count': <20}: {video.get(cv2.CAP_PROP_FRAME_COUNT)}")
    print(f"{'Video fps': <20}: {video.get(cv2.CAP_PROP_FPS)}")
    print(
        f"{'Total playback': <20}: "
        f"{
            time.strftime('%H:%M:%S', time.gmtime(
                video.get(cv2.CAP_PROP_FRAME_COUNT) /
                video.get(cv2.CAP_PROP_FPS)
            ))
        }"
    )
    print("\n")
    start_time = time.time()
    point_1 = False
    # for current_frame in range(0, int(video.get(cv2.CAP_PROP_FRAME_COUNT)), 15):
    for current_frame in range(start_frame, end_frame, steps):
        success, frame = video.read()
        if int(video.get(cv2.CAP_PROP_POS_FRAMES)) < start_frame:
            print(
                f"Current frame ({video.get(cv2.CAP_PROP_POS_FRAMES)}) is less "
                f"than start frame ({start_frame}). Set it to start frame..."
            )
            video.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        else:
            video.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
        if success:
            frame_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            frame_hash = imagehash.average_hash(frame_image)
            hamming_distance = ref_img_hash - frame_hash
            if hamming_distance < HAMMING_THRESHOLD:
                if current_frame < 60 * 5:
                    print("Skip detection within first 5 seconds...")
                    continue
                if point_1:
                    continue
                current_time = time.strftime(
                    "%H:%M:%S",
                    time.gmtime(current_frame / video.get(cv2.CAP_PROP_FPS)),
                )
                print(f"{'Hamming distance': <20}: {hamming_distance}")
                print(f"{'Frame number': <20}: {current_frame}")
                print(f"{'Time': <20}: {current_time}")
                output = f"{Path(__file__).parent.joinpath(
                    'output', current_time.replace(':', '-'))}.jpg"
                print(f"{'Current frame': <20}: {output}")
                marks.append([current_time, None])
                cv2.imwrite(output, frame)
                point_1 = True
            elif hamming_distance > HAMMING_THRESHOLD and point_1:
                current_time = time.strftime(
                    "%H:%M:%S",
                    time.gmtime(current_frame / video.get(cv2.CAP_PROP_FPS)),
                )
                print(f"{'Frame number': <20}: {current_frame}")
                print(f"{'Time': <20}: {current_time}")
                output = f"{Path(__file__).parent.joinpath(
                    'output', current_time.replace(':', '-'))}.jpg"
                print(f"{'Current frame': <20}: {output}")
                marks[-1][1] = current_time
                cv2.imwrite(output, frame)
                point_1 = False
    print(
        f"{'Process time': <20}: {str(timedelta(seconds=(time.time() - start_time)))}"
    )
    video.release()
    return marks


def get_command_details(split_mark: int) -> list:
    commands = []
    video = cv2.VideoCapture(VIDEO_PATH)
    fps = video.get(cv2.CAP_PROP_FPS)
    frame_total = video.get(cv2.CAP_PROP_FRAME_COUNT)
    frame_per_mark = fps * 60 * split_mark
    process_count = frame_total // frame_per_mark
    last_process_frames = frame_total % frame_per_mark
    video.release()
    print(f"{'fps': <20}: {fps}")
    print(f"{'frame total': <20}: {frame_total}")
    print(f"{'frame per mark': <20}: {frame_per_mark}")
    print(f"{'process count': <20}: {process_count}")
    print(f"{'last process frames': <20}: {frame_total % frame_per_mark}")
    for count in range(0, int(process_count)):
        items = []
        items.append(process_video)
        items.append(int(frame_per_mark * count) + 1)
        items.append(int(frame_per_mark * (count + 1)))
        items.append(STEPS)
        commands.append(items)
    if last_process_frames != 0:
        items = []
        items.append(process_video)
        items.append(int(frame_per_mark * process_count) + 1)
        items.append(int(frame_total % frame_per_mark))
        items.append(STEPS)
        commands.append(items)
    return commands


def main() -> None:
    print(f"{'Number of CPU cores': <20}: {multiprocessing.cpu_count()}")
    max_processes = multiprocessing.cpu_count() - 2
    marks: list[list[int]] = []
    start_time = time.time()
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_processes) as executor:
        futures = []
        futures.append(
            executor.submit(
                process_video,
                start_frame=1,
                end_frame=60 * 60 * 5,
                steps=15,
            )
        )
        futures.append(
            executor.submit(
                process_video,
                start_frame=18001,
                end_frame=60 * 60 * 10,
                steps=15,
            )
        )
        futures.append(
            executor.submit(
                process_video,
                start_frame=36001,
                end_frame=60 * 60 * 15,
                steps=15,
            )
        )
        futures.append(
            executor.submit(
                process_video,
                start_frame=54001,
                end_frame=60 * 60 * 20,
                steps=15,
            )
        )
        for future in concurrent.futures.as_completed(futures):
            for item in future.result():
                for submark in item:
                    marks.append(submark)
    print(
        f"{'Total main time': <20}: {str(timedelta(seconds=(time.time() - start_time)))}"
    )
    print(marks)


if __name__ == "__main__":
    from pprint import pprint

    pprint(get_command_details(split_mark=5))
    # main()
