"""Акт 1: локальные разговоры — design/dialogs/12_act1_local.md, согласовано 2026-09-27.

  * «!» над ней (Л1, Л5–Л8) — отдельные диалоги ALFSV_WRD_Local_*, ванильная PROC_RelationshipDialog: знак только
    в мире, гаснет, если отойти дальше 30 м (как у WRD Larian). Основа DEN_Bard_InParty, стоя.
  * Сцена перед диалогом NPC (Л2–Л4) — Origin Moment (COM) по тегу ALFIRA на диалоги Ашарака, Лакриссы и Даммона
    (PROC_DefineSingleOriginMoment, goal ALFSV_Talks.txt). Сцена на троих: основа HAV_AlfiraTale_ReunionWithFlirty
    (0 — NPC, 1 — Альфира, 2 — герой: так ванильный COM раздаёт спикеров), у Ашарака и Даммона их uuid встаёт на
    место Лакриссы (Scene.other_base). Реплики NPC — say(..., speaker=OTHER): свой handle, в личной сборке —
    клон его голоса. Даммон при Карлах в отряде — тот же диалог через «!» после его разговора (talks.py).
  * Реплики над головой К1–К15 — места конвейера этапа 5 (ads.place), запуск — goal ALFSV_Talks.txt (custom="talk")
    или глобальный флаг игры (flags).
"""
from ads import place, variant
from dsl import ALFIRA, OTHER, PLAYER, Scene, check, narrate, new_flag, opt, outcome, say, voice
from scenes.events import SAY_NOTHING, STATUS, gendered
from scenes.recruitment import SPARK
from vanilla import DC, LAKRISSA

BASE = "DEN_Bard_InParty"
TRIO = "HAV_AlfiraTale_ReunionWithFlirty"        # спикеры: 0 Лакрисса, 1 Альфира, 2 герой
ASHARAK = "02025646-347a-4235-aef7-e46b7c94b435"  # S_DEN_Trainer — Ашарак, учит детей деревянным мечам
DAMMON = "e2ad06ec-8034-479a-9f69-b86faea6dc79"   # S_DEN_Weaponsmith — Даммон

# 🔁 на герое
ON_MAP = new_flag("ALFSV_Talk_LihalaOnMap", "Object", "L1: Lihala's name is on Zevlor's map")
NOTICED_LAKRISSA = new_flag("ALFSV_Talk_NoticedLakrissa", "Object", "L3: the hero noticed she likes Lakrissa")
LIHALA_PHRASE = new_flag("ALFSV_Talk_LihalaPhrase", "Object", "L5: she played Lihala's unfinished phrase")
FOUND_NOTE = new_flag("ALFSV_Talk_FoundTheNote", "Object", "L5: the hero found the note after Lihala's phrase (Performance)")
SING_FOR_ROOM = new_flag("ALFSV_Talk_SingForTheRoom", "Object", "L8: 'Sing for the room you're in'")


def S(en, ru, **kw):
    return say(en, ru, speaker=OTHER, **kw)


# --- Л1. Карта Зевлора ---

L1 = Scene(name="ALFSV_WRD_Local_ZevlorMap", dialog_id="92ebdc2b-f65a-444a-aa29-de9991d059cd", base=BASE, status=STATUS)
L1.greeting("G",
            say("Zevlor's map. That's us. Every camp is a little ink dot. Some of the dots have names next to them. Those "
                "are the ones we buried.",
                "Карта Зевлора. Это мы. Каждый лагерь — точка чернилами. У некоторых точек подписаны имена. Это те, кого "
                "мы похоронили.", emo="thinking>sad", note="(проводит пальцем по линии)"),
            say("...There's no dot here. We didn't stop. We ran.", "…А здесь точки нет. Мы не остановились. Мы бежали.",
                emo="sad", note="(палец останавливается)"),
            choices=[
                opt("Здесь погибла Лихейла?", "Is that where Lihala died?", approve=+1,
                    reply=[say("Nobody wrote her name. There wasn't time. ...Would it be terrible if I did? It's not my map.",
                               "Никто не написал её имя. Не было времени. …Будет ужасно, если я напишу? Это не моя карта.",
                               emo="sad>thinking", note="(кивает, достаёт уголёк)")], go="NAME"),
                opt("Нарисуй точку. Она заслужила.", "Draw the dot. She earned one.", approve=+3, go="DRAW"),
                opt("Зачем смотреть назад? Лучше смотри, куда идём.", "Why look back? Look where we're going.",
                    reply=[say("Where we're going is the same line, just further. You can't read a road from one end.",
                               "Туда, куда мы идём, ведёт та же линия, только дальше. Дорогу с одного конца не прочитать.",
                               emo="thinking", note="(пожимает плечами)")], end=True),
                opt("Нарисуй ещё одну точку. Здесь. Где мы встретились.", "Draw one more. Here. Where we met.",
                    when=[SPARK(PLAYER)], approve=+2,
                    reply=[say("That's not how maps work. ...Don't tell Zevlor.", "Карты так не работают. …Только Зевлору не говори.",
                               emo="happy/2", note="(смеётся, тихо; всё равно рисует — крошечную, с краю)")], end=True),
            ])
