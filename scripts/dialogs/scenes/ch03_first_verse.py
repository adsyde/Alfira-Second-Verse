"""Глава 3 «Первый куплет» — design/dialogs/04_act1_ch3_first_verse.md, согласовано 2026-09-27.

Открывается после долгого отдыха, когда сыграны главы 1–2 и была «первая крупная победа» акта 1 —
одно из (story_any, по данным игры):
  * вожаки гоблинов разбиты — GOB_State_LeadersAreDead (все трое, Act1_GOB_GoblinHunt.txt);
  * спасена Майрина от Тетушки Этель — запись журнала HAG_HagSpawn / SavedMayrina (флага у игры нет:
    Act1_HAG_HagAmbush.txt и Act1_HAG_HagSpawn.txt проверяют её через QuestUpdateIsUnlocked);
  * отбит налёт на Рощу — DEN_AttackOnDen_State_DenVictory (Act1_DEN_AttackOnDen.txt, «Raiders defeated!»).
Глава необязательная (optional): пока победы нет, она очередь не держит; только в акте 1 (act=1).
Вход — в любом разговоре в отряде или в лагере. При одобрении ниже 0 — холодная реплика, глава ждёт.
Сыгранной глава считается после первого ответа героя в V1, кроме «Потом» (CH.done): с ним — конец,
глава предлагается снова.

Куплет — по мотиву героя из вербовки (🔁 A5, ALFSV_HeroMotive_*), припев — по правилу дороги из главы 1
(🔁 ALFSV_HeroRule_*). voice("h…") — её озвученная реплика игры, say(...) — новая, только текст,
narrate(...) — ремарка рассказчика. Английские реплики героя — из сценария.
"""
from dsl import ALFIRA, PLAYER, Scene, chapter, check, narrate, new_flag, opt, osi, outcome, say, voice
from scenes.ch01_first_night import RULE_DISTRUST, RULE_FORCE, RULE_LOYALTY
from scenes.ch02_lute import DURGE_URGE_NEAR
from scenes.recruitment import MOTIVE_DUTY, MOTIVE_HONESTY, MOTIVE_MODESTY, MOTIVE_PROFIT, SPARK
from vanilla import APPROVAL_SP1, DC, F, T

NULL = "NULL_00000000-0000-0000-0000-000000000000"
SAVED_MAYRINA = osi(f'QuestUpdateIsUnlocked({NULL}, "HAG_HagSpawn", "SavedMayrina", 1)',
                    "спасена Майрина (журнал HAG_HagSpawn / SavedMayrina)")

CH = chapter(3, "Первый куплет", after_rest=True, optional=True, act=1,
             story_any=[F.GoblinLeadersDead.on, SAVED_MAYRINA, F.GroveRaidRepelled.on])

SCENE = Scene(
    name="ALFSV_Alfira_Ch03_FirstVerse",
    dialog_id="ae06974a-c262-4fdc-8a9c-eed5d4b5596e",      # ID ресурса вложенного диалога главы, не менять
    base="DEN_Bard_InParty",
    # DEN_TieflingBard_Bard — песня в Роще (V1, «размер», V4); DEN_AttackOnDen_Bard — «злодеев-тифлингов полно»;
    # HAV_AlfiraTale_Bard — «целый список песен» (V4, одобрение 20+)
    voice_from=["DEN_TieflingBard_Bard", "DEN_AttackOnDen_Bard", "HAV_AlfiraTale_Bard"],
    chapter=CH,
    status="согласовано 2026-09-27",
)
S = SCENE

# 🔁 Запоминается — на герое, как воспоминания глав 1–2.
# «В главе 3 была песня» — её вспомнит праздник (глава 4, «первый куплет — серьёзный»)
FIRST_VERSE = new_flag("ALFSV_Song_FirstVerse", "Object", "Alfira showed the hero the first verse of his song (chapter 3)")
HONEST_CRITIC = new_flag("ALFSV_Song_HonestCritic", "Object", "Hero was Alfira's honest critic (the metre limps)")
CO_AUTHOR = new_flag("ALFSV_Song_CoAuthor", "Object", "Hero improved a rhyme: the song has both names (co-author)")
TIEFLING_SONG = new_flag("ALFSV_Song_Tieflings", "Object", "Hero gave the verse away: a song about the tieflings (act 3)")
# 💞 шаги романа (их вспомнит «Первый поцелуй»)
OUR_SONG = new_flag("ALFSV_Romance_OurSong", "Object", "Romance step: 'our song' (co-author with a spark)")
SECOND_VERSE = new_flag("ALFSV_Romance_SecondVerse", "Object", "Romance step: 'maybe in the second verse' - she is in the song")
# 🏷️ Темный Соблазн посмотрел на свои руки (этап 7)
DURGE_HANDS = new_flag("ALFSV_Durge_LookedAtHands", "Object", "Dark Urge looked at his hands while Alfira sang of gentle hands")

