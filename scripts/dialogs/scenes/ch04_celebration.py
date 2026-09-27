"""Глава 4 «Праздник» — design/dialogs/05_act1_ch4_celebration.md, согласовано 2026-09-27.

Ночь праздника тифлингов в лагере (NIGHT_GoblinHunt_TieflingCelebration). Глава-событие: входа в разговоре
в отряде нет (hub=False), диалоги той ночи выбирает Osiris (ALFSV_Companion.txt, регион «Tiefling
celebration»), пока стоит ALFSV_Celebration_Tonight — от начала праздника с ней до сцены сна.
Если она в отряде, но праздник прошёл без неё (не в лагере), флаг не ставится: глава необязательная
и очередь не держит; не сыгранная за ночь — закрывается (expire).

Два диалога:
  * ALFSV_Alfira_Ch04_Celebration — её разговор на празднике: ванильный CAMP_GoblinHuntCelebration_Bard
    узел в узел (её реплики и реплики героя — голос, текст и постановка Larian, основа — сама эта сцена)
    с нашими вставками: F1 — «первый куплет — серьёзный» после выбора темы, если в главе 3 была песня;
    тема — флаг-группа на герое; позже ночью — F3, пьяная Альфира.
    Ванильные корни с DEN_TieflingBard_State_ConvincedToQuit (N23, N19) и N39 (после N2 недостижим)
    не переносятся: у завербованной Альфиры этого флага нет (вербовка его исключает).
  * ALFSV_Alfira_Ch04_Lakrissa — F2, после их сцены флирта (AD CAMP_GoblinHuntCelebration_AD_Bard_Flirty):
    Лакрисса замечает героя, развилка R2. Сцена на троих (Лакрисса, Альфира, герой), основа —
    HAV_AlfiraTale_ReunionWithFlirty (их встреча в «Последнем свете», общая сцена bnz_standing_Px2 и свет
    EXT_NIGHT). Реплики Лакриссы — текст без голоса.

Сыгранной глава считается при выборе темы песни (любой ответ на «Any ideas?»).
"""
from dsl import ALFIRA, OTHER, PLAYER, Scene, chapter, narrate, new_flag, opt, say, voice
from scenes.ch03_first_verse import FIRST_VERSE
from scenes.recruitment import SPARK
from vanilla import LAKRISSA, F, T

# --- состояние ночи: ставит и снимает Osiris (ALFSV_Companion.txt) ---
TONIGHT = new_flag("ALFSV_Celebration_Tonight", "Global",
                   "Tiefling celebration night with Alfira in camp (set at the celebration setup, cleared at the sleep scene)")
LAKRISSA_HERE = new_flag("ALFSV_Celebration_LakrissaHere", "Global",
                         "Lakrissa is at the celebration (not defeated, as in PROC_CAMP_GoblinHuntCelebration_SetupTieflings)")
F3_READY = new_flag("ALFSV_Celebration_LateNight", "Global",
                    "Later that night: the Lakrissa scene (F2) is over or cannot happen - drunk Alfira (F3) is next")

CH = chapter(4, "Праздник", after_rest=False, optional=True, act=1, story=[TONIGHT.on], expire=True, hub=False)

SCENE = Scene(
    name="ALFSV_Alfira_Ch04_Celebration",
    dialog_id="ba151298-664c-43b8-9271-844a2153d101",      # ID ресурса, на него ссылается Osiris, не менять
    base="CAMP_GoblinHuntCelebration_Bard",
    voice_from=["CAMP_GoblinHuntCelebration_Bard"],
    chapter=CH,
    status="согласовано 2026-09-27",
)
S = SCENE