L1.block("DRAW", say("There. Lihala. Now she's on the map. Zevlor will shout at me. Worth it.",
                     "Вот. Лихейла. Теперь она на карте. Зевлор будет орать. Оно того стоит.", emo="thinking>happy",
                     note="(рисует точку и подписывает — медленно, аккуратно)"),
         set=[ON_MAP(PLAYER)], end=True)
L1.menu("NAME",
        opt("Напиши.", "Write it.", approve=+2, go="DRAW"),
        opt("Спроси сначала Зевлора.", "Ask Zevlor first.", approve=+1,
            reply=[say("You're right. He'll say yes. He'll pretend it was his idea. Fine.",
                       "Ты {прав|права}. Он скажет «да» и сделает вид, что сам придумал. Ладно.", emo="thinking>happy",
                       note="(улыбается)")], end=True))

# --- Л2. Ашарак и деревянные мечи (сцена перед его диалогом) ---

L2 = Scene(name="ALFSV_OM_Local_Asharak", dialog_id="154c85d2-9e41-4ab0-9c48-67a47cd4044a", base=TRIO,
           other=ASHARAK, other_name="Ашарак", other_base=LAKRISSA, status=STATUS)
L2.greeting("G",
            say("Asharak. They're *seven*.", "Ашарак. Им *семь*.", emo="angry>sad"),
            S("And the gnolls don't ask their age. Stand straighter, you at the back - no, the *other* straight.",
              "А гноллы про возраст не спрашивают. Выпрямись, ты, сзади… нет, в *другую* сторону.", emo="angry"),
            say("He's right. That's the worst part. When I was their age I learned the lute. They're learning where the heart "
                "is on a goblin.",
                "Он прав. Это хуже всего. В их возрасте я училась играть на лютне. А они учатся, где у гоблина сердце.",
                emo="sad>thinking", shot="alfira_close", note="(герою, тише)"),
            choices=[
                opt("Научи их и музыке. Пусть будет и то и другое.", "Teach them music too. Let them have both.", approve=+2,
                    reply=[say("After drills. Everyone's too tired to argue after drills. ...Asharak, you're getting a "
                               "percussion section.",
                               "После тренировки. После тренировки все слишком устали, чтобы спорить. …Ашарак, у тебя будут "
                               "барабанщики.", emo="surprise>happy/2", note="(загорается)")], end=True),
                opt("Умение драться спасёт им жизнь.", "Knowing how to fight will save their lives.",
                    reply=[say("I know. I just want them to have something that isn't about surviving.",
                               "Знаю. Просто хочу, чтобы у них было хоть что-то не про выживание.", emo="sad",
                               note="(вздыхает)")], end=True),
                opt("Покажи им, как ты держала нож в убежище.", "Show them how you held the knife in the hollow.", approve=+1,
                    reply=[say("Upside down? That's a lesson in what *not* to do. ...Actually, that's a good lesson.",
                               "Вверх ногами? Это урок, как *не* надо. …А вообще, урок хороший.", emo="happy/2>thinking",
                               note="(смеётся)")], end=True),
            ])

# --- Л3. Лакрисса на посту (до праздника, один раз) ---

L3 = Scene(name="ALFSV_OM_Local_Lakrissa", dialog_id="5858cd09-6f15-4c79-8092-f058a464ac10", base=TRIO,
           other=LAKRISSA, other_name="Лакрисса", status=STATUS)
