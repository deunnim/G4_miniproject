from html import escape
from io import BytesIO
import json
from pathlib import Path
import random
import re
import unicodedata
import time
from uuid import uuid4

import altair as alt
import pandas as pd
import sqlite3
import os
from storage import Storage, ProgressChanged

from gtts import gTTS
from gtts.tts import gTTSError
import streamlit as st


st.set_page_config(page_title="VOCA POP! · 3000", page_icon="🍬", layout="centered")
DATA_FILE = Path(__file__).with_name("vocabulary.json")
STAGES = ("뒤집기", "뜻 고르기", "문맥 빈칸")


@st.cache_resource
def load_words():
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


DATA = load_words()
WORDS = DATA["words"]
LEVELS = {level["key"]: level for level in DATA["levels"]}
DAYS = {day["key"]: day for level in LEVELS.values() for day in level["days"]}
WORD_ID = {word["word"]: i for i, word in enumerate(WORDS) if i >= 10}
S = st.session_state

for key, value in {
    "nickname": None, "screen": "level",
    "level": None, "day": None, "stage": 1, "accent": "미국 US",
}.items():
    S.setdefault(key, value)


def normalize(text):
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


@st.cache_resource
def get_storage(path):
    return Storage(path)


def store():
    default_path = Path(__file__).resolve().parent / "data" / "voca.sqlite3"
    return get_storage(os.environ.get("VOCA_DB_PATH") or str(default_path))


def login(name, pin, register):
    name = name.strip()
    key = normalize(name)
    if not name or len(key) > 16 or not re.fullmatch(r"[0-9]{5}", pin):
        st.warning("닉네임 1~16자와 숫자 비밀번호 5자리를 입력해 주세요.")
        return
    client = st.context.ip_address or "unknown-client"
    result = store().authenticate(key, name, pin, register, client)
    if result != "ok":
        st.warning({
            "exists": "이미 사용 중인 닉네임이에요.",
            "limited": "로그인 시도가 많아요. 10분 뒤 다시 시도해 주세요.",
            "invalid": "닉네임과 비밀번호를 확인해 주세요. 5번 연속 틀렸다면 10분 뒤 다시 시도해 주세요.",
        }[result])
        return
    profile = store().load(key)
    resume = profile.get("resume", {})
    if resume.get("day") in DAYS:
        go("study", nickname=key, **resume)
    else:
        go("level", nickname=key, level=None, day=None)
    S.pop("question_clock", None)
    st.rerun()


def save(profile, event=None):
    try:
        store().save(S.nickname, profile, event)
    except ProgressChanged:
        S.notice = "다른 탭이나 기기의 최신 진도를 불러왔어요. 이 화면의 입력은 저장되지 않았어요."
        st.rerun()


def activity(profile, word, kind, xp=0):
    current = time.monotonic()
    clock = S.get("question_clock")
    elapsed = min(120, max(0, int(current-clock[1]))) if clock else 0
    if clock:
        S.question_clock = (clock[0], current)
    word_id = WORD_ID[word["word"]]
    if kind in ("incorrect", "review", "revealed"):
        record = profile.setdefault("mistakes", {}).setdefault(str(word_id), {"count": 0, "resolved": False})
        record["count"] += 1
        record["resolved"] = False
    save(profile, (word_id, S.day, S.stage, kind, xp, elapsed))


def go(screen, **changes):
    S.update(changes)
    S.screen = screen
    S.pop("question_clock", None)


def prepare_stage(profile, day, number):
    record = profile.setdefault("days", {}).setdefault(day["key"], {"stage": number, "runs": {}})
    number_key = str(number)
    resume = {"level": S.level, "day": S.day, "stage": number}
    changed = record["stage"] != number or profile.get("resume") != resume
    record["stage"] = number
    if number_key not in record["runs"]:
        ids = list(day["ids"])
        if number != 1:
            random.shuffle(ids)
        queue = [(word_id, False) for word_id in ids]
        if number == 1:
            queue += [(word_id, True) for word_id in ids]
        record["runs"][number_key] = {
            "id": uuid4().hex, "queue": queue, "index": 0, "xp": 0, "correct": 0,
            "review": [], "done": False, "question": {},
        }
        changed = True
    profile["resume"] = resume
    if changed:
        save(profile)
    return record["runs"][number_key]