APPROVAL20 = APPROVAL_SP1[20]

# --- V1. Приветствие ---

S.greeting("V1", voice("hed1a383age7dfg4fdcg8258g6897ba40b68c"),      # It's still rough, but my song is getting there!
           go="V1_menu")

S.menu("V1_menu",
       # любопытный
       opt("Покажи.", "Show me.", approve=+1, set=[CH.done],
           reply=[say("Now? Right now? ...Fine. Don't laugh. Actually, laugh if it's funny. Not if it's sad.",
                      "Сейчас? Прямо сейчас? …Ладно. Не смейся. Вернее, смейся, если смешно. Если грустно — не смейся.",
                      emo="surprise>thinking>happy/2")],
           go="V2"),
       # шутливый
       opt("Надеюсь, про меня только хорошее?", "Only flattering things about me, I hope?", set=[CH.done],
           reply=[say("Oh, I'm *brutally* honest. Lihala's rule. You'll see.",
                      "О, я *беспощадно* честна. Правило Лихейлы. Сейчас увидишь.", emo="happy/2>happy")],
           go="V2"),
       # скромный
       opt("Не надо песен обо мне.", "Please don't write songs about me.", approve=+1, set=[CH.done],
           reply=[say("Too late. Songs don't ask permission. That's rather the point of them.",
                      "Поздно. Песни не спрашивают разрешения. В этом, собственно, их смысл.", emo="happy>thinking")],
           go="V2"),
       # 🏷️ отказался от песни на празднике (CAMP_GoblinHuntCelebration_Event_RefusedBardSong, флаг на герое)
       opt("Я же говорил — не надо.", "I told you - no songs.", when=[F.RefusedBardSong(PLAYER), ~T.FEMALE(PLAYER)],
           set=[CH.done], reply=[say("You did. And I *listened*. I just didn't *agree*.",
                                     "{Говорил|Говорила}. И я *выслушала*. Просто *не согласилась*.", emo="happy/2")],
           go="V2", key="V1_menu.refused_m"),
       opt("Я же говорила — не надо.", "I told you - no songs.", when=[F.RefusedBardSong(PLAYER), T.FEMALE(PLAYER)],
           set=[CH.done], reply=[say("You did. And I *listened*. I just didn't *agree*.",
                                     "{Говорил|Говорила}. И я *выслушала*. Просто *не согласилась*.", emo="happy/2")],
           go="V2", key="V1_menu.refused_f"),
       # деловой: конец, глава ждёт
       opt("Потом.", "Later.",
           reply=[say("Right. Later. It'll be longer by then. You've been warned.",
                      "Ладно. Потом. К тому времени она станет длиннее. Я предупредила.", emo="happy>thinking")],
           end=True),
       )

# --- V2. Куплет: по мотиву героя из вербовки 🔁 A5 ---

VERSE_NEXT = ["V2_loyalty", "V2_force", "V2_distrust", "V2_wait"]      # припев: по правилу дороги из главы 1

S.block("V2",
        narrate("She clears her throat, looks down at the sheet, then over it - at you.",
                "Она прочищает горло, смотрит в листок, потом — поверх него, на тебя.", emo="thinking",
                set=[FIRST_VERSE(PLAYER)]),
        go=["V2_duty", "V2_modesty", "V2_honesty", "V2_profit", "V2_default"])

DUTY = say("*When the sky rained fire and the brave all fled,<br>one stayed behind where the others bled.<br>"
           "\"Someone has to,\" was all they said -<br>and the road bent low where the hero led.*",
           "*Когда пылало небо и храбрый люд бежал,<br>{один остался|одна осталась} там, где раненый лежал.<br>"
           "«Кто-то должен», — вот и весь ответ, —<br>и путь склонился {герою|героине} вслед.*",
           emo="thinking>happy", note="мотив «долг»")
