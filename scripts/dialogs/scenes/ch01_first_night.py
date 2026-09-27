"""Глава 1 «Первая ночь в дороге» — design/dialogs/02_act1_ch1_first_night.md, согласовано 2026-09-26.

Открывается сразу после вербовки (after_rest=False), играет вечером в лагере (GLO_CAMP_State_NightMode)
при одобрении 0 и выше. При одобрении ниже 0 разговор в отряде отвечает своей холодной репликой
(та же озвученная «The sooner we go to sleep…», что в C1 сценария), глава ждёт.
«Завтра рано вставать» (деловой ответ) главу не закрывает: она предлагается снова.
Сыгранной глава считается после любого другого первого ответа героя (CH.done).

voice("h…") — её озвученная реплика игры, say(...) — новая, только текст, narrate(...) — ремарка
рассказчика (действие без слов). Английские реплики героя и ремарок — на вычитку.
"""
from dsl import ALFIRA, PLAYER, Scene, chapter, check, narrate, new_flag, opt, outcome, say, voice
from scenes.recruitment import SPARK
from vanilla import DC, F, T

CH = chapter(1, "Первая ночь в дороге", after_rest=False, when=[F.CampNight.on], approval=0)

SCENE = Scene(
    name="ALFSV_Alfira_Ch01_FirstNight",
    dialog_id="d6df7c3b-aa68-4335-9407-f343bb356245",      # ID ресурса вложенного диалога главы, не менять
    base="DEN_Bard_InParty",                                # её разговор в лагере ночью (ветка Темного Соблазна)
    voice_from=["DEN_Bard_InParty", "DEN_TieflingBard_Bard", "CAMP_DarkUrge_MurderOfAlfira_CFM_AlfiraArrives"],
    chapter=CH,
    status="согласовано 2026-09-26",
)
S = SCENE

# 🔁 Запоминается — на герое (у каждого героя своё правило и своя история с сапогами).
RULE_LOYALTY = new_flag("ALFSV_HeroRule_Loyalty", "Object", "Hero's road rule: always go back for your own")
RULE_DISTRUST = new_flag("ALFSV_HeroRule_Distrust", "Object", "Hero's road rule: trust no one")
RULE_FORCE = new_flag("ALFSV_HeroRule_Force", "Object", "Hero's road rule: strike first")
RULE_STRANGERS = new_flag("ALFSV_HeroRule_Strangers", "Object", "Hero's road rule (Dark Urge): never fall asleep next to strangers")
RULE_JOKE = new_flag("ALFSV_HeroRule_Joke", "Object", "Hero's road rule: don't sleep next to Astarion")
BOOTS_PROMISED = new_flag("ALFSV_Boots_Promised", "Object", "Hero told Alfira she won't have to run here")
BOOTS_TRUTH = new_flag("ALFSV_Boots_TruthKnown", "Object", "Hero learned why Alfira sleeps in her boots (Lihala's last night)")
# «Танец — первая романтическая сцена… Её запомнит сцена „Утро после“ (R3)» — сценарий, «Что это даёт дальше»
FIRST_DANCE = new_flag("ALFSV_Romance_FirstDance", "Object", "Hero danced with Alfira under the stars (chapter 1)")

# --- C1. Приветствие (одобрение 0 и выше; ниже — холодная реплика разговора в отряде) ---

S.greeting("C1", voice("h94c66b2ag36cbg4fafg9decgbd3f033b843d"), go="C2")      # We should probably hit the hay…

# --- C2. Первые слова героя ---

S.block("C2_warm",
        say("Me too. I keep counting heads - you, the fire, the others. Old habit from the road.",
            "Я тоже. Всё пересчитываю головы: ты, костёр, остальные. Старая привычка с дороги.",
            emo="happy>thinking"),
        go="C3")