@st.cache_data(max_entries=256, show_spinner=False)
def speech(text, accent):
    audio = BytesIO()
    gTTS(text, lang="en", tld=accent, timeout=8).write_to_fp(audio)
    return audio.getvalue()


def pronunciation(text, key, label="발음 듣기"):
    if st.button("🔊 " + label, key="say-" + key):
        try:
            with st.spinner("음성을 준비하고 있어요."):
                audio = speech(text, "us" if S.accent == "미국 US" else "co.uk")
            st.audio(audio, format="audio/mpeg", autoplay=True)
        except (gTTSError, OSError):
            st.info("음성 서비스에 연결하지 못했어요. 잠시 뒤 다시 눌러 주세요.")


def source_note(word, stage):
    if stage == 2 and word.get("example"):
        return
    source = word.get("contextSource")
    if isinstance(source, int):
        st.caption(f"예문 출처 · [Tatoeba](https://tatoeba.org/en/sentences/show/{source}) · CC0")
    elif source == "wn":
        st.caption("예문 출처 · WordNet 3.0")
    else:
        st.caption("학습용 예문")


def lexical_details(word):
    with st.expander("유의어 · 반의어 · 관련 어휘"):
        syn_tab, ant_tab, family_tab = st.tabs(["유의어", "반의어", "관련 형태"])
        for tab, field, index in [(syn_tab, "syn", 2), (ant_tab, "ant", 3)]:
            with tab:
                if word.get(field):
                    st.write(word[field])
                if index == 2 and word["extra"][0]:
                    st.markdown("**비슷한 표현**")
                    st.write(word["extra"][0].replace("; ", " · "))
                if index == 2 and word.get("paraphrase"):
                    st.markdown("**뜻을 풀어 쓴 표현**")
                    st.write(word["paraphrase"])
                found = False
                for sense in word["senses"]:
                    if sense[index]:
                        found = True
                        st.markdown(f"**{sense[0]}** · {sense[1]}")
                        st.write(" · ".join(sense[index]))
                if index == 3:
                    contrasts = list(dict.fromkeys(
                        ([v for v in word["extra"][1].split("; ") if v])
                        + [v for sense in word["senses"] for v in sense[4]]
                    ))
                    if contrasts:
                        st.markdown("**문맥에 따라 대비되는 표현**")
                        st.write(" · ".join(contrasts))
                if index == 3 and not found and not word.get(field):
                    st.caption("확인된 직접 반의어가 없어요.")
                if index == 2 and not (found or word.get(field) or word["extra"][0] or word.get("paraphrase")):
                    st.caption("확인된 유의어가 없어요.")
        with family_tab:
            forms = list(dict.fromkeys(word["family"] + word.get("related", []) + word["variation"]))
            st.write(" · ".join(forms) if forms else "등록된 파생어와 철자 변형이 없어요.")
        st.caption("유의어와 반의어는 품사와 뜻에 따라 달라요. WordNet의 다른 의미도 포함돼요.")


def sentence(word, stage):
    passage = word["passage"]
    surface = word.get("surface") or word["answer"]
    if stage == 2 and word.get("example"):
        example = word["example"]
        target = re.escape(word["word"])
        hit = re.search(rf"\b{target}(?:s|d|ed|ing)?\b", example, re.I)
        if hit:
            return example[:hit.start()], hit.group(), example[hit.end():]
    before, after = passage.split("_____", 1)
    return before, surface, after


def show_sentence(before, target, after, blank=False):
    highlighted = "□□□□" if blank else escape(target)
    st.markdown(
        f'<p lang="en" style="font-size:1.3rem;line-height:1.75">'
        f'{escape(before)}<mark style="background:#f3dbff;color:#24162e;'
        f'padding:.1em .24em;border-radius:.3em">{highlighted}</mark>{escape(after)}</p>',
        unsafe_allow_html=True,
    )


def award(profile, run, word, stage, success=True, first=True):
    base = {1: 5, 2: 15, 3: 25}[stage]
    xp = int(base * (1 if first or stage == 1 else .4) * (1.5 if word.get("bonus") else 1) + .5)
    if success and first:
        run["correct"] += 1
    if not first and word["word"] not in run["review"]:
        run["review"].append(word["word"])
    run["xp"] += xp
    if stage == 1:
        advance(run)
    else:
        run["question"]["result"] = (success, first, xp)
    kind = ("correct" if first else "review") if stage == 1 else (
        "revealed" if not success else "correct" if first else "hinted")
    activity(profile, word, kind, xp)


