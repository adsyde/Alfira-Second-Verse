"""Глава 8 «Первый поцелуй» — design/dialogs/09_act1_ch8_first_kiss.md, согласовано 2026-09-27.

Необязательная, акт 1, после долгого отдыха, вечер в лагере (GLO_CAMP_State_NightMode), одобрение 40+ (на входе
и при открытии). Открывается, если в главе 5 кто-то из героев открыл роман, получил «спроси меня снова» или
«отложено» (глобальный ALFSV_Romance_Act1Candidate). Вход (when_any, по корню на вариант):
  K1а — ALFSV_Romance_Open; K1б — ALFSV_Romance_AskAgain или ALFSV_Romance_Postponed.
Поцелуй ставит ALFSV_Romance_Started (его ждут 💞-реплики мест и пути) и CH.done. «Не сейчас» — глава не
закрыта, предлагается снова. Отказы — CH.done и ALFSV_Romance_Closed на герое.
"""
from dsl import ALFIRA, PLAYER, Scene, chapter, check, narrate, new_flag, opt, outcome, say
from scenes.ch02_lute import PLAYED_TOGETHER
from scenes.ch04_celebration import LAKRISSA_HERE
from scenes.ch05_morning_after import ASK_AGAIN, CANDIDATE, OPEN, POSTPONED, READ_LINE
from scenes.ch07_fear import CH as CH7
from scenes.recruitment import ROMANCE
from vanilla import DC, F, T

CH = chapter(8, "Первый поцелуй", after_rest=True, optional=True, act=1, approval=40, story=[CANDIDATE.on],
             when=[F.CampNight.on], when_any=[[OPEN(PLAYER)], [ASK_AGAIN(PLAYER)], [POSTPONED(PLAYER)]])

SCENE = Scene(
    name="ALFSV_Alfira_Ch08_FirstKiss",
    dialog_id="5e9d2b47-1a8c-4e36-b0f7-3c6a9d1e8b54",      # ID ресурса вложенного диалога главы, не менять
    base="DEN_Bard_InParty",
    voice_from=[],
    chapter=CH,
    status="согласовано 2026-09-27",
)
S = SCENE

CLOSED = new_flag("ALFSV_Romance_Closed", "Object", "The hero turned the romance down (chapter 8) - no romance in act 1")
TELL_LAKRISSA = new_flag("ALFSV_Romance_TellLakrissa", "Object", "Alfira will tell Lakrissa herself (R6, act 2)")
KISS = [ROMANCE(PLAYER), OPEN(PLAYER), CH.done]


def gendered(ru_m, ru_f, en, when=(), **kw):
    return [opt(ru_m, en, when=[~T.FEMALE(PLAYER), *when], **kw),
            opt(ru_f, en, when=[T.FEMALE(PLAYER), *when], **kw)]


# --- K1а. Роман открыт ---

S.greeting("K1a",
           narrate("She sits by the fire, the lute on her knees, not playing.", "Она сидит у огня с лютней на коленях и не играет.",
                   emo="thinking"),
           say("I've been sober for three days. On purpose. I wanted to be sure it's me talking, and not the wine.",
               "Я три дня не пила. Нарочно. Хотела быть уверенной, что говорю я, а не вино.", emo="thinking>fear"),
           say("It's me. I checked. Several times.", "Это я. Я проверила. Несколько раз.", emo="happy/2"),
           narrate("A nervous laugh.", "Нервный смешок.", emo="happy/2"),
           say("Sit down before I lose my nerve.", "Садись, пока я не струсила.", emo="fear>happy"),
           when=[OPEN(PLAYER)], go="K2")

# --- K1б. Вторая попытка ---

K1B_MENU = [
    opt("Мне тоже.", "Me too.", approve=+1, set=[OPEN(PLAYER)],
        reply=[narrate("She lets out a breath as if she's been holding it since the Grove.",
                       "Она выдыхает так, будто держала воздух с самой Рощи.", emo="surprise>happy"),
               say("...Oh, *good*.", "…Ох, *хорошо*.", emo="happy/2", shot="alfira_close")],
        go="K2"),
    *gendered("Я всё ещё не уверен.", "Я всё ещё не уверена.", "I'm still not sure.", set=[CH.done],
              reply=[narrate("She nods.", "Она кивает.", emo="thinking"),
                     say("That's all right. That's honest. I'll be here. Writing. Badly, probably.",
                         "Это ничего. Это честно. Я буду здесь. Сочинять. Скорее всего, скверно.", emo="sad>happy")],
              end=True),
    opt("Прости. Ты мне друг.", "I'm sorry. You're my friend.", set=[CH.done, CLOSED(PLAYER)],
        reply=[say("...Right. Thank you for saying it to my face. That's more than most people manage.",
                   "…Ясно. Спасибо, что {сказал|сказала} это в лицо. Большинство так не может.", emo="sad>happy",
                   note="(улыбается, и почти получается)")],
        end=True),
]
S.greeting("K1b_ask",
           say("You asked me something, the morning after the party. I told you to ask again when I was sure.",
               "Утром после праздника ты меня кое о чём {спросил|спросила}. Я сказала — спроси снова, когда я буду уверена.",
               emo="thinking"),
           narrate("A deep breath.", "Глубокий вдох.", emo="fear"),
           say("You don't have to ask. I'm sure.", "…Можешь не спрашивать. Я уверена.", emo="happy", shot="alfira_close"),
           when=[ASK_AGAIN(PLAYER)], choices=K1B_MENU)