S.menu("C2",
       # тёплый: русская реплика героя зависит от пола героя — два варианта по тегу FEMALE
       opt("Рад, что ты с нами.", "I'm glad you're with us.", when=[~T.FEMALE(PLAYER)], approve=+1,
           set=[CH.done], go="C2_warm"),
       opt("Рада, что ты с нами.", "I'm glad you're with us.", when=[T.FEMALE(PLAYER)], approve=+1,
           set=[CH.done], go="C2_warm"),
       # любопытный
       opt("Куда бы ты пошла, если бы могла куда угодно?", "If you could go anywhere, where would you go?",
           approve=+1, set=[CH.done],
           reply=[voice("h8e9d685age2bdg4858g8c9bg8b45545d804f"),      # I can't wait to hit the road…
                  voice("h78247de5g47f4g491cga023g280acd8ebba5")],     # Hah, sorry - I'm getting ahead of myself…
           go="C3"),
       # заботливый
       opt("Не спится? Первая ночь без своих.", "Can't sleep? First night away from your people.",
           approve=+2, set=[CH.done],
           reply=[say("Since Elturel I've slept in a heap of tieflings. Dozens of us - someone's tail always in my face, "
                      "someone always snoring. ...It's too quiet out here. I can hear myself think. I don't like it.",
                      "С самого Элтуриэля я спала в куче тифлингов. Несколько десятков — вечно чей-то хвост в лицо, "
                      "вечно кто-то храпит. …А здесь слишком тихо. Слышно собственные мысли. Мне это не нравится.",
                      emo="thinking>happy>sad", note="(не сразу)")],
           go="C3"),
       # насмешливый
       opt("Ты всю ночь будешь так сиять?", "Are you going to glow like that all night?", set=[CH.done],
           reply=[say("Probably. Lihala said I only had two settings: *glowing* and *sulking*. You're getting the good one.",
                      "Наверное. Лихейла говорила, что у меня только два режима: *сияю* и *дуюсь*. Тебе достался хороший.",
                      emo="happy/2>happy")],
           go="C3"),
       # деловой: конец, глава остаётся доступной
       opt("Завтра рано вставать. Спи.", "Early start tomorrow. Get some sleep.",
           reply=[voice("hdb83bb64ga330g4966gabddg5ccd5448a7cd")],       # I'm afraid I don't have your stamina…
           end=True),
       )

# --- C3. Правила дороги ---

S.block("C3",
        narrate("She draws her knees up to her chest, boots right by the fire.",
                "Она подтягивает колени к груди, сапоги у самого огня.", emo="thinking"),
        say("Lihala had rules for the road. First night out, she'd make me recite them. Every. Single. Time.",
            "У Лихейлы были правила для дороги. В первую ночь пути она заставляла меня их повторять. Каждый. Божий. Раз.",
            emo="happy>thinking>happy/2"),
        choices=[
            opt("Какие правила?", "What rules?", go="RULES"),
            opt("Дай угадаю: не петь фальшиво?", "Let me guess - never sing off-key?",
                reply=[say("Ha! No, that one was *every* night.", "Ха! Нет, это правило было на *каждую* ночь.",
                           emo="happy/2")],
                go="RULES"),
            # правила пропускаются, «сапоги» не раскрываются
            opt("Лучше расскажи о ней самой.", "Tell me about her instead.", go="C4"),
        ])

