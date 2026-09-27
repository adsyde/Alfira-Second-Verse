"""Глава 7 «Страх» — design/dialogs/08_act1_ch7_fear.md, согласовано 2026-09-27.

Необязательная, акт 1, после долгого отдыха, одобрение 10+. Условие — первый спуск в Подземье
(GLO_Underdark_EverEnteredBefore), вход в Гримфордж (GLO_DuergarCamp_EverEnteredBefore) или Горный перевал
(уровень CRE_Main_A сейчас или флаг движка VISITEDREGION_CRE_Main_A). S1: вариант перевала, если перевал
посещён, иначе — Подземья [решение сборки: какое место было «последним», игра не хранит]. Сыграна — с ответа в S3.
"""
from dsl import ALFIRA, PLAYER, Scene, chapter, check, narrate, new_flag, opt, osi, outcome, say, voice
from scenes.ch01_first_night import RULE_LOYALTY
from scenes.ch05_morning_after import OPEN
from vanilla import DC, F, T

CH = chapter(7, "Страх", after_rest=True, optional=True, act=1, approval=10,
             story_any=[F.UnderdarkEntered.on, F.GrymforgeEntered.on, F.MountainPassVisited.on,
                        osi('DB_CurrentLevel("CRE_Main_A")', "сейчас Горный перевал / Ясли (акт 1b)")])

SCENE = Scene(
    name="ALFSV_Alfira_Ch07_Fear",
    dialog_id="c47a1e93-2b6d-4f08-8e5c-9d3a6b1f7e42",      # ID ресурса вложенного диалога главы, не менять
    base="DEN_Bard_InParty",
    # HAV_AlfiraTale_Bard — «talent and courage», «not ashamed of running»; DEN_AttackOnDen_Bard — «much use in a battle»
    voice_from=["HAV_AlfiraTale_Bard", "DEN_AttackOnDen_Bard"],
    chapter=CH,
    status="согласовано 2026-09-27",
)
S = SCENE

# 🔁 на герое: что такое храбрость (S3) и «храбрость, которой никто не видел» (S4) — для песни о герое
BRAVE_KEEP = new_flag("ALFSV_Brave_KeepUsStanding", "Object", "Bravery by the hero: keeping the others on their feet")
BRAVE_RETURN = new_flag("ALFSV_Brave_GoingBack", "Object", "Bravery by the hero: going back")
BRAVE_LUCK = new_flag("ALFSV_Brave_Luck", "Object", "Bravery by the hero: just luck")
BRAVE_TACTIC = new_flag("ALFSV_Brave_Tactic", "Object", "Bravery by the hero: retreat is a tactic")
REAL_FEAR = new_flag("ALFSV_Fear_RunFromYou", "Object", "Alfira's real fear: that she will run from the hero (Insight)")
UNSEEN_TADPOLE = new_flag("ALFSV_Unseen_Tadpole", "Object", "Unseen bravery: waking up with a tadpole every morning")
UNSEEN_STAYED = new_flag("ALFSV_Unseen_WantedToRun", "Object", "Unseen bravery: wanted to run today and stayed")
UNSEEN_WITH_HER = new_flag("ALFSV_Unseen_StayedWithHer", "Object", "Unseen bravery: stayed with her (romance)")
UNSEEN_TRUTH = new_flag("ALFSV_Unseen_Truth", "Object", "Unseen bravery: telling her the truth right now")
UNSEEN_RESIST = new_flag("ALFSV_Unseen_Resisting", "Object", "Unseen bravery (Dark Urge): not giving in to what's inside")
UNSEEN_SURVIVE = new_flag("ALFSV_Unseen_Surviving", "Object", "Unseen bravery: bravery's for songs, I survive")


def gendered(ru_m, ru_f, en, when=(), **kw):
    return [opt(ru_m, en, when=[~T.FEMALE(PLAYER), *when], **kw),
            opt(ru_f, en, when=[T.FEMALE(PLAYER), *when], **kw)]


