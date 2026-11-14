# VOCA POP! 3000 · Streamlit

## GitHub에서 배포하기

1. 이 ZIP을 풀고 안의 파일을 GitHub 저장소에 업로드합니다. `streamlit_app.py`, `vocabulary.json`, `requirements.txt`, `WORDNET_LICENSE.txt`를 같은 폴더에 둡니다.
2. [Streamlit Community Cloud](https://share.streamlit.io/)에서 **Create app**을 선택하고 GitHub의 저장소와 브랜치를 지정합니다.
3. **Main file path**에 `streamlit_app.py`를 입력한 뒤 **Deploy**를 누릅니다. 별도 API 키는 필요하지 않습니다.

[Streamlit 공식 배포 안내](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)

## 내 컴퓨터에서 실행하기

```bash
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

## 수업에서 사용하기

- 닉네임 → 레벨 → DAY → 학습 단계를 선택합니다. 레벨별로 단어를 섞은 101개 DAY와 표제어 3,000개가 포함됩니다.
- 2단계는 문장에서 강조된 영어 단어의 한글 뜻을 고릅니다. 3단계는 문맥을 읽고 빈칸에 단어를 입력합니다.
- 유의어와 반의어는 품사와 어의별로 표시합니다. 직접 반의어, 문맥상 대비 표현, 뜻을 풀어 쓴 표현을 구분합니다.
- 미국·영국 발음은 gTTS 외부 음성 서비스에 연결될 때 재생됩니다. 서버에서 음성 요청을 보내므로 인터넷이 필요합니다.
- 학습 진행, XP와 닉네임 순위는 현재 접속 세션에 저장됩니다. 페이지를 새로고침하거나 접속을 종료하면 초기화될 수 있습니다.

## 출처

- 영어 예문 · 사용자 제공 앱, 학습용 작성 문장, [Tatoeba CC0 문장](https://tatoeba.org/en/downloads), 일부 [Princeton WordNet 3.0](https://wordnet.princeton.edu/) 예문
- 유의어·반의어·파생어 · Princeton WordNet 3.0 및 학습용 보충 표현. 라이선스는 `WORDNET_LICENSE.txt`에 포함되어 있습니다.
- 한글 뜻과 DAY 구성 · 사용자 제공 VOCA POP! 어휘 데이터