# 🔁 Запоминается — на герое (глава 5 «Утро после» и песня о герое).
TALKED = new_flag("ALFSV_Celebration_Talked", "Object", "Hero talked to Alfira at the celebration (her song talk, F1)")
# Тема праздника — второй куплет песни о герое: пять групп вариантов ванильной сцены
THEME_COURAGE = new_flag("ALFSV_Celebration_Theme_Courage", "Object", "Celebration song theme: courage, prowess, battle")
THEME_BEAUTY = new_flag("ALFSV_Celebration_Theme_Beauty", "Object", "Celebration song theme: the hero's body, beauty")
THEME_EVERYONE = new_flag("ALFSV_Celebration_Theme_Everyone", "Object", "Celebration song theme: everyone who fought, our people")
THEME_OTHER_HERO = new_flag("ALFSV_Celebration_Theme_OtherHero", "Object", "Celebration song theme: someone else (Blade of Frontiers, Mystra, Vlaakith, a god)")
THEME_NO_SONG = new_flag("ALFSV_Celebration_Theme_NoSong", "Object", "Celebration song theme: the hero refused the song")
# R2
CHOSE_HER = new_flag("ALFSV_Celebration_ChoseHer", "Object", "R2: the hero took Alfira's attention from Lakrissa (one dance)")
PUSHED = new_flag("ALFSV_Celebration_PushedToLakrissa", "Object", "R2: the hero told Alfira and Lakrissa they make a lovely pair")
DEFERRED = new_flag("ALFSV_Celebration_Deferred", "Object", "R2: the hero didn't interrupt - the choice is postponed")
# F3: что она сказала и чем кончилась ночь
SAID_EYEBROWS = new_flag("ALFSV_Celebration_Said_Eyebrows", "Object", "Drunk Alfira praised the hero's symmetrical eyebrows")
SAID_LOVELY = new_flag("ALFSV_Celebration_Said_Lovely", "Object", "Drunk Alfira: Lakrissa's lovely, everyone's lovely, you're lovely")
SAID_FRIEND = new_flag("ALFSV_Celebration_Said_GoodFriend", "Object", "Drunk Alfira: you're a good friend")
CLOAK = new_flag("ALFSV_Celebration_Cloak", "Object", "The hero covered Alfira with a cloak; it stayed on her until morning")
SHOULDER = new_flag("ALFSV_Celebration_Shoulder", "Object", "Alfira fell asleep on the hero's shoulder by the fire")
TO_LAKRISSA = new_flag("ALFSV_Celebration_GaveToLakrissa", "Object", "The hero asked Lakrissa to look after Alfira")
F3_DONE = new_flag("ALFSV_Celebration_LateNightDone", "Object", "The late-night talk with drunk Alfira (F3) is over")

# --- корни: позже ночью (F3) важнее повторных реплик игры ---

S.greeting("F3",
           narrate("Later that night. Alfira sits on a log by the dying fire.",
                   "Позже ночью. Альфира сидит на бревне у догорающего костра.", emo="happy/2"),
           say("You know what's funny? I was going to play for coppers. On street corners. Alone. And now I'm...",
               "Знаешь, что смешно? Я собиралась играть за медяки. На перекрёстках. Одна. А теперь я…",
               emo="happy/2>thinking"),
           narrate("She waves a hand at the camp, at you.", "Она машет рукой на лагерь, на тебя.", emo="happy/2"),
           say("...this.", "…вот это.", emo="happy/2", shot="alfira_close"),
           when=[TALKED(PLAYER), F3_READY.on, F3_DONE(PLAYER, False)],
           # «подтолкнул к Лакриссе» важнее искры [решение сборки]: в сценарии эти строки таблицы не пересекаются
           go=["F3_chose", "F3_pushed", "F3_spark", "F3_friend"])
S.greeting("N130", voice("h82305238g7ea4g4ad2gad35gc91de55ed2de"),    # Don't worry: I'm not secretly composing…
           when=[F.RefusedBardSong(PLAYER)], end=True)
S.greeting("N15", voice("h03bb6754g221bg43ccg962fg1f6cc4a2a02f"),     # Your song was coming along…
           when=[F.CelebrationHasMetBard(PLAYER)], end=True)
S.greeting("N2",
           voice("h6c9202f3ga40dg4b8bg9372gebda4227ec36",              # This might be the wine talking… about you.
                 set=[F.CelebrationHasMetBard(PLAYER), TALKED(PLAYER)]),
           voice("hac3d9970g976fg462bga320g960abc2255d8"),             # But I need an angle. Any ideas?
           go="THEME")

