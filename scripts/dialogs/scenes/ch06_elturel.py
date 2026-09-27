"""Глава 6 «Элтуриэль» — design/dialogs/07_act1_ch6_elturel.md, согласовано 2026-09-27.

Необязательная, акт 1, после долгого отдыха, одобрение 10+ (и на входе, и при открытии — иначе ждала бы,
держа очередь). Условие — первая встреча с адским: Карлах (ORI_Karlach_HasMet) или Рафаил
(GLO_TheMonitor_HasMet_TheMonitor). E1 — вариант Рафаила, если были обе встречи. Сыграна — с ответа в E2.

«Мотив матери» и «её злость» — флаги диалога (на герое) для E3; обещание про дьяволов — флаг на герое
(акт 3: договор с Рафаилом бьёт сильнее).
"""
from dsl import ALFIRA, PLAYER, Scene, chapter, check, narrate, new_flag, opt, outcome, say, voice
from scenes.ch05_morning_after import OPEN
from vanilla import DC, F, T

CH = chapter(6, "Элтуриэль", after_rest=True, optional=True, act=1, approval=10,
             story_any=[F.KarlachHasMet.on, F.RaphaelHasMet.on])

SCENE = Scene(
    name="ALFSV_Alfira_Ch06_Elturel",
    dialog_id="8b2e5d71-4c3a-4f9e-a6d0-7e1c9b3f5a28",      # ID ресурса вложенного диалога главы, не менять
    base="DEN_Bard_InParty",
    # CAMP_Bard_AD_Volo — её ответ Воло про пламя Аверно (AD: фаза по длине голоса)
    voice_from=["CAMP_Bard_AD_Volo"],
    chapter=CH,
    status="согласовано 2026-09-27",
)
S = SCENE

MOTHER_TUNE = new_flag("ALFSV_Elturel_MotherTune", "Dialog", "Alfira told the hero about her mother's tune (chapter 6, for E3)")
ANGER = new_flag("ALFSV_Elturel_Anger", "Dialog", "The hero saw Alfira's anger about Elturel (chapter 6, for E3)")
# 🔁 на герое
MOTHER_SONG = new_flag("ALFSV_Elturel_MotherSong", "Object", "'Write about her, the candles' - the song about her mother (acts 2-3)")
HUMMED = new_flag("ALFSV_Elturel_HummedTune", "Object", "Hero hummed her mother's tune (Performance success)")
LIHALA_CITY = new_flag("ALFSV_Elturel_LihalaCity", "Object", "'Some songs don't need writing' - Lihala's own city (personal quest, stage 7)")
ANGRY_SONG = new_flag("ALFSV_Elturel_AngrySong", "Object", "Hero told Alfira to sing an angry song, loudly (chapter 6; banter B12 with Karlach)")
DEVIL_PROMISE = new_flag("ALFSV_DevilPromise", "Object", "Hero promised Alfira not to take a devil's deal (act 3 reaction)")

# --- E1. Приветствие: Рафаил (если были обе встречи), иначе Карлах ---

GROVE = say("Everyone in the Grove has an Elturel story. Mine's short. It's just - the ending's bad.",
            "У каждого в Роще есть своя история про Элтуриэль. Моя короткая. Просто… конец у неё плохой.",
            emo="thinking>sad")
S.greeting("E1_raphael",
           say("That man at the village. The one in red. He smelled of brimstone and cinnamon. ...I know that smell.",
               "Тот человек у деревни. В красном. От него пахло серой и корицей. …Я знаю этот запах.",
               emo="thinking>fear"),
           GROVE, when=[F.RaphaelHasMet.on], go="E2")
S.greeting("E1_karlach",
           say("Karlach told me about the Hells. She talks about Avernus like it's a place you *live*. Like it has weather.",
               "Карлах рассказывала мне про ад. Она говорит об Аверно, как о месте, где *живут*. Будто там бывает погода.",
               emo="thinking>sad"),
           GROVE, go="E2")

# --- E2. Падение ---