S.greeting("K1b_road",
           say("So. The road. Has it shown you anything yet?", "Ну что. Дорога. Показала тебе что-нибудь?", emo="thinking>happy/2"),
           say("Because it's shown *me*. Quite a lot, actually. Rather loudly.",
               "…Потому что *мне* показала. И немало. И довольно громко.", emo="happy/2", note="(не даёт ответить)"),
           when=[POSTPONED(PLAYER)], choices=K1B_MENU)

# --- K2. Строчка ---

S.block("K2",
        narrate("She pulls the same sheet from her boot - crumpled, wine-stained.",
                "Она достаёт из-за голенища тот самый листок, мятый, в винных пятнах.", emo="thinking"),
        say("Remember the line I crossed out? At the bottom?", "Помнишь строчку, которую я зачеркнула? Внизу?", emo="thinking"),
        go=["K2_read", "K2_line"])
S.block("K2_read",
        say("...Of course you remember. You read it upside down, you sneak.",
            "…Конечно, помнишь. Ты её вверх ногами {прочитал|прочитала}, {хитрец|хитрюга}.", emo="happy/2"),
        when=[READ_LINE(PLAYER)], go="K2_line")
S.block("K2_line",
        say("I un-crossed it. Sober. With a steady hand.", "Я её раззачеркнула. Трезвой. Твёрдой рукой.", emo="happy"),
        narrate("She shows you.", "Она показывает.", emo="happy"),
        say("...Mostly steady.", "…Почти твёрдой.", emo="happy/2"),
        narrate("Written neatly over the crossing-out: ...and I think I'd follow them anywhere.",
                "Поверх зачёркнутого аккуратно выведено: …и, кажется, я пошла бы за {ним|ней} куда угодно.",
                emo="thinking", shot="alfira_close"),
        go=["K2_gap", "K3_wait"])
# глава 7 была: проверила проход у камней
S.block("K2_gap",
        say("And I checked for the gap. Just now. Out of habit.", "И я проверила, где проход. Только что. По привычке.",
            emo="thinking"),
        narrate("She shakes her head.", "Она качает головой.", emo="happy"),
        say("There isn't one. I checked twice.", "…Его нет. Я проверила дважды.", emo="happy", shot="alfira_close"),
        when=[CH7.done_flag.on], go="K3")
# [решение сборки] перед выбором героя — ремарка без слов (у K2_gap и без неё одно меню)
S.block("K3_wait", narrate("She waits.", "Она ждёт.", emo="thinking>fear", shot="alfira_close"), go="K3")

# --- K3. Поцелуй → R4 ---

