"""Акт 1: разговоры по событиям — design/dialogs/11_act1_events.md, согласовано 2026-09-27.

Семь разговоров (С1–С7, С2 — два), каждый — отдельный диалог ALFSV_WRD_Event_*: «!» над ней через ванильную
PROC_RelationshipDialog (goal ALFSV_Talks.txt, scripts/dialogs/talks.py). Постановка — как у глав: стоя, основа
DEN_Bard_InParty. Знак «в мире или в лагере» (DB_RelationshipDialog_WRD_TriggerInCamp) и не гаснет, если отойти
(DB_ExclamationDialog_NeverStop): она узнаёт о событии, где бы ни была.

Начало — общая реплика по тону события и выбор героя: «Я слушаю, продолжай.» [решение сборки: реплика героя игры,
чтобы отказ был до разговора] или «Не сейчас.» — тогда флаг ALFSV_Talk_Postponed на ней, и Osiris ставит знак
снова (текст тот же). С2б — прощание без отказа и без выбора.
"""
from dsl import ALFIRA, PLAYER, Scene, check, new_flag, opt, outcome, say
from scenes.recruitment import SPARK
from vanilla import APPROVAL_SP1, DC, T

STATUS = "согласовано 2026-09-27"
BASE = "DEN_Bard_InParty"

# --- флаги ---
POSTPONED = new_flag("ALFSV_Talk_Postponed", "Object",
                     "Alfira's '!' talk: the hero said 'Not now' - Osiris puts the mark up again (cleared by Osiris)")
MIRKON = new_flag("ALFSV_Talk_Children_Mirkon", "Object",
                  "S4: Mirkon was saved first (set on Alfira by Osiris) - the talk starts with Mirkon, not Arabella")
LEFT_WITH_REFUGEES = new_flag("ALFSV_LeftWithRefugees", "Global",
                              "S2a: Alfira left the party with the expelled refugees (returns in act 2, Last Light)")
GATES_FAREWELL = new_flag("ALFSV_Talk_GatesFarewell", "Global",
                          "S2b: the farewell after the gates were opened has been said - she goes to the Grove")
# 🔁 на герое
VICTORY_SONG = new_flag("ALFSV_Talk_VictorySong", "Object", "S1: she will write Lihala's song about the day of victory")
NOT_GUEST = new_flag("ALFSV_Talk_NotAGuest", "Object", "S3: 'You're not a guest any more. You've got a party.'")
NAME_FUNNY = new_flag("ALFSV_Talk_StoryName_Funny", "Object", "S4: in her Balduran story the hero is 'the One Who Was Late for Supper'")
BIG_HAND = new_flag("ALFSV_Talk_StoryName_BigHand", "Object", "S4: the Big Hand who got her out of Elturel goes into the story")
TALK_KARLACH = new_flag("ALFSV_Talk_WillTalkToKarlach", "Object", "S5: she will talk to Karlach about Avernus (chapter 6)")
HEARS_VOICE = new_flag("ALFSV_Talk_HearsYourVoice", "Object", "S6: she knows the hero's voice and will hear the change first")
BLOOD_WARNED = new_flag("ALFSV_Talk_Blood_Warned", "Object", "S7: 'They deserved it' - she is still here, for now")

OSIRIS_FLAGS = [MIRKON]

LISTEN = ("h13b674acg102dg439fg88c7gec894804809f", 1)      # I'm listening. / Я слушаю, продолжай.
NOT_NOW = ("h13b3ab30ga7b6g424agb2b8g158302a8fb13", 1)     # Not now. / Не сейчас.
SAY_NOTHING = ("h0c196edcg1f18g44dfgb346g7fba4a559d72", 1)  # *Say nothing.* / *Промолчать.*

GOOD = ("Hey - hold on. Give me a moment? I need to say this before it goes stale.",
        "Эй… подожди. Можно минутку? Хочу сказать, пока не остыло.", "surprise>happy")
BAD = ("Can we stop. Just - for a moment. Please.", "Давай остановимся. Хоть… на минуту. Пожалуйста.", "sad>fear")