# Правила [вымысел]
S.block("RULES",
        say("One: never play the sad song first. Make them laugh, then make them cry, *then* pass the hat.",
            "Первое: никогда не начинай с грустной песни. Сначала рассмеши, потом доведи до слёз — и *только потом* пускай шляпу по кругу.",
            emo="happy>happy/2"),
        say("Two: sleep with your boots on the first night in a new camp. In case you have to run.",
            "Второе: в первую ночь на новом месте спи в сапогах. На случай, если придётся бежать.",
            emo="thinking"),
        narrate("A pause. She looks down at her boots.", "Пауза. Она смотрит на свои сапоги.", emo="sad",
                shot="alfira_close"),
        say("...I've slept with my boots on every night since Elturel.",
            "…Я сплю в сапогах каждую ночь с самого Элтуриэля.", emo="sad>sad/1", shot="alfira_close"),
        choices=[
            opt("Здесь тебе не придётся бежать.", "You won't have to run here.", approve=+2,
                set=[BOOTS_PROMISED(PLAYER)],
                reply=[say("...You can't promise that. But it's nice that you tried.",
                           "…Ты не можешь этого обещать. Но приятно, что ты {попробовал|попробовала}.",
                           emo="thinking>sad>happy", shot="alfira_close", note="(долго смотрит на героя)")],
                go="THREE"),
            opt("Сапоги — это разумно. Я тоже так сплю.", "Keeping your boots on is sensible. I sleep in mine too.",
                approve=+1,
                reply=[say("Oh, good. Then we can be ready to flee *together*. Very romantic.",
                           "О, отлично. Значит, сбегать будем *вместе*. Очень романтично.", emo="happy>happy/2")],
                go="THREE"),
            check("*Понять, что за этим стоит.*", "*Try to understand what's really behind it.*",
                  skill="Insight", ability="Wisdom", dc=DC.Act1_Medium,
                  success=outcome(approve=+2, set=[BOOTS_TRUTH(PLAYER)], reply=[
                      say("It's not the running. It's that last time I *didn't* have my boots on. Lihala did. She... she told me to go.",
                          "Дело не в беге. В тот раз сапоги были *не на мне*. А на ней. Она… она велела мне бежать.",
                          emo="sad>fear/1>sad/1", shot="alfira_close")], go="THREE"),
                  failure=outcome(reply=[
                      say("It's just a habit. Forget it.", "Просто привычка. Забудь.", emo="happy>neutral",
                          note="(отмахивается)")], go="THREE")),
            opt("Ну и вонища, наверное.", "Must reek something awful.",
                reply=[say("Rude. *Accurate*, but rude.", "Грубо. *Честно*, но грубо.", emo="happy/2>happy",
                           note="(смеётся против воли)")],
                go="THREE"),
        ])

# Третье правило и её вопрос 🔁
S.block("THREE",
        say("And three - never, *ever* let the fighter carry the lute.",
            "И третье: никогда, *никогда* не давай нести лютню воину.", emo="happy/2"),
        say("Your turn. Everyone on the road has a rule. What's yours?",
            "Твоя очередь. У каждого в дороге есть своё правило. Какое у тебя?", emo="thinking>happy"),
        choices=[
            opt("Всегда возвращайся за своими.", "Always go back for your own.", approve=+2,
                set=[RULE_LOYALTY(PLAYER)],
                reply=[say("...Oh. That's a good one. That's a *really* good one. I'm stealing it.",
                           "…О. Хорошее. *Очень* хорошее. Я его украду.", emo="surprise>happy")],
                go="C4"),
            opt("Никому не доверяй.", "Trust no one.", set=[RULE_DISTRUST(PLAYER)],
                reply=[say("Then I'll just have to be the exception. Lihala always said I was stubborn.",
                           "Значит, придётся мне стать исключением. Лихейла всегда говорила, что я упрямая.",
                           emo="thinking>happy")],
                go="C4"),
            opt("Бей первым.", "Strike first.", approve=-1, set=[RULE_FORCE(PLAYER)],
                reply=[say("...That one's not going in the song.", "…Это в песню не пойдёт.", emo="thinking>sad")],
                go="C4"),
            opt("Никогда не засыпай рядом с незнакомцами.", "Never fall asleep next to strangers.",
                when=[T.REALLY_DARK_URGE(PLAYER)], set=[RULE_STRANGERS(PLAYER)],
                reply=[say("Bit late for that, isn't it? I'm about to sleep ten feet from you.",
                           "Поздновато, не находишь? Я вот-вот усну в трёх шагах от тебя.", emo="happy/2>happy",
                           note="(смеётся)")],
                go="C4"),
            opt("Не спать рядом с Астарионом.", "Never sleep next to Astarion.",
                when=[F.AstarionCompanionInCamp.on], set=[RULE_JOKE(PLAYER)],
                reply=[say("Noted. Underlined. *Twice.*", "Записала. Подчеркнула. *Дважды.*", emo="happy>happy/2")],
                go="C4"),
            opt("Сегодня — не дать тебе замёрзнуть.", "Tonight? Making sure you don't get cold.",
                when=[SPARK(PLAYER)], approve=+2,
                reply=[say("You can't just *say* things like that.", "Нельзя же вот так просто *говорить* такое.",
                           emo="surprise>happy/2", shot="alfira_close", note="(замирает, потом прячет лицо в колени)")],
                go="C4"),
        ])

