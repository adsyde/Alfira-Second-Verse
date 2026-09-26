"""Глава 2 «Лютня» — design/dialogs/03_act1_ch2_lute.md, согласовано 2026-09-26.

Открывается после долгого отдыха, когда сыграна глава 1 (after_rest=True). Вход — в любом разговоре
в отряде или в лагере («Нам нужно поговорить»), днём и вечером: условия ночи у главы нет. При
одобрении ниже 0 разговор в отряде отвечает холодной репликой, глава ждёт.
Сыгранной глава считается после первого ответа героя в L2 (CH.done).

Где лютня Лихейлы (проверено по данным игры, см. vanilla.F.PlayWithInstrument): если герой играл
дуэт на её лютне (DEN_TieflingBard_Event_PlayWithInstrument на герое), лютня осталась у него
(«Оставь лютню себе») — вариант «лютня у героя». Иначе лютня у Альфиры.

voice("h…") — её озвученная реплика игры, say(...) — новая, только текст, narrate(...) — ремарка
рассказчика (действие без слов). Английские реплики героя — из сценария.
"""
from dsl import ALFIRA, PLAYER, Scene, chapter, check, narrate, new_flag, opt, outcome, say, voice
from scenes.recruitment import SPARK
from vanilla import DC, F, T

CH = chapter(2, "Лютня", after_rest=True)

SCENE = Scene(
    name="ALFSV_Alfira_Ch02_Lute",
    dialog_id="7f3c1e52-9a6b-4c1d-8e2f-5b0a4d6c9e13",      # ID ресурса вложенного диалога главы, не менять
    base="DEN_Bard_InParty",
    # DEN_TieflingBard_Bard — песня в Роще; SCE_Alfira — предложение сыграть вместе (акт 2);
    # SCE_AD_Alfira — «I can't remember the last time I played like that» (это AD: фаза строится
    # по длине её голоса, без постановки сцены — staging.py, voiced_phase)
    voice_from=["DEN_TieflingBard_Bard", "SCE_Alfira", "SCE_AD_Alfira"],
    chapter=CH,
    status="согласовано 2026-09-26",
)
S = SCENE

LUTE_HERO = F.PlayWithInstrument(PLAYER)           # лютня Лихейлы у героя

# 🔁 Запоминается — на герое, как и воспоминания главы 1.
NOTCH_CITY = new_flag("ALFSV_Notch_City", "Object", "Hero promised to cut the thirteenth notch together in Baldur's Gate")
NOTCH_GROVE = new_flag("ALFSV_Notch_Grove", "Object", "The thirteenth notch was cut for the Emerald Grove")
PLAYED_TOGETHER = new_flag("ALFSV_PlayedTogether", "Object", "Hero played the lute together with Alfira (chapter 2)")
LUTE_LESSON = new_flag("ALFSV_LuteLesson", "Object", "Alfira gave the hero a lute lesson (chapter 2)")
DURGE_RESISTED = new_flag("ALFSV_Durge_Resisted", "Object", "Dark Urge resisted the urge while Alfira played (chapter 2)")
DURGE_URGE_NEAR = new_flag("ALFSV_Durge_UrgeNear", "Object", "Dark Urge felt the urge near Alfira and said nothing (chapter 2)")
# ✨💞 шаги романа (их вспомнят «Утро после» и первый поцелуй)
ROMANCE_LESSON = new_flag("ALFSV_Romance_LuteHands", "Object", "Romance step: Alfira placed the hero's fingers on the lute")
ROMANCE_WATCHED = new_flag("ALFSV_Romance_MissedNote", "Object", "Romance step: the hero watched Alfira and she missed a note")

# --- L1. Приветствие ---

S.greeting("L1_hero",
           say("Can I ask you something odd? Do you still have her lute? I - I'd just like to see it.",
               "Можно странную просьбу? Лютня Лихейлы всё ещё у тебя? Я… просто хочу на неё посмотреть.",
               emo="thinking>sad"),
           when=[LUTE_HERO], go="L2")
S.greeting("L1",
           narrate("She sits hugging the lute to her chest, running a finger along its neck.",
                   "Она сидит, прижав лютню к груди, и водит пальцем по грифу.", emo="thinking"),
           say("Oh - hi. Don't mind me. I'm just... counting.",
               "Ой, привет. Не обращай внимания. Я просто… считаю.", emo="surprise>happy"),
           go="L2")

# --- L2. Первые слова героя (любой ответ — глава сыграна) ---