def advance(run):
    run["index"] += 1
    run["question"] = {}
    if run["index"] == len(run["queue"]) and not run["done"]:
        run["done"] = True



def render_flashcard(profile, run, question, word, reverse, key):
    st.write("한글 뜻을 보고 영어를 떠올려 보세요." if reverse else "영어를 보고 한글 뜻을 떠올려 보세요.")
    with st.container(border=True):
        flipped = question.get("flipped", False)
        show_meaning = reverse != flipped
        st.subheader(word["meaning"] if show_meaning else word["word"])
        if st.button("카드 뒤집기 ↻", key="flip-" + key):
            question["flipped"] = not flipped
            question["checked"] = True
            save(profile)
            st.rerun()
    if not reverse or question.get("checked"):
        pronunciation(word["word"], key)
    if question.get("checked"):
        known, review = st.columns(2)
        if known.button("기억했어요 ✓", key="know-" + key, width="stretch"):
            award(profile, run, word, 1)
            st.rerun()
        if review.button("다시 볼래요 ↻", key="review-" + key, width="stretch"):
            award(profile, run, word, 1, success=False, first=False)
            st.rerun()
        lexical_details(word)


def choices(day, word_id):
    correct = normalize(WORDS[word_id]["meaning"])
    seen = {correct}
    options = [word_id]
    for pool in (day["ids"], range(10, len(WORDS))):
        for candidate in random.sample(pool, len(pool)):
            meaning = normalize(WORDS[candidate]["meaning"])
            if meaning in seen:
                continue
            options.append(candidate)
            seen.add(meaning)
            if len(options) == 4:
                random.shuffle(options)
                return options
    return options


def render_quiz(profile, day, run, question, word, word_id, stage, key):
    before, target, after = sentence(word, stage)
    result = question.get("result")
    with st.container(border=True):
        if stage == 2:
            st.subheader("강조된 단어의 뜻은 무엇일까요?")
            st.caption("앞뒤 표현을 읽고 이 문장에서 사용된 뜻을 골라 보세요.")
            show_sentence(before, target, after)
            pronunciation(before + target + after, key, "예문 듣기")
        else:
            st.subheader("어떤 단어가 빈칸에 들어갈까요?")
            st.caption("문장이 묘사하는 상황과 앞뒤 표현을 보고 DAY에서 학습한 단어를 입력하세요.")
            show_sentence(before, target, after, blank=not result)
            pronunciation(before + ("blank" if not result else target) + after, key, "문장 듣기")
    if result:
        success, first, xp = result
        st.success(f"{'정답이에요!' if success else '정답을 확인해요.'}  +{xp} XP")
        st.write(f"**{word['word']}** · {word['meaning']}")
        if stage == 2 and word.get("translation"):
            st.write(word["translation"])
        if stage == 3 and word.get("contextSource") is None:
            st.write(word["explain"])
        source_note(word, stage)
        lexical_details(word)
        if st.button("다음 문제 →" if run["index"] + 1 < len(run["queue"]) else "단계 결과 보기 →",
                     key="next-" + key, type="primary"):
            advance(run)
            save(profile)
            st.rerun()
        return

    if stage == 2:
        if "options" not in question:
            question["options"] = choices(day, word_id)
            save(profile)
        wrong = question.setdefault("wrong", [])
        for option in question["options"]:
            if st.button(WORDS[option]["meaning"], key=f"choice-{key}-{option}",
                         disabled=option in wrong, width="stretch"):
                if option == word_id:
                    award(profile, run, word, stage, first=not wrong)
                else:
                    wrong.append(option)
                    activity(profile, word, "incorrect")
                st.rerun()
        if wrong:
            st.warning("문장에 어울리는 뜻을 다시 골라 보세요.")
    else:
        with st.form("answer-" + key):
            answer = st.text_input("빈칸에 들어갈 영어 단어", max_chars=80)
            submitted = st.form_submit_button("정답 확인 ✓", type="primary")
        if submitted:
            accepted = [word["answer"], target, *word["variation"], *word.get("accepted", [])]
            if normalize(answer) and normalize(answer) in {normalize(a) for a in accepted}:
                award(profile, run, word, stage,
                      first=not question.get("attempts") and not question.get("hint"))
                st.rerun()
            elif answer.strip():
                question["attempts"] = question.get("attempts", 0) + 1
                activity(profile, word, "incorrect")
            else:
                st.info("영어 단어를 먼저 입력해 주세요.")
        if question.get("attempts"):
            st.warning("아직 아니에요. 빈칸 앞뒤의 표현을 다시 읽어 보세요.")
        hint_col, reveal_col = st.columns(2)
        if hint_col.button("💡 힌트 보기", key="hint-" + key, width="stretch"):
            question["hint"] = True
            save(profile)
        if question.get("hint"):
            st.info(f"뜻: {word['meaning']}  ·  첫 글자: {target[0]}")
        if reveal_col.button("정답을 보며 배우기", key="reveal-" + key, width="stretch"):
            award(profile, run, word, stage, success=False, first=False)
            st.rerun()


