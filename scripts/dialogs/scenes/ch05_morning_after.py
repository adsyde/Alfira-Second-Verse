"""Глава 5 «Утро после» — design/dialogs/06_act1_ch5_morning_after.md, согласовано 2026-09-27.

Открывается на первом долгом отдыхе после праздника, если глава 4 сыграна (story: ALFSV_Chapter04_Done).
Необязательная (без праздника с ней главы нет и очередь она не держит), акт 1, приоритет 1: в этой
проверке открывается раньше других глав — это именно утро после. Вход — любой разговор в отряде или в
лагере. Сыграна (CH.done) — с первого ответа героя в U2.

Всё из праздника — флаги главы 4 на герое (ALFSV_Celebration_*): как кончилась ночь (U1), что она сказала
(U2), тема песни (U3, куплет на листке), R2 (U4). «Роман возможен» — искра, или «герой выбрал её», или
одобрение 40+ (три условия — три узла, «или» как у Larian). Порог «роман открыт» — 30.

voice("h…") — её озвученная реплика игры, say(...) — новая, только текст, narrate(...) — ремарка.
"""
from dataclasses import replace

from dsl import ALFIRA, PLAYER, Scene, chapter, check, narrate, new_flag, opt, outcome, say, voice
from scenes.ch04_celebration import (CH as CH4, CHOSE_HER, CLOAK, F3_DONE, LAKRISSA_HERE, PUSHED, SAID_EYEBROWS,
                                     SAID_FRIEND, SAID_LOVELY, SHOULDER, THEME_BEAUTY, THEME_EVERYONE, THEME_NO_SONG,
                                     THEME_OTHER_HERO, TO_LAKRISSA)
from scenes.recruitment import SPARK
from vanilla import APPROVAL_SP1, DC, T

CH = chapter(5, "Утро после", after_rest=True, optional=True, act=1, story=[CH4.done_flag.on], priority=1)

SCENE = Scene(
    name="ALFSV_Alfira_Ch05_MorningAfter",
    dialog_id="3f0c9a4e-7d21-4b8e-9c5a-1e6b2d8f4a07",      # ID ресурса вложенного диалога главы, не менять
    base="DEN_Bard_InParty",
    # DEN_TieflingBard_Bard — «This is embarrassing. Gods.»; LOW_Elfsong_Alfira — «Oh, hush - I know you love me really.»
    voice_from=["DEN_TieflingBard_Bard", "LOW_Elfsong_Alfira"],
    chapter=CH,
    status="согласовано 2026-09-27",
)
S = SCENE

# 🔁 на герое (главе 8 и роману акта 2)
OPEN = new_flag("ALFSV_Romance_Open", "Object", "R3: the romance with Alfira is open (morning after, approval 30+)")
ASK_AGAIN = new_flag("ALFSV_Romance_AskAgain", "Object", "R3: 'ask me again when I'm sure' - second try in chapter 8")
POSTPONED = new_flag("ALFSV_Romance_Postponed", "Object", "R3: postponed ('let's see where the road takes us' / 'wanted to see how you'd react')")
FRIEND = new_flag("ALFSV_Romance_Friend", "Object", "R3: 'you're my friend' - no romance in act 1")
FORGET = new_flag("ALFSV_Romance_Forget", "Object", "R3: 'you were drunk, let's forget it' - no romance in act 1")
READ_LINE = new_flag("ALFSV_MorningAfter_ReadLine", "Object", "Hero read the crossed-out line of the second verse (Insight)")
SPARED = new_flag("ALFSV_MorningAfter_Spared", "Object", "Hero kindly lied: 'you sang and fell asleep'")
# для Osiris глав: глава 8 открывается, когда у кого-то роман открыт, «спросить снова» или «отложено»
CANDIDATE = new_flag("ALFSV_Romance_Act1Candidate", "Global",
                     "Some hero opened the romance or was asked to ask again (chapter 5) - chapter 8 can open")

