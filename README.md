# VOCA POP! 3000 · SQLite 버전

1. ZIP을 풀어 파일들을 GitHub 저장소의 같은 폴더에 올립니다.
2. Streamlit Community Cloud에서 그 저장소를 선택하고 Main file path를 `app.py`로 지정해 배포합니다.
3. 앱을 처음 실행하면 `data/voca.sqlite3`에 저장소가 자동 생성됩니다. 앱에서 회원가입을 눌러 닉네임과 숫자 비밀번호 5자리를 등록하세요.

같은 배포 주소에 접속하는 학습자는 공용 랭킹을 보며, 다른 기기에서 같은 계정으로 로그인하면 마지막 문항과 XP를 이어갈 수 있습니다. 랭킹 화면은 5초마다 갱신됩니다. 학습 기록은 문항 단위로 저장됩니다.

Streamlit Community Cloud는 로컬 파일 보존을 보장하지 않습니다. 서버 교체나 재배포 등으로 DB 파일이 사라지면 계정과 기록도 초기화됩니다. 이전 버전의 기록은 자동 이전되지 않습니다.

## 로컬 또는 직접 운영하는 서버에서 실행

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

직접 호스팅할 경우 `VOCA_DB_PATH` 환경변수에 영구 디스크 안의 SQLite 파일 경로를 지정할 수 있습니다. 같은 SQLite 파일을 쓰는 단일 서버에서 운영하세요. DB에는 계정과 학습 기록이 있으므로 GitHub에 올리지 않습니다. 실행 중 백업할 때는 SQLite 백업 API를 사용하세요.

## 어휘 출처

- 한글 뜻과 DAY 구성 · 사용자 제공 VOCA POP! 데이터
- 예문 · 학습용 작성 문장, [Tatoeba CC0](https://tatoeba.org/en/downloads), 일부 Princeton WordNet 3.0
- 유의어·반의어·파생어 · [Princeton WordNet 3.0](https://wordnet.princeton.edu/)과 학습용 보충 자료. 라이선스는 WORDNET_LICENSE.txt에 있습니다.