def navigate(profile):
    if S.screen == "level":
        st.header("어떤 레벨을 공부할까요?")
        st.write("레벨을 고르면 해당 레벨의 DAY가 열려요.")
        for col, (key, level) in zip(st.columns(3), LEVELS.items()):
            count = sum(len(day["ids"]) for day in level["days"])
            col.button(f"{level['label']} · {count:,}개", on_click=go,
                       args=("day",), kwargs={"level": key}, width="stretch")
        return

    level = LEVELS[S.level]
    if S.screen == "day":
        st.button("← 레벨 선택", on_click=go, args=("level",))
        st.header(f"{level['label']} · DAY 선택")
        st.caption("하루 29~30개 단어를 학습해요. ✓는 세 단계 완료 표시예요.")
        cols = st.columns(4)
        for index, day in enumerate(level["days"]):
            saved = profile.get("days", {}).get(day["key"])
            completed = sum(run["done"] for run in saved["runs"].values()) if saved else 0
            status = " ✓" if completed == 3 else f" · {completed}/3" if saved else ""
            cols[index % 4].button(f"DAY {index+1}{status}", key=day["key"],
                                   on_click=go, args=("preview",), kwargs={"day": day["key"]},
                                   width="stretch")
        return

    day = DAYS[S.day]
    st.button("← DAY 선택", on_click=go, args=("day",))
    st.header(day["label"])
    if S.screen == "preview":
        st.caption(f"단어 {len(day['ids'])}개 · 원하는 단계부터 시작할 수 있어요.")
        st.write(" · ".join(WORDS[i]["word"] for i in day["ids"]))
        saved = profile.get("days", {}).get(day["key"])
        if saved:
            st.button("이어서 학습하기 →", type="primary", on_click=go,
                      args=("study",), kwargs={"stage": saved["stage"]})
        for stage, col in enumerate(st.columns(3), 1):
            col.button(f"{stage}단계 · {STAGES[stage-1]}", on_click=go,
                       args=("study",), kwargs={"stage": stage}, width="stretch")
        return

    run = prepare_stage(profile, day, S.stage)
    for stage, col in enumerate(st.columns(3), 1):
        col.button(f"{stage}단계 · {STAGES[stage-1]}", key=f"stage-{stage}", on_click=go,
                   args=("study",), kwargs={"stage": stage}, width="stretch", disabled=stage == S.stage)
    total = len(run["queue"])
    st.progress(run["index"] / total, text=f"{run['index']} / {total} 완료")
    if run["done"]:
        st.success(f"{S.stage}단계 완료 · +{run['xp']} XP")
        label = "기억한 카드" if S.stage == 1 else "첫 시도 정답"
        st.write(f"{label} {run['correct']} / {total}")
        if run["review"]:
            st.write("**다시 볼 단어** · " + " · ".join(run["review"]))
        if S.stage < 3:
            st.button("다음 단계로 →", type="primary", on_click=go, args=("study",),
                      kwargs={"stage": S.stage + 1})
        with st.expander("이 단계 다시 연습"):
            st.caption("이미 받은 XP는 유지돼요.")
            if st.button("진행 초기화 후 다시 시작"):
                del profile["days"][day["key"]]["runs"][str(S.stage)]
                save(profile)
                st.rerun()
        return

    word_id, reverse = run["queue"][run["index"]]
    word = WORDS[word_id]
    key = f"{run['id']}-{run['index']}"
    if S.get("question_clock", (None,))[0] != key:
        S.question_clock = (key, time.monotonic())
    if S.stage == 1:
        render_flashcard(profile, run, run["question"], word, reverse, key)
    else:
        render_quiz(profile, day, run, run["question"], word, word_id, S.stage, key)