# --- F1. Тема песни: ванильные варианты (N6) в их порядке; тема — флаг на герое; глава сыграна ---

AFTER = ["F1"]      # после её ответа: «первый куплет — серьёзный», если в главе 3 была песня; иначе конец
S.block("F1", say("Oh, the *first* verse is serious. This one's for dancing.",
                  "О, *первый* куплет — серьёзный. А этот — чтобы танцевать.", emo="happy/2>happy"),
        when=[FIRST_VERSE(PLAYER)], end=True)
# «Ты видишь это тело?»: её «Лакрисса одобрила бы» — только если герой обещал Лакриссе выпить (как у игры)
S.block("BODY", voice("hc7173ae8gaf76g469fg9069g838ab4a7fa50"),       # Heh. Lakrissa would approve.
        voice("h33a5dac5g1dddg497fg8058gde100efe4fca"),               # One raunchy ballad, coming up!
        when=[F.LakrissaPromisedDrink(PLAYER)], go=AFTER)


def theme(ru, en, handle, version, group, reply, when=(), go=AFTER, extra_set=()):
    """Вариант героя из игры: его реплика (голос и текст Larian), тема, её ответ."""
    kw = {"go": go} if go else {"end": True}
    return opt(ru, en, game_line=(handle, version), when=list(when), set=[group(PLAYER), CH.done, *extra_set],
               reply=[voice(h) for h in reply], **kw)


