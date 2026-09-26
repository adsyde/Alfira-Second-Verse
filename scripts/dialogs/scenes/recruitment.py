"""Сцена A «Ученица без наставницы» — design/dialogs/01_recruitment.md, согласовано (v3).

Альфира закончила «Плач рассвета» с помощью героя; при следующем разговоре с ней
(QRY_ALFSV_CanOfferRecruitment в ALFSV_Companion.txt) открывается этот диалог.
voice("h…") — её озвученная реплика из игры (голос, текст и перевод Larian); say(...) — новая,
только текст. Английские фразы героя — перевод со сценария, на вычитку.
"""
from dsl import ALFIRA, PLAYER, Join, Scene, check, new_flag, opt, outcome, say, voice
from vanilla import DC, F, NESTED, T

SCENE = Scene(
    name="ALFSV_Alfira_Recruitment",
    dialog_id="009896a5-580c-4135-98db-99234865b61d",      # ID из этапа 2, на него ссылается Osiris
    base="DEN_Bard_InParty",
    voice_from=[
        "CAMP_DarkUrge_MurderOfAlfira_CFM_AlfiraArrives",  # её вербовка в ветке Темного Соблазна
        "DEN_TieflingBard_Bard", "HAV_AlfiraTale_Bard", "DEN_AttackOnDen_Bard",
    ],
    nested=[NESTED.SwapRecruitment],
    status="согласовано v3",
)
S = SCENE

# Новые флаги мода. «Dialog» — хранится на Альфире, как DEN_TieflingBard_HasMet у игры.
POSTPONED = new_flag("ALFSV_Recruitment_Postponed", "Dialog", "Hero answered 'not now' to Alfira's request to join")
REFUSED = new_flag("ALFSV_Recruitment_Refused", "Dialog", "Hero refused Alfira's request to join")
# На герое (Object, спикер 1): у каждого героя своя искра и свой мотив для песни.
SPARK = new_flag("ALFSV_Romance_Spark", "Object", "Romance spark with Alfira (fork R1)")
MOTIVE_DUTY = new_flag("ALFSV_HeroMotive_Duty", "Object", "Hero's motive for the song: someone has to")
MOTIVE_MODESTY = new_flag("ALFSV_HeroMotive_Modesty", "Object", "Hero's motive for the song: wrong place, right time")
MOTIVE_HONESTY = new_flag("ALFSV_HeroMotive_Honesty", "Object", "Hero's motive for the song: the tadpole, honesty")
MOTIVE_PROFIT = new_flag("ALFSV_HeroMotive_Profit", "Object", "Hero's motive for the song: who said it's free")

JOIN = Join(
    nested=NESTED.SwapRecruitment,
    to_camp_line=say("I'll find your camp and wait for you there.",
                     "Я найду твой лагерь и подожду тебя там.", emo="happy", note="черновик"),
    to_camp_flag=F.SwapToCamp,
)

# --- повторный разговор после «Не сейчас» / «Нет» (приоритет выше приветствий A1) ---

S.greeting("reask_refused",
           say("Changed your mind? I won't say I told you so. *Out loud.*",
               "{Передумал|Передумала}? Не скажу «я же говорила». Вслух.", emo="happy/1",
               note="сценарий: A4 п. 13, при следующем разговоре"),
           when=[REFUSED(ALFIRA)], go="A4")
S.greeting("reask_later",
           voice("h4eaf39c1g6319g42aaga94bgdc97635a2fbe", note="«I want to join you…» — [решение автора] повтор просьбы"),
           when=[POSTPONED(ALFIRA)], go="A4")

# --- A1. Приветствие: как была закончена песня ---

S.greeting("A1_cold",
           say("Oh. It's you. I'll admit - you did help me finish it. I haven't decided yet what to make of you.",
               "А. Это ты. Признаю — закончить песню ты мне {помог|помогла}. Но что о тебе думать, я пока не решила.",
               emo="neutral>thinking", note="холоднее; лютню украли и вернули"),
           when=[F.ReturnedInstrument.on], go="A2")