L3.greeting("G",
            S("Well. The bard's found herself a bodyguard.", "Смотри-ка. Бард нашла себе телохранителя.", emo="happy/2"),
            say("Travelling companion. We're - it's a professional arrangement. Why did I say it like that.",
                "Попутчика. У нас… это деловое соглашение. …Зачем я так сказала?", emo="surprise>happy>fear",
                note="(слишком быстро; герою, шёпотом)"),
            choices=[
                opt("Она тебе нравится.", "You like her.", approve=+1, set=[NOTICED_LAKRISSA(PLAYER)],
                    reply=[say("She has a *spear*. I like the spear. It's a - nice spear.",
                               "У неё *копьё*. Мне нравится копьё. Хорошее… копьё.", emo="surprise>happy/2",
                               shot="alfira_close", note="(краснеет до кончиков рогов)")], end=True),
                *gendered("Профессиональное? А я-то думал…", "Профессиональное? А я-то думала…",
                          "Professional? And there I was thinking...", when=[SPARK(PLAYER)], approve=+1,
                          reply=[say("...I'm going to stop talking now. For the rest of the day.",
                                     "…Я сейчас замолчу. До конца дня.", emo="surprise>happy/2",
                                     note="(смотрит то на героя, то на Лакриссу)")], end=True),
                opt("Промолчать.", "Say nothing.", game_line=SAY_NOTHING,
                    reply=[say("Thank you for not saying anything. Whatever you were about to say.",
                               "Спасибо, что ничего не {сказал|сказала}. Что бы ты там ни {собирался|собиралась} сказать.",
                               emo="happy", note="(выдыхает)")], end=True),
            ])

# --- Л4. Даммон и Аверно ---

HAND = ("h91276cf3g2153g4c9fgbcd4g7b75eb9936bd", 1)    # *Place your hand on her shoulder.* / *Опустить руку ей на плечо.*
L4 = Scene(name="ALFSV_OM_Local_Dammon", dialog_id="f5c9b87d-667d-4938-9309-9a12c77f9c91", base=TRIO,
           other=DAMMON, other_name="Даммон", other_base=LAKRISSA, status=STATUS)
L4.greeting("G",
            say("Dammon - can I ask you something? You were there. In Avernus. After the city fell. Is it true the sky doesn't "
                "have a colour, just a temperature?",
                "Даммон, можно спросить? Ты там был. В Аверно. После Падения. Правда, что у неба там нет цвета, только "
                "температура?", emo="thinking>fear"),
            S("It's true. Why?", "Правда. А что?", emo="sad", note="(долгая пауза)"),
            say("My mother's there. Somewhere. I wanted to know what she's looking at.",
                "Там моя мама. Где-то. Хотела знать, на что она смотрит.", emo="sad", shot="alfira_close"),
            choices=[
                opt("Опустить руку ей на плечо.", "Place your hand on her shoulder.", game_line=HAND, approve=+2,
                    reply=[say("...Thanks. I'm fine. Dammon, sorry. Go on - they need their swords.",
                               "…Спасибо. Я в порядке. Даммон, прости. Продолжай — им нужны мечи.", emo="sad>happy",
                               note="(накрывает руку своей)")], end=True),
                opt("Может, она давно не там.", "Maybe she's not there any more.", approve=+1,
                    reply=[say("Maybe. I like that version better. I'll keep it.",
                               "Может быть. Мне эта версия больше нравится. Оставлю её.", emo="thinking>happy",
                               note="(кивает)")], end=True),
                opt("Зачем бередить?", "Why pick at it?",
                    reply=[say("Because nobody else ever answers. He did.", "Потому что больше никто не отвечает. А он ответил.",
                               emo="sad", note="(тихо)")], end=True),
            ])

# --- Л5. Стая гноллов ---

L5 = Scene(name="ALFSV_WRD_Local_Gnolls", dialog_id="500b4d1f-d161-40d6-9456-2fad81c04985", base=BASE,
           voice_from=["DEN_TieflingBard_Bard"], status=STATUS)