AP30, AP40 = APPROVAL_SP1[30](ALFIRA), APPROVAL_SP1[40](ALFIRA)
ROMANCE_GATES = [("chose", [CHOSE_HER(PLAYER)]), ("spark", [SPARK(PLAYER)]), ("ap40", [AP40])]


def gendered(ru_m, ru_f, en, when=(), **kw):
    """Реплика героя с родом по-русски: два варианта по тегу FEMALE (reply и переход общие)."""
    return [opt(ru_m, en, when=[~T.FEMALE(PLAYER), *when], **kw),
            opt(ru_f, en, when=[T.FEMALE(PLAYER), *when], **kw)]


U4 = ["U4_chose", "U4_spark", "U4_ap40", "U4_friendly"]      # «роман возможен» — три узла «или», иначе дружеская версия


# --- U1. Приветствие ---

S.greeting("U1",
           narrate("She squints at the light and holds her head in both hands.",
                   "Она щурится на свет и держится за голову обеими руками.", emo="pain"),
           say("Don't. Talk. Loudly. Is this what wine does? Every time? And people drink it *on purpose*?",
               "Не. Говори. Громко. Вино всегда так делает? Каждый раз? И его пьют *нарочно*?", emo="pain>disgust"),
           go=["U1_cloak", "U1_shoulder", "U1_lakrissa", "U1_pooper", "U2"])
S.block("U1_cloak",
        narrate("She holds out your folded cloak.", "Она протягивает тебе сложенный плащ.", emo="thinking"),
        say("I woke up in your cloak. I've decided not to ask how. ...It smells like campfire. That's not a compliment. "
            "It's not *not* one, either.",
            "Я проснулась в твоём плаще. Решила не спрашивать, как так вышло. …Он пахнет костром. Это не комплимент. "
            "Но и не *не* комплимент.", emo="thinking>happy/2"),
        when=[CLOAK(PLAYER)], go="U2")
S.block("U1_shoulder",
        say("I woke up on a log. With a crick in my neck the exact shape of your shoulder.",
            "Я проснулась на бревне. Шея затекла — точно по форме твоего плеча.", emo="pain>happy"),
        when=[SHOULDER(PLAYER)], go="U2")
S.block("U1_lakrissa",
        say("Lakrissa says I sang to her tent. For an hour. The tent did not ask for an encore.",
            "Лакрисса говорит, я пела её палатке. Целый час. На бис палатка не звала.", emo="happy/2>pain"),
        when=[TO_LAKRISSA(PLAYER)], go="U2")
# «Иди проспись»: F3 сыгран, а плаща, плеча и Лакриссы нет
S.block("U1_pooper",
        say("Party pooper. I remember *that* bit, at least.", "Зануда. Уж это-то я помню.", emo="angry", note="(прохладно)"),
        when=[F3_DONE(PLAYER)], go="U2")

# --- U2. «Я тебе *что* сказала?» ---

S.block("U2",
        voice("hd4b808dcg88bag4abcga6a6gbad1e6044a76"),                    # This is embarrassing. Gods.
        say("I remember the wine. And the fire. And then it's... patches. Did I say something? I said something. "
            "I can *feel* that I said something.",
            "Помню вино. И костёр. А дальше… обрывки. Я что-то сказала? Я что-то сказала. Я *чувствую*, что что-то сказала.",
            emo="thinking>fear>pain"),
        go="U2_menu")