S.block("V2_duty", DUTY, when=[MOTIVE_DUTY(PLAYER)], go=VERSE_NEXT)
S.block("V2_modesty",
        say("*They never meant to be a hero's tale,<br>just lost, just late, just off the trail -<br>"
            "but every wrong turn and every road gone pale<br>led right to the place where the dark would fail.*",
            "*{Не рвался|Не рвалась} в легенду наш герой —<br>{плутал|плутала}, {спешил|спешила} не той тропой, —<br>"
            "но каждый неверный поворот<br>туда, где гибнет тьма, ведёт.*",
            emo="happy>thinking>happy", note="мотив «скромность»"),
        when=[MOTIVE_MODESTY(PLAYER)], go=VERSE_NEXT)
S.block("V2_honesty",
        say("*There's a worm in the hero's head, they say,<br>that whispers of death by night and day.<br>"
            "They carry that dark like a candle's glow,<br>so I can finish the songs I know.*",
            "*Червь в голове у героя живёт,<br>смерть {ему|ей} шепчет — и шепчет, и ждёт.<br>"
            "{Он|Она} же несёт эту тьму, как свечу,<br>чтоб я допела всё, что хочу.*",
            emo="thinking>sad>happy", note="мотив «честность»"),
        when=[MOTIVE_HONESTY(PLAYER)], go=VERSE_NEXT)
S.block("V2_profit",
        say("*Pay the hero, pay them well,<br>coin for every beast they fell -<br>"
            "yet when the poor have naught to give,<br>the hero fights so they may live.*",
            "*Плати герою звонкой монетой<br>за каждого зверя, за каждую победу.<br>"
            "Но если бедняк не может платить —<br>{герой|героиня} всё равно пойдёт защитить.*",
            emo="happy/2>thinking>happy", note="мотив «выгода»"),
        when=[MOTIVE_PROFIT(PLAYER)], go=VERSE_NEXT)
# [решение сборки] мотива нет (другой герой в совместной игре, старое сохранение) — куплет «долг»
S.block("V2_default", DUTY, go=VERSE_NEXT)

# Правило дороги в припеве 🔁 глава 1; «другое или нет» — без реплики
S.block("V2_loyalty",
        say("And the chorus is yours. *\"Always go back for your own.\"* I told you I'd steal it.",
            "А припев — твой. *«Всегда возвращайся за своими».* Я же говорила, что украду.", emo="happy>happy/2"),
        when=[RULE_LOYALTY(PLAYER)], go="V2_wait")
S.block("V2_force",
        say("I left out \"strike first\". It didn't scan. ...And I didn't like it.",
            "«Бей первым» я не взяла. Не легло в размер. …И не понравилось.", emo="thinking>sad"),
        when=[RULE_FORCE(PLAYER)], go="V2_wait")
S.block("V2_distrust",
        say("There's a line about trust. It's the saddest one. I'm not singing it yet.",
            "Там есть строчка про доверие. Самая грустная. Её я пока не пою.", emo="sad>thinking"),
        when=[RULE_DISTRUST(PLAYER)], go="V2_wait")
# [решение сборки] переход к ответу героя: ремарка без слов (у реплик без условий должен быть общий узел)
S.block("V2_wait",
        narrate("She lowers the sheet and waits.", "Она опускает листок и ждёт.", emo="thinking"),
        go="V3")

# --- V3. Что скажет герой ---