@st.fragment(run_every="5s")
def leaderboard():
    st.subheader("🏆 전체 랭킹")
    try:
        rows = store().ranking()
    except sqlite3.Error:
        st.warning("랭킹 데이터를 읽지 못했어요. 잠시 뒤 자동으로 다시 확인해요.")
        return
    if rows:
        st.dataframe(pd.DataFrame([
            {"순위": index, "닉네임": row["display_name"], "누적 XP": row["xp"]}
            for index, row in enumerate(rows, 1)
        ]), hide_index=True, width="stretch")
    else:
        st.info("아직 XP를 얻은 학습자가 없어요.")
    st.caption("XP를 얻은 전체 학습자 · 이 화면을 보는 동안 5초마다 업데이트돼요.")


def review_words(profile):
    st.header("오답 복습")
    st.caption("틀린 적이 있거나 다시 보기를 눌렀거나 정답을 공개한 단어만 모아요.")
    records = profile.get("mistakes", {})
    pending = {key: value for key, value in records.items() if not value["resolved"]}
    show_all = st.toggle("복습 완료 단어도 보기")
    current = records if show_all else pending
    if not current:
        st.success("지금 복습할 단어가 없어요.")
        return
    ids = sorted(current, key=lambda key: (-current[key]["count"], WORDS[int(key)]["word"]))
    key = st.selectbox(
        "복습할 단어", ids,
        format_func=lambda k: f"{WORDS[int(k)]['meaning']} · {records[k]['count']}회 기록",
    )
    word = WORDS[int(key)]
    st.subheader("한글 뜻을 보고 영어 단어를 써 보세요.")
    st.write(word["meaning"])
    with st.form("review-word-" + key):
        answer = st.text_input("영어 단어", max_chars=80)
        submitted = st.form_submit_button("복습 정답 확인")
    if submitted:
        valid = [word["word"], word["answer"], *word["variation"], *word.get("accepted", [])]
        if normalize(answer) in {normalize(item) for item in valid}:
            records[key]["resolved"] = True
            save(profile)
            st.success("정답이에요! 복습 완료로 저장했어요.")
        else:
            st.warning("철자를 다시 확인해 보세요.")
    with st.expander("정답과 예문 보기"):
        st.write(f"**{word['word']}**")
        show_sentence(*sentence(word, 2))
        lexical_details(word)


