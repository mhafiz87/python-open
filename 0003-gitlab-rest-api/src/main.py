import os
from dataclasses import dataclass

import httpx
from dotenv import load_dotenv

__all__ = ["IssueFilter", "list_issues"]


@dataclass
class IssueFilter:
    """Class for filtering issues

    Attributes:
        milestone: str
        assignee: str
    """

    milestone: str = ""
    assignee_username: str = ""


load_dotenv()

TOKEN = os.getenv("TOKEN", "")
URL = os.getenv("URL")
PROJECT_ID = os.getenv("PROJECT_ID", "")

if not TOKEN:
    raise ValueError("TOKEN is not set")
if not PROJECT_ID:
    raise ValueError("PROJECT_ID is not set")


def find_id(name: str) -> str:
    """Find project id

    Args:
        name(str): name of project

    Returns:
        str: project id
    """
    id = ""
    headers = {"PRIVATE-TOKEN": TOKEN}
    url = f"{URL}/projects"
    found = False
    response = httpx.get(url, headers=headers)
    total_pages = int(response.headers["X-Total-Pages"])
    print(f"Total pages: {total_pages}")
    for page in range(1, total_pages + 1):
        print(f"Page: {page}")
        params = {"page": page}
        response = httpx.get(url, headers=headers, params=params)
        for item in response.json():
            if name.lower() in item["name"].lower():
                print(f"{item['name']}: {item['id']}")
                id = item["id"]
                found = True
                break
        if found:
            break
    return id


# def list_issues(milestone: str = "", assignee: str = ""):
def list_issues(issues: IssueFilter | None = None):
    # """list issues
    # Args:
    #     milestone(str): to filter by milestone
    #     assignee(str): to filter by assignee
    # """
    issues_count: int = 1
    headers = {"PRIVATE-TOKEN": TOKEN}
    # url = f"{URL}/projects/{PROJECT_ID}/issues_statistics"
    # response = httpx.get(url, headers=headers)
    url = f"{URL}/projects/{PROJECT_ID}/issues"
    params = {"scope": "all", "state": "opened", "issue_type": "issue"}
    if issues:
        for key, value in vars(issues).items():
            if key == "assignee_username" and value == "None":
                params.update({"assignee_id": value})
            elif value:
                params.update({key: value})
    print(f"Params: {params}")
    response = httpx.get(url, headers=headers, params=params)
    total_pages = int(response.headers["X-Total-Pages"])
    for page in range(1, total_pages + 1):
        params.update({"page": str(page)})
        response = httpx.get(url, headers=headers, params=params)
        for item in response.json():
            assignee = item["assignee"]["name"] if item["assignee"] else "Unassigned"
            print(f"{issues_count:<2}: {assignee} : {item['title']}")
            issues_count += 1
    print(f"Total open issues: {issues_count - 1}")


if __name__ == "__main__":
    # find_id("orbital-runtime")
    list_issues()
