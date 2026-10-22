# G4 Mini-project: Vocabulary Learning App (ver. 1.0; asof 10/22, 2026)

## 👥 Group Information

| Item | Details |
|---|---|
| Group | G4 |
| Members | [정든님 (Leader)], [정해윤], [김수현], [박정휴] |
| README editor | [정해윤] |
| Date & Time | 10/22, [13:00] – [16:00] |
| Location | [e.g., 1층 미래교육센터 / Room 118] |


> Take photos at the **start, middle, and end** of the meeting (with a clock visible). You will upload them in the Google Form.

---

## 💙 1. What We Learned from the Two Articles

### 1-1. Webb (2007): Vocabulary Learning

- **Main point:** 반복적인 문맥 노출은 단어의 의미뿐 아니라 철자와 사용법 등 다양한 어휘 지식을 점진적으로 발달시킨다.
- **What teachers can learn:** 단어를 몇 번 가르쳤는가보다 학생이 얼마나 단어를 다양하고 포괄적으로 이해하고 사용할 수 있는가에 초점을 둬야 한다.

### 1-2. Nakata et al. (2021)

- **Main point:** 어휘 시험은 학습 결과를 확인하는 동시에 학습을 촉진하는 도구이다. 이전의 단어를 다시 출제하는 누적 학습은 장기적인 기억 향상에 도움에 된다.
- **What teachers can learn:** 영어교사는 평가를 학습의 일부로 설계를 하고, 당장의 시험결과와 장기적인 기억, 학습자의 동기를 모두 고려해야 한다.

### 1-3. Our Takeaway for the App

- 유의어 및 반의어, 파생 관계의 단어를 이해하고, 반복적으로 학습하여 연계가 가능한 학습을 유도하는 앱을 만들고자 한다.

---

## 💙 2. Our Selected Words from the Basic Vocabulary List

### 2-1. About the List

- [목록을 살펴보고 알게 된 점. 예: 3,000개 단어, `*`/`**`로 학교급 표시, 단어군(word family)과 변이형(variation) 정보 포함 등]

### 2-2. Selected Words (10–20)

`[accurate]`, `[common]`, `[polite]`, `[refuse]`, `[permit]`, `[increase]`, `[reduce]`, `[improve]`, `[succeed]`, `[complex]`

### 2-3. Why We Chose These Words

- 초등학교과 고등학교 사이의 중2 정도의 아이들을 대상으로 하기에 비교적 쉬운 단어와 어려운 단어를 적절히 배합하고자 했다.
- 유의어와 반의어 관계에 있는 쉽고 이해 가능한 단어쌍을 가지고 있어 포괄적인 학습을 가능케 한다.
- 원어민 화자가 일상적으로 사용하는 단어이자 향후 영어 시험 지문에서도 빈출하는 단어이다.

---

## 💙 3. App Design Draft

### 3-1. Design Concept

- 플래쉬카드, 퀴즈, 밝고 귀여운 배경화면, BGM과 상호작용 시 나오는 효과음

### 3-2. Learners

- Korean Middle School Grade 3 (K8) learners

### 3-3. Goal

- 단어의 의미를 적절히 이해하고, 이를 응용하여 지문 맥락 속에서 어떤 단어가 들어가야 할지 이해할 수 있다.

### 3-4. Learning Activities

- **Encounters (Webb 2007):** 3번 정도 반복적으로 학습하고, 유의어와 반의어, 혹은 변형이 모두 들어간 지문(1-2 문장)을 읽으며, fill in the blank, 실제 문장에서 사용할 수 있는지 확인한다.
- **Retrieval (Nakata et al. 2021):** 앱을 활용할 수록 학생은 본인이 학습하는 단어를 더욱 머릿속에 저장하게 된다.

### 3-5. Use of the List Information

| Information | How our app uses it |
|---|---|
| Level (`*`, `**`) | 레벨 간의 구분은 해두지 않고 무작위하게 섞어 학생들이 이해할 수 있는 플래쉬카드, 퀴즈 등을 제작함 |
| Word family (e.g., *species* ~ *specify*) | 단어의 파생형 중 어떤 것이 있는지 보여주는 칸을 배치함 |
| Variation (e.g., *rumor* / *rumour*) | 이 앱에서는 variation을 활용한 문제를 내기보다는 variation이 있는지 없는지를 설명하는 부분을 추가함 |

