import os
import httpx
from pprint import pprint as print
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
URL = os.getenv("URL")
PROJECT_ID = os.getenv("PROJECT_ID")

def main():
    headers = {"PRIVATE-TOKEN": TOKEN}
    url = f"{URL}/projects"
    print(url)
    response = httpx.get(url, headers=headers)
    for item in response.json():
        print(item["id"])


def issues():
    issues_count: int = 0
    headers = {"PRIVATE-TOKEN": TOKEN}
    url = f"{URL}/projects/{PROJECT_ID}/issues_statistics"
    print(url)
    response = httpx.get(url, headers=headers)
    print(response.json())
    params = {"state": "opened", "issue_type": "issue"}
    url = f"{URL}/projects/{PROJECT_ID}/issues"
    print(url)
    response = httpx.get(url, headers=headers, params=params)
    for item in response.json():
        if item["project_id"] == int(PROJECT_ID):
            issues_count += 1
            print(item["title"])
    print(f"Total issues: {issues_count}")


if __name__ == "__main__":
    # main()
    issues()