def gendered(ru_m, ru_f, en, when=(), **kw):
    """Реплика героя с родом по-русски — два варианта по тегу FEMALE (как в главах)."""
    return [opt(ru_m, en, when=[~T.FEMALE(PLAYER), *when], **kw),
            opt(ru_f, en, when=[T.FEMALE(PLAYER), *when], **kw)]


def event(name, dialog_id, tone, main):
    """Сцена разговора по событию: общее начало по тону, «Я слушаю» → main, «Не сейчас» → отложить."""
    s = Scene(name=name, dialog_id=dialog_id, base=BASE, status=STATUS)
    en, ru, emo = GOOD if tone == "good" else BAD
    s.greeting("open", say(en, ru, emo=emo), choices=[
        opt("Я слушаю, продолжай.", "I'm listening.", game_line=LISTEN, go=main),
        opt("Не сейчас.", "Not now.", game_line=NOT_NOW, set=[POSTPONED(ALFIRA)],
            reply=[say("Right. Of course. Later, then.", "Да. Конечно. Тогда позже.", emo="sad>happy",
                       note="(знак над ней остаётся)")], end=True),
    ])
    return s


# --- С1. «Мы выстояли» ---

C1 = event("ALFSV_WRD_Event_GroveHeld", "1cc0cfa0-7c85-4d08-a036-b3d4c84e678f", "good", "main")
C1.block("main",
         say("I hid with the little ones, you know. In the back of the hollow. I had a story ready - Balduran, the long "
             "version - and a knife I don't know how to use. I was going to use it anyway.",
             "Знаешь, я пряталась с малышами. В глубине пещеры. У меня была наготове сказка — про Балдурана, длинная — и "
             "нож, которым я не умею пользоваться. Я всё равно собиралась им воспользоваться.", emo="thinking>fear>thinking"),
         say("And now everyone's alive and laughing and I - I keep thinking Lihala should've had this. One grove. One night "
             "where nobody died.",
             "А теперь все живы, смеются, а я… всё думаю, что Лихейле это должно было достаться. Одна роща. Одна ночь, когда "
             "никто не погиб.", emo="happy>sad"),
         choices=[
             opt("Ты имеешь право радоваться.", "You're allowed to be happy.", approve=+2,
                 reply=[say("That's what she'd say. \"Emotions are to be felt, not feared.\" I just didn't think she meant "
                            "the *good* ones too.",
                            "Она бы так и сказала: «Эмоции надо проживать, а не страшиться их». Я просто не думала, что это "
                            "и про *хорошие* тоже.", emo="sad>happy", note="(смеётся сквозь слёзы)")], go="end"),
             opt("Сегодня ты была храбрее многих воинов.", "Tonight you were braver than most soldiers.",
                 when=[SPARK(PLAYER)], approve=+2,
                 reply=[say("I was *terrified*. ...But thank you. I'll pretend you said it in front of everyone.",
                            "Мне было *страшно*. …Но спасибо. Буду считать, что ты {сказал|сказала} это при всех.",
                            emo="surprise>happy/2", note="(краснеет)")], go="end"),
             opt("Какой была бы её песня об этом дне?", "What would her song about today sound like?", approve=+1,
                 set=[VICTORY_SONG(PLAYER)],
                 reply=[say("Loud. Badly danced to. She'd make the goblins the heroes of the second verse, just to annoy "
                            "everyone. ...I think I'll write it. For her.",
                            "Громкой. И под неё плохо бы танцевали. Гоблинов она бы во втором куплете сделала героями, "
                            "просто всем назло. …Пожалуй, я её напишу. Для неё.", emo="happy>thinking>happy",
                            note="(улыбается)")], go="end"),
             opt("Радоваться рано. Абсолют никуда не делся.", "It's too early to celebrate. The Absolute is still out there.",
                 reply=[say("I know. Let me have tonight, though? One night. Then we can go back to being doomed.",
                            "Знаю. Но дай мне хотя бы сегодня. Одну ночь. А потом снова будем обречены.", emo="sad>happy",
                            note="(вздыхает)")], go="end"),
             opt("Мёртвым всё равно, кто выжил.", "The dead don't care who survived.", approve=-2,
                 reply=[say("...My teacher said the dead deserve to be remembered. She never said they'd *care*. That's "
                            "the point, isn't it? We do it anyway.",
                            "…Моя наставница говорила, что усопшие заслуживают, чтобы о них помнили. Она не говорила, что им "
                            "*не всё равно*. В этом и смысл. Мы всё равно помним.", emo="surprise>sad>thinking",
                            note="(застывает)")], go="end"),
             opt("Для таких, как мы, это редкость.", "For people like us, that's rare.", when=[T.REALLY_TIEFLING(PLAYER)],
                 approve=+2,
                 reply=[say("Rare as a clean note on my lute. Let's be rare together, then.",
                            "Реже, чем чистая нота на моей лютне. Значит, будем редкостью вместе.", emo="happy/2",
                            note="(толкает плечом)")], go="end"),
         ])