S.menu("V3",
       opt("Это прекрасно.", "It's beautiful.", approve=+2,
           reply=[say("Oh, thank the gods. I've been rewriting line three since the Grove.",
                      "Ох, слава богам. Я третью строчку переписываю с самой Рощи.", emo="surprise>happy",
                      note="(выдыхает)")],
           go="V4"),
       opt("Во второй строке хромает размер.", "The metre limps in the second line.", approve=+2,
           set=[HONEST_CRITIC(PLAYER)],
           reply=[voice("h35f52e08gba2bg44cag94edg8b6f0318084a"),      # Heh. She'd yell at me for that metre…
                  say("You're right. You're *annoyingly* right. Nobody's been annoyingly right at me in months. I missed it.",
                      "Ты {прав|права}. До *обидного* {прав|права}. Мне уже несколько месяцев никто не говорил такого. "
                      "Я соскучилась.", emo="thinking>happy")],
           go="V4"),
       check("*Дай-ка я. Может, так?* [Предложить свою рифму.]", "*Here - what if it went like this?* [Offer your own rhyme.]",
             skill="Performance", ability="Charisma", dc=DC.Act1_Medium,
             success=outcome(approve=+3, set=[CO_AUTHOR(PLAYER)], reply=[
                 say("...Oh. Oh, that's *better*. That's annoyingly better. It's going in.",
                     "…Ой. Так *лучше*. До обидного лучше. Беру.", emo="surprise>happy")],
                 go=["V3_names_spark", "V3_names"]),
             failure=outcome(approve=+1, reply=[
                 say("You rhymed \"hero\" with \"hero\".", "Ты {зарифмовал|зарифмовала} «герой» с «героем».",
                     emo="happy/2", note="(давится смехом)")],
                 go="V4")),
       opt("Сделай меня героичнее. Драконы, армии…", "Make me more heroic. Dragons, armies...", approve=-1,
           reply=[say("Lihala had a rule: *a song that flatters the living insults the dead.* When you kill a dragon, "
                      "I'll write the dragon in.",
                      "У Лихейлы было правило: *песня, которая льстит живым, оскорбляет мёртвых.* Убьёшь дракона — "
                      "впишу дракона.", emo="thinking>happy")],
           go="V4"),
       opt("Убери меня. Пусть будет песня о тифлингах.", "Leave me out. Make it a song about the tieflings.", approve=+2,
           set=[TIEFLING_SONG(PLAYER)],
           reply=[voice("h5b6e4cd3g0a08g4b77g99abgaf9c35487c70"),      # Huh. Plenty with tiefling villains…
                  say("...You'd do that? Give the verse away? That's - I'm going to write a second song now. Thanks *so* much.",
                      "…Ты бы так {сделал|сделала}? {Отдал|Отдала} бы куплет? Это… Теперь мне придётся писать вторую "
                      "песню. Огромное *спасибо*.", emo="surprise>happy/2")],
           go="V4"),
       # ✨ 💞
       opt("А ты в этой песне есть?", "Are you in this song?", when=[SPARK(PLAYER)], approve=+2,
           set=[SECOND_VERSE(PLAYER)],
           reply=[say("Bards aren't in their own songs. That's the rule.", "Барды не поют о себе. Таково правило.",
                      emo="happy>thinking"),
                  narrate("A pause.", "Пауза.", emo="thinking", shot="alfira_close"),
                  say("...Maybe in the second verse. Don't hold me to it.", "…Может, во втором куплете. Не лови меня на слове.",
                      emo="surprise>happy/2", shot="alfira_close")],
           go="V4"),
       # 🏷️ Темный Соблазн, Побуждение рядом (🔁 гл. 2)
       opt("[Посмотреть на свои руки.]", "[Look at your hands.]",
           when=[T.REALLY_DARK_URGE(PLAYER), DURGE_URGE_NEAR(PLAYER)], set=[DURGE_HANDS(PLAYER)],
           reply=[say("What? You've got lovely hands. They're in the second line, actually. \"Gentle hands that...\" - "
                      "what? Why are you looking at me like that?",
                      "Что? У тебя красивые руки. Они, кстати, во второй строчке. «Нежные руки, что…» — что? "
                      "Чего ты так смотришь?", emo="happy>surprise>confusion")],
           go="V4"),
       opt("Кому вообще нужны песни.", "Who even needs songs.", approve=-2,
           reply=[narrate("She folds the sheet.", "Она сворачивает листок.", emo="sad"),
                  say("The people who can't fight, mostly. The ones you keep saving. Ask them.",
                      "В основном те, кто не может сражаться. Те, кого ты всё время спасаешь. Спроси у них.",
                      emo="angry>sad")],
           go="V4"),
       )

# Успех Исполнения: «на этой песне будут оба наших имени» — с искрой ещё и 💞 «наша песня»
NAMES = ("Both our names on this one.", "На этой песне будут оба наших имени.")
S.block("V3_names_spark", say(*NAMES, emo="happy/2", shot="alfira_close", set=[OUR_SONG(PLAYER)]),
        when=[SPARK(PLAYER)], go="V4")
S.block("V3_names", say(*NAMES, emo="happy/2"), go="V4")

# --- V4. Конец ---

S.block("V4", voice("h7f705d14gb965g49eegbc96g7e5d6b80b5f8"),        # Heh. And then some. But I have the bones of the song…
        go=["V4_catalogue"])
S.block("V4_catalogue", voice("hb85188d5geb00g452fgb791gc859831ca00e"),  # …an entire catalogue of songs about you.
        when=[APPROVAL20(ALFIRA)], end=True)
