"""Беседы отряда, акт 1 — design/banter/03_act1_party.md, согласовано 2026-09-27.

Каждая беседа — AD на двоих (Альфира и собеседник), текст над головами, один раз за игру (ванильные беседы из
двух корней — дважды, по корню за раз), не чаще раза в 5 минут, не в бою и не в диалоге. Механизм — ads.banter
и регион «Party banters» goal ALFSV_World.txt (генерируется):
  * road — оба в активном отряде, не в лагере, собеседник в 10 м;
  * camp — оба в лагере (собеседник в 20 м от неё), герой в 10 м от неё.

Б1–Б2, Б5, Б7, Б14 — ванильные AD CAMP_Bard_AD_Astarion / _GaleTressym / _Wyll / _Volo как есть: голоса обеих
сторон и постановка Larian; своих условий у них нет (только локальные флаги корней, по которым идёт второй
корень), в игре их запускает не Osiris. Непристойная часть Б7 («bawdy») в данных игры идёт в обеих ветках —
и у Уилла с рогами (WYLL_DEVIL), и без. Остальные — наши AD (основа — CAMP_Bard_AD_Astarion с заменой
собеседника): реплики спутников — текстом, её озвученные реплики — по handle.
"""
from ads import banter
from dsl import OTHER, narrate, new_flag, say, voice
from scenes.ch06_elturel import ANGRY_SONG
from scenes.recruitment import ROMANCE

ASTARION = "S_Player_Astarion_c7c13742-bacd-460a-8f65-f864fe41f255"
GALE = "S_Player_Gale_ad9af97d-75da-406a-ae13-7071c563f604"
TARA = "S_GLO_Gale_Tressym_ada7ee81-829d-48c7-ba73-9c9ec191d236"
WYLL = "S_Player_Wyll_c774d764-4a17-48dc-b470-32ace9ce447d"
SHADOWHEART = "S_Player_ShadowHeart_3ed74f06-3c60-42dc-83f6-f034cb47c679"
LAEZEL = "S_Player_Laezel_58a69333-40bf-8358-1d17-fff240d7fb12"
KARLACH = "S_Player_Karlach_2c76687d-93a2-477b-8b18-8a14b549304c"
HALSIN = "S_GLO_Halsin_7628bc0e-52b8-42a7-856a-13a6fd413323"
VOLO = "S_GLO_Volo_2af25a85-5b9a-4794-85d3-0bd4c4d262fa"
LAKRISSA = "S_DEN_Tiefling_010_23129d6c-8d39-4a4c-a4f6-cfc6637b597c"
NULL = "NULL_00000000-0000-0000-0000-000000000000"

# Лакрисса мертва (Б8): флага у игры нет — DB_Dead, как проверяет сама игра (Act3b_LOW_ElfsongTavern.txt)
LAKRISSA_DEAD = new_flag("ALFSV_LakrissaDead", "Global", "Lakrissa is dead (set from DB_Dead for the banters)")
OSIRIS_FLAGS = [LAKRISSA_DEAD]
EXTRA_OSI = [
    "// Lakrissa dead: the game has no flag (DB_Dead, as Act3b_LOW_ElfsongTavern.txt checks it)",
    "IF", f"DB_Dead({LAKRISSA})", "THEN", "PROC_GlobalSetFlagAndCache({LakrissaDead});", "",
]
EXTRA_OSI_FLAGS = {"LakrissaDead": LAKRISSA_DEAD}


def team(who):
    return f"DB_PartOfTheTeam({who})"


def any_hero(flag):
    return flag            # в requires флаг мода = «у кого-то из аватаров стоит этот флаг» (ads.banter_goal_block)


def S(en, ru, **kw):
    return say(en, ru, speaker=OTHER, **kw)


B8_REST = [
    S("Please tell me she didn't teach you.", "Только не говори, что она тебя научила.", emo="fear"),
    say("Third verse. The one about the \"blade\". ...It's not about the blade.",
        "Третий куплет. Который про «клинок». …Он не про клинок.", emo="happy/2", note="(давится смехом)"),
    S("It is *entirely* about the blade, and we will never speak of this again.",
      "Он *целиком и полностью* про клинок, и мы больше никогда об этом не говорим.", emo="angry>happy"),
    say("I'm learning it for the next celebration.", "Я разучиваю его к следующему празднику.", emo="happy/2"),
]