S.menu("L2",
       # тёплый
       opt("Что для тебя значит эта лютня?", "What does that lute mean to you?", approve=+2, set=[CH.done],
           reply=[voice("hb4b9d4a4g95b7g45d7g97dbge0209c7a5d4c"),      # It was my teacher's. And it's - it's all I have left.
                  voice("h0fa7196dgbaf6g4c65g86d0g5a46c630f20e")],     # It was awful. I couldn't look at a lute without hearing her…
           go="L3"),
       # любопытный — отвечает на её «я просто… считаю», поэтому только при лютне у неё
       opt("Что ты там считаешь?", "What are you counting?", when=[~LUTE_HERO], approve=+1, set=[CH.done], go="L3"),
       # шутливый
       opt("Надеюсь, воину ты её не давала?", "I hope you never let a fighter carry it.", approve=+1, set=[CH.done],
           reply=[say("Never. Rule three. I'd sooner hand it to an owlbear.",
                      "Никогда. Правило третье. Я бы скорее отдала её медвесычу.", emo="happy/2")],
           go="L3"),
       # 🏷️ лютня у героя
       opt("Возьми её обратно. Она твоя.", "Take it back. It's yours.", when=[LUTE_HERO], approve=+2, set=[CH.done],
           reply=[voice("hc8b99da7g1fffg4039g9f57ge00f1eeb031f"),      # Keep the lute. Please. You've earned it.
                  say("She'd want it played, not hung on a wall. And you play it better than I would right now. "
                      "Don't tell anyone I said that.",
                      "Она бы хотела, чтобы на ней играли, а не вешали на стену. И ты сейчас играешь на ней лучше меня. "
                      "Никому не говори, что я это сказала.", emo="sad>happy>happy/2")],
           go="L3"),
       # циничный
       opt("Это просто дерево и струны.", "It's just wood and strings.", approve=-2, set=[CH.done],
           reply=[say("So's a bow. Go tell a ranger that.", "Лук — тоже. Пойди скажи это рейнджеру.",
                      emo="angry", note="(резко)")],
           go="L3"),
       )

# --- L3. Зарубки [вымысел] ---

S.block("L3",
        narrate("She turns the neck towards the fire. A row of small notches runs along it.",
                "Она поворачивает гриф к огню. На нём ряд мелких зарубок.", emo="thinking", shot="alfira_close"),
        say("Lihala cut one for every town we played. Twelve. Beregost, Nashkel, a pig farm she swore was a town...",
            "Лихейла делала по зарубке за каждый город, где мы выступали. Двенадцать. Берегост, Нашкель, свиноферма, "
            "которую она клялась считать городом…", emo="happy>thinking>happy/2"),
        say("The thirteenth was going to be Baldur's Gate. She had the knife out on the road. She was going to cut it early, for luck.",
            "Тринадцатая должна была быть за Врата Балдура. Она уже достала нож, там, на дороге. Хотела вырезать заранее, на удачу.",
            emo="thinking>sad", shot="alfira_close"),
        choices=[
            opt("Вырежи тринадцатую, когда дойдём до города. Вместе.", "Cut the thirteenth when we reach the city. Together.",
                approve=+2, set=[NOTCH_CITY(PLAYER)],
                reply=[say("...Deal. And you're holding the knife steady, because my hands will be shaking.",
                           "…По рукам. И нож держишь ты, потому что у меня будут трястись руки.",
                           emo="thinking>happy", note="(не сразу)")],
                go=["L4_bard", "L4"]),
            opt("Вырежи её сейчас. Роща тоже считается.", "Cut it now. The Grove counts.",
                approve=+1, set=[NOTCH_GROVE(PLAYER)],
                reply=[say("Here? The Grove... yes. Yes, it does, doesn't it. It's where I finished her song.",
                           "Здесь? Роща… да. Ведь считается, правда? Здесь я закончила её песню.",
                           emo="surprise>thinking>happy")],
                go=["L4_bard", "L4"]),
            opt("Может, лучше оставить как есть.", "Maybe it's better left as it is.",
                reply=[say("Maybe. Twelve is a good number. Unfinished is a good song, sometimes.",
                           "Может быть. Двенадцать — хорошее число. Иногда и недописанное — хорошая песня.",
                           emo="thinking>sad/1")],
                go=["L4_bard", "L4"]),
        ])

# --- L4. «Сыграем вместе?» ---

# ✨ пока она играет (после «Лучше я послушаю тебя»)
WATCH = opt("*Смотреть на неё, а не на струны.*", "*Watch her, not the strings.*", when=[SPARK(PLAYER)],
            approve=+2, set=[ROMANCE_WATCHED(PLAYER)],
            reply=[narrate("She stumbles half a note.", "Она сбивается на полуноте.", emo="surprise"),
                   say("...You made me miss a note. Nobody's made me miss a note since I was twelve.",
                       "…Из-за тебя я сбилась. Со мной такого не случалось с двенадцати лет.",
                       emo="surprise>happy/2", shot="alfira_close")],
            go="L5")