SAID = [
    (SAID_EYEBROWS, say("*Symmetrical?* That's what I went with? I had every word in the world and I picked *symmetrical*?",
                        "«Симметричные»? Вот что я выбрала? У меня были все слова на свете, а я выбрала «симметричные»?",
                        emo="surprise>disgust>happy/2")),
    (SAID_LOVELY, say("Oh, no. I did the *lovely* thing. Lihala used to say two sips of cider made me sentimental. "
                      "She never saw me on a whole cup.",
                      "О нет. Я устроила своё «все милые». Лихейла говорила, мне хватает двух глотков сидра, чтобы "
                      "расчувствоваться. Целой кружки она не видела.", emo="fear>happy/2")),
    (SAID_FRIEND, say("...Oh. Well. That one I'd say sober. I just wouldn't cry after.",
                      "…А. Ну, это я сказала бы и трезвой. Только без слёз потом.", emo="surprise>happy>sad/1",
                      note="(тише на второй фразе)")),
]
S.menu("U2_menu",
       # «Сказала. Рассказать?» — её ответ по тому, что она сказала ночью (у героя одна из трёх фраз)
       *[opt("Сказала. Рассказать?", "You did. Want to hear it?", when=[flag(PLAYER)], approve=+1, set=[CH.done],
             reply=[line], go="U3") for flag, line in SAID],
       opt("Ты сделала мне предложение. Дважды.", "You proposed. Twice.", once=True, approve=+1, set=[CH.done],
           reply=[say("I *what* -", "Я *что*…", emo="surprise"),
                  narrate("She sees your face.", "Она видит твоё лицо.", emo="surprise>angry"),
                  say("You bastard. You utter - I nearly died. I'm *hungover*, I can't die twice in one morning.",
                      "Ах ты гад. Вот же ты… Я чуть не умерла. У меня *похмелье*, нельзя умирать дважды за одно утро.",
                      emo="angry>happy/2")],
           go="U2_menu"),
       opt("Ничего. Спела и уснула.", "Nothing. You sang and fell asleep.", approve=+1, set=[CH.done, SPARED(PLAYER)],
           reply=[say("You're a very kind, very terrible liar. ...Thank you. I'll pretend it worked.",
                      "Ты очень {добрый и очень плохой лжец|добрая и очень плохая лгунья}. …Спасибо. Сделаю вид, что сработало.",
                      emo="thinking>happy", note="(прищуривается)")],
           go="U3"),
       *gendered("Я сам мало что помню.", "Я сама мало что помню.", "I barely remember it myself.", set=[CH.done],
                 reply=[say("Good. Great. Then it never happened. We're agreed.",
                            "Хорошо. Отлично. Значит, ничего не было. Договорились.", emo="happy>thinking",
                            note="(не верит ни слову)")],
                 go="U3"),
       )

# --- U3. Листок: куплет по теме праздника ---

VERSE_COURAGE = narrate("*We laughed in the face of the dark, we two -<br>and I didn't run. Not once. Not from you.*",
                        "*Смеялись мы в лицо темноте вдвоём —<br>и я не сбежала. Ни ночью, ни днём.*", emo="thinking")
S.block("U3",
        narrate("She pulls a crumpled, wine-stained sheet out of her boot.",
                "Она вытаскивает из-за голенища смятый листок в винных пятнах.", emo="thinking"),
        say("And there's this. Found it in my boot. It's the second verse. Of *your* song. Written by - well. Wine, mostly.",
            "А ещё вот. Нашла в сапоге. Второй куплет. *Твоей* песни. Автор — ну. В основном вино.", emo="happy/2>pain"),
        go=["U3_beauty", "U3_everyone", "U3_other", "U3_nosong", "U3_courage"])
S.block("U3_beauty", narrate("*Oh, sing of the hero, so fair of face -<br>I'd write it all down, but I've run out of space.*",
                             "*Воспою {героя|героиню}: {хорош|хороша} на лицо, —<br>да листок маловат, чтоб вместить это всё.*",
                             emo="thinking"), when=[THEME_BEAUTY(PLAYER)], go="U3_bottom")
S.block("U3_everyone", narrate("*Not one hero, but a hundred and three -<br>and one of them turned and waited for me.*",
                               "*Не один герой — нас сто и ещё,<br>но кто-то обернулся и подставил плечо.*", emo="thinking"),
        when=[THEME_EVERYONE(PLAYER)], go="U3_bottom")
S.block("U3_other", narrate("*I was told to sing of another name -<br>but my quill kept writing yours all the same.*",
                            "*Мне велено петь о другом — а перо<br>упрямо выводит лишь имя твоё.*", emo="thinking"),
        when=[THEME_OTHER_HERO(PLAYER)], go="U3_bottom")