# --- S1. Приветствие по месту ---

S.greeting("S1_pass",
           say("Up here the wind sounds like someone screaming a long way off. I keep turning round.",
               "Здесь ветер звучит, будто кто-то кричит очень далеко. Я всё время оборачиваюсь.", emo="fear>thinking"),
           when=[F.MountainPassVisited.on], go="S2")
S.greeting("S1_underdark",
           say("It's the dark. Not the monsters - the monsters I can *see*. It's that the dark doesn't end. You walk and walk, "
               "and it's just... more.",
               "Дело в темноте. Не в чудовищах — чудовищ я хотя бы *вижу*. А темнота не кончается. Идёшь, идёшь — а её "
               "только… больше.", emo="fear>thinking"),
           go="S2")

# --- S2. Где выход [вымысел] ---

S.block("S2",
        say("Can I tell you a secret? Every camp we make, I find the way out first. Before the fire, before the bedroll. "
            "Which way I'd run.",
            "Можно открою секрет? На каждой стоянке я первым делом нахожу, куда бежать. Раньше костра, раньше постели.",
            emo="thinking>fear"),
        say("I did it tonight. I'm doing it now.", "Сегодня тоже. И прямо сейчас.", emo="thinking"),
        narrate("She nods to one side.", "Она кивает в сторону.", emo="thinking"),
        say("That gap, by the rocks.", "Вон тот проход, у камней.", emo="fear/1"),
        say("We didn't hear the gnolls coming. Lihala was playing. And when we did hear them - I ran. I've been checking for "
            "the gap ever since.",
            "Мы не услышали гноллов. Лихейла играла. А когда услышали — я побежала. С тех пор я всё время ищу проход.",
            emo="sad>fear>sad/1", shot="alfira_close"),
        say("And in the last fight I stayed at the back and played. Behind a rock, mostly. Was that cowardly? Be - no, don't be honest.",
            "А в последнем бою я держалась сзади и играла. В основном за камнем. Это трусость? Скажи… нет, не говори честно.",
            emo="thinking>fear"),
        narrate("A pause.", "Пауза.", emo="thinking"),
        say("Yes. Be honest.", "…Да. Скажи честно.", emo="sad"),
        go="S3")

# --- S3. Ответ героя ---