C1.block("end", say("Right. I'm going to go and find the loudest tiefling in the Grove and hug them until they complain.",
                    "Так. Пойду найду самого шумного тифлинга в Роще и буду обнимать, пока не начнёт жаловаться.",
                    emo="happy>happy/2"), end=True)

# --- С2а. Тифлингов выгнали: итог по одобрению 20 (после реакции −10) ---

AP20 = APPROVAL_SP1[20](ALFIRA)
C2A = event("ALFSV_WRD_Event_RoadExpelled", "198867ca-3ab9-4f1a-b81d-994fa27a6087", "bad", "main")
C2A.block("main",
          say("They're going out on the road. Tonight. With children. On *that* road - the one with the gnolls.",
              "Они уходят на дорогу. Сегодня. С детьми. На *ту самую* дорогу — где гноллы.", emo="fear>angry"),
          say("I should be with them. I'm the only one who knows what the gnolls sound like before they -",
              "Я должна быть с ними. Я одна знаю, как кричат гноллы, прежде чем…", emo="fear>sad", note="(замолкает)"),
          choices=[
              *gendered("Я не хотел этого.", "Я не хотела этого.", "I never wanted this.",
                        reply=[say("I know. I think I know. ...That doesn't make the road any shorter.",
                                   "Знаю. Кажется, знаю. …Дорога от этого короче не станет.", emo="sad>thinking",
                                   note="(долгая пауза)")], go=["stay", "leave"]),
              opt("Иди с ними. Я пойму.", "Go with them. I'll understand.", approve=+1,
                  reply=[say("...You'd let me go. Just like that.", "…Ты бы меня {отпустил|отпустила}. Вот так просто.",
                             emo="surprise>sad", note="(смотрит на героя очень долго)")], go=["stay", "leave"]),
              opt("Останься. Ты нужна мне.", "Stay. I need you.",
                  reply=[say("Everyone needs a bard until the bard needs something. ...Sorry. That was unfair. Maybe.",
                             "Бард нужен всем, пока ему самому ничего не нужно. …Прости. Это было нечестно. Наверное.",
                             emo="angry>sad", note="(горько)")], go=["stay", "leave"]),
              opt("Они справятся без тебя.", "They'll manage without you.", approve=-2,
                  reply=[say("Lihala thought so too. About herself.", "Лихейла тоже так думала. О себе.", emo="sad>angry",
                             note="(отворачивается)")], go=["stay", "leave"]),
          ])
C2A.block("stay", say("I'll stay. Someone has to remember them properly - the names, not just the numbers. That's what bards "
                      "are for. ...Don't make me regret it.",
                      "Я останусь. Кто-то должен помнить их как следует — имена, а не только число. Для этого и нужны "
                      "барды. …Не заставляй меня пожалеть.", emo="thinking>sad"),
          when=[AP20], end=True)