### 3-6. Context Elements (LPGCTXF, Week 03)

| Element | Our decision |
|---|---|
| L | [Korean Middle School Grade 3 (K8) learners] |
| P | [A2-B1, 기본적인 단어 사용은 가능하나, 문맥에서의 활용에 어려움이 있는 학생들에게 활용] |
| G | [입력된 단어의 의미를 적절히 이해하고, 이를 응용하여 지문 맥락 속에서 어떤 단어가 들어가야 할지 이해할 수 있다.] |
| C | [10개의 단어와 그의 유의어와 반의어, 파생 관계의 단어들] |
| T | [10-15분, 개별적으로 활동을 진행함] |
| X | [학교 Wi-fi에 문제가 생기면 진행하기 어려움, 1인당 디바이스 하나가 있어야 함] |
| F | [학생이 틀린 답을 골랐을 때 기회를 계속 제공하며, 학생이 스스로 생각하고 답안을 찾을 수 있도록 한다.] |

---

## 💙 4. App Features

1. **[Flashcards (word → meaning)]**: This feature helps learners memorize vocabulary because they can practice recalling words and meanings in both directions.
2. **Example Sentences & Multiple-choice**: This feature helps learners understand vocabulary in context because they can see how target words are used in sentences and choose the correct meaning..
3. **Read the Passage & Fill-in-the-blank**: This feature helps learners apply vocabulary in context because they can read short passages and recall the correct words to complete the blanks.

---

## 💙 5. Sample Word Data

| Word | Word-family | Variation | Level | Meaning (Korean) | Example sentence | Synonym | Antonym |
|---|---|---|---|---|---|---|---|
| accurate | accuracy, accurately | NA | NA | 정확한 | We need accurate information. | correct, precise | inaccurate |
| common | commonly, uncommon | NA | ** | 흔한, 일반적인 | This is a common mistake. | usual, ordinary | rare, uncommon |
| polite | politely, politeness, impolite | NA | ** | 예의 바른 | Please be polite to others. | NA | rude, impolite |
| refuse | refusal | NA | ** | 거절하다 | He refused to answer the question. | decline | accept |
| permit | permission, permissible | NA | NA | 허락하다 | The rules permit students to work together. | allow | forbid |
| increase | increasing, increasingly | NA | ** | 증가하다, 증가시키다 | The number of visitors increased. | rise, grow | decrease |
| reduce | reduction, reducible | NA | ** | 줄이다, 감소시키다 | We should reduce plastic waste. | decrease, lessen | increase |
| improve | improvement, improved | NA | ** | 향상되다, 향상시키다 | Practice can improve your English. | get better | worsen |
| succeed | success, successful, successfully, unsuccessful | NA | ** | 성공하다 | She succeeded in finding the answer. | NA | fail |
| complex | complexity | NA | ** | 복잡한 | This problem is complex. | complicated | simple |

---



## 💙 6. Test and Improve

### 6-1. Checklist

- [O] All features work (every button was clicked).
- [O] All words, meanings, and sentences are correct.
- [O] The app gives clear feedback for right and wrong answers.
- [O] Learners **retrieve** words and meet each word **more than once**.
- [O] The app is easy to use on a phone.

### 6-2. Problems Found and How We Fixed Them

| Problem | Fix |
|---|---|
| [한 단계를 완료하기 전에는 다른 단계로 나아갈 수 없었음] | [한 단계를 완료하기 전에도 다른 단계로 나아갈 수 있음] |
| [BGM 음향 조절이 안 되었음] | [BGM 음향 조절이 가능하게 변경함] |
| [학생들에게는 굳이 드러낼 필요 없는 레벨(NA, *, **)가 보임] | [학생들에게는 레벨이 보이지 않게 함] |

### 6-3. Saved Versions

- `index_v1.html`: [what this version has]
- `index_v2.html`: [what changed]
- `G1_project_draft.html`: final version

---

## 💙 7. Next Steps

- 단어의 파생형을 학습할 수 있도록 리스트를 확장하고 이를 검증할 퀴즈 등을 구성한다.