S.menu("S3",
       opt("Ты держала нас на ногах. Это не трусость.", "You kept us on our feet. That's not cowardice.", approve=+2,
           set=[CH.done, BRAVE_KEEP(PLAYER)],
           reply=[say("Music as armour. Lihala would've said that. She'd have said it *louder*, and then made me practise.",
                      "Музыка как доспех. Лихейла так бы и сказала. Только *громче*, а потом усадила бы меня упражняться.",
                      emo="surprise>happy")],
           go="S4"),
       opt("А что для тебя храбрость?", "What does brave mean to you?", approve=+1, set=[CH.done, BRAVE_RETURN(PLAYER)],
           reply=[say("Oh, you don't get to answer a question with a question.", "О, нет, на вопрос вопросом не отвечают.",
                      emo="happy/2"),
                  say("...Going back, I think. Not the not-running. The going back.",
                      "…Возвращаться, наверное. Не «не бежать». А возвращаться.", emo="thinking", note="(но задумывается)")],
           go="S4"),
       *gendered("Я и сам не храбрый. Мне просто везёт.", "Я и сама не храбрая. Мне просто везёт.",
                 "I'm not brave either. I just get lucky.", approve=+1, set=[CH.done, BRAVE_LUCK(PLAYER)],
                 reply=[voice("h38bbd78fg5b10g4fb4g87c2gd9681fb27018"),      # I believe in ballads they call that 'talent'…
                        say("...Fine. I'll call mine \"luck\" too. See how you like it.",
                            "…Ладно. Тогда и я буду свою звать «везением». Посмотрим, как тебе понравится.", emo="happy/2")],
                 go="S4"),
       # 🏷️ воин, варвар или паладин — «или» тремя взаимоисключающими узлами: у мультикласса вариант один
       *[opt("Отступление — тоже тактика. Оно спасает армии.", "Retreat is a tactic. It saves armies.", when=when,
             approve=+1, set=[CH.done, BRAVE_TACTIC(PLAYER)], key=f"S3.tactic{i}",
             reply=[say("*Tactical* retreat. I'm having that carved into my lute. Right next to the pig farm.",
                        "*Тактическое* отступление. Вырежу на грифе. Рядом со свинофермой.", emo="happy/2")],
             go="S4") for i, when in enumerate([
                 [T.FIGHTER(PLAYER)],
                 [~T.FIGHTER(PLAYER), T.BARBARIAN(PLAYER)],
                 [~T.FIGHTER(PLAYER), ~T.BARBARIAN(PLAYER), T.PALADIN(PLAYER)]])],
       opt("Держись сзади. Так и надо.", "Stay at the back. That's where you belong.", set=[CH.done],
           reply=[voice("h0db432d4gf83fg45b1gb675g0fdbcd8ae82b"),          # Hardly going to be much use in a battle, am I?
                  say("...That wasn't a question you were meant to *agree* with.",
                      "…Вообще-то с этим не надо было *соглашаться*.", emo="angry>sad")],
           go="S4"),
       opt("Ты сбежала, когда погибла Лихейла.", "You ran when Lihala died.", approve=-2, set=[CH.done],
           reply=[voice("h55e6f5bdg5968g4237g9065gb23afbfdc214")],        # I know what I am and what I'm not…
           go="S4"),
       check("*Она спрашивает не о бое.*", "*She isn't asking about the fight.*", skill="Insight", ability="Wisdom",
             dc=DC.Act1_Medium,
             success=outcome(approve=+2, set=[CH.done, REAL_FEAR(PLAYER)],
                             reply=[narrate("A long silence.", "Она долго молчит.", emo="sad")],
                             go=["S3_fear_us", "S3_fear_you"]),
             failure=outcome(set=[CH.done], reply=[
                 say("What? No. It's about the rock. It was a very cowardly rock.",
                     "Что? Нет. Я про камень. Это был очень трусливый камень.", emo="surprise>happy/2")], go="S4")),
       )
S.block("S3_fear_us",
        say("...No. I'm asking whether I'll run from *us*. When it gets bad. Because it will. And I always do.",
            "…Нет. Я спрашиваю, не сбегу ли я от *нас*. Когда станет совсем плохо. А станет. А я всегда сбегаю.",
            emo="sad>fear/1", shot="alfira_close"),
        when=[OPEN(PLAYER)], go="S4")
S.block("S3_fear_you",
        say("...No. I'm asking whether I'll run from *you*. When it gets bad. Because it will. And I always do.",
            "…Нет. Я спрашиваю, не сбегу ли я от *тебя*. Когда станет совсем плохо. А станет. А я всегда сбегаю.",
            emo="sad>fear/1", shot="alfira_close"),
        go="S4")

# --- S4. Её правило храбрости [вымысел] ---