S.menu("THEME",
       theme("Ох, вряд ли. Бард из меня так себе.", "Not really. I'm not much of a bard.",
             "h7144a0b2ga661g42c4g9cabg8b5c081b0602", 3, THEME_COURAGE, ["hf6d80797g352bg4d0cgaea6g064d037ebeca"],
             when=[~T.BARD(PLAYER)], go=None),                                        # N40 → N131, конец
       theme("Как насчет храбрости? Чем не тема для песни?", "How about courage? Classic song material.",
             "h1424a01bg9fb2g4287g8c56g288bc1c99109", 3, THEME_COURAGE, ["h85914147g6262g4672g94dcgfa1d6dcdfbd1"]),   # N7
       opt("Ты видишь это тело? Не воспеть его – просто преступление.",
           "Have you seen this body? It would be a crime not to sing about it.",
           game_line=("h6c938d9cg28bfg44ceg9fd8g2af6e641ba06", 2), when=[~T.REALLY_ASTARION(PLAYER)],
           set=[THEME_BEAUTY(PLAYER), CH.done], go=["BODY", "F1"]),                   # N9 → N31 → N35
       theme("Если честно, мне кажется, что лучше не стоит.", "Honestly? I'd rather you didn't.",
             "h035e67d1gf82fg42beg8b9bgcd83722c3000", 3, THEME_NO_SONG, ["hba247258g684eg4a41gb577g1397b3daeef0"],
             go=None, extra_set=[F.RefusedBardSong(PLAYER)]),                         # N10 → N138
       theme("Если услышу свое имя в песне – поплатишься жизнью.", "If I hear my name in a song, your life is forfeit.",
             "hf135c347gded0g4c6ag9eb8g6b82decab4eb", 2, THEME_NO_SONG, ["hf9cfc727gc9acg46abgbd66gb5320d2fbcb7"],
             go=None, extra_set=[F.RefusedBardSong(PLAYER)]),                         # N99 → N33
       theme("У меня нет сомнений, что ты опытный бард, но я не жажду увековечить свои деяния в песне.",
             "Skilled as I'm sure you are, I don't need my exploits put to song.",
             "ha689a25cg53c0g4ec6g994ag44d6dd30894c", 3, THEME_NO_SONG, ["he39eb3e8g9e67g4cd4g96deg0a1f17b04b75"],
             when=[T.REALLY_SHADOWHEART(PLAYER)], go=None),                           # N72 → N75
       theme("О-о, не всё так сразу. Давай пока начнем с моей непревзойденной красоты – и там видно будет.",
             "There's just so much. Let's start with my physical beauty and go from there.",
             "he5347f6eg900bg4b24g971cg8066b1d33fd4", 3, THEME_BEAUTY, ["h25c154c1g4b55g450dga5ceg01705c004f9e"],
             when=[T.REALLY_ASTARION(PLAYER)]),                                       # N66 → N86
       theme("Воспой мой боевой дух – и его схожесть с духом свирепой и возлюбленной королевы Влаакит.",
             "Sing of my battle spirit, and how it mirrors that of the ferocious and beloved Queen Vlaakith.",
             "hb0b633f7gf207g439fg931eg6e3c00d4bbf4", 3, THEME_OTHER_HERO,
             ["h85bae149ge2deg4226g87e4gbb20eb797691", "h0058c006g6136g40c7gb519g5a00389b00e5"],
             when=[T.REALLY_LAEZEL(PLAYER)]),                                         # N71 → N78 → N87
       theme("Просто спой о легендарном герое – Клинке Фронтира, самом крутом воине, что когда-либо ступал на Побережье Мечей.",
             "Just mention the legend that is the Blade of Frontiers, the hardiest hero to ever travel the Sword Coast.",
             "hc62e9114gf6f7g43c2g9657g35750b46b39a", 3, THEME_OTHER_HERO, ["h89b3fffbg78e8g4aa6g8b6cg4db174090a64"],
             when=[T.REALLY_WYLL(PLAYER)]),                                           # N70 → N80
       theme("Я бы лучше послушал песню о Мистре.", "I'd rather hear a song about Mystra.",
             "h962da064g29f1g4891g8fd4g17cc42b5df85", 3, THEME_OTHER_HERO,
             ["he0a03843g6baag4c21g9c8cg12ce0d9df7fe", "h894acf1eg157bg4160g9c28g1be7b32a4d82"],
             when=[T.REALLY_GALE(PLAYER)]),                                           # N68 → N82 → N90
       theme("Пусть это будет песня обо всех, кто сражался. Такие дела не делаются в одиночку.",
             "Make it a song for everyone who fought. Couldn't have done it alone.",
             "h7f8a7478gb477g4adcga7fcgcc9a5519ca3e", 1, THEME_EVERYONE, ["h578b8a41gbdcfg4025g8ee8gce0b9498a935"],
             when=[T.REALLY_KARLACH(PLAYER)]),                                        # N140 → N141
       theme("Спой о нашем народе. Мы это заслужили.", "Sing about our people. We deserve it.",
             "h2a9557ecg017eg4d66ga1edg14dd1592a488", 2, THEME_EVERYONE, ["h1b1be6bag2754g4378gb4f1g91624c7b61ae"],
             when=[T.REALLY_TIEFLING(PLAYER)]),                                       # N62 → N63
       theme("Может, это будет песня о моем происхождении от двух народов? Я им горжусь.",
             "Maybe a song about my mixed heritage? It's a point of pride for me.",
             "h7946da47ge443g4fd1g8808ga8dbaf270dca", 3, THEME_EVERYONE, ["h59f26c5ag3c03g49a9gb682g6b89ddc273c8"]),   # N97
       theme("Заткнись. Последнее, что мне нужно – это какая-то слюнявая песенка обо мне.",
             "Shut it. The last thing I want is some sappy song about me.",
             "h3e991f64ge63dg47adg828bg2a6f26e2c3b8", 2, THEME_NO_SONG, ["h35cc8ed9gb96cg49b2gaeccg88482a3679c7"],
             when=[T.REALLY_DUERGARDWARF(PLAYER)], go=None),                          # N112 → N134
       theme("Спой об эльфах с поверхности – какие они грязные жалкие твари.",
             "Sing about surface elves - and how filthy and pathetic they are.",
             "h6c2eec63g72aag4b95gaf91gbe497ac2c31b", 2, THEME_COURAGE, ["h3c2296afgd34ag45f2g8c71g9d118575a3e7"],
             when=[T.REALLY_LOLTHDROWELF(PLAYER)]),                                   # N118 → N120
       theme("Не загоняй поэзию в рамки скучных фактов. Следуй за музой.",
             "Let it be only as truthful as true poetry would permit.",
             "h71114c04g22a3g4a6cga3d0ge834a95c668a", 4, THEME_COURAGE,
             ["hf92ca759g61d9g4a88ga519gdf710120aece", "h94e56911ge1ebg4c05g888bgd939f0fa3ed7"],
             when=[T.BARD(PLAYER)]),                                                  # N29 → N143 → N32
       theme("Если мне понадобится песня, я напишу ее без посторонней помощи.", "If I want a song about me, I'll write it myself.",
             "h021927eeg7d22g4bd7g9e64gf7f642534b40", 2, THEME_NO_SONG, ["h585ed777g1a68g439cg9608gf9d065af583e"],
             when=[T.BARD(PLAYER)], go=None),                                         # N124 → N125
       theme("Спой о моей воинской доблести.", "Sing about my prowess in battle.",
             "haf5c34a9g146fg4dcegbd05g161158f2153d", 3, THEME_COURAGE,
             ["hb78a4c68g91e5g42b2ga18fgb0090ffa1f19", "h94e56911ge1ebg4c05g888bgd939f0fa3ed7"],
             when=[T.FIGHTER(PLAYER)]),                                               # N28 → N53 → N32
       theme("Как насчет гоблинских хребтов, вырванных из спины голыми руками?",
             "How about the goblin spines I'd ripped out with my bare hands?",
             "h8d5b4a66gdf13g4693gad5fg2dde526630ad", 2, THEME_COURAGE, ["h3c7aaf07ga335g485ag977dga3df8c547b0d"],
             when=[T.BARBARIAN(PLAYER)]),                                             # N136 → N137
       theme("Я не заслуживаю такого восхваления. Я служу высшей силе.", "I don't deserve such praise. I serve a higher power.",
             "h2e988489g37a1g4cd7g80a2g7292c2dbbe42", 2, THEME_OTHER_HERO, ["h2a898c12g8001g4c54g8462g7cfffacf4a7f"]),   # N64
       )