# [решение сборки] нейтральный выход из меню «пока она играет» — в сценарии его нет, а меню из одних
# условных вариантов оставило бы героя без ответа
LISTEN_ON = opt("*Слушать.*", "*Listen.*",
                reply=[narrate("When the song ends, she smiles to herself.",
                               "Доиграв, она улыбается сама себе.", emo="happy")],
                go="L5")

L4_MENU = [
    check("*Давай.*", "*Let's.*", skill="Performance", ability="Charisma", dc=DC.Act1_Medium,
          success=outcome(approve=+3, set=[PLAYED_TOGETHER(PLAYER)], reply=[
              voice("h6b39e0a7g0444g4b65gbb20g221def3ac95e"),        # I can't remember the last time I played like that.
              voice("he6103663g48c4g41cbgaf48gaea31cf66375")],       # That was a blast - thank you! I hope we get to play again…
              go="L5"),
          failure=outcome(approve=+1, set=[PLAYED_TOGETHER(PLAYER)], reply=[
              say("That was *terrible*. Truly awful. Again!", "Это было *ужасно*. Просто кошмар. Ещё раз!",
                  emo="happy/2>happy", note="(хохочет)")],
              go="L5")),
    opt("Я не умею.", "I don't know how.", approve=+2, set=[LUTE_LESSON(PLAYER)],
        reply=[voice("h51a61f72g1630g435dga0c1g4ba78bd90059"),       # Hm. It can't hurt. I have her... I have an extra lute…
               say("Fingers here. No - *here*. Lihala did this to me for a *year*.",
                   "Пальцы сюда. Нет — *сюда*. Лихейла мучила меня так *целый год*.", emo="thinking>happy/2")],
        choices=[
            opt("Поправь мне пальцы сама.", "Show me. Put my fingers where they go.", when=[SPARK(PLAYER)],
                approve=+2, set=[ROMANCE_LESSON(PLAYER)],
                reply=[narrate("She takes your hand - and holds it a moment longer than she needs to.",
                               "Она берёт тебя за руку — и держит на мгновение дольше, чем нужно.",
                               emo="thinking>surprise", shot="alfira_close"),
                       say("...There. That's a chord. Don't - don't look at me like that, you'll lose it.",
                           "…Вот. Это аккорд. Не… не смотри на меня так, собьёшься.", emo="happy/2", shot="alfira_close")],
                go="L5"),
            # [решение сборки] нейтральный вариант (в сценарии после урока — только ✨)
            opt("*Взять аккорд.*", "*Play the chord.*", go="L5"),
        ]),
    opt("Лучше я послушаю тебя.", "I'd rather listen to you.", approve=+1, go=["L4_listen_urge", "L4_listen"]),
]

S.block("L4_bard", voice("hceb586adg61d1g4cd3ga3f0g56120fd6508f"),        # Ah! A fellow bard…
        when=[T.BARD(PLAYER)], choices=L4_MENU)
S.block("L4", voice("h6902a9deg38f3g4b99g924bgacb218866398"),             # Oh, oh! I have an idea - why don't we play together?
        choices=L4_MENU)

PLAYS = ("She plays something simple, something bright.", "Она играет что-то простое, светлое.")
# 🏷️ Темный Соблазн: пока она играет — шёпот Побуждения. Убить её здесь нельзя.
S.block("L4_listen_urge", narrate(*PLAYS, emo="happy"),
        narrate("[The Urge] The string at her throat. One move - and the song is over.",
                "[Побуждение] Струна у её горла. Одно движение — и песня кончится.", emo="happy"),
        when=[T.REALLY_DARK_URGE(PLAYER)],
        choices=[
            opt("*Сопротивляться. Слушать музыку.*", "*Resist. Listen to the music.*", set=[DURGE_RESISTED(PLAYER)],
                reply=[say("You all right? You look like you've seen a ghost.",
                           "Ты в порядке? Ты будто призрака {увидел|увидела}.", emo="surprise>thinking")],
                choices=[WATCH, LISTEN_ON]),
            opt("*Сжать кулак и промолчать.*", "*Clench your fist. Say nothing.*", set=[DURGE_URGE_NEAR(PLAYER)],
                reply=[narrate("She notices nothing, and plays on.", "Она ничего не замечает и играет дальше.", emo="happy")],
                choices=[WATCH, LISTEN_ON]),
        ])
S.block("L4_listen", narrate(*PLAYS, emo="happy"), choices=[WATCH, LISTEN_ON])

# --- L5. Конец ---

S.block("L5", voice("hce5aebf2g351fg47a1gaff7g9f8e7b9a83d5"),             # Thanks. Lihala made me love music…
        voice("hd478ade9gb9e8g45c1g9cfbg46fac9eee961"),                    # Until now. I'd forgotten what it was like…
        end=True)