S.block("E2",
        narrate("She sits closer to the fire, though it isn't cold.", "Она садится ближе к огню, хотя не холодно.", emo="sad"),
        say("It was a festival night. The Companion was up - that light over the city, like a second sun. And then it just... "
            "wasn't. The sky went red. Not sunset red. *Wound* red.",
            "Был праздник. Спутник горел — этот свет над городом, как второе солнце. А потом его просто… не стало. Небо "
            "стало красным. Не закатным. Красным, как *рана*.", emo="happy>fear>sad"),
        say("We were in Avernus before anyone understood we'd moved. My mother went back for the candles. She sold them by "
            "the cathedral - she went back for the *candles*.",
            "Мы оказались в Аверно раньше, чем кто-то понял, что город сдвинулся с места. Мама вернулась за свечами. Она "
            "продавала их у собора — она вернулась за *свечами*.", emo="fear>sad/1", shot="alfira_close"),
        say("The city came back, eventually. She didn't. And then Elturel took one look at our horns and decided whose fault it was.",
            "Потом город вернулся. Она — нет. А Элтуриэль посмотрел на наши рога и решил, кто во всём виноват.",
            emo="sad>angry"),
        choices=[
            opt("Мне жаль. Правда.", "I'm sorry. Truly.", approve=+1, set=[CH.done],
                reply=[say("Everyone says that. You're the first one who's said it like it costs something.",
                           "Все так говорят. Ты {первый|первая}, кто сказал это так, будто это чего-то стоит.",
                           emo="sad>happy")],
                go="E3"),
            opt("Какой она была?", "What was she like?", approve=+2, set=[CH.done, MOTHER_TUNE(PLAYER)],
                reply=[say("Her hands smelled of wax. Always. I can't remember her face properly any more - isn't that awful? - "
                           "but I remember the wax. And she hummed. One tune, over and over, and always flat.",
                           "Руки у неё пахли воском. Всегда. Лицо я уже толком не помню — ужасно, правда? — а воск помню. "
                           "И она напевала. Один мотив, снова и снова, и всегда фальшиво.", emo="happy>sad>happy",
                           note="(улыбается впервые за разговор)")],
                go="E3"),
            opt("Каково оно, пламя Аверно?", "What are the flames of Avernus like?", approve=-2, set=[CH.done],
                reply=[voice("h399f33fcg3e6eg4e3bg9ebbgfc1ed10a5762"),       # They were hot enough to burn my mother alive…
                       voice("hdbc657b9g93a1g47cegb748g60902698926d")],      # Sorry. I didn't mean to snap.
                go="E3"),
            opt("Город подписал договор — город и расплатился.", "The city made a deal. The city paid for it.", approve=-3,
                set=[CH.done],
                reply=[say("My mother didn't sign anything. She sold *candles*.", "Мама ничего не подписывала. Она продавала *свечи*.",
                           emo="angry>sad"),
                       narrate("She turns away.", "Она отворачивается.", emo="sad")],
                go="E3"),
            opt("Нас везде винят за чужие сделки.", "They blame us for everyone's deals.", when=[T.REALLY_TIEFLING(PLAYER)],
                approve=+2, set=[CH.done],
                reply=[say("Horns first, questions never. You too, then.", "Сначала рога, вопросы — никогда. Значит, и тебя тоже.",
                           emo="sad>happy"),
                       narrate("She nudges you with her shoulder.", "Она толкает тебя плечом.", emo="happy"),
                       say("At least we're in good company.", "Хоть компания хорошая.", emo="happy/2")],
                go="E3"),
            opt("Мой отец был в Элтуриэле, когда он пал.", "My father was in Elturel when it fell.",
                when=[T.REALLY_WYLL(PLAYER)], approve=+2, set=[CH.done],
                reply=[say("The Duke. Ravengard.", "Герцог. Рейвенгард.", emo="surprise"),
                       narrate("A long pause.", "Долгая пауза.", emo="thinking"),
                       say("...He came back, didn't he? Some people came back. I'm glad yours did. I mean that. I'm also a bit "
                           "jealous. I mean that too.",
                           "…Он ведь вернулся? Кто-то возвращался. Я рада, что твой вернулся. Правда. И немного завидую. "
                           "Тоже правда.", emo="sad>happy>sad/1")],
                go="E3"),
            check("*Она говорит спокойно. Слишком спокойно.*", "*She's calm. Too calm.*",
                  skill="Insight", ability="Wisdom", dc=DC.Act1_Medium,
                  success=outcome(approve=+2, set=[CH.done, ANGER(PLAYER)], reply=[
                      say("...I'm not sad. I was sad for a year. Now I'm just - *angry*. And I don't know where to put it. "
                          "You can't write a song about being angry. Well, you can. They're terrible.",
                          "…Мне не грустно. Грустно было год. А теперь я просто *злюсь*. И не знаю, куда это деть. Про "
                          "злость песню не напишешь. Ну, напишешь. Только они ужасные.", emo="sad>angry>happy/2",
                          shot="alfira_close")], go="E3"),
                  failure=outcome(set=[CH.done], reply=[
                      say("I'm fine. Really. It was ages ago.", "Я в порядке. Правда. Это было давно.", emo="happy>neutral")],
                      go="E3")),
        ])