S.greeting("A1_duet",
           say("There they are - my accompanist! I've been humming that bridge all morning. Lihala would've said I'm *insufferable*.",
               "А вот и мой аккомпаниатор! Всё утро напеваю тот переход. Лихейла сказала бы, что я *невыносима*.",
               emo="happy>happy/2"),
           when=[F.GiveProficiency(PLAYER)], go="A2")
S.greeting("A1_bard",
           say("You. You *sang* that line like you'd known her. I still can't get over it.",
               "Ты. Ты *{спел|спела}* ту строку так, будто {знал|знала} её. До сих пор в себя прийти не могу.",
               emo="surprise>happy", note="[решение автора] определяем по тегу BARD героя"),
           when=[T.BARD(PLAYER)], go="A2")
S.greeting("A1_mentor",
           say("I keep thinking about what you asked me. *What would I say to her.* Turns out I had a whole song's worth.",
               "Всё думаю о том, что ты {спросил|спросила}. «Что бы я ей сказала». Оказалось — на целую песню.",
               emo="thinking>happy"),
           go="A2")

# --- A2. Первые слова героя ---

S.menu("A2",
       opt("Ты чудесно пела. Правда.", "You sang beautifully. Truly.", approve=+1, set=[SPARK(PLAYER)],
           reply=[say("Stop it. No - actually, don't stop, I could get used to this.",
                      "Перестань. Нет — вообще-то не переставай, я могу к этому привыкнуть.",
                      emo="happy/2>happy", shot="alfira_close", note="(краснеет)")],
           go="A3"),
       opt("Как ты теперь?", "How are you holding up?", approve=+1,
           reply=[say("Lighter. Like I put down a pack I'd been carrying since the road.",
                      "Легче. Будто сняла мешок, который тащила с самой той дороги.", emo="thinking>happy")],
           go="A3"),
       opt("Зачем вообще нужны погребальные песни?", "What's the point of a eulogy, anyway?", approve=+1,
           reply=[voice("hb17ca2bbgacb8g4e8dg9bfage4cdd0804851")],
           go="A3"),
       opt("Белки больше не жалуются на твоё пение?", "Have the squirrels stopped complaining about your singing?",
           reply=[say("The squirrels have *terrible* taste. Everyone knows that. ...They did go quiet at the end, though. I'm choosing to count that.",
                      "У белок *ужасный* вкус, это все знают. …Хотя под конец они притихли. Решила считать это успехом.",
                      emo="happy>thinking>happy", note="(фыркает)")],
           go="A3"),
       opt("Мне пора.", "I should go.",
           reply=[say("Right. Of course, heroes, busy - *wait.* Wait, just - one thing.",
                      "Да. Конечно, у героев дела… *Стой.* Постой, всего одно.", emo="sad>surprise")],
           go="A3"),
       )

# --- A3. Просьба (её озвученные реплики) ---

S.block("A3",
        voice("h9bf81d3age040g4102g808dg8e9439a931a6"),   # You've, well, inspired me…
        voice("h4eaf39c1g6319g42aaga94bgdc97635a2fbe"),   # I want to join you - to fight by your side…
        go="A4")

# --- A4. Выбор героя ---