# --- F3. Пьяная Альфира: одна фраза по тому, что было раньше ---

EYEBROWS = ("You have very... *symmetrical* eyebrows. That's a compliment. I'll regret it tomorrow. I regret it now, actually.",
            "У тебя очень… *симметричные* брови. Это комплимент. Завтра пожалею. Вообще-то, уже жалею.")
S.block("F3_chose", say(*EYEBROWS, emo="happy/2>surprise>happy", shot="alfira_close", set=[SAID_EYEBROWS(PLAYER)]),
        when=[CHOSE_HER(PLAYER)], go="F3_menu")
S.block("F3_pushed",
        say("Lakrissa's lovely. Everyone's lovely. You're lovely. Why is everyone *lovely*.",
            "Лакрисса милая. Все милые. Ты {милый|милая}. Почему все такие *милые*.", emo="happy>sad>happy/2",
            set=[SAID_LOVELY(PLAYER)]),
        when=[PUSHED(PLAYER)], go="F3_menu")
S.block("F3_spark", say(*EYEBROWS, emo="happy/2>surprise>happy", shot="alfira_close", set=[SAID_EYEBROWS(PLAYER)]),
        when=[SPARK(PLAYER)], go="F3_menu")
S.block("F3_friend",
        say("You're a good friend. I haven't had a good friend since - since. Don't let me cry, it's a party.",
            "Ты хороший друг. У меня не было хороших друзей с тех… с тех пор. Не дай мне расплакаться, это же праздник.",
            emo="happy>sad>happy", set=[SAID_FRIEND(PLAYER)]),
        go="F3_menu")