L5.greeting("G",
            narrate("She stands over the gnoll's body longer than she needs to.",
                    "Она стоит над телом гнолла дольше, чем нужно.", emo="sad"),
            say("I used to think they'd be bigger. In my head they're the size of houses. They're just... animals. Hungry, "
                "stupid animals. That's worse, somehow.",
                "Мне казалось, они больше. В голове они размером с дом. А они просто… звери. Голодные, тупые звери. "
                "Почему-то от этого только хуже.", emo="thinking>angry>sad", note="(пинает камень)"),
            voice("h09f7a033g8dd7g495bg8b17gdff23f0b8822"),          # There was so much blood. I - I can still smell it.
            say("She was playing. That's why we didn't hear them. She was in the middle of a phrase, and she never - she never "
                "finished it. I've tried to finish it for her. I can't find the note.",
                "Она играла. Поэтому мы их и не услышали. Она была на середине фразы и так и не… так и не доиграла её. Я "
                "пыталась доиграть за неё. Не могу найти ноту.", emo="sad>fear>sad", shot="alfira_close"),
            choices=[
                opt("Сыграй её сейчас. Здесь.", "Play it now. Here.", approve=+3, set=[LIHALA_PHRASE(PLAYER)],
                    reply=[say("...There. That's where. Maybe it doesn't have an end. Maybe that's the end.",
                               "…Вот. Вот тут. Может, у неё нет конца. Может, это и есть конец.", emo="sad>thinking",
                               note="(достаёт лютню, играет обрывок — и замирает там, где оборвалось; тише)")], end=True),
                check("*Подобрать ноту после её обрывка.*", "*Find the note after her phrase.*", skill="Performance",
                      ability="Charisma", dc=DC.Act1_Challenging,
                      success=outcome(approve=+3, set=[FOUND_NOTE(PLAYER)], reply=[
                          say("...That's it. That's - how did you - That's *it*.", "…Она. Это она… как ты… Это *она*.",
                              emo="surprise>happy/2>sad", note="(смотрит широко открытыми глазами; смеётся и плачет разом)")],
                                      end=True),
                      failure=outcome(approve=+1, reply=[
                          say("Close. She'd have said close. She'd have made you play it till your fingers bled.",
                              "Близко. Она бы сказала «близко». И заставила бы играть, пока пальцы не сотрёшь.",
                              emo="sad>happy", note="(улыбается сквозь слёзы)")], end=True)),
                opt("Они больше никого не тронут.", "They won't hurt anyone again.", approve=+1,
                    reply=[say("These ones won't. There are always more of them. That's what she used to say about songs, too.",
                               "Эти — нет. Их всегда больше. Лихейла так же говорила про песни.", emo="thinking>sad",
                               note="(смотрит на дорогу)")], end=True),
                opt("Ты не одна.", "You're not alone.", when=[SPARK(PLAYER)], approve=+2,
                    reply=[say("...I know. That's the first time I've believed it out here.",
                               "…Знаю. Здесь, на дороге, я верю в это впервые.", emo="sad>happy", note="(закрывает глаза)")],
                    end=True),
                opt("Это просто звери. Пошли.", "They're just animals. Let's go.", approve=-1,
                    reply=[say("Yes. Just animals.", "Да. Просто звери.", emo="sad",
                               note="(отступает от тела; идёт, не оглядываясь)")], end=True),
            ])

# --- Л6. «Беженцы» в Таможне ---

L6 = Scene(name="ALFSV_WRD_Local_Tollhouse", dialog_id="19b3079b-058c-4c55-9e5b-85c5307d1659", base=BASE, status=STATUS)
L6.greeting("G",
            say("They were wearing *us*. Our story. \"Poor refugees, fleeing the Hells\" - and they *worship* the thing that "
                "put us there.",
                "Они надели *нас*. Нашу историю. «Несчастные беженцы, бегут из ада» — а сами *поклоняются* той, кто нас туда "
                "отправила.", emo="angry"),
            say("Do you know how long it took to get anyone to open a door for us? And now the next real refugee who knocks - "
                "they'll remember *this*.",
                "Знаешь, сколько времени нам понадобилось, чтобы кто-то открыл нам дверь? А теперь следующему настоящему "
                "беженцу, который постучит, припомнят *это*.", emo="angry>sad"),
            choices=[
                opt("Правда всё равно выйдет наружу.", "The truth will come out anyway.", approve=+1,
                    reply=[say("Truth's slow. Rumour has a horse. ...Then we'd better be louder than them.",
                               "Правда медленная. А у слухов лошадь. …Значит, нам надо быть громче них.", emo="thinking>happy",
                               note="(выдыхает)")], end=True),
                opt("Ты злишься. Это хорошо.", "You're angry. That's good.", approve=+2,
                    reply=[say("Is it? I thought I'd run out of angry. Apparently I keep a spare.",
                               "Правда? Я думала, злость у меня кончилась. Оказывается, есть запасная.",
                               emo="surprise>happy/2")], end=True),
                opt("Сложи о них песню. Такую, чтоб их узнавали.", "Write a song about them. One that gets them recognised.",
                    approve=+2,
                    reply=[say("Oh, I'll write them a song. A *catchy* one.", "О, я им песню напишу. *Прилипчивую*.",
                               emo="happy/2", note="(медленно улыбается — нехорошо)")], end=True),
                opt("Все прячутся за чужой историей. Бывает.", "Everyone hides behind someone else's story. It happens.",
                    approve=-2,
                    reply=[say("Not *mine*.", "Только не за *моей*.", emo="angry", note="(холодно)")], end=True),
            ])

