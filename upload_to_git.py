# -*- coding: utf-8 -*-

import requests
import base64
from datetime import datetime
import json

try:
    with open("secrets.json", "r", encoding="utf-8") as f:
        secret_data = json.load(f)
except (FileNotFoundError, KeyError):
    print("❌ Error: secrets.json 파일이 없거나 GITHUB_TOKEN이 설정되지 않았습니다.")
    exit(1)

# GitHub 설정
GITHUB_TOKEN = secret_data["GITHUB_TOKEN"]  # 개인 액세스 토큰 입력
REPO_OWNER = "Grassyeochi"  # GitHub 사용자명
REPO_NAME = "crawling_news"  # 저장소 이름
HTML_FILE_PATH = "index.html"  # HTML 파일 경로
BRANCH_NAME = "release"  # 브랜치 이름
TEXT_FILE_PATH = "upload.txt"  # 크롤링한 텍스트 파일 경로

change = True

def read_txt_file():
    with open(TEXT_FILE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    return content


def read_html_template():
    with open(HTML_FILE_PATH, 'r', encoding='utf-8') as f:
        template = f.read()
    return template


def update_html_file(template, content):
    # 크롤링한 텍스트 내용을 JSON 형식으로 변환
    news_items = []
    lines = content.strip().split('\n\n')
    for line in lines:
        parts = line.split('\n')
        if len(parts) >= 3:
            title = parts[0].replace("제목 : ", "").strip()
            link = parts[1].replace("링크 : ", "").strip()
            press = parts[2].replace("언론사 : ", "").strip()
            news_items.append({'title': title, 'link': link, 'press': press})

    # JSON 형식으로 변환하여 JavaScript 배열로 생성
    json_data = str(news_items).replace("'", '"')

    # 현재 날짜 및 시간 추가
    with open("timetable.txt", "r", encoding="utf-8") as f:
        latest_datetime = f.readline()

    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    updated_template = template.replace('const newsData = [];', f'const newsData = {json_data};')
    updated_template = updated_template.replace('<div class="timestamp" id="timestamp-now"></div',
                                                f'<div class="timestamp" id="timestamp-now">최신화 확인 : {current_datetime}</div>')

    if (change == True):
        updated_template = updated_template.replace('<div class="timestamp" id="timestamp"></div>',
                                                    f'<div class="timestamp" id="timestamp">최신화 : {current_datetime}</div>')
        with open("timetable.txt", "w", encoding="utf-8") as f:
            f.write(current_datetime)
    else:
        updated_template = updated_template.replace('<div class="timestamp" id="timestamp"></div>',
                                                    f'<div class="timestamp" id="timestamp">최신화 : {latest_datetime}</div>')

    return updated_template


def update_github_file(content):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{HTML_FILE_PATH}?ref={BRANCH_NAME}"

    # 현재 파일의 SHA 가져오기
    response = requests.get(url, headers={'Authorization': f'token {GITHUB_TOKEN}'})

    #오류 처리
    if response.status_code == 404:
        print(f"Error: 파일 또는 브랜치 '{BRANCH_NAME}'이(가) 존재하지 않습니다.(404 Not found)")
        return

    response.raise_for_status()
    sha = response.json().get('sha')

    # 파일 업데이트
    data = {
        "message": "뉴스 데이터 최신화를 위해 HTML 코드를 수정 합니다.",
        "content": base64.b64encode(content.encode('utf-8')).decode('utf-8'),
        "sha": sha,
        "branch": BRANCH_NAME
    }
    response = requests.put(url, headers={'Authorization': f'token {GITHUB_TOKEN}'}, json=data)

    #오류 처리
    if response.status_code == 409:
        print("Conflict: 파일 업데이트 중 충돌이 발생했습니다.(409 Client Error)")
        print(response.json())
        return

    response.raise_for_status()
    print("HTML 파일이 GitHub에 업데이트되었습니다.")


def main():
    global change

    # 텍스트 파일 읽기
    content = read_txt_file()

    # HTML 템플릿 읽기
    template = read_html_template()

    isChange = input("IsChanged?(Y/N) : ")
    if (isChange.upper() == "N"):
        change = not change

    # HTML 파일 내용 생성
    html_content = update_html_file(template, content)

    # GitHub에 업데이트
    update_github_file(html_content)


if __name__ == "__main__":
    main()
