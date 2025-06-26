from fastapi import FastAPI, Request, HTTPException
import httpx
import asyncio
from collections import defaultdict
import requests
from datetime import datetime
import re
from genderComputer import GenderComputer
import concurrent.futures
import numpy as np
import scipy.stats as stats
import pandas as pd
import os
import csv
from dotenv import load_dotenv
from pydantic import BaseModel

app = FastAPI()

load_dotenv()

query = """
query($login: String!) {
    user(login: $login) {
        pronouns
        bio
        name
        location
    }
}
"""


async def get_user(client, username, token):
    response = await client.post(
        "https://api.github.com/graphql",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": query, "variables": {"login": username}}
    )
    user_data = response.json()
    user_info = user_data.get("data", {}).get("user", {})

    return username, user_info


async def get_all_users(usernames, token):
    async with httpx.AsyncClient() as client:
        tasks = [get_user(client, username, token) for username in usernames]
        responses = await asyncio.gather(*tasks)

    return {username: user_info for username, user_info in responses}


async def extract_data(owner_repo, max_commit, token, request):
    owner, repo = owner_repo.split("/")

    data = defaultdict(lambda: {
        "pronouns": None,
        "bio": None,
        "name": None,
        "email": None,
        "location": None,
        #"loc": 0,
        "commits": 0
    })

    commit_count = 0
    per_page = 100
    page = 1
    seen_users = set()
    oldest_commit_date = None

    async with httpx.AsyncClient() as client:
        while commit_count < max_commit:
            if await request.is_disconnected():
                print("Request cancelled during data extraction")
                raise asyncio.CancelledError()

            response = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}/commits",
                headers={"Authorization": f"Bearer {token}"},
                params={"per_page": per_page, "page": page}
            )
            page_data = response.json()

            if not page_data:
                break

            for commit in page_data:
                if commit_count >= max_commit:
                    break

                # [{
                #     commit {
                #         author {
                #             email,
                #             date
                #         }
                #     },
                #     author {
                #         login
                #     }
                # }]
                commit_info = commit.get("commit", {})
                commit_author = commit_info.get("author", {})
                email = commit_author.get("email")
                date = commit_author.get("date")
                author = commit.get("author")
                if author is None:
                    continue
                username = author.get("login")
                # sha = commit.get("sha")
                # if not sha:
                #     continue

                seen_users.add(username)

                if "noreply.github.com" not in email:
                    data[username]["email"] = email

                # details_response = requests.get(
                #     f"https://api.github.com/repos/{owner}/{repo}/commits/{sha}",
                #     headers={"Authorization": f"Bearer {token}"}
                # )
                # detail_data = details_response.json()
                # stats = detail_data.get("stats", {})
                # additions = stats.get("additions", 0)
                # deletions = stats.get("deletions", 0)
                # data[username]["loc"] += additions - deletions

                data[username]["commits"] += 1
                commit_count += 1

                commit_date = datetime.fromisoformat(date.replace("Z", "+00:00"))
                if oldest_commit_date is None or commit_date < oldest_commit_date:
                    oldest_commit_date = commit_date

            page += 1

    users = await get_all_users(list(seen_users), token)
    for username, user_info in users.items():
        if user_info is not None:
            data[username].update(user_info)

    return data, commit_count, commit_date.date()


def get_gender_from_pronouns(pronouns):
    pronouns = pronouns.lower()
    tokens = re.findall(r'\b\w+\b', pronouns)

    female_count = sum(1 for t in tokens if t in {"she", "her", "hers"})
    male_count = sum(1 for t in tokens if t in {"he", "him", "his"})
    nonbinary_count = sum(1 for t in tokens if t in {"they", "them", "theirs"})

    if nonbinary_count > 0 or (female_count > 0 and male_count > 0):
        return "nonbinary"
    elif female_count > 0 and male_count == 0:
        return "female"
    elif male_count > 0 and female_count == 0:
        return "male"
    else:
        return None