# --- Л7. Разорённый лагерь у болота ---

L7 = Scene(name="ALFSV_WRD_Local_Campsite", dialog_id="d14d576b-cd22-4b09-b2f7-789668649f96", base=BASE, status=STATUS)
L7.greeting("G",
            say("After Lihala, I went back. The next morning. Everyone said don't. I went anyway, to pick up her things. The "
                "gnolls don't take things. They just - leave them.",
                "После Лихейлы я вернулась. Наутро. Все говорили — не надо. А я всё равно пошла, собрать её вещи. Гноллы "
                "вещей не берут. Они просто… оставляют.", emo="sad>thinking",
                note="(поднимает детский башмак, кладёт аккуратно на ящик)"),
            say("I found the lute. And one shoe. I still don't know what happened to the other shoe. Isn't that stupid? That's "
                "the thing I think about.",
                "Я нашла лютню. И одну туфлю. До сих пор не знаю, куда делась вторая. Глупо, правда? Вот о чём я думаю.",
                emo="sad>happy>sad"),
            choices=[
                opt("Не глупо. Так горе и выглядит.", "It's not stupid. That's what grief looks like.", approve=+2,
                    reply=[say("Shoe-shaped. Yes. I suppose it is.", "В форме туфли. Да. Наверное.", emo="sad>happy",
                               note="(слабо улыбается)")], end=True),
                opt("Давай похороним то, что осталось.", "Let's bury what's left.", approve=+3,
                    reply=[say("I'll sing. Not well. The dead deserve to be remembered - even the ones whose names we'll "
                               "never know.",
                               "Я спою. Не очень хорошо. Усопшие заслуживают, чтобы о них помнили — даже те, чьих имён мы не "
                               "узнаем.", emo="sad>thinking", note="(кивает)")], end=True),
                opt("Нам некогда. Здесь опасно.", "We don't have time. It's dangerous here.", approve=-1,
                    reply=[say("Right. Of course. Right.", "Да. Конечно. Да.", emo="sad",
                               note="(кладёт башмак на место)")], end=True),
            ])

# --- Л8. Воло поёт гоблинам (после К10) ---

L8 = Scene(name="ALFSV_WRD_Local_Volo", dialog_id="f3914786-316d-411f-9f9f-a74581ba7de3", base=BASE, status=STATUS)
L8.greeting("G",
            say("He's rhyming \"goblin\" with \"hobblin'\". In front of *goblins*. And they're *clapping*.",
                "Он рифмует «гоблин» с «гоблин-то хромой». Перед *гоблинами*. И они *хлопают*.", emo="surprise>angry"),
            say("I spent a year on one verse. He made that up on the way to the stage. I hate him. I want to learn everything "
                "he knows.",
                "Я год сидела над одним куплетом. А он это придумал по дороге на сцену. Ненавижу его. Хочу узнать всё, что он "
                "знает.", emo="angry>happy/2", note="(хватается за голову)"),
            choices=[
                opt("Ты поёшь лучше. Он просто громче.", "You sing better. He's just louder.", approve=+2,
                    reply=[say("Say that again, but slower, so I can remember the exact words.",
                               "Повтори, только медленнее, чтобы я запомнила слово в слово.", emo="happy/2",
                               note="(светится)")], end=True),
                opt("Он поёт, чтобы остаться в живых. Это тоже искусство.", "He sings to stay alive. That's an art too.",
                    approve=+2, set=[SING_FOR_ROOM(PLAYER)],
                    reply=[say("...Lihala said the same about taverns. \"Sing for the room you're in.\" He's singing for a "
                               "room full of knives.",
                               "…Лихейла так же говорила про таверны: «Пой для той комнаты, в которой стоишь». А он поёт для "
                               "комнаты, полной ножей.", emo="thinking", note="(задумывается)")], end=True),
                opt("Хочешь выйти на сцену после него?", "Want to go on after him?", approve=+1,
                    reply=[say("In a *goblin* camp? ...No. Maybe. *No.* Ask me again if we survive this.",
                               "В лагере *гоблинов*? …Нет. Может быть. *Нет.* Спроси ещё раз, если мы выживем.",
                               emo="surprise>thinking>fear", note="(смотрит на сцену… и ещё раз)")], end=True),
                opt("Бездарь.", "Hack.",
                    reply=[say("He's a hack who's *alive*. I'd like to be one of those.",
                               "Он бездарь, который *жив*. Я бы тоже хотела быть такой.", emo="sad>happy")], end=True),
            ])