# --- E3. Песня, которую она не может написать [вымысел] ---

S.block("E3",
        say("I've written songs about everything. Lihala. Squirrels. A pig farm. Never Elturel. Every time I try, the first "
            "line is fire, and the second line is fire, and then I put the lute down.",
            "Я писала песни обо всём. О Лихейле. О белках. О свиноферме. Об Элтуриэле — никогда. Каждый раз первая "
            "строчка — огонь, вторая — огонь, и я откладываю лютню.", emo="thinking>sad"),
        choices=[
            opt("Напиши о ней, а не об огне. О свечах.", "Write about her, not the fire. The candles.", approve=+2,
                set=[MOTHER_SONG(PLAYER)],
                reply=[narrate("She freezes.", "Она замирает.", emo="surprise"),
                       say("...Candles. Stars, *candles*. I could do candles. Candles don't scream.",
                           "…Свечи. Звёзды, *свечи*. Про свечи я смогу. Свечи не кричат.", emo="thinking>happy")],
                go="E4"),
            check("*Напеть мотив, как она его описала: снова и снова, фальшиво.*",
                  "*Hum the tune the way she described it - over and over, flat.*",
                  when=[MOTHER_TUNE(PLAYER)], skill="Performance", ability="Charisma", dc=DC.Act1_Medium,
                  success=outcome(approve=+3, set=[HUMMED(PLAYER)], reply=[
                      narrate("She joins in; her voice breaks on the second line.", "Она подхватывает, голос срывается на второй строке.",
                              emo="sad/1"),
                      say("That's it. You've got the third bar wrong, and it's *perfect*. She got it wrong too.",
                          "Вот он. Третий такт ты {переврал|переврала}, и это *идеально*. Она тоже его перевирала.",
                          emo="sad>happy", shot="alfira_close")], go="E4"),
                  failure=outcome(approve=+1, reply=[
                      say("No - no, that's a different song entirely. That's a drinking song. She'd have *loved* it.",
                          "Нет-нет, это вообще другая песня. Застольная. Ей бы *понравилось*.", emo="sad>happy/2",
                          note="(смеётся сквозь слёзы)")], go="E4")),
            opt("Так спой злую песню. Громко.", "Then sing an angry one. Loudly.", when=[ANGER(PLAYER)], approve=+2,
                set=[ANGRY_SONG(PLAYER)],
                reply=[say("An angry song.", "Злую песню.", emo="thinking", note="(пробует слово на вкус)"),
                       say("...Karlach would sing along. Karlach would sing along *very* loudly.",
                           "…Карлах бы подпевала. Карлах бы подпевала *очень* громко.", emo="happy/2")],
                go="E4"),
            opt("Некоторые песни не нужно писать.", "Some songs don't need writing.", approve=+1, set=[LIHALA_CITY(PLAYER)],
                reply=[say("Lihala said that. Once. About her own city. She never told me which one.",
                           "Лихейла так говорила. Один раз. О своём городе. Какой это был город, она так и не сказала.",
                           emo="thinking"),
                       narrate("She shrugs.", "Она пожимает плечами.", emo="thinking"),
                       say("I used to think it was wisdom. Now I think it was just *hurting*.",
                           "Я думала, это мудрость. Теперь думаю — ей просто было *больно*.", emo="sad")],
                go="E4"),
            opt("Я буду рядом, когда допишешь.", "I'll be there when you finish it.", when=[OPEN(PLAYER)], approve=+2,
                reply=[say("...Stay for the first line. It's always the worst one.", "…Останься на первую строчку. Она всегда самая худшая.",
                           emo="sad>happy", shot="alfira_close", note="(тихо)")],
                go="E4"),
        ])