def report(profile):
    st.header("내 학습 리포트")
    daily, summary = store().events(S.nickname)
    if not summary:
        st.info("학습을 시작하면 이곳에서 나의 기록을 볼 수 있어요.")
        return
    total_seconds = sum(row["seconds"] or 0 for row in summary)
    incorrect = sum(row["count"] for row in summary if row["kind"] == "incorrect")
    cols = st.columns(3)
    cols[0].metric("추정 학습시간", f"{total_seconds // 60}분 {total_seconds % 60}초")
    cols[1].metric("오답 시도", f"{incorrect}회")
    cols[2].metric("미복습 어휘", sum(not item["resolved"] for item in profile.get("mistakes", {}).values()))
    frame = pd.DataFrame([
        {"날짜": row["day"], "학습시간(분)": round(float(row["seconds"] or 0) / 60, 2),
         "오답 시도": int(row["wrong"]), "XP": int(row["xp"] or 0)} for row in daily
    ])
    if not frame.empty:
        frame["날짜"] = pd.to_datetime(frame["날짜"])
        st.subheader("최근 31일")
        time_tab, mistakes_tab, xp_tab = st.tabs(["학습시간", "틀린 개수", "획득 XP"])
        with time_tab:
            st.line_chart(frame, x="날짜", y="학습시간(분)")
        with mistakes_tab:
            st.bar_chart(frame, x="날짜", y="오답 시도")
        with xp_tab:
            st.bar_chart(frame, x="날짜", y="XP")
    st.subheader("어떤 단계가 어려웠나요?")
    counts = {}
    for row in summary:
        if row["kind"] == "incorrect":
            continue
        stage = STAGES[row["stage"] - 1]
        counts.setdefault(stage, {"전체": 0, "첫 시도 성공": 0})
        counts[stage]["전체"] += row["count"]
        if row["kind"] == "correct":
            counts[stage]["첫 시도 성공"] += row["count"]
    if counts:
        chart = pd.DataFrame([
            {"단계": stage, "첫 시도 성공률": values["첫 시도 성공"] / values["전체"],
             "평가 문항": values["전체"]} for stage, values in counts.items()
        ])
        st.altair_chart(alt.Chart(chart).mark_bar().encode(
            x=alt.X("첫 시도 성공률:Q", axis=alt.Axis(format="%"), scale=alt.Scale(domain=[0, 1])),
            y=alt.Y("단계:N", sort=list(STAGES)),
            tooltip=["단계:N", alt.Tooltip("첫 시도 성공률:Q", format=".0%"), "평가 문항:Q"],
        ), use_container_width=True)
    stage_errors = {}
    for row in summary:
        if row["kind"] in {"incorrect", "review", "revealed"}:
            stage = STAGES[row["stage"] - 1]
            stage_errors[stage] = stage_errors.get(stage, 0) + row["count"]
    if stage_errors:
        st.caption("단계별 어려움 기록 · 오답, 다시 보기, 정답 공개")
        st.bar_chart(pd.DataFrame([
            {"단계": stage, "기록": count} for stage, count in stage_errors.items()
        ]), x="단계", y="기록")
    weak = sorted(profile.get("mistakes", {}).items(), key=lambda item: -item[1]["count"])[:10]
    if weak:
        st.subheader("자주 헷갈린 단어")
        st.bar_chart(pd.DataFrame([
            {"단어": WORDS[int(key)]["word"], "복습 기록": value["count"]} for key, value in weak
        ]), x="단어", y="복습 기록")
    st.caption("학습시간은 문항 표시 후 학습 동작 사이 시간을 합산한 추정치예요. 한 번에 최대 2분까지 기록해요. 오답 시도는 실제 틀린 입력 횟수예요.")


def main():
    st.title("🍬 VOCA POP! 3000")
    try:
        if S.nickname is None:
            st.write("닉네임으로 회원가입한 뒤, 다른 기기에서도 같은 닉네임과 비밀번호로 들어오세요.")
            mode = st.radio("계정", ["로그인", "회원가입"], horizontal=True)
            with st.form("account-form", clear_on_submit=True):
                name = st.text_input("닉네임", max_chars=16)
                pin = st.text_input("숫자 비밀번호 5자리", type="password", max_chars=5)
                submitted = st.form_submit_button(mode, type="primary")
            if submitted:
                login(name, pin, mode == "회원가입")
            return

        profile = store().load(S.nickname)
        if S.get("notice"):
            st.warning(S.pop("notice"))
        with st.sidebar:
            st.header(profile["name"])
            st.metric("누적 XP", f"{profile['xp']:,}")
            st.button("학습 홈", on_click=go, args=("level",), width="stretch")
            resume = profile.get("resume")
            if resume:
                st.button("최근 학습 이어하기", on_click=go, args=("study",), kwargs=resume, width="stretch")
            for label, screen in [("전체 랭킹", "ranking"), ("오답 복습", "review"), ("내 리포트", "report")]:
                st.button(label, on_click=go, args=(screen,), width="stretch")
            st.radio("발음", ["미국 US", "영국 UK"], key="accent", horizontal=True)
            st.button("로그아웃", on_click=go, args=("level",), kwargs={"nickname": None})
        if S.screen == "ranking":
            leaderboard()
        elif S.screen == "review":
            review_words(profile)
        elif S.screen == "report":
            report(profile)
        else:
            navigate(profile)
    except (sqlite3.Error, OSError):
        st.error("학습 기록을 읽거나 저장하지 못했어요. 잠시 뒤 다시 시도해 주세요.")


if __name__ == "__main__":
    main()