C2A.block("leave", say("I can't. Not this time. If they're walking into the dark, I'm walking with them. Goodbye. ...I mean it "
                       "kindly. Mostly.",
                       "Не могу. Не в этот раз. Если они идут в темноту, я иду с ними. Прощай. …Я говорю это по-доброму. "
                       "Почти.", emo="sad>happy>sad"),
          set=[LEFT_WITH_REFUGEES.on], end=True)

# --- С2б. Ворота открыты: прощание, без выбора ---

C2B = Scene(name="ALFSV_WRD_Event_GatesOpened", dialog_id="101ef669-22d4-4503-9d62-ee778f46ae19", base=BASE, status=STATUS)
C2B.greeting("farewell",
             say("You opened the gates. I watched you do it. I don't - there isn't a song for this. There isn't a *word*.",
                 "Ты {открыл|открыла} ворота. Я видела, как ты это {сделал|сделала}. У меня нет… для такого нет песни. Нет "
                 "даже *слова*.", emo="sad>angry>sad", note="(голос дрожит, но она не плачет)"),
             say("Don't follow me.", "Не иди за мной.", emo="angry"),
             set=[GATES_FAREWELL.on], end=True)

# --- С3. «Кага» ---

C3 = event("ALFSV_WRD_Event_Kagha", "5aa81e7a-ef5f-4c96-8840-632f9f242297", "good", "main")
C3.block("main",
         say("She was working with the Shadow Druids. The whole time she was telling us to leave, she was - I thought "
             "everyone would take her side. The druids always get the benefit of the doubt. It's their grove.",
             "Она работала на круг Теней. Всё это время, пока гнала нас отсюда, она… Я думала, все встанут на её сторону. "
             "Друидам всегда верят на слово. Это их роща.", emo="angry>thinking", note="(качает головой)"),
         say("When you've been running as long as we have, you're always a guest. You wipe your feet. You say thank you. You "
             "don't argue with the host, even when the host is lying.",
             "Когда бежишь так долго, как мы, ты всегда в гостях. Вытираешь ноги. Говоришь спасибо. С хозяином не споришь, "
             "даже когда хозяин врёт.", emo="thinking>sad"),
         say("How did you know? That she was lying?", "Как ты {понял|поняла}? Что она врёт?", emo="thinking"),
         choices=[
             *gendered("Я не знал. Просто не поверил ей.", "Я не знала. Просто не поверила ей.",
                       "I didn't. I just didn't believe her.", approve=+2,
                       reply=[say("That's braver than knowing. Knowing is easy. Not believing the host - that's hard.",
                                  "Это смелее, чем знать. Знать легко. А не поверить хозяину — вот это трудно.",
                                  emo="surprise>happy", note="(улыбается)")], end=True),
             opt("Спасибо Нетти.", "Thank Nettie.", approve=+1,
                 reply=[say("I will. With a song she'll pretend to hate. ...She's the only druid who ever asked my name.",
                            "Обязательно. Песней, которую она будет делать вид, что ненавидит. …Она единственная из друидов, "
                            "кто спросил, как меня зовут.", emo="happy>thinking", note="(пауза)")], end=True),
             opt("Ты больше не гостья. У тебя есть отряд.", "You're not a guest any more. You've got a party.", approve=+2,
                 set=[NOT_GUEST(PLAYER)],
                 reply=[say("...Do I wipe my feet before I come into the tent, or-? Sorry. That was a lot. Thank you.",
                            "…А перед палаткой ноги вытирать, или…? Прости. Меня это немного выбило. Спасибо.",
                            emo="surprise>happy/2>happy", note="(моргает, смеётся)")], end=True),
             opt("Друиды тоже спасали вас. Не все они Кага.", "The druids saved you too. Not all of them are Kagha.",
                 reply=[say("I know. That's what makes it hard. You can't even hate them properly.",
                            "Знаю. Поэтому и тяжело. Их даже ненавидеть как следует не получается.", emo="sad>thinking")],
                 end=True),
         ])

# --- С4. «Сказка для малышей»: Арабелла или Миркон — кого спасли первым (флаг ставит Osiris) ---