# --- C4. Танец под звёздами ---

S.block("C4",
        narrate("She tips her head back towards the sky.", "Она запрокидывает голову к небу.", emo="thinking"),
        say("Our first night on the road, I woke up to this awful thumping. Thought it was bandits.",
            "В нашу первую ночь в пути я проснулась от жуткого топота. Решила, что разбойники.",
            emo="thinking>fear>happy"),
        voice("h2a3bb0b9g759bg4b41gaa05g99a2e914a064"),                 # I woke up, and there she was - dancing…
        say("Two left feet and not a care in the world. That's where the first line came from. *Dance upon the stars tonight.*",
            "Две левые ноги — и ни одной заботы. Оттуда и первая строка. «Ты танцуешь среди звёзд».",
            emo="happy>happy/2"),
        choices=[
            opt("Она бы гордилась тобой.", "She'd be proud of you.", approve=+2,
                reply=[say("...Thank you. I needed someone to say it who isn't me.",
                           "…Спасибо. Мне нужно было услышать это не от себя.", emo="sad>happy", shot="alfira_close",
                           note="(тихо)")],
                go="C5"),
            check("*Сыграть что-нибудь на ночь.*", "*Play her something to fall asleep to.*",
                  skill="Performance", ability="Charisma", dc=DC.Act1_Medium,
                  # уснула — «спокойной ночи» уже некому сказать: сразу к сапогам (или конец)
                  success=outcome(approve=+2, reply=[
                      narrate("She hums along without words, and falls asleep halfway through a verse.",
                              "Она подпевает без слов и засыпает посреди куплета.", emo="happy>sleeping")],
                      go=["C5_boots_promised", "C5_boots_truth"]),
                  failure=outcome(approve=+1, reply=[
                      say("...We'll work on it. Lihala would've made you play 'til your fingers bled.",
                          "…Поработаем над этим. Лихейла заставила бы тебя играть, пока пальцы не сотрёшь.",
                          emo="thinking>happy", note="(улыбается)")], go="C5")),
            opt("Потанцуем?", "Shall we dance?", when=[SPARK(PLAYER)], approve=+3, set=[FIRST_DANCE(PLAYER)],
                reply=[say("Here? Now? With - ...One dance. Badly. In her honour.",
                           "Здесь? Сейчас? При всех?.. …Один танец. Плохо. В её честь.",
                           emo="surprise>fear/1>happy/2", note="(оглядывается на лагерь)")],
                go="C5"),
            opt("Спокойной ночи, Альфира.", "Goodnight, Alfira.", go="C5"),
        ])

# --- C5. Конец ---

S.block("C5", voice("h4571b86egfc8dg4c8bga1bbga52e77fb7123"),                 # Goodnight, and thank you. I mean it.
        go=["C5_boots_promised", "C5_boots_truth"])

BOOTS_OFF = ("Half-asleep, she sits up and slowly pulls off her boots. She sets them beside her. For the first time since Elturel.",
             "Уже засыпая, она садится и медленно стягивает сапоги. Ставит их рядом. Впервые с Элтуриэля.")
# герой пообещал, что бежать не придётся, или узнал правду о той ночи (два узла — «или» в условиях игры)
S.block("C5_boots_promised", narrate(*BOOTS_OFF, emo="sleeping>happy"), when=[BOOTS_PROMISED(PLAYER)], end=True)
S.block("C5_boots_truth", narrate(*BOOTS_OFF, emo="sleeping>happy"), when=[BOOTS_TRUTH(PLAYER)], end=True)

S.blocks["C3"].seated = "knees"      # «Она подтягивает колени к груди» — с C3 и дальше сидя (staging.SEATED)