S.block("U3_nosong", narrate("*You said \"no song\", so I'm keeping it small:<br>a verse in my boot that's not there at all.*",
                             "*Ты песен не хочешь — что ж, будет секрет:<br>куплет в моём сапоге. Его вроде бы нет.*",
                             emo="thinking"), when=[THEME_NO_SONG(PLAYER)], go="U3_bottom")
# «храбрость, бой» — и по умолчанию («не бард», «эльфы жалки», «правдиво, насколько позволит поэзия»)
S.block("U3_courage", VERSE_COURAGE, go="U3_bottom")
S.block("U3_bottom",
        narrate("At the bottom of the sheet, a line is crossed out so hard you could only read it up close.",
                "Внизу листка — строчка, зачёркнутая так, что прочесть можно только вблизи.", emo="thinking"),
        go="U3_menu")

LINE_ROMANCE = narrate("...and I think I'd follow them anywhere.", "…и, кажется, я пошла бы за {ним|ней} куда угодно.",
                       emo="thinking", shot="alfira_close")
LINE_FRIEND = narrate("...and I'm not alone anymore.", "…и я больше не одна.", emo="thinking", shot="alfira_close")
SNATCH = [narrate("She snatches the sheet away.", "Она выхватывает листок.", emo="surprise"),
          say("That's - the wine wrote that. The wine's a *liar*.", "Это… это вино написало. Вино — врун.",
              emo="fear>angry"),
          narrate("A pause.", "Пауза.", emo="thinking"),
          say("...The wine's not a liar.", "…Вино не врун.", emo="sad/1>happy", shot="alfira_close")]
for key, when in ROMANCE_GATES:
    S.block(f"U3_line_{key}", LINE_ROMANCE, *SNATCH, when=when, go=U4)
S.block("U3_line_friend", LINE_FRIEND, *SNATCH, go=U4)

S.menu("U3_menu",
       opt("Это хорошо. Правда.", "It's good. Really.", approve=+1,
           reply=[say("It's *drunk*. The metre's drunk, the rhyme's drunk, the ink is - is that wine or blood? ...Wine. "
                      "Thank the gods.",
                      "Он *пьяный*. Размер пьяный, рифма пьяная, чернила… это вино или кровь? …Вино. Слава богам.",
                      emo="disgust>fear>happy"),
                  narrate("She hides the sheet, but doesn't throw it away.", "Она прячет листок, но не выбрасывает.",
                          emo="happy")],
           go=U4),
       check("*Прочитать зачёркнутую строчку, пока она не видит.*", "*Read the crossed-out line while she isn't looking.*",
             skill="Insight", ability="Wisdom", dc=DC.Act1_Medium,
             success=outcome(approve=+1, set=[READ_LINE(PLAYER)],
                             reply=[narrate("You make out the crossed-out line.", "Ты разбираешь зачёркнутую строчку.",
                                            emo="thinking")],
                             go=[f"U3_line_{k}" for k, _ in ROMANCE_GATES] + ["U3_line_friend"]),
             failure=outcome(reply=[narrate("She hides the sheet behind her back.", "Она прячет листок за спину.",
                                            emo="surprise"),
                                    say("Nope. No. Some verses are for burning.", "Не-а. Нет. Некоторые куплеты — только в огонь.",
                                        emo="happy/2"),
                                    narrate("She doesn't burn it.", "Она его не сжигает.", emo="happy")],
                             go=U4)),
       opt("Спой его.", "Sing it.", approve=+1,
           reply=[say("Sober? Absolutely not.", "Трезвой? Ни за что.", emo="surprise>happy/2"),
                  narrate("She hums the first line anyway - off-key, and loses her place.",
                          "Она всё-таки напевает первую строчку — фальшивит и сбивается.", emo="happy>pain"),
                  say("...See? The wine was a better singer.", "…Видишь? Вино пело лучше.", emo="happy/2")],
           go=U4),
       opt("Сожги. Пьяные стихи — не стихи.", "Burn it. Drunk verses aren't verses.", approve=-1,
           reply=[narrate("She hides the sheet.", "Она прячет листок.", emo="sad"),
                  say("Lihala kept every bad draft I ever wrote. She said you have to be able to see how far you've come. "
                      "...I'm keeping it.",
                      "Лихейла хранила каждый мой плохой черновик. Говорила, что надо видеть, сколько ты прошла. …Я его оставлю.",
                      emo="sad>thinking")],
           go=U4),
       )