C4 = event("ALFSV_WRD_Event_Children", "c4d68914-884b-435c-8249-f89297f4d241", "good", ["mirkon", "arabella"])
C4.block("mirkon", say("Mirkon walked straight into the harpies because the song was pretty. ...I understand that more than "
                       "I'd like to.",
                       "Миркон пошёл прямо к гарпиям, потому что песня была красивая. …Я понимаю это лучше, чем хотелось "
                       "бы.", emo="thinking>sad", note="(тихо)"),
         when=[MIRKON(ALFIRA)], go="common")
C4.block("arabella", say("Arabella. Stars. She stole a god's idol and got caught by a *snake druid*, and she's back at the Grove "
                         "sulking like it was all someone else's fault. ...I love her.",
                         "Арабелла. Звёзды. Стащила идола у бога, попалась *друиду-змее*, а теперь сидит в Роще и дуется, "
                         "будто кто-то другой виноват. …Обожаю её.", emo="surprise>happy/2>happy"),
         go="common")
C4.block("common",
         say("I wasn't much older than them when Elturel fell. Someone got me out. I don't remember who. I remember a big hand "
             "and a voice telling me a story about a dragon, so I'd stop screaming.",
             "Я была не намного старше их, когда пал Элтуриэль. Кто-то меня вывел. Не помню кто. Помню большую руку и голос, "
             "который рассказывал сказку про дракона, чтобы я перестала кричать.", emo="thinking>sad"),
         say("I'm going to put you in the Balduran story. The little ones will want a new hero. What should I call you? Not "
             "your real name - they'll follow you around forever.",
             "Я впишу тебя в сказку про Балдурана. Малышам нужен новый герой. Как тебя назвать? Только не настоящим именем — "
             "иначе они от тебя не отстанут.", emo="happy>happy/2"),
         choices=[
             opt("Назови меня Тем, Кто Опоздал к Ужину.", "Call me the One Who Was Late for Supper.", approve=+2,
                 set=[NAME_FUNNY(PLAYER)],
                 reply=[say("Perfect. Heroic *and* relatable. The children will be insufferable.",
                            "Идеально. И героически, и жизненно. Дети станут невыносимы.", emo="happy/2",
                            note="(хохочет)")], end=True),
             opt("Лучше впиши того, кто вывел тебя.", "Put in the one who got you out instead.", approve=+3,
                 set=[BIG_HAND(PLAYER)],
                 reply=[say("...The Big Hand. The Big Hand who told stories about dragons. Yes. Yes, I'll do that.",
                            "…Большая Рука. Большая Рука, которая рассказывала сказки про драконов. Да. Да, так и сделаю.",
                            emo="surprise>sad>happy", note="(замолкает, шмыгает носом)")], end=True),
             opt("Назови как хочешь. Лишь бы в твоём голосе.", "Whatever you like. As long as it's in your voice.",
                 when=[SPARK(PLAYER)], approve=+2,
                 reply=[say("That's a very unfair thing to say to a bard.", "Нечестно говорить такое барду.",
                            emo="happy/2", note="(прячет улыбку)")], end=True),
             opt("Мне не нужны сказки.", "I don't need stories.",
                 reply=[say("They're not for you. They're for the ones who can't sleep.",
                            "Они не для тебя. Они для тех, кто не может уснуть.", emo="thinking",
                            note="(пожимает плечами)")], end=True),
         ])

# --- С5. «Карлах» ---