AFTER = "K4"
S.menu("K3",
       opt("Можно?", "May I?", approve=+3, set=KISS,
           reply=[say("You're *asking*?", "Ты *спрашиваешь*?", emo="surprise>happy/2"),
                  narrate("She laughs, hides her face and immediately lifts it again.",
                          "Она смеётся, прячет лицо и тут же поднимает его.", emo="happy/2"),
                  say("Gods. Yes. Yes - quickly, before I go looking for another gap.",
                      "Боги. Да. Да — быстрее, пока я не пошла искать другой проход.", emo="happy", shot="alfira_close"),
                  narrate("She kisses you first.", "Она целует тебя первой.", emo="happy", shot="alfira_close")],
           go=AFTER),
       opt("*Поцеловать её.*", "*Kiss her.*", approve=+2, set=KISS,
           reply=[narrate("She freezes for a moment - and kisses you back. The sheet falls into the grass.",
                          "Она на миг замирает — и отвечает. Листок падает в траву.", emo="surprise>happy", shot="alfira_close"),
                  say("Oh. Oh, that's - Lihala never covered *that* in lessons.", "Ой. Ой, это… такому Лихейла меня не учила.",
                      emo="surprise>happy/2")],
           go=AFTER),
       opt("*Ждать. Пусть решится сама.*", "*Wait. Let her decide.*", approve=+2, set=KISS,
           reply=[say("Right. I'm doing this. I'm -", "Так. Я это делаю. Я…", emo="fear>thinking"),
                  narrate("She kisses you - quickly, clumsily - and pulls back.", "Она целует тебя — быстро и неловко — и отстраняется.",
                          emo="surprise", shot="alfira_close"),
                  say("That was terrible.", "Это было ужасно.", emo="fear>happy/2"),
                  narrate("A pause.", "Пауза.", emo="thinking"),
                  say("Again?", "…Ещё раз?", emo="happy/2", shot="alfira_close"),
                  narrate("The second time goes better.", "Второй раз получается лучше.", emo="happy")],
           go=AFTER),
       # 🔁 сыграли вместе в главе 2
       check("*Сыграем? Вдвоём.*", "*Play with me? Just us.*", when=[PLAYED_TOGETHER(PLAYER)], skill="Performance",
             ability="Charisma", dc=DC.Act1_Medium,
             success=outcome(approve=+4, set=KISS, reply=[
                 narrate("You play what you played that evening with the lute. On the last note she doesn't take her hand "
                         "off the strings - or off yours.",
                         "Вы играете то, что играли в вечер с лютней, и на последней ноте она не убирает руку со струн — и с твоей руки.",
                         emo="happy", shot="alfira_close"),
                 say("...That's a better ending than I wrote.", "…Такой концовки я не писала. Эта лучше.", emo="happy",
                     shot="alfira_close")], go=AFTER),
             failure=outcome(approve=+2, set=KISS, reply=[
                 narrate("You play the wrong chord. She laughs, takes the lute away and kisses you herself.",
                         "Ты берёшь не тот аккорд. Она смеётся, отбирает лютню и целует тебя сама.", emo="happy/2"),
                 say("You're hopeless. Come here.", "Ты {безнадёжен|безнадёжна}. Иди сюда.", emo="happy/2",
                     shot="alfira_close")], go=AFTER)),
       opt("Не сейчас.", "Not now.",
           reply=[say("...Okay.", "…Ладно.", emo="sad"),
                  narrate("She hides the sheet.", "Она прячет листок.", emo="sad"),
                  say("Not now isn't never. I'm good at waiting. I'm *excellent* at waiting.",
                      "«Не сейчас» — это не «никогда». Я умею ждать. Я *превосходно* умею ждать.", emo="sad>happy")],
           end=True),
       *gendered("Я передумал. Останемся друзьями.", "Я передумала. Останемся друзьями.",
                 "I've changed my mind. Let's stay friends.", set=[CH.done, CLOSED(PLAYER)],
                 reply=[say("...Oh.", "…Ох.", emo="surprise>sad"),
                        narrate("She nods and folds the sheet.", "Она кивает и складывает листок.", emo="sad"),
                        say("Thank you for saying it to my face.", "Спасибо, что {сказал|сказала} в лицо.", emo="sad>happy")],
                 end=True),
       )

# --- K4. После ---

S.block("K4",
        narrate("You sit by the fire. She doesn't let go of your hand.", "Вы сидите у огня. Она не отпускает твою руку.",
                emo="happy"),
        say("So. That happened.", "Ну вот. Случилось.", emo="happy/2"),
        narrate("A pause.", "Пауза.", emo="thinking"),
        say("I'm going to be *unbearable* about this, you know. For days.", "…Имей в виду, теперь я буду *невыносимой*. Несколько дней.",
            emo="happy/2"),
        choices=[
            opt("Хорошо.", "Good.", approve=+1,
                reply=[narrate("She rests her head on your shoulder.", "Она кладёт голову тебе на плечо.", emo="happy"),
                       say("Good.", "Хорошо.", emo="happy")],
                go="K5"),
            opt("Ты покраснела до кончиков рогов.", "You've gone red to the tips of your horns.", approve=+1,
                reply=[say("My horns are *not* - they're not. Are they?", "Мои рога *не*… не краснеют. Или краснеют?",
                           emo="surprise>fear"),
                       narrate("She touches a horn.", "Она трогает рог.", emo="surprise"),
                       say("Don't look at them. Look at the fire.", "Не смотри на них. Смотри на огонь.", emo="happy/2")],
                go="K5"),
            opt("А Лакрисса?", "What about Lakrissa?", when=[LAKRISSA_HERE.on], approve=+1, set=[TELL_LAKRISSA(PLAYER)],
                reply=[say("I'll tell her. Myself. I owe her that. She'll be kind about it, which is worse. She's always kind.",
                           "Я ей скажу. Сама. Я ей это должна. Она отнесётся по-доброму, и от этого будет только хуже. Она "
                           "всегда добрая.", emo="thinking>sad", note="(серьёзнеет)"),
                       say("She'll say \"about time\".", "…Она скажет: «Давно пора».", emo="sad>happy", note="(тише)")],
                go="K5"),
        ])

# --- K5. Конец ---

S.block("K5",
        narrate("She picks the sheet up out of the grass and smooths it out on her knee.",
                "Она поднимает листок из травы и разглаживает его на колене.", emo="happy"),
        say("Second verse is finished.", "Второй куплет закончен.", emo="happy"),
        narrate("She smiles.", "Она улыбается.", emo="happy/2"),
        say("Don't ask to hear it. It's *very* soppy.", "Не проси спеть. Он *очень* слащавый.", emo="happy/2"),
        end=True)