# --- E4. Дьяволы ---

S.block("E4",
        say("One more thing, and then I'll stop being gloomy, I promise. If one of them offers you something - that man in "
            "red, or any of them - please don't. The High Overseer signed one contract, and a whole city fell into the Hells.",
            "Ещё одно — и я перестану хандрить, обещаю. Если кто-то из них что-то тебе предложит — тот, в красном, или "
            "любой другой, — пожалуйста, не надо. Высший смотритель подписал договор с дьяволами, и целый город "
            "провалился в ад.", emo="thinking>fear"),
        choices=[
            opt("Обещаю.", "I promise.", approve=+1, set=[DEVIL_PROMISE(PLAYER)],
                reply=[say("Good. I'm holding you to that. I'll write it into a song, so you can't wriggle out.",
                           "Хорошо. Я тебя на слове поймала. Впишу в песню — не отвертишься.", emo="happy",
                           note="(выдыхает)")],
                go=["E5_tune", "E5_anger", "E5"]),
            opt("Не обещаю. Иногда сделка — единственный выход.", "I won't promise. Sometimes a deal is the only way out.",
                reply=[say("...Then at least tell me first. So I can be scared in advance.",
                           "…Тогда хотя бы скажи мне заранее. Чтобы я успела испугаться.", emo="fear>sad")],
                go=["E5_tune", "E5_anger", "E5"]),
            opt("Он уже предлагал мне сделку.", "He's already offered me a deal.", when=[F.RaphaelOfferedDeal.on],
                reply=[narrate("She goes pale.", "Она бледнеет.", emo="fear"),
                       say("...And you said no.", "…И ты {отказался|отказалась}.", emo="fear"),
                       say("Don't - don't tell me. Just say no next time. Say it *loudly*.",
                           "Нет, не говори. Просто в следующий раз скажи «нет». Скажи *громко*.", emo="fear>thinking",
                           note="(не даёт ответить)")],
                go=["E5_tune", "E5_anger", "E5"]),
            opt("Это не твоё дело.", "That's none of your business.", approve=-2,
                reply=[say("It became my business the day the sky went red.", "Это стало моим делом в тот день, когда небо стало красным.",
                           emo="angry")],
                go=["E5_tune", "E5_anger", "E5"]),
        ])

# --- E5. Конец: спросил о матери или заметил злость — тёплый; иначе — «о белках» ---

THANKS = say("Thank you for listening. Most people want the *story*. You wanted *me*. That's... rarer than you'd think.",
             "Спасибо, что {выслушал|выслушала}. Большинству нужна *история*. А тебе была нужна *я*. Это… реже, чем ты думаешь.",
             emo="sad>happy", shot="alfira_close")
S.block("E5_tune", THANKS, when=[MOTHER_TUNE(PLAYER)], end=True)
S.block("E5_anger", THANKS, when=[ANGER(PLAYER)], end=True)
S.block("E5",
        say("Right. Gloom over.", "Так. Хандра окончена.", emo="sad>happy"),
        narrate("She wipes her eyes with her sleeve.", "Она вытирает глаза рукавом.", emo="happy"),
        say("Next time we talk, it's squirrels. Strictly squirrels.", "В следующий раз говорим о белках. Только о белках.",
            emo="happy/2"),
        end=True)
