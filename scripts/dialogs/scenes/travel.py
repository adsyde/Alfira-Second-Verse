"""Случайные фразы в пути, акт 1 — design/banter/01_act1_world.md §2, согласовано 2026-09-26.

Одна фраза раз в 3–6 минут (случайно), пока Альфира идёт с отрядом: не в лагере, не в бою и не в
разговоре. Каждая фраза звучит один раз («без повторов»): флаг ALFSV_Travel_NN_Played на Альфире.
Набор зависит от настроения (флаги ads.MOOD, их ставит Osiris перед запуском):
  ❄️ одобрение ниже 0 — только «…Just keep walking.», обычные фразы молчат;
  высокое одобрение (40+) — «Ты ходишь, как герой баллады»;
  ✨ искра или 💞 роман (флаг SPARK ставится и при романе) — «Я смотрела мимо тебя»; 💞 роман — «Второй куплет».
Игра берёт первую по порядку фразу, чьи условия выполнены, — порядок ниже перемешивает наборы.
Три озвученные — её лагерные реплики из CAMP_Bard_AD (голос и эмоции Larian).
"""
from ads import COLD, ROMANCE, SPARK, WARM, MOOD, travel
from dsl import ALFIRA, say, voice

NOT_COLD = MOOD.Cold(ALFIRA, False)

TRAVEL = travel(
    (say("...Just keep walking.", "…Просто иди.", emo="angry>sad"), [COLD]),
    (voice("haa70d8f1gae64g4199g9eaag6e37ae8efb72"), [NOT_COLD]),                  # This is so exciting.
    (say("Hm? No, I wasn't looking at you. I was looking *past* you. Very intently.",
         "М? Нет, я не на тебя смотрела. Я смотрела *мимо* тебя. Очень пристально.", emo="surprise>happy/2"),
     [NOT_COLD, SPARK]),
    (voice("he8c95031g4a4ag4d7dg9fbbg67cd2dcc462c"), [NOT_COLD]),                  # Should I write a song? No, they'd…
    (say("...*dance upon the*... no. No, that's hers.", "…*ты танцуешь среди*… нет. Нет, это её.",
         emo="happy>sad", note="(напевает)"), [NOT_COLD]),
    (say("You walk like someone out of a ballad. It's very annoying.",
         "Ты ходишь, как герой баллады. Это очень раздражает.", emo="thinking>happy/2"), [NOT_COLD, WARM]),
    (say("What rhymes with \"tadpole\"? Nothing. Nothing rhymes with tadpole.",
         "Что рифмуется с «личинкой»? Ничего. С «личинкой» не рифмуется ничего.", emo="thinking>angry"), [NOT_COLD]),
    (say("Second verse is coming along. It's mostly about your hands. Don't ask.",
         "Второй куплет продвигается. Он в основном про твои руки. Не спрашивай.", emo="happy/2"), [NOT_COLD, ROMANCE]),
    (voice("hd08860f4g5095g4e51g8915gf36ae73be676"), [NOT_COLD]),                  # I hope I do a good job.
    (say("My feet hurt. Heroes' feet must hurt too, right? They just don't put it in the songs.",
         "У меня болят ноги. У героев ведь тоже болят, да? Просто в песнях про это не поют.", emo="sad>thinking>happy"),
     [NOT_COLD]),
)
SCENE = TRAVEL.scene