BANTERS = [
    # --- Астарион
    banter("B1_2", "Б1–Б2. Астарион: «Экскурсия», «Лютней по башке»", ASTARION, "camp", plays=2, requires=[team(ASTARION)],
           vanilla="CAMP_Bard_AD_Astarion_8072bdb9-de5d-5f1c-a759-c690c4b39cdd", source="ванильный AD: корень N1, потом N9"),
    banter("B3", "Б3. Астарион: «Рифма»", ASTARION, "road", after=("B1_2", 2),
           *[S("Tell me, darling - am I in this famous song of yours?", "Скажи-ка, дорогуша, я есть в твоей знаменитой песне?",
               emo="happy/2"),
             say("You're in the second verse. As a warning.", "Ты во втором куплете. В качестве предостережения.", emo="happy"),
             S("A warning. How flattering. And what rhymes with \"Astarion\"?",
               "Предостережения. Как лестно. И что же рифмуется с «Астарионом»?", emo="thinking"),
             say("\"Carrion.\"", "«Вон».", emo="happy/2"),
             S("...I'm beginning to regret asking.", "…Я начинаю жалеть, что спросил.", emo="disgust")]),
    banter("B4", "Б4. Астарион: «Муза» 💞", ASTARION, "road", requires=[any_hero(ROMANCE)],
           *[S("I see our bard has found herself a *muse*.", "Смотрю, у нашего барда появилась *муза*.", emo="happy/2"),
             say("I don't know what you mean.", "Не понимаю, о чём ты.", emo="surprise"),
             S("You've rhymed \"eyes\" with \"eyes\" three times today. Out loud.",
               "Ты сегодня трижды зарифмовала «глаза» с «глазами». Вслух.", emo="happy"),
             say("...It's a *refrain*.", "…Это *припев*.", emo="happy/2")]),
    # --- Гейл и Тара
    banter("B5", "Б5. Тара", TARA, "camp", plays=2,
           vanilla="CAMP_Bard_AD_GaleTressym_283fb1de-0587-991a-58e4-eb7d412b3813", source="ванильный AD: корень N1, потом N6"),
    banter("B6", "Б6. Гейл: «Баллада для Мистры»", GALE, "road",
           *[say("Gale, is it true Mystra... *talks* to you? Actually talks?",
                 "Гейл, это правда, что Мистра… с тобой *разговаривает*? Прямо разговаривает?", emo="surprise>happy"),
             S("Talked. Past tense. It's a long story, and not the sing-along kind.",
               "Разговаривала. В прошедшем времени. Это долгая история, и подпевать там нечему.", emo="sad"),
             say("Everything's a sing-along if you're brave enough. I could write her a ballad. From you. Anonymous, obviously.",
                 "Подпевать можно всему, было бы смелости. Я могла бы написать ей балладу. От тебя. Анонимно, конечно.",
                 emo="happy/2"),
             S("I suspect the goddess of magic would recognise my... style.", "Подозреваю, богиня магии узнала бы мой… стиль.",
               emo="thinking", note="(кашляет)"),
             say("Oh, then she'd *love* it.", "О, тогда ей точно *понравится*.", emo="happy/2")]),
    # --- Уилл
    banter("B7", "Б7. Уилл: «Настоящий Клинок Фронтира»", WYLL, "camp", requires=[team(WYLL)],
           vanilla="CAMP_Bard_AD_Wyll_e56f19d9-db4c-198d-320d-59175acfe2a3", source="ванильный AD: корень N1"),
    banter("B8", "Б8. Уилл: «Непристойная версия»", WYLL, "road", after=("B7", 1),
           variants=[
               ([LAKRISSA_DEAD.off], [say("Lakrissa knows the bawdy \"Endless Blade\". All of it.",
                                          "Лакрисса знает непристойный «Бесконечный клинок». Целиком.", emo="happy/2"),
                                      *B8_REST]),
               ((), [say("A tiefling in the Grove knew the bawdy \"Endless Blade\". All of it.",
                         "Один тифлинг в Роще знал непристойный «Бесконечный клинок». Целиком.", emo="happy/2"), *B8_REST]),
           ]),
    # --- Шэдоухарт
    banter("B9", "Б9. Шэдоухарт: «Помнить»", SHADOWHEART, "road",
           *[voice("he4532a09g6b7fg40aeg8ccbgb3cb21c96147"),      # And the dead deserve to be remembered…
             S("And if someone would rather forget?", "А если кто-то предпочёл бы забыть?", emo="thinking"),
             say("Then they get a very short song. ...Why? Is there something you'd rather forget?",
                 "Тогда им достаётся очень короткая песня. …А что? Ты что-то хочешь забыть?", emo="happy>thinking"),
             S("I'd rather not remember whether there is. ...Forget I said that.",
               "Я бы предпочла не помнить, есть ли такое. …Забудь, что я сказала.", emo="sad>angry"),
             say("That's exactly the sort of line I'd put in a song.", "Именно такую строчку я бы вставила в песню.",
                 emo="thinking", note="(тихо)")]),
    # --- Лаэзель
    banter("B10", "Б10. Лаэзель: «Дурацкий меч»", LAEZEL, "road",
           *[S("Your songs will not stop a blade, tiefling.", "Твои песни не остановят клинок, тифлинг.", emo="disgust"),
             voice("hffc113bcg4ca4g4d96g9493g1f326f83da6b"),      # Violence doesn't fix everything…
             S("*Silly.* My blade has taken more heads than you have written verses.",
               "*Дурацкий.* Мой клинок снял больше голов, чем ты написала куплетов.", emo="angry"),
             say("Vicious Mockery is a song, you know. I could demonstrate.",
                 "Вообще-то «Язвительная насмешка» — тоже песня. Могу показать.", emo="happy/2"),
             S("...Do not.", "…Не надо.", emo="angry")]),
    # --- Карлах
    banter("B11", "Б11. Карлах: «Аверно»", KARLACH, "camp", requires=[team(KARLACH)],
           *[voice("h92477c68gad89g464eg8444g69646e3027f5", speaker=OTHER),   # Bad luck to turn a bard away from a campfire.
             say("You were in Avernus. For years.", "Ты была в Аверно. Годами.", emo="thinking"),
             S("Long enough to hate the smell. Brimstone and burnt hair. You're from Elturel, yeah?",
               "Достаточно, чтобы возненавидеть запах. Сера и палёные волосы. Ты ведь из Элтуриэля?", emo="disgust>thinking"),
             say("...My mother didn't make it out.", "…Мама оттуда не выбралась.", emo="sad"),
             S("Then I'll carry her out with me. Next time I punch one of Zariel's lot in the teeth - that one's for her. Deal?",
               "Тогда я вынесу её с собой. В следующий раз, когда я дам кому-то из шайки Зариэль в зубы, — это будет за неё. Идёт?",
               emo="sad>happy", note="(тихо, что для неё редкость)"),
             say("That's the nicest thing anyone's ever said to me with the word \"teeth\" in it.",
                 "Это самое доброе, что мне говорили со словом «зубы».", emo="sad>happy/2", note="(смеётся сквозь слёзы)")]),
    banter("B12", "Б12. Карлах: «Злая песня» 🔁", KARLACH, "road", requires=[any_hero(ANGRY_SONG)],
           *[say("Karlach. I need someone to sing an angry song with. Loudly.", "Карлах. Мне нужен кто-то, с кем спеть злую песню. Громко.",
                 emo="angry"),
             S("*Finally.* Someone in this camp with taste. What are we angry at?",
               "*Наконец-то.* Хоть у кого-то в лагере есть вкус. На что злимся?", emo="happy/2"),
             say("Devils. Elturel. The High Overseer. Gnolls. Squirrels, a bit.",
                 "На дьяволов. На Элтуриэль. На Высшего смотрителя. На гноллов. Немножко на белок.", emo="angry>thinking"),
             S("Squirrels?", "На белок?", emo="surprise"),
             say("They know what they did.", "Они знают, что натворили.", emo="angry"),
             S("...I'm in. ONE, TWO -", "…Я в деле. РАЗ, ДВА…", emo="happy/2")]),
    # --- Хальсин
    banter("B13", "Б13. Хальсин: «Деревья помнят»", HALSIN, "camp", requires=[team(HALSIN)],
           *[S("You sang in the Grove, before all this. The trees remember it.", "Ты пела в Роще, ещё до всего этого. Деревья это помнят.",
               emo="happy"),
             say("The trees? Oh gods - which bit? The bit where I threw the quill?",
                 "Деревья? О боги — какой кусок? Тот, где я швырнула перо?", emo="surprise>fear"),
             S("The end. When the song finally held. They were patient with you.",
               "Конец. Когда песня наконец сложилась. …Они были к тебе терпеливы.", emo="happy", note="(улыбается)"),
             say("...Everyone was. I don't think I noticed at the time.", "…Все были. Кажется, тогда я этого не замечала.",
                 emo="thinking>sad/1")]),
    # --- Воло
    banter("B14", "Б14. Воло: «Двойникозад»", VOLO, "camp", plays=2,
           vanilla="CAMP_Bard_AD_Volo_b5a2ed4f-7bb0-5bb1-bb78-0a2fbaa0d921", source="ванильный AD: корень N2, потом N12"),
]
EXTRA_SCENES = [b.scene for b in BANTERS if b.scene is not None]