C5 = event("ALFSV_WRD_Event_Karlach", "aa3e67b0-dee8-4e64-b7ce-1947a50cbfc4", "good", "main")
C5.block("main",
         say("She fought for Zariel. *Zariel.* The one who pulled my city into the Hells. And she's - she's lovely. She "
             "laughed at my joke about the horns. Nobody laughs at that joke.",
             "Она воевала за Зариэль. *Зариэль.* За ту, что утащила мой город в ад. А она… она чудесная. Смеялась над моей "
             "шуткой про рога. Над этой шуткой никто не смеётся.", emo="angry>surprise>happy"),
         say("For a moment, when she said it, I wanted to hate her. Just for a moment. And then I thought - that's exactly "
             "what Elturel did to us.",
             "На миг, когда она это сказала, мне захотелось её возненавидеть. Всего на миг. А потом я подумала: именно так "
             "Элтуриэль поступил с нами.", emo="angry>thinking>sad"),
         choices=[
             opt("Её забрали против воли. Как и вас.", "She was taken against her will. Like you were.", approve=+2,
                 reply=[say("I know. I just needed to hear someone else say it.",
                            "Знаю. Мне просто нужно было услышать это от кого-то ещё.", emo="sad>happy",
                            note="(выдыхает)")], end=True),
             opt("Ты могла бы ей злиться. Имеешь право.", "You could be angry with her. You'd have every right.", approve=+1,
                 reply=[say("I've got plenty of angry saved up. I'd rather spend it on someone who deserves it.",
                            "Злости у меня запасено много. Лучше потратить её на того, кто заслужил.", emo="sad>happy",
                            note="(невесело улыбается)")], end=True),
             opt("Спроси её про Аверно. Ей, наверное, тоже нужно выговориться.",
                 "Ask her about Avernus. She probably needs to talk too.", approve=+2, set=[TALK_KARLACH(PLAYER)],
                 reply=[say("You think so? ...Two runaways from the same fire. That's a duet, isn't it. A horrible one.",
                            "Думаешь? …Две беглянки из одного огня. Это же дуэт. Жуткий.", emo="surprise>thinking>happy",
                            note="(задумывается)")], end=True),
             *gendered("Дьяволы есть дьяволы. Я бы ей не доверял.", "Дьяволы есть дьяволы. Я бы ей не доверяла.",
                       "Devils are devils. I wouldn't trust her.", approve=-2,
                       reply=[say("She's not a devil. She's someone who *got away* from them. There's a difference. I'd know.",
                                  "Она не дьявол. Она та, кто *сбежала* от них. Это разные вещи. Уж я-то знаю.",
                                  emo="angry", note="(жёстко)")], end=True),
         ])

# --- С6. «Голос» ---

C6 = event("ALFSV_WRD_Event_Tadpole", "b2d25c91-3df4-4828-ba15-cf5a251257d6", "bad", "main")
C6.block("main",
         say("So there's a worm in your head. And it's going to turn you into one of those - squid people. And you've known "
             "this the entire time I've been making jokes about squirrels.",
             "Значит, у тебя в голове червяк. И он превратит тебя в одного из этих… кальмаролюдей. И ты {знал|знала} это всё "
             "время, пока я шутила про белок.", emo="happy>fear>angry", note="(старается говорить легко, не выходит)"),
         choices=[
             *gendered("Я не хотел тебя пугать.", "Я не хотела тебя пугать.", "I didn't want to scare you.", approve=+1,
                       reply=[say("Too late. ...Thank you for not wanting to, though.",
                                  "Поздно. …Но спасибо, что не {хотел|хотела}.", emo="fear>sad>happy", note="(пауза)")],
                       end=True),
             opt("Если я начну меняться — уходи.", "If I start to change - leave.", approve=+2, set=[HEARS_VOICE(PLAYER)],
                 reply=[say("No. I'm a bard. I know your voice now - how you say \"rest\" when you're tired, how you breathe "
                            "before a lie. If something starts to change, I'll hear it before you do. And then I'll be *very* "
                            "loud about it.",
                            "Нет. Я бард. Я уже знаю твой голос — как ты говоришь «отдых», когда {устал|устала}, как "
                            "вдыхаешь перед враньём. Если что-то начнёт меняться, я услышу раньше тебя. И тогда буду "
                            "*очень* громкой.", emo="angry>thinking>happy", note="(сразу)")], end=True),
             *gendered("Тогда пой мне почаще. Чтобы я помнил, кто я.", "Тогда пой мне почаще. Чтобы я помнила, кто я.",
                       "Then sing to me more often. So I remember who I am.", when=[SPARK(PLAYER)], approve=+2,
                       reply=[say("...That's the best request I've ever had. Every night, then. Even the bad songs.",
                                  "…Лучшая просьба в моей жизни. Тогда каждый вечер. Даже плохие песни.",
                                  emo="surprise>happy", note="(тихо)")], end=True),
             check("*Она шутит слишком быстро.*", "*She's joking too fast.*", skill="Insight", ability="Wisdom",
                   dc=DC.Act1_Medium,
                   success=outcome(approve=+1, reply=[
                       say("...I just got people back. Lihala's gone, the Grove nearly - and now you. Don't you *dare* turn "
                           "into a squid.",
                           "…Я только-только снова обрела людей. Лихейлы нет, Роща чуть не… — а теперь ты. Только *попробуй* "
                           "стать кальмаром.", emo="sad>fear>angry")], end=True),
                   failure=outcome(reply=[say("I'm fine! Squid. Fine. Totally normal day.",
                                              "Я в порядке! Кальмар. Нормально. Обычный денёк.", emo="happy/2>fear")],
                                   end=True)),
             opt("Это не твоя забота.", "It's not your concern.", approve=-1,
                 reply=[say("You're in my songs. That makes it my concern. Those are the rules.",
                            "Ты в моих песнях. Значит, моя забота. Таковы правила.", emo="angry>thinking")], end=True),
         ])