def infer_gender(pronouns, bio, name, email, location):
    if pronouns:
        gender = get_gender_from_pronouns(pronouns)
        if gender:
            return gender

    if bio:
        matches = re.findall(r'\b(?:\w+\s*/\s*){1,}\w+\b', bio)

        if matches:
            gender = get_gender_from_pronouns(" ".join(matches))
            if gender:
                return gender

    gc = GenderComputer()
    gender = None

    if name:
        gender = gc.resolveGender(name, location)

    if gender is None and email:
        gender = gc.resolveGender(email.split("@")[0], location)

    return gender


def get_user_gender(username, user_info):
    pronouns = user_info.get("pronouns", None)
    bio = user_info.get("bio", None)
    name = user_info.get("name", None)
    email = user_info.get("email", None)
    location = user_info.get("location", None)

    gender = infer_gender(pronouns, bio, name, email, location)

    return username, gender


async def separate_by_gender(data, request: Request):
    female, male, nonbinary, unknown = {}, {}, {}, {}

    loop = asyncio.get_event_loop()
    futures = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        for username, user_info in data.items():
            future = loop.run_in_executor(executor, get_user_gender, username, user_info)
            futures.append(future)

        for future in futures:
            if await request.is_disconnected():
                print("Request cancelled during gender inference")
                raise asyncio.CancelledError()

            username, gender = await future

            if gender == "female":
                female[username] = data[username]
            elif gender == "male":
                male[username] = data[username]
            elif gender == "nonbinary":
                nonbinary[username] = data[username]
            else:
                unknown[username] = data[username]

    return female, male, nonbinary, unknown


def separate_by_team(data):
    core, noncore = {}, {}

    sorted_data = sorted(data.items(), key=lambda item: item[1]["commits"], reverse=True)

    commit_count = 0
    total_commits = sum(contributor[1]["commits"] for contributor in sorted_data)
    last_core_commit_count = None
    is_tie = False

    for username, user_info in sorted_data:
        if user_info["commits"] >= 0.8 * total_commits:
            core[username] = user_info
            commit_count += user_info["commits"]
            last_core_commit_count = user_info["commits"]
        elif commit_count + user_info["commits"] <= 0.8 * total_commits:
            core[username] = user_info
            commit_count += user_info["commits"]
            last_core_commit_count = user_info["commits"]
        else:
            if user_info["commits"] == last_core_commit_count:
                core[username] = user_info
                commit_count += user_info["commits"]
                is_tie = True
            else:
                noncore[username] = user_info

    if is_tie:
        tied_users = {
            username: user_info for username, user_info in sorted_data
            if user_info["commits"] == last_core_commit_count
        }
        tied_commit_count = sum(user["commits"] for user in tied_users.values())
        commit_count_without_ties = commit_count - tied_commit_count

        if commit_count_without_ties < 0.7 * total_commits:
            return core, noncore
        else:
            percentage_with_ties = commit_count / total_commits
            percentage_without_ties = commit_count_without_ties / total_commits

            if abs(percentage_with_ties - 0.8) < abs(percentage_without_ties - 0.8):
                return core, noncore
            else:
                for username in tied_users:
                    if username in core:
                        noncore[username] = core.pop(username)

                return core, noncore

    return core, noncore


def compute_blau_index(counts):
    total = sum(counts.values())
    if total == 0:
        return 0.00
    proportions = [count / total for count in counts.values()]

    blau = 1 - sum(proportion**2 for proportion in proportions)
    max_blau = 1 - (1 / 3)
    normalized_blau = blau / max_blau

    return round(normalized_blau, 3)


def compute_fisher(core_counts, noncore_counts):
    core_male = core_counts["male"]
    noncore_male = noncore_counts["male"]
    core_non_male = core_counts["female"] + core_counts["nonbinary"]
    noncore_non_male = noncore_counts["female"] + noncore_counts["nonbinary"]

    data = np.array([
        [core_male, noncore_male],
        [core_non_male, noncore_non_male]
    ])
    odds_ratio, p_value = stats.fisher_exact(data)

    return round(odds_ratio, 3), round(p_value, 3)