# --- U4. Прямой вопрос → R3 ---

ASK = say("Can I ask you something? Straight out, before I lose my nerve - and I *will* lose it, I can feel it going.",
          "Можно спрошу? Прямо, пока не струсила — а я струшу, я уже чувствую, как начинаю.", emo="fear>thinking")
DANCE = say("Last night. The dance, the - whatever I said.", "Вчера. Танец, и… что я там наговорила.", emo="thinking>happy/2")
FIRE = say("Last night. By the fire - whatever I said.", "Вчера. У костра… что я там наговорила.", emo="thinking")
REAL = say("Was any of it... real? For you? *Be honest.* I'd rather have a true \"no\" than a kind \"maybe\".",
           "В этом было хоть что-то… настоящее? Для тебя? *Скажи честно.* Лучше честное «нет», чем доброе «может быть».",
           emo="fear>thinking", shot="alfira_close")
PUSHED_LINE = say("And don't - last night you as good as handed me to Lakrissa. So if this is you being *nice*, please don't be nice.",
                  "И не надо… вчера ты практически {вручил|вручила} меня Лакриссе. Так что если ты сейчас из вежливости — "
                  "пожалуйста, не надо вежливости.", emo="sad>angry")

S.block("U4_chose", ASK, DANCE, when=ROMANCE_GATES[0][1], go=["U4_real_pushed", "U4_real"])
S.block("U4_spark", ASK, FIRE, when=ROMANCE_GATES[1][1], go=["U4_real_pushed", "U4_real"])
S.block("U4_ap40", ASK, FIRE, when=ROMANCE_GATES[2][1], go=["U4_real_pushed", "U4_real"])

# ответы на признание: одобрение 30+ — роман открыт (и её «ещё одна реплика» героя, U5), ниже — «спроси снова»
U5_OPEN = [
    opt("Ты покраснела.", "You're blushing.",
        reply=[voice("h3d30c96fg5f1cg4eaag8739gf2ca9de54cd9"),           # Oh, hush - I know you love me really.
               narrate("She realises what she said and blushes even harder.", "Она понимает, что сказала, и краснеет ещё сильнее.",
                       emo="surprise>happy/2", shot="alfira_close")],
        end=True),
    opt("Пойдём. Нас ждут.", "Come on. They're waiting.", end=True),
]
LOW = [say("I - *want* that to be true. I do. But I've known you a handful of days, and I've cried on you twice. "
           "Ask me again when I'm sure it's me and not the wine.",
           "Я *хочу*, чтобы это было правдой. Правда хочу. Но мы знакомы считаные дни, и я уже дважды плакала у тебя на "
           "плече. Спроси меня снова, когда я буду уверена, что это я, а не вино.", emo="happy>sad>thinking")]
YES = [narrate("A long silence.", "Она долго молчит.", emo="surprise", shot="alfira_close"),
       say("Oh. Oh, I - right. Okay.", "Ой. Ой, я… так. Ладно.", emo="surprise>happy"),
       narrate("She laughs and covers her face with her hands.", "Она смеётся и закрывает лицо ладонями.", emo="happy/2"),
       say("I had a whole speech for \"no\". I don't have *anything* for \"yes\".",
           "У меня была целая речь на случай «нет». На «да» у меня *ничего* нет.", emo="happy/2"),
       say("Can we - not rush? Everyone I've loved ended up in a song. I'd like to keep you out of the sad ones. For a long time.",
           "Можно мы… не будем спешить? Все, кого я любила, в итоге попали в песню. Тебя я хочу держать подальше от "
           "грустных. Очень долго.", emo="thinking>sad>happy", shot="alfira_close")]