# --- С7. «Кровь»: только первый убитый тифлинг ---

C7 = event("ALFSV_WRD_Event_Blood", "09f9a65a-0062-4a0c-951b-7319ab8b8f61", "bad", "main")
C7.block("main",
         say("Explain it to me. Slowly. Because I'd like very much to be wrong about what I heard.",
             "Объясни мне. Медленно. Потому что мне очень хочется ошибиться в том, что я услышала.", emo="angry",
             note="(без привычной улыбки)"),
         choices=[
             *gendered("Они напали первыми. Я защищался.", "Они напали первыми. Я защищалась.",
                       "They attacked first. I defended myself.", approve=+2,
                       reply=[say("...Then I'll mourn them, and I won't blame you. But I'll ask them. When I can. And if the "
                                  "story's different-",
                                  "…Тогда я буду их оплакивать, а тебя винить не стану. Но я спрошу у них. Когда смогу. И "
                                  "если окажется иначе…", emo="sad>thinking>angry", note="(долго молчит)")], end=True),
             opt("Это вышло случайно.", "It was an accident.",
                 reply=[say("An accident. Accidents are what happen to people who aren't careful with other people. Be careful.",
                            "Случайно. Случайности бывают у тех, кто неосторожен с другими. Будь осторожнее.", emo="angry",
                            note="(ровно)")], end=True),
             opt("Они это заслужили.", "They deserved it.", approve=-3, set=[BLOOD_WARNED(PLAYER)],
                 reply=[say("Nobody in that Grove deserved anything but a roof. I'm still here. For now. Don't mistake that "
                            "for agreement.",
                            "Никто в этой Роще не заслуживал ничего, кроме крыши над головой. Я ещё здесь. Пока. Не путай "
                            "это с согласием.", emo="angry>disgust", note="(отступает на шаг)")], end=True),
             opt("Промолчать.", "Say nothing.", game_line=SAY_NOTHING, approve=-1,
                 reply=[say("...Right.", "…Ясно.", emo="sad>angry", note="(уходит к краю лагеря и садится спиной ко всем)")],
                 end=True),
         ])

SCENE = C1
EXTRA_SCENES = [C2A, C2B, C3, C4, C5, C6, C7]
# ключ разговора (goal ALFSV_Talks.txt, DB_ALFSV_Talk) → сцена; ключи не менять: по ним «уже было» в сохранениях
TALKS = {"GroveHeld": C1, "RoadExpelled": C2A, "GatesOpened": C2B, "Kagha": C3, "Children": C4, "Karlach": C5,
         "Tadpole": C6, "Blood": C7}