S.menu("A4",
       # Согласиться
       opt("Пойдем со мной.", "Come with me.", game_line=("h5a66bcc9g765dg409cga6c7g4b710426b6ac", 1), approve=+2,
           reply=[voice("h4d653a62g29e7g4ce3g813fg184db5a4e691")], go="A5"),
       opt("Бард барду не откажет.", "A bard never turns down another bard.", when=[T.BARD(PLAYER)], approve=+3,
           reply=[say("A *duet*. On the road. Oh, Lihala would have *loved* this.",
                      "*Дуэт*. В пути. Ох, Лихейла была бы *в восторге*.", emo="happy/2", shot="alfira_close",
                      note="(сияет)")],
           go="A5"),
       opt("Нам, тифлингам, стоит держаться вместе.", "We tieflings should stick together.",
           when=[T.TIEFLING(PLAYER)], approve=+2,
           reply=[say("Two tieflings walk into a goblin camp... no, I'm not finishing that joke. But yes. Yes, we should.",
                      "Два тифлинга заходят в лагерь гоблинов… нет, эту шутку я не закончу. Но да. Да, стоит.",
                      emo="happy>thinking>happy")],
           go="A5"),
       opt("Скажи «пожалуйста».", "Say please.", approve=+1,
           reply=[voice("he9161544g3342g47cfga453g85fb867293a4")],
           choices=[opt("Ладно, ладно — пойдём.", "All right, all right - come along.",
                        reply=[voice("hb6193a59g18f8g48a5gab3eg6e7b3074230c"),
                               voice("h2e21e261g656fg4dd7g838bg2d12aae867d0")],
                        go="A5b")]),
       # Узнать о ней
       opt("Почему именно со мной?", "Why me, of all people?", once=True, approve=+2, set=[SPARK(PLAYER)],
           reply=[voice("h1ab50334g4c41g4736g83c9gb5a739bd60e9"), voice("h2b0f4b62g616eg4617gbaa2gc560c395164c")],
           go="A4"),
       opt("Расскажи о Лихейле.", "Tell me about Lihala.", once=True, approve=+1,
           reply=[voice("h25df4bd2gecbag4c37gb47eg3ae4992011fe"), voice("h870f133ageb8dg406fg8d2cgd615cc64878c"),
                  say("She'd have liked you. She'd have yelled at you too, mind - she yelled at everyone she liked.",
                      "Ты бы ей {понравился|понравилась}. И на тебя бы она тоже наорала — она орала на всех, кто ей нравился.",
                      emo="happy>sad/1>happy")],
           go="A4"),
       opt("Что ты умеешь в бою?", "What can you do in a fight?", once=True,
           reply=[say("I can insult a goblin so badly it actually *hurts* - that's a real spell, don't laugh. And I know a few words that close wounds.",
                      "Могу так оскорбить гоблина, что ему станет *по-настоящему больно* — это настоящее заклинание, не смейся. И знаю пару слов, от которых затягиваются раны.",
                      emo="happy>thinking"),
                  voice("hffc113bcg4ca4g4d96g9493g1f326f83da6b")],
           go="A4"),
       # Сомнение
       opt("Там опасно. Ты уверена?", "It's dangerous out there. Are you sure?", once=True, approve=+1,
           reply=[voice("hb3e9de10gbf12g4055gb0ceg52b715403fb7"), voice("h7215e9acgd418g490fg8f4ag1f008ccb731c")],
           go="A4"),
       check("*Присмотреться к ней внимательнее.*", "*Look at her more closely.*",
             skill="Insight", ability="Wisdom", dc=DC.Act1_Medium,
             success=outcome(approve=+2, reply=[
                 say("...Is it that obvious? I'm terrified. I've been terrified since the road. I just - I'm tired of being terrified *sitting still*.",
                     "…Так заметно? Мне страшно. Мне страшно с той самой дороги. Просто… надоело бояться, *сидя на месте*.",
                     emo="fear>sad", shot="alfira_close", note="улыбка держится, пальцы на грифе побелели"),
                 voice("h557bfb24gd83bg45f5g84b7g132bee971243")], go="A4"),
             failure=outcome(reply=[
                 say("What? I'm fine. Perfectly fine. Why are you looking at me like that?",
                     "Что? Я в порядке. В полном порядке. Чего ты так на меня смотришь?",
                     emo="happy>fear/1>happy", note="(слишком широкая улыбка)")], go="A4")),
       opt("Ты не боец.", "You're no fighter.", once=True,
           reply=[voice("h371faf10g12d2g4af8ga9f3gcff782b3f7ff")], go="A4"),
       opt("Бард в отряде — лишний рот.", "A bard is just another mouth to feed.", once=True, approve=-1,
           reply=[say("I eat very little. Mostly my own words, lately.",
                      "Я мало ем. В последнее время — в основном собственные слова.", emo="thinking>sad"),
                  voice("h55e6f5bdg5968g4237g9065gb23afbfdc214")],
           go="A4"),
       # Отказаться
       opt("Не сейчас.", "Not now.", set=[POSTPONED(ALFIRA), REFUSED(ALFIRA, False)],
           reply=[say("Oh - no, of course. The offer stands. I'll be here. Composing. Probably badly.",
                      "А… нет, конечно. Предложение в силе. Я буду здесь. Сочинять. Скорее всего, скверно.",
                      emo="surprise>happy>thinking")],
           end=True),
       opt("Нет.", "No.", approve=-1, set=[REFUSED(ALFIRA), POSTPONED(ALFIRA, False)],
           reply=[say("Right. No - that's fair. That's... fair. Thank you anyway. For the song.",
                      "Ясно. Нет, это справедливо. Это… справедливо. Всё равно спасибо. За песню.",
                      emo="sad>sad/1", note="(пауза)")],
           end=True),
       )