def answer(key, yes_lines, yes_approve, low_approve):
    """Два исхода признания: 30+ — роман открыт; ниже — «спроси меня снова» (глава 8)."""
    first, *rest = yes_lines
    S.block(f"{key}_30", replace(first, approve=yes_approve), *rest, when=[AP30], set=[OPEN(PLAYER), CANDIDATE.on],
            choices=U5_OPEN)
    S.block(f"{key}_low", replace(LOW[0], approve=low_approve),
            set=[ASK_AGAIN(PLAYER), CANDIDATE.on], go="U5")
    return [f"{key}_30", f"{key}_low"]


CONFESS = answer("U4_confess", YES, +3, +1)
NERVE = answer("U4_nerve", YES, 0, 0)                  # после «я струсил(а)»: одобрение +1 у варианта, дальше — как у признания
BARD = answer("U4_bard", [say("That is the most *bard* thing anyone has ever said to me. I hate it. I love it. ...Yes. Together.",
                              "Это самое *бардовское*, что мне говорили в жизни. Ненавижу. Обожаю. …Да. Вместе.",
                              emo="surprise>happy/2>happy", shot="alfira_close")], +4, +1)
ANYWHERE = answer("U4_anywhere", [say("You *read* it. Of course you read it.", "Ты её *{прочитал|прочитала}*. Ну конечно.",
                                      emo="surprise>happy/2"),
                                  say("...Anywhere, then. But slowly.", "…Значит, куда угодно. Только не спеша.",
                                      emo="happy", shot="alfira_close", note="(тихо)")], +4, +1)

U4_MENU = [
    opt("Настоящее. Всё, до последнего шага.", "It was real. Every step of it.", when=[CHOSE_HER(PLAYER)], go=CONFESS),
    opt("Настоящее. Всё.", "It was real. All of it.", when=[~CHOSE_HER(PLAYER)], go=CONFESS),
    *gendered("Я струсил. Думал, с ней тебе будет лучше.", "Я струсила. Думала, с ней тебе будет лучше.",
              "I lost my nerve. I thought you'd be happier with her.", when=[PUSHED(PLAYER)],
              approve=+1,
              reply=[narrate("She lets out a breath.", "Она выдыхает.", emo="sad"),
                     say("...That's the stupidest, kindest thing. Don't decide what makes me happy. *Ask.*",
                         "…Это самое глупое и самое доброе, что можно было сделать. Не решай за меня, от чего я буду "
                         "счастлива. *Спрашивай.*", emo="sad>happy")],
              go=NERVE),
    *gendered("Хотел посмотреть, как ты отреагируешь.", "Хотела посмотреть, как ты отреагируешь.",
              "I wanted to see how you'd react.", when=[PUSHED(PLAYER)], approve=-2,
              set=[POSTPONED(PLAYER), CANDIDATE.on],
              reply=[narrate("She steps back.", "Она отступает на шаг.", emo="surprise>angry"),
                     say("That's a horrible reason. ...I need to think. Not now.", "Это ужасная причина. …Мне надо подумать. Не сейчас.",
                         emo="angry>sad")],
              go="U5"),
    opt("Ответ — в третьем куплете. Напишем его вместе.", "The answer's in the third verse. We'll write it together.",
        when=[T.BARD(PLAYER)], go=BARD),
    opt("«Куда угодно» — это далеко. Пойдём вместе.", "\"Anywhere\" is a long way. Let's go together.",
        when=[READ_LINE(PLAYER)], go=ANYWHERE),
    opt("Пусть дорога покажет.", "Let's see where the road takes us.", set=[POSTPONED(PLAYER), CANDIDATE.on],
        reply=[say("That's... fair. That's a very sober answer. I hate sober answers.",
                   "Это… честно. Очень трезвый ответ. Ненавижу трезвые ответы.", emo="thinking>happy/2"),
               say("All right. The road, then.", "Ладно. Значит, дорога.", emo="happy", note="(улыбается)")],
        go="U5"),
    opt("Ты мой друг. И это много.", "You're my friend. That's a lot.", approve=+2, set=[FRIEND(PLAYER)],
        go=["U4_friend_lakrissa", "U4_friend_alone"]),
    opt("Ты была пьяна. Забудем.", "You were drunk. Let's forget it.", set=[FORGET(PLAYER)],
        reply=[say("Forgotten. Completely. Already gone.", "Забыто. Совсем. Уже нет.", emo="sad>happy"),
               narrate("She folds the sheet in four, and again, and again.", "Она складывает листок вчетверо, ещё раз и ещё.",
                       emo="sad")],
        go="U5"),
    opt("Пьяные слова — трезвые сожаления. Не раздувай.", "Drunk words, sober regrets. Don't make it a thing.", approve=-2,
        reply=[narrate("She flushes - with anger, this time.", "Она краснеет — теперь от злости.", emo="angry"),
               say("I wasn't making it a *thing*. I was making it a *question*. You could've just said no.",
                   "Я не *раздуваю*. Я *спрашиваю*. {Мог|Могла} бы просто сказать «нет».", emo="angry>sad")],
        go="U5"),
]
S.block("U4_real_pushed", REAL, PUSHED_LINE, when=[PUSHED(PLAYER)], choices=U4_MENU)
S.block("U4_real", REAL, choices=U4_MENU)

