from html import escape
from io import BytesIO
import json
from pathlib import Path
import random
import re
import unicodedata

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
S = st.session_state

for key, value in {
    "profiles": {}, "nickname": None, "screen": "level",
    "level": None, "day": None, "stage": 1, "accent": "미국 US",
}.items():
    S.setdefault(key, value)


def normalize(text):
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def login():
    name = S.name_input.strip()
    if not name:
        return
    key = normalize(name)
    S.profiles.setdefault(key, {"name": name, "xp": 0, "days": {}})
    S.nickname = key
    S.screen = "level"
    S.level = S.day = None


def go(screen, **changes):
    S.update(changes)
    S.screen = screen


def prepare_stage(profile, day, number):
    record = profile["days"].setdefault(day["key"], {"stage": number, "runs": {}})
    record["stage"] = number
    if number not in record["runs"]:
        ids = list(day["ids"])
        if number != 1:
            random.shuffle(ids)
        queue = [(word_id, False) for word_id in ids]
        if number == 1:
            queue += [(word_id, True) for word_id in ids]
        record["runs"][number] = {
            "queue": queue, "index": 0, "xp": 0, "correct": 0,
            "review": [], "done": False, "question": {},
        }
    return record["runs"][number]


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
        advance(profile, run)
    else:
        run["question"]["result"] = (success, first, xp)


def advance(profile, run):
    run["index"] += 1
    run["question"] = {}
    if run["index"] == len(run["queue"]) and not run["done"]:
        run["done"] = True
        profile["xp"] += run["xp"]


def render_flashcard(profile, run, question, word, reverse, key):
    st.write("한글 뜻을 보고 영어를 떠올려 보세요." if reverse else "영어를 보고 한글 뜻을 떠올려 보세요.")
    with st.container(border=True):
        flipped = question.get("flipped", False)
        show_meaning = reverse != flipped
        st.subheader(word["meaning"] if show_meaning else word["word"])
        if st.button("카드 뒤집기 ↻", key="flip-" + key):
            question["flipped"] = not flipped
            question["checked"] = True
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
            advance(profile, run)
            st.rerun()
        return

    if stage == 2:
        if "options" not in question:
            question["options"] = choices(day, word_id)
        wrong = question.setdefault("wrong", [])
        for option in question["options"]:
            if st.button(WORDS[option]["meaning"], key=f"choice-{key}-{option}",
                         disabled=option in wrong, width="stretch"):
                if option == word_id:
                    award(profile, run, word, stage, first=not wrong)
                else:
                    wrong.append(option)
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
            else:
                st.info("영어 단어를 먼저 입력해 주세요.")
        if question.get("attempts"):
            st.warning("아직 아니에요. 빈칸 앞뒤의 표현을 다시 읽어 보세요.")
        hint_col, reveal_col = st.columns(2)
        if hint_col.button("💡 힌트 보기", key="hint-" + key, width="stretch"):
            question["hint"] = True
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
            saved = profile["days"].get(day["key"])
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
        saved = profile["days"].get(day["key"])
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
                del profile["days"][day["key"]]["runs"][S.stage]
                st.rerun()
        return

    word_id, reverse = run["queue"][run["index"]]
    word = WORDS[word_id]
    key = f"{day['key']}-{S.stage}-{run['index']}"
    if S.stage == 1:
        render_flashcard(profile, run, run["question"], word, reverse, key)
    else:
        render_quiz(profile, day, run, run["question"], word, word_id, S.stage, key)


def main():
    st.title("🍬 VOCA POP! 3000")
    if S.nickname is None:
        st.write("하루 한 세트씩, 뜻을 떠올리고 문장에서 직접 써 봐요.")
        with st.form("nickname-form"):
            st.text_input("닉네임", max_chars=16, key="name_input")
            st.form_submit_button("학습 시작 →", on_click=login, type="primary")
        return

    profile = S.profiles[S.nickname]
    with st.sidebar:
        st.header(profile["name"])
        st.metric("누적 XP", f"{profile['xp']:,}")
        st.button("닉네임 변경", on_click=go, args=("level",), kwargs={"nickname": None})
        st.radio("발음", ["미국 US", "영국 UK"], key="accent", horizontal=True)
        with st.expander("이 세션의 XP 순위"):
            for index, item in enumerate(sorted(S.profiles.values(), key=lambda p: -p["xp"]), 1):
                st.write(f"{index}. {item['name']} · {item['xp']:,} XP")
        st.caption("학습 기록은 현재 접속 세션에 저장돼요. 브라우저 새로고침이나 접속 종료 시 초기화될 수 있어요.")
    navigate(profile)


if __name__ == "__main__":
    main()