class ParametersRequest(BaseModel):
    repo: str
    count: int
    # code: str


# async def get_token_from_code(code):
#     async with httpx.AsyncClient() as client:
#         response = await client.post(
#             "https://github.com/login/oauth/access_token",
#             json={
#                 "client_id": os.getenv("GITHUB_CLIENT_ID"),
#                 "client_secret": os.getenv("GITHUB_CLIENT_SECRET"),
#                 "code": code,
#             },
#             headers={"Accept": "application/json"}
#         )
#     token_data = response.json()
#
#     return token_data.get("access_token")


@app.post("/repo-stats")
async def repo_stats(parameters: ParametersRequest, request: Request):
    # token = await get_token_from_code(request.code)
    token = os.getenv("TOKEN")

    try:
        data, commit_count, commit_date = await extract_data(parameters.repo, parameters.count, token, request)

        if await request.is_disconnected():
            raise asyncio.CancelledError("Request cancelled before team composition inference")

        core, noncore = separate_by_team(data)

        female_core, male_core, nonbinary_core, unknown_core = await separate_by_gender(core, request)
        female_noncore, male_noncore, nonbinary_noncore, unknown_noncore = await separate_by_gender(noncore, request)

        core_counts = {
            "female": len(female_core),
            "male": len(male_core),
            "nonbinary": len(nonbinary_core),
        }

        noncore_counts = {
            "female": len(female_noncore),
            "male": len(male_noncore),
            "nonbinary": len(nonbinary_noncore),
        }

        blau_core = compute_blau_index(core_counts)
        blau_noncore = compute_blau_index(noncore_counts)
        odds_ratio, p_value = compute_fisher(core_counts, noncore_counts)

        avg_blau_core = 0.00
        avg_blau_noncore = 0.00
        repo_count = 0

        file_name = "stats.csv"
        file_exists = os.path.exists(file_name)

        if file_exists:
            df = pd.read_csv(file_name, parse_dates=["datetime"])
            df_sorted = df.sort_values(by="datetime", ascending=False)
            df_filtered = df_sorted.drop_duplicates(subset="repo", keep="first")
            df_unique = df_filtered[df_filtered["repo"] != parameters.repo]

            if df_unique.shape[0] != 0:
                avg_blau_core = round(df_unique["blau_core"].mean(), 3)
                avg_blau_noncore = round(df_unique["blau_noncore"].mean(), 3)
                repo_count = df_unique.shape[0]

        if await request.is_disconnected():
            raise asyncio.CancelledError("Request cancelled before writing to file")

        with open(file_name, mode='a', newline='') as file:
            writer = csv.writer(file)

            if not file_exists:
                writer.writerow(["datetime", "repo", "commit_count", "blau_core", "blau_noncore", "odds_ratio", "p_value"])

            writer.writerow([
                datetime.utcnow().isoformat(),
                parameters.repo,
                commit_count,
                blau_core,
                blau_noncore,
                odds_ratio,
                p_value
            ])

        female_count = len(female_core) + len(female_noncore)
        male_count = len(male_core) + len(male_noncore)
        nonbinary_count = len(nonbinary_core) + len(nonbinary_noncore)
        unknown_count = len(unknown_core) + len(unknown_noncore)
        total_count = female_count + male_count + nonbinary_count + unknown_count

        core_counts["unknown"] = len(unknown_core)
        noncore_counts["unknown"] = len(unknown_noncore)

        return {"count": commit_count,
                "date": commit_date,
                "female": round((female_count / total_count) * 100, 2),
                "male": round((male_count / total_count) * 100, 2),
                "nonbinary": round((nonbinary_count / total_count) * 100, 2),
                "unknown": round((unknown_count / total_count) * 100, 2),
                "core": core_counts,
                "noncore": noncore_counts,
                "blauCore": blau_core,
                "avgBlauCore": avg_blau_core,
                "blauNoncore": blau_noncore,
                "avgBlauNoncore": avg_blau_noncore,
                "repos": repo_count}

    except asyncio.CancelledError:
        return {"detail": "Request cancelled by user"}