S.block("U4_friend_lakrissa",
        say("Yes. It is. It's *loads*.", "Да. Много. Это *уйма*.", emo="happy>sad", note="(слишком быстро кивает)"),
        narrate("A pause.", "Пауза.", emo="thinking"),
        say("Lakrissa asked me to meet her sister. And the nephews. I think I'll say yes.",
            "Лакрисса звала познакомиться с её сестрой. И с племянниками. Кажется, я соглашусь.", emo="thinking>happy"),
        when=[LAKRISSA_HERE.on], go="U5")
S.block("U4_friend_alone",
        say("Yes. It is. It's *loads*.", "Да. Много. Это *уйма*.", emo="happy>sad", note="(слишком быстро кивает)"),
        say("...Good. Friends. I've been short on those.", "…Хорошо. Друзья. Мне их как раз не хватало.", emo="sad>happy"),
        go="U5")

# U4д. Роман невозможен — дружеская версия
S.block("U4_friendly",
        say("Can I say something? Sober, this time. What I said last night - that you're a good friend. I meant it. "
            "Since Elturel, every friend I've had was running too. ...You're not running. It's nice.",
            "Можно скажу? На этот раз трезвой. То, что я вчера сказала — что ты хороший друг. Я это всерьёз. С Элтуриэля "
            "все мои друзья тоже бежали. …А ты не бежишь. Это приятно.", emo="thinking>sad>happy"),
        choices=[
            opt("Ты тоже хороший друг.", "You're a good friend too.", approve=+2,
                reply=[say("Good. Settled. Now - breakfast? I'm told it helps. I'm told a lot of lies.",
                           "Отлично. Решено. А теперь — завтрак? Говорят, помогает. Мне много чего говорят.",
                           emo="happy/2", note="(сияет)")],
                go="U5"),
            opt("Я-то как раз бегу. От личинки.", "I am running, actually. From a tadpole.", approve=+1,
                reply=[say("Then we'll run together. I'm *very* good at it. Practically a professional.",
                           "Значит, побежим вместе. Я в этом *очень* хороша. Почти профессионал.", emo="happy/2")],
                go="U5"),
            opt("Не привыкай.", "Don't get used to it.", approve=-1,
                reply=[say("...Noted. Too late, though.", "…Учту. Только уже поздно.", emo="thinking>happy",
                           note="(но улыбка остаётся)")],
                go="U5"),
        ])

# --- U5. Конец (роман не открыт) ---

S.block("U5",
        say("Right. Water. Lots of water. And never wine again.", "Так. Вода. Много воды. И больше никакого вина.",
            emo="pain>thinking"),
        narrate("A pause.", "Пауза.", emo="thinking"),
        say("...Maybe a little wine. At the next victory.", "…Ну, может, немного. На следующей победе.", emo="happy/2"),
        end=True)