S.block("S4",
        say("Lihala used to say the brave part of a ballad isn't the charge. It's the verse after - when someone stays, and "
            "sings over the dead, so the dead aren't alone. I always thought she meant herself. Maybe she meant the job.",
            "Лихейла говорила: храбрость в балладе — не атака. А куплет после неё, когда кто-то остаётся и поёт над "
            "павшими, чтобы павшие не были одни. Я думала, она о себе. А может, она о ремесле.", emo="thinking>sad"),
        say("What about you? What's the bravest thing you've done that nobody saw?",
            "А ты? Какой твой самый храбрый поступок, который никто не видел?", emo="thinking>happy"),
        choices=[
            opt("Просыпаюсь каждое утро с личинкой в голове.", "I wake up every morning with a tadpole in my head.", approve=+1,
                set=[UNSEEN_TADPOLE(PLAYER)],
                reply=[say("...Every morning. That's going in. First line, fourth verse.",
                           "…Каждое утро. Это я беру. Первая строчка, четвёртый куплет.", emo="thinking",
                           note="(медленно кивает)")],
                go=["S5_fear", "S5"]),
            *gendered("Сегодня не сбежал.", "Сегодня не сбежала.", "I didn't run today.", approve=+2,
                      set=[UNSEEN_STAYED(PLAYER)],
                      reply=[say("You never run.", "Ты никогда не бежишь.", emo="thinking"),
                             narrate("A pause.", "Пауза.", emo="thinking"),
                             say("Oh - you mean you *wanted* to. ...Thank you for telling me that. That's worth more than "
                                 "the not-running.",
                                 "…А, ты хочешь сказать, что *хотелось*. …Спасибо, что {сказал|сказала}. Это дороже, чем "
                                 "«не бежать».", emo="surprise>sad>happy")],
                      go=["S5_fear", "S5"]),
            *gendered("Остался с тобой.", "Осталась с тобой.", "I stayed with you.", when=[OPEN(PLAYER)], approve=+2,
                      set=[UNSEEN_WITH_HER(PLAYER)],
                      reply=[say("...That's not fair. You can't just - that's *my* line. I was saving it.",
                                 "…Нечестно. Нельзя вот так… это *моя* строчка. Я её берегла.", emo="surprise>happy/2",
                                 shot="alfira_close", note="(не сразу)")],
                      go=["S5_fear", "S5"]),
            opt("Говорю тебе правду. Прямо сейчас.", "Telling you the truth. Right now.", approve=+2, set=[UNSEEN_TRUTH(PLAYER)],
                reply=[say("...Oh. That's a cheat. That counts.", "…Ой. Это жульничество. …Засчитано.", emo="surprise>happy",
                           note="(улыбается)")],
                go=["S5_fear", "S5"]),
            opt("Не поддаваться тому, что внутри.", "Not giving in to what's inside me.", when=[T.REALLY_DARK_URGE(PLAYER)],
                approve=+2, set=[UNSEEN_RESIST(PLAYER)],
                reply=[say("Whatever's inside you - I've only ever seen the outside be kind. ...I'll take the outside's word for it.",
                           "Что бы там ни было внутри — я видела только, как снаружи ты {добр|добра}. …Поверю снаружи на слово.",
                           emo="thinking>happy")],
                go=["S5_fear", "S5"]),
            opt("Храбрость — для песен. Я выживаю.", "Bravery's for songs. I survive.", set=[UNSEEN_SURVIVE(PLAYER)],
                reply=[say("Then I'll sing about the surviving. Someone has to. It's the harder verse to write.",
                           "Тогда я спою о выживании. Кто-то же должен. Этот куплет писать труднее.", emo="thinking")],
                go=["S5_fear", "S5"]),
        ])

# --- S5. Конец ---

NEXT = say("Next fight, I'm not taking the gap. I'll be at the back - I'm not *stupid* - but I'll stay.",
           "В следующем бою я не побегу в проход. Буду сзади — я же не *дура*, — но останусь.", emo="thinking>happy")
SITS = narrate("She sits down with her back to the gap by the rocks.", "Она садится спиной к проходу у камней.", emo="happy")
S.block("S5_fear", NEXT,
        say("And if I ever do run - from anything - come and get me. You're good at that. Coming back for people.",
            "А если я всё-таки сбегу — от чего угодно, — приди за мной. Ты это умеешь. Возвращаться за людьми.",
            emo="sad>happy", shot="alfira_close"),
        when=[REAL_FEAR(PLAYER)], go=["S5_rule", "S5_sit"])
S.block("S5_rule",
        say("...You told me that on the first night, actually. I'm only just hearing it.",
            "…Вообще-то ты {сказал|сказала} мне это в первую ночь. Я только сейчас расслышала.", emo="surprise>happy"),
        SITS, when=[RULE_LOYALTY(PLAYER)], end=True)
S.block("S5_sit", SITS, end=True)
S.block("S5", NEXT, SITS, end=True)