# --- A5. Вступление и её вопрос ---

S.block("A5", voice("h9db9f172gcc9ag4b30gb501g61ce63265e38"), go="A5b")          # Yes! Thank you…
S.block("A5b",
        voice("h4b161bafg8267g40e8gb331g0bc11953e5d2"),                              # I won't let you down…
        say("Can I ask you something? For the song, obviously. Why do *you* do it? All of this - helping people you don't even know.",
            "Можно спросить? Для песни, разумеется. Зачем *ты* это делаешь? Всё это — помогаешь людям, которых даже не знаешь.",
            emo="thinking>happy"),
        choices=[
            opt("Потому что кто-то должен.", "Because someone has to.", approve=+1, set=[MOTIVE_DUTY(PLAYER)],
                reply=[say("Hah. That's a verse right there. Simple. Stubborn. I like it.",
                           "Ха. Вот тебе и куплет. Просто. Упрямо. Мне нравится.", emo="happy")],
                go="A5end"),
            opt("Просто оказываюсь не в том месте в нужное время.", "I just keep ending up in the wrong place at the right time.",
                set=[MOTIVE_MODESTY(PLAYER)],
                reply=[say("Oh, the ballads *hate* modest heroes. I'll fix you in the chorus.",
                           "Ох, баллады *терпеть не могут* скромных героев. Поправлю тебя в припеве.",
                           emo="happy/2>happy", note="(смеётся)")],
                go="A5end"),
            opt("У меня в голове личинка. Хочу, чтобы кто-то выжил, если я — нет.",
                "There's a tadpole in my head. If I don't make it, I want someone to.",
                approve=+2, set=[MOTIVE_HONESTY(PLAYER), SPARK(PLAYER)],
                reply=[say("...Then I'll make sure they remember you. Whatever happens.",
                           "…Тогда я сделаю так, чтобы тебя помнили. Что бы ни случилось.",
                           emo="sad>thinking", shot="alfira_close", note="(тихо)")],
                go="A5end"),
            opt("Кто сказал, что бесплатно?", "Who said I do it for free?", set=[MOTIVE_PROFIT(PLAYER)],
                reply=[say("A soft heart behind a price tag. I can work with that. It rhymes with *everything.*",
                           "Мягкое сердце за ценником. С этим можно работать. Рифмуется со *всем*.",
                           emo="thinking>happy")],
                go="A5end"),
        ])
S.block("A5end",
        voice("h3c696a13g3484g4c06g8eb5g32c291cef204"),                              # write a song about you
        say("Mattis is going to be *furious* I didn't say goodbye properly. I'll write him a song. He'll hate it. He'll hum it for a week.",
            "Маттис будет *в ярости*, что я толком не попрощалась. Напишу ему песню. Он её возненавидит. И будет мурлыкать неделю.",
            emo="happy>thinking>happy"),
        join=JOIN)
