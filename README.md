# VOCA POP! 3000 · SQLite

## Streamlit Community Cloud

1. `app.py`와 `requirements.txt`를 GitHub 저장소의 같은 폴더에 업로드합니다. ZIP을 푼 파일을 올려 주세요.
2. **Main file path**를 `app.py`로 지정해 배포합니다. 기존 진입점이 `streamlit_app.py`라면 ZIP에 있는 같은 이름의 파일로 교체해도 됩니다.
3. 앱에서 회원가입으로 닉네임과 숫자 비밀번호 5자리를 등록합니다.

`app.py`에 단어 3,000개와 저장 코드가 포함되어 있습니다. 외부 DB, Secrets, 별도 단어 파일 설정 없이 실행됩니다. SQLite 파일은 `data/voca.sqlite3`에 자동 생성됩니다.

기존 PostgreSQL 버전을 사용 중이었다면 이번 ZIP의 `requirements.txt`로 교체하세요. 로그에 오류가 표시되면 Streamlit 앱 관리 화면에서 Traceback 마지막 줄과 Main file path를 확인해 주세요.

같은 배포 주소의 사용자들이 랭킹을 공유합니다. 같은 계정으로 로그인하면 다른 기기에서도 저장된 학습을 이어갑니다. Streamlit Community Cloud에서 로컬 DB 파일이 삭제되면 계정과 학습 기록이 초기화될 수 있습니다. 기존 SQLite 배포와 DB 파일이 유지되는 경우에는 그 파일을 그대로 사용합니다.

## 로컬 실행

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

직접 호스팅할 때는 `VOCA_DB_PATH` 환경변수에 영구 디스크의 파일 경로를 지정할 수 있습니다. SQLite 파일은 학습자 기록을 담으므로 GitHub에 올리지 않습니다.

## 어휘 출처

- 한글 뜻과 DAY 구성 · 사용자 제공 VOCA POP! 데이터
- 예문 · 학습용 작성 문장, [Tatoeba CC0](https://tatoeba.org/en/downloads), 일부 Princeton WordNet 3.0
- 유의어·반의어·파생어 · [Princeton WordNet 3.0](https://wordnet.princeton.edu/) 및 학습용 보충 자료. WORDNET_LICENSE.txt 참고.