S.menu("F3_menu",
       opt("Пора спать, Альфира.", "Time to sleep, Alfira.", approve=+2, set=[CLOAK(PLAYER), F3_DONE(PLAYER)],
           reply=[narrate("You cover her with your cloak. She falls asleep before you finish. The cloak stays on her until morning.",
                          "Ты укрываешь её плащом. Она засыпает, не дослушав. Плащ до утра остаётся на ней.",
                          emo="sleeping")],
           end=True),
       opt("Посиди со мной ещё.", "Sit with me a while longer.", approve=+1, set=[SHOULDER(PLAYER), F3_DONE(PLAYER)],
           reply=[narrate("You sit in silence until the fire burns out. She falls asleep on your shoulder. Nothing more.",
                          "Вы сидите молча, пока не прогорит костёр. Она засыпает у тебя на плече. Больше ничего.",
                          emo="happy>sleeping")],
           end=True),
       opt("Лакрисса, присмотри за ней.", "Lakrissa, look after her.", when=[LAKRISSA_HERE.on],
           set=[TO_LAKRISSA(PLAYER), F3_DONE(PLAYER)],
           reply=[narrate("Lakrissa leads her away to the tents.", "Лакрисса уводит её к палаткам.", emo="happy/2")],
           end=True),
       opt("Иди проспись.", "Go sleep it off.", approve=-1, set=[F3_DONE(PLAYER)],
           reply=[say("...Fine. *Fine.* Party pooper.", "…Ладно. *Ладно.* Зануда.", emo="angry>sad", note="(обиженно)")],
           end=True),
       )

# --- F2. Лакрисса замечает героя → R2 (сцена на троих; запускает Osiris) ---

R2 = Scene(
    name="ALFSV_Alfira_Ch04_Lakrissa",
    dialog_id="e36a27f8-a3b1-4e6f-9c9b-464b02534b7a",      # ID ресурса, на него ссылается Osiris, не менять
    base="HAV_AlfiraTale_ReunionWithFlirty",               # спикеры: 0 Лакрисса, 1 Альфира, 2 герой
    other=LAKRISSA, other_name="Лакрисса",
    status="согласовано 2026-09-27",
)
R2.greeting("R2",
            say("Oh, look who it is. Come to steal my bard, hero?", "О, гляньте, кто пришёл. {Решил|Решила} украсть моего барда, герой?",
                speaker=OTHER, emo="happy/2"),
            narrate("Alfira blushes to the tips of her horns.", "Альфира краснеет до кончиков рогов.",
                    emo="surprise>happy/2", shot="alfira_close"),
            choices=[
                # ✨ забрать её внимание
                opt("Украсть? Она сама со мной ушла.", "Steal her? She came with me of her own free will.",
                    when=[SPARK(PLAYER)], approve=+2, set=[CHOSE_HER(PLAYER)],
                    reply=[say("Fair. Fair! I know when I'm outplayed. Go on, Alfie - dance with the hero.",
                               "Справедливо! Справедливо. Проигрывать тоже надо уметь. Иди, Альфи, — потанцуй с героем.",
                               speaker=OTHER, emo="happy/2>happy", note="(смеётся, поднимает руки)"),
                           say("I - we -", "Я… мы…", emo="surprise"),
                           narrate("She grabs your hand.", "Она хватает тебя за руку.", emo="happy/2"),
                           say("One dance. I'm *very* drunk. It doesn't count.", "Один танец. Я *очень* пьяна. Не считается.",
                               emo="happy/2", shot="alfira_close")],
                    end=True),
                # подтолкнуть к Лакриссе
                opt("Вы с Лакриссой — отличная пара.", "You two make a lovely pair.", set=[PUSHED(PLAYER)],
                    reply=[say("Hear that, Alfie? Even the hero agrees.", "Слышала, Альфи? Даже {герой согласен|героиня согласна}.",
                               speaker=OTHER, emo="happy/2", note="(подмигивает)"),
                           say("...Right. Yes. Lovely.", "…Да. Конечно. Отличная.", emo="happy>sad>happy",
                               shot="alfira_close", note="(улыбается, но улыбка на секунду гаснет)")],
                    end=True),
                # промолчать: выбор отложен
                opt("Не буду мешать.", "I won't interrupt.", approve=+1, set=[DEFERRED(PLAYER)],
                    reply=[say("You're not interrupting! You're - sit. Sit! There's wine.",
                               "Ты не мешаешь! Ты… садись. Садись! Тут вино.", emo="surprise>happy/2")],
                    end=True),
            ])

EXTRA_SCENES = [R2]
OSIRIS_FLAGS = [TONIGHT]

S.blocks["F3"].seated = "fire"      # «Альфира сидит на бревне у догорающего костра» — F3 и ответы после неё сидя (staging.SEATED)