SCENE = L1
EXTRA_SCENES = [L2, L3, L4, L5, L6, L7, L8]
TALKS = {"ZevlorMap": L1, "Gnolls": L5, "Tollhouse": L6, "Campsite": L7, "Volo": L8, "Dammon": L4}
OMS = {"Asharak": L2, "Lakrissa": L3, "Dammon": L4}

# --- К1–К15: реплики над головой (ads.place). Ключи не менять: по ним «уже сказано» в сохранениях. ---

G1 = "Gustav/Mods/Gustav/Story/RawFiles/Goals/"
GD = "Gustav/Mods/GustavDev/Story/RawFiles/Goals/"
HF = "Patch8_HotFix9/Mods/Gustav/Story/RawFiles/Goals/"

PLACES = [
    place("Talk_K01_Gnolls", "К1. Первая встреча с гноллами",
          variant(say("Gnolls. Don't let them get behind us. Please.", "Гноллы. Не давай им зайти сзади. Пожалуйста.",
                      emo="fear", note="(шёпотом)")),
          act=1, flags=["PLA_ConflictedFlind_Knows_Gnolls_c353a7d3-7561-05dc-c725-32e363ce6bf3"],
          source=G1 + "Act1_PLA_ConflictedFlind.txt:1195-1231 (зона наблюдения за стаей или первый бой с ней)"),
    place("Talk_K02_Hyena", "К2. Гиена бежит звать стаю (в бою)",
          variant(say("It's calling the others - stop it, *stop it!*", "Она зовёт остальных — останови её, *останови!*",
                      emo="fear>angry")),
          act=1, custom="talk", source=G1 + "Act1_PLA_DyingHyenas.txt:409 (VoiceBarkStarted PLA_DyingHyena_VB_HyenaRunning)"),
    place("Talk_K03_DeadGnolls", "К3. Мёртвые гноллы у Таможни",
          variant(say("Someone did our work for us. ...I hope it hurt.", "Кто-то сделал за нас нашу работу. …Надеюсь, им было больно.",
                      emo="thinking>angry")),
          act=1, flags=["PLA_KarlachRecruitmentTollhouse_Knows_GnollsDead_9dab2061-e12d-435e-99f0-d9dbe075813d"],
          source=G1 + "Act1_PLA_KarlachRecruitment.txt:389-398"),
    place("Talk_K04_Gruel", "К4. Каша Окты",
          variant(say("Okta's gruel. It's the flavour of home. Home was also terrible.",
                      "Каша Окты. Вкус дома. Дома тоже было ужасно.", emo="happy>disgust>happy/2")),
          act=1, custom="talk", source=GD + "Act1_OriginMoments_Karlach.txt:603-624 (PROC_FlagReactionAfterDialog TookGruel)"),
    place("Talk_K05_Ritual", "К5. Ритуал у Священного пруда",
          variant(say("They're going to close the Grove? With us *inside* or *outside*? ...Don't answer.",
                      "Они закроют Рощу? С нами *внутри* или *снаружи*? …Не отвечай.", emo="surprise>fear")),
          act=1, custom="talk", source=HF + "Act1_DEN_SacredPond.txt:268-281 (DialogEnded DB_DEN_RitualDialogs)"),
    place("Talk_K06_KidsGame", "К6. Дети играют на полу в деревне",
          variant(say("We played that in Elturel. With chalk. The rules were different, and I always lost.",
                      "Мы в Элтуриэле в это играли. Мелом. Правила были другие, и я всегда проигрывала.",
                      emo="happy>sad>happy")),
          act=1, custom="talk", source=G1 + "Act1_FOR_Misc.txt:7 (VoiceBarkEnded FOR_KidsGame_VB) [вымысел в деталях]"),
    place("Talk_K07_HoleBook", "К7. Вино в пустой книге",
          variant(say("Wine in a book. My teacher would've confiscated both.", "Вино в книге. Наставница отобрала бы и то, и другое.",
                      emo="surprise>happy/2")),
          act=1, custom="talk", source=G1 + "Act1_FOR_Boosters.txt:733-741 (UseStarted S_FOR_HoleBook)"),
    place("Talk_K08_DangerousBook", "К8. Опасная книга уничтожена",
          variant(say("Good. In the old stories the villain with the evil book is always a tiefling. One fewer book.",
                      "Хорошо. В старых сказках злодей со злой книгой — всегда тифлинг. Одной книгой меньше.",
                      emo="angry>happy")),
          act=1, custom="talk", source=G1 + "FOR_DangerousBook.txt:145-165 (DestroyedBy S_FOR_DangerousBook_Tome)"),
    place("Talk_K09_GoblinGate", "К9. Лагерь гоблинов, вход",
          variant(say("Everyone smile. Smile like we're *invited*. I'm smiling. Am I smiling?",
                      "Все улыбаемся. Улыбаемся, будто нас *пригласили*. Я улыбаюсь. Я улыбаюсь?", emo="fear>happy/2")),
          act=1, flags=["GLO_GoblinHunt_Quest_CampEntered_58d47a99-0e37-4fe8-a5ff-d47f069a3886"],
          source=G1 + "Act1_GOB_Checkpoint.txt:118-128 (первый вход на пост у ворот лагеря)"),
    place("Talk_K10_Volo", "К10. Воло на сцене у гоблинов (перед Л8)",
          variant(say("Is that - is that *Volo*? Oh no. Oh, he's *good*.", "Это… это *Воло*? О нет. О, а он *хорош*.",
                      emo="surprise>happy/2")),
          act=1, custom="talk", source=G1 + "Act1_GOB_VoloBallad.txt:5,145-152 (EnteredTrigger FirstHeardArea + OnStage)"),
    place("Talk_K11_Drums", "К11. Герой сыграл на барабанах на посту гоблинов",
          variant(say("Tempo was rushed. Crowd loved it. That's showbusiness.", "Темп загнал. Публике понравилось. Такой он, шоу-бизнес.",
                      emo="thinking>happy", note="(вздыхает)")),
          act=1, custom="talk", source=G1 + "Act1_GOB_Checkpoint.txt:234-244 (ReactOnPlayerPerformingSong)"),
    place("Talk_K12_Poems", "К12. Стихи в Тайной башне",
          variant(say("Rhyming \"moon\" with \"soon\". Twice. Whoever wrote this deserved the tower.",
                      "Рифмует «луна» и «одна». Дважды. Кто это писал, тот заслужил эту башню.", emo="disgust>happy/2")),
          act=1, custom="talk", source=G1 + "Act1_UND_ArcaneTower.txt:702-714 (GameBookInterfaceClosed, DB_UND_ArcaneTower_Poems)"),
    place("Talk_K13_Lathander", "К13. Статуя Латандера у Яслей",
          variant(say("Lathander. God of the dawn. My song's called *The Weeping Dawn* - I hope he doesn't take it personally.",
                      "Латандер. Бог рассвета. Моя песня называется «Плач рассвета» — надеюсь, он не примет на свой счёт.",
                      emo="thinking>happy/2")),
          act=1, custom="talk", source=GD + "Act1b_CRE_Exterior.txt:355,362 (PROC_GLO_KnowledgeCheckSuccess, Религия)"),
    place("Talk_K14_GithYouth", "К14. Учебный зал юных гитов в Яслях",
          variant(say("They train their children too. Everybody trains their children for war. Nobody trains them for after.",
                      "Они тоже учат своих детей. Все учат детей войне. Никто не учит тому, что будет после.",
                      emo="thinking>sad", note="(тихо)")),
          act=1, custom="talk", source=GD + "Act1b_CRE_Creche_Misc.txt:139-142 (VB учебного зала: манекены, анатомия)"),
    place("Talk_K15_Underdark", "К15. Подземье, первый вход",
          variant(say("No sky. No stars. Right. I'll just - hum something. Loudly.",
                      "Ни неба. Ни звёзд. Ладно. Я просто… что-нибудь напою. Погромче.", emo="fear>happy")),
          act=1, custom="talk", source="после реплики места UnderdarkFirst (S_UND_Underdark_SUB), ALFSV_Talks.txt"),
]
