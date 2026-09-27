"""Разговор с Альфирой в отряде и в лагере. С этапа 4 — ещё и вход в главы разговоров.

Приветствия — её озвученные реплики из ванильного DEN_Bard_InParty (там она спутница
Темного Соблазна на одну ночь): голос и постановка Larian. Холодная реплика — только при
одобрении ниже 0 (флаг порога игры Approval_AtLeast_0_For_Sp1). Остальные идут по кругу.
Новые тексты — только ответы на «пойдём» и «жди в лагере» (черновик).
Если открыта новая глава (scripts/dialogs/scenes/chNN_*.py), после холодной реплики и до ротации
стоит вход в неё (S.chapter_entries()); ротация играет, пока новой главы нет.
"""
from dsl import ALFIRA, PLAYER, Join, Scene, cinematic, narrate, nested, new_flag, opt, say, voice
from scenes.ch04_celebration import CLOAK, SAID_FRIEND
from scenes.ch07_fear import CH as CH7
from scenes.recruitment import ROMANCE
from vanilla import APPROVAL_SP1, F, NESTED, T

SCENE = Scene(
    name="ALFSV_Alfira_InParty",
    dialog_id="b2950129-fdd2-4cda-8182-cf41cfd5d809",      # ID из этапа 2 (DB_OriginInPartyDialog)
    base="DEN_Bard_InParty",
    voice_from=["DEN_Bard_InParty", "LOW_Elfsong_Alfira"],       # LOW — «Oh, hush…» (поцелуй)
    nested=[NESTED.SwapCamp],
    status="черновик",
)
S = SCENE

TALKED_1 = new_flag("ALFSV_InParty_Greeting1", "Dialog", "In-party greeting rotation: first greeting played")
TALKED_2 = new_flag("ALFSV_InParty_Greeting2", "Dialog", "In-party greeting rotation: second greeting played")

MENU = [
    opt("Пойдем со мной.", "Come with me.", game_line=("h5a66bcc9g765dg409cga6c7g4b710426b6ac", 1), when=[F.Recruited(ALFIRA, False)],
        join=Join(nested=NESTED.SwapCamp,
                  reply=say("Right behind you.", "Я за тобой.", emo="happy", note="черновик"))),
    opt("Я прошу тебя оставаться пока в лагере.", "I need you to remain at camp for now.",
        game_line=("h30e8c62bg3b77g4b4fg90beg6ee27760bc5a", 1),
        when=[F.BlockWaitInCamp(ALFIRA, False), F.Recruited(ALFIRA)],
        reply=[say("I'll keep the fire going.", "Буду поддерживать костёр.", emo="happy>thinking", note="черновик")],
        set=[F.RemoveFromParty(ALFIRA)], end=True),
    opt("Уйти.", "Leave.", game_line=("h001ead64g9497g45c9g9176gf389ce24eb2e", 1), end=True),
]


# --- Поцелуй и объятия в любой момент — design/dialogs/10_romance_kiss.md, согласовано 2026-09-27 ---
#
# Как у спутников Larian: вариант «Поцеловать её» / «Обнять её» в меню разговора в отряде (реплики героя игры),
# её ответ — и снова меню. Одобрения нет. Ответ: сначала особые случаи, иначе круг по порядку без повторов
# подряд: у каждого ответа круга флаг «сыгран» на Альфире; берётся первый несыгранный, последний сбрасывает круг.
# Особые случаи «вечер в лагере» звучат по разу за вечер (флаги снимает Osiris на PROC_LongRest), «Подземье» —
# по разу за спуск (снимает LeftTrigger подрегиона Подземья). Постановка — ремаркой рассказчика: анимации
# поцелуя Larian (TagCinematic, отдельный узел на каждое тело героя) на Альфиру надёжно не переносятся —
# docs/STAGE4.md §13. Проба переноса — один узел под отладочным флагом (KISS_CINEMATIC_TRIAL ниже).

KISS_OPT = ("h57aba6c9g5230g4cdcg9d57g0daa34b784ed", 1)       # Kiss her. / Поцеловать ее.
HUG_OPT = ("h4e908b98g9055g4a21gb8b3g118fa3b5250c", 2)        # *Hug her.* / *Обнять ее.*
AP20 = APPROVAL_SP1[20](ALFIRA)
AP40 = APPROVAL_SP1[40](ALFIRA)
IN_UNDERDARK = new_flag("ALFSV_InUnderdark", "Object", "Alfira is in the Underdark subregion (set and cleared by Osiris)")

# --- Проба: поцелуй Larian на Альфире (docs/STAGE4.md §13, этап 9). Не проверено в игре. ---
#
# Вложенный диалог ALFSV_Alfira_KissTrial на основе ShadowHeart_InParty2_Nested_ShadowheartKiss: спикер 0
# (Шэдоухарт) → Альфира, зрители-спутники убраны, сцена основы (стадии Kiss_Tall/…, её камеры) — целиком. Один узел:
# вариант A (ORI_Kiss_VersionA) на обычное тело героя — у Larian это узел без тегов тела, остальные тела выбирают
# свои узлы раньше него. Его фаза копируется целиком (staging.Stager.cinematic_phase): анимации обоих, TLTransform,
# стадия, 4 плана своих камер, звуки, эмоции, взгляды.
# Вариант героя «[Проба] Поцеловать её» виден, только если на Альфире стоит отладочный флаг — из консоли SE:
# Osi.PROC_ALFSV_Debug_KissCinematic() (снять — …Off()), и тело героя обычное. Остальные поцелуи — ремарки.
KISS_CINEMATIC_TRIAL = True          # False — пробы нет в сборке вовсе
SHADOWHEART = "3ed74f06-3c60-42dc-83f6-f034cb47c679"            # спикер 0 основы поцелуя
KISS_A_NORMAL = "5f5e750e-d2e2-4e2e-90fe-e6f7fc8eea71"          # узел: ORI_Kiss_VersionA, тело героя без тегов
KISS_A_FEMALE = "2e786fd7-bbc4-df6b-0df2-e8413461e992"          # тот же вариант, FEMALE — для следующей пробы
NORMAL_BODY = [~T.FEMALE(PLAYER), ~T.SHORT(PLAYER), ~T.DWARF(PLAYER), ~T.DRAGONBORN(PLAYER), ~T.BODYTYPE_STRONG(PLAYER)]
DEBUG_KISS = new_flag("ALFSV_Debug_KissCinematic", "Object",
                      "Debug: show the Larian kiss staging trial in the party talk (Osi.PROC_ALFSV_Debug_KissCinematic)")
KISS_TRIAL = Scene(
    name="ALFSV_Alfira_KissTrial",
    dialog_id="af94d8ab-d2f7-4b6b-adef-4d264223fad1",
    base="ShadowHeart_InParty2_Nested_ShadowheartKiss",
    alfira_base=SHADOWHEART,
    kind="cinematic",
    status="проба постановки, не проверено в игре",
)
KISS_TRIAL.greeting("A", cinematic(KISS_A_NORMAL, note="вариант A, обычное тело героя"), end=True)


MENU[-1:-1] = [
    opt("Поцеловать ее.", "Kiss her.", game_line=KISS_OPT, when=[ROMANCE(PLAYER)],
        go=["kiss_cold", "kiss_deep", "kiss_night1", "kiss_cloak", "kiss_night2", *[f"Kiss_{i:02d}" for i in range(1, 13)]]),
    opt("Обнять ее.", "Hug her.", game_line=HUG_OPT, when=[ROMANCE(PLAYER)], key="menu.hug",
        go=["hug_cold", "hug_night", "Hug_01", "Hug_02", "Hug_03", "Hug_04", "Hug_05", "Hug_05_last", "Hug_06"]),
    opt("Обнять ее.", "Hug her.", game_line=HUG_OPT, when=[~ROMANCE(PLAYER), AP40], key="menu.hug_friend",
        go=["HugFriend_01", "HugFriend_02", "HugFriend_03", "HugFriend_03_last", "HugFriend_04"]),
]

if KISS_CINEMATIC_TRIAL:
    MENU[-1:-1] = [opt("[Проба] Поцеловать её (постановка Larian).", "[Trial] Kiss her (Larian staging).",
                       when=[ROMANCE(PLAYER), DEBUG_KISS(ALFIRA), *NORMAL_BODY], key="menu.kiss_trial", go="kiss_trial")]
    SCENE.nested.append(KISS_TRIAL.dialog_id)


def circle(prefix, items):
    """items: [(реплики, доп. условия)] → блоки круга. Последний (или последний доступный) сбрасывает флаги."""
    played = [new_flag(f"ALFSV_{prefix}_{i + 1:02d}", "Object", f"{prefix} rotation: answer {i + 1} played")
              for i in range(len(items))]
    ids = []
    for i, (lines, extra) in enumerate(items):
        last = i == len(items) - 1
        bid = f"{prefix}_{i + 1:02d}"
        reset = [p(ALFIRA, False) for p in played[:i]]
        S.block(bid, *lines, when=[played[i](ALFIRA, False), *extra],
                set=reset if last else [played[i](ALFIRA)], choices=MENU)
        ids.append(bid)
    return ids, played


def kiss(direction_en="", direction_ru=""):
    en = "You kiss her." + (f" {direction_en}" if direction_en else "")
    ru = "Ты целуешь её." + (f" {direction_ru}" if direction_ru else "")
    return narrate(en, ru, emo="happy", shot="alfira_close")


def hug(direction_en="", direction_ru=""):
    en = "You hug her." + (f" {direction_en}" if direction_en else "")
    ru = "Ты обнимаешь её." + (f" {direction_ru}" if direction_ru else "")
    return narrate(en, ru, emo="happy", shot="alfira_close")


if KISS_CINEMATIC_TRIAL:
    S.block("kiss_trial", nested(KISS_TRIAL.dialog_id, note="кат-сцена поцелуя Larian"),
            say("Mm. Hello to you too.", "Ммм. И тебе привет.", emo="happy"), choices=MENU)

# особые случаи поцелуя
KISS_NIGHT = [new_flag(f"ALFSV_KissNight_{i}", "Object", f"Kiss: camp-evening special {i} said tonight") for i in (1, 2, 3)]
KISS_DEEP = new_flag("ALFSV_KissUnderdark", "Object", "Kiss: Underdark special said on this descent")
S.block("kiss_cold", narrate("She turns away.", "Она отворачивается.", emo="sad"),
        say("Not now. Please.", "Не сейчас. Пожалуйста.", emo="sad"), when=[~AP20], choices=MENU)
S.block("kiss_deep", kiss(), say("No stars down here. You'll have to do.", "Звёзд тут нет. Придётся тебе их заменить.",
                                 emo="happy"),
        when=[IN_UNDERDARK(ALFIRA), KISS_DEEP(ALFIRA, False)], set=[KISS_DEEP(ALFIRA)], choices=MENU)
S.block("kiss_night1", kiss(), say("Stay a bit. The fire's not done yet.", "Посиди ещё. Костёр ещё не догорел.", emo="happy"),
        when=[F.CampNight.on, KISS_NIGHT[0](ALFIRA, False)], set=[KISS_NIGHT[0](ALFIRA)], choices=MENU)
S.block("kiss_cloak", kiss(), narrate("She throws her cloak over your shoulders.", "Она набрасывает на тебя свой плащ.",
                                      emo="happy/2"),
        say("Your turn to borrow a cloak.", "Теперь твоя очередь мёрзнуть в чужом плаще. Держи.", emo="happy/2"),
        when=[F.CampNight.on, CLOAK(PLAYER), KISS_NIGHT[2](ALFIRA, False)], set=[KISS_NIGHT[2](ALFIRA)], choices=MENU)
S.block("kiss_night2", kiss(), say("Everyone's asleep.", "Все спят.", emo="thinking"),
        narrate("A pause.", "Пауза.", emo="thinking"),
        say("Probably. Let's pretend everyone's asleep.", "…Наверное. Давай сделаем вид, что все спят.", emo="happy/2"),
        when=[F.CampNight.on, KISS_NIGHT[1](ALFIRA, False)], set=[KISS_NIGHT[1](ALFIRA)], choices=MENU)

KISS_CIRCLE, KISS_PLAYED = circle("Kiss", [
    ([kiss("She rises on her toes.", "Она встаёт на цыпочки."), say("Mm. Hello to you too.", "Ммм. И тебе привет.", emo="happy")], []),
    ([kiss(), say("In front of *everyone*?", "При *всех*?", emo="surprise"),
      narrate("She glances around.", "Она оглядывается.", emo="surprise>happy"),
      say("...Do it again.", "…Ещё раз.", emo="happy/2")], []),
    ([kiss(), say("You taste like campfire. I'm putting that in a song. No, I'm not. ...Yes, I am.",
                  "На вкус ты как костёр. Вставлю это в песню. Нет, не вставлю. …Вставлю.", emo="happy>thinking>happy/2")], []),
    ([kiss(), say("I've lost my place. I was thinking something very important, and now it's just - you.",
                  "Я сбилась. Я думала о чём-то очень важном, а теперь там только… ты.", emo="thinking>happy")], []),
    ([kiss(), voice("h3d30c96fg5f1cg4eaag8739gf2ca9de54cd9")], []),          # Oh, hush - I know you love me really.
    ([kiss("She doesn't let go.", "Она не отпускает."),
      say("Lihala always said a good musician knows when to hold a note.",
          "Лихейла говорила: хороший музыкант знает, когда тянуть ноту.", emo="happy"),
      narrate("A pause.", "Пауза.", emo="happy"), say("I'm holding it.", "…Я тяну.", emo="happy/2")], []),
    ([kiss("She laughs right into the kiss.", "Она смеётся прямо в поцелуй."),
      say("Sorry - sorry. I'm just happy. It keeps leaking out.", "Прости, прости. Мне просто хорошо. Оно само наружу лезет.",
          emo="happy/2")], []),
    ([kiss(), say("That's another one. I'm keeping count. For the song. *Obviously* for the song.",
                  "Это ещё один. Я веду счёт. Для песни. Разумеется, *для песни*.", emo="happy/2")], []),
    ([kiss("She reaches for a second one.", "Она тянется за вторым."),
      say("What? Encores are traditional.", "Что? Бис — это традиция.", emo="happy/2")], []),
    ([kiss(), say("If a goblin saw that, it would write a ballad about it. A terrible one. Goblins can't rhyme.",
                  "Увидел бы это гоблин — сложил бы балладу. Ужасную. Гоблины не умеют рифмовать.", emo="happy>happy/2")], []),
    ([kiss("She rests her forehead on your shoulder.", "Она утыкается лбом тебе в плечо."),
      say("Give me a moment. I'm composing myself. Badly.", "Дай минутку. Собираюсь с мыслями. Получается скверно.",
          emo="happy/2")], []),
    ([kiss(), say("Don't look at me like that. I'll forget the words to every song I know.",
                  "Не смотри так. Я забуду слова всех песен, какие знаю.", emo="happy/2")], []),
])

# объятия при романе
HUG_NIGHT = new_flag("ALFSV_HugNight", "Object", "Hug: camp-evening special said tonight")
S.block("hug_cold", narrate("She steps back.", "Она отступает на шаг.", emo="sad"),
        say("...I'd rather not.", "…Лучше не надо.", emo="sad"), when=[~AP20], choices=MENU)
S.block("hug_night", hug("She rests her head on your shoulder.", "Она кладёт голову тебе на плечо."),
        say("Five more minutes. Then sleep. Then five more minutes.", "Ещё пять минут. Потом спать. Потом ещё пять минут.",
            emo="happy"),
        when=[F.CampNight.on, HUG_NIGHT(ALFIRA, False)], set=[HUG_NIGHT(ALFIRA)], choices=MENU)
GAP = [CH7.done_flag.on]
HUG_ITEMS = [
    ([hug("She holds on tight.", "Она крепко прижимается."), say("...Just a bit longer.", "…Ещё чуть-чуть.", emo="happy")], []),
    ([hug(), say("You're warm. Why are you always warm? It's very unfair on the rest of us.",
                 "Ты {тёплый|тёплая}. Почему ты всегда {тёплый|тёплая}? Это нечестно по отношению к остальным.", emo="happy/2")], []),
    ([hug("She mumbles into your shoulder.", "Она бормочет тебе в плечо."),
      say("I'm not crying. It's road dust.", "Я не плачу. Это дорожная пыль.", emo="sad>happy")], []),
    ([hug(), say("Mm. Best part of the day. Don't tell the song.", "Ммм. Лучшая часть дня. Только песне не говори.", emo="happy")], []),
]
LAST5 = ([hug(), say("Lihala hugged like a bear trap. You hug like - like home. Is that soppy? That's soppy.",
                     "Лихейла обнимала, как медвежий капкан. А ты обнимаешь, как… как дом. Это слащаво? Слащаво.",
                     emo="happy>thinking>happy/2")], GAP)
HUG_CIRCLE, HUG_PLAYED = circle("Hug", HUG_ITEMS + [LAST5] + [(
    [hug("She doesn't let go.", "Она не отпускает."),
     say("I've checked. There's no gap. I'm staying right here.", "Я проверила. Прохода нет. Я остаюсь здесь.", emo="happy")],
    [])])
# без главы 7 шестого ответа нет: пятый (без «прохода») замыкает круг
S.block("Hug_05_last", *LAST5[0], when=[HUG_PLAYED[4](ALFIRA, False), ~GAP[0]],
        set=[p(ALFIRA, False) for p in HUG_PLAYED[:4]], choices=MENU)

# объятия по дружбе (без романа, одобрение 40+)
FRIEND_ITEMS = [
    ([say("Oh!", "Ой!", emo="surprise"), narrate("She laughs and hugs you back.", "Она смеётся и обнимает тебя в ответ.",
                                                 emo="happy/2"),
      say("Hello, you.", "Привет-привет.", emo="happy")], []),
    ([hug(), say("Friends hug. It's a rule. I've just made it a rule.", "Друзья обнимаются. Это правило. Я его только что придумала.",
                 emo="happy/2")], []),
    ([hug("She pats you on the back.", "Она хлопает тебя по спине."),
      say("There. Now we're both braver.", "Вот. Теперь мы оба храбрее.", emo="happy")], []),
]
LAST4 = [hug(), say("You're a good friend. I said that drunk once. I'm saying it sober now.",
                    "Ты хороший друг. Я как-то сказала это пьяной. Теперь говорю трезвой.", emo="happy>thinking")]
FRIEND_CIRCLE, FRIEND_PLAYED = circle("HugFriend", FRIEND_ITEMS + [(LAST4, [])])
S.blocks["HugFriend_03"].when.append(SAID_FRIEND(PLAYER))      # третий ведёт к четвёртому, если она это говорила
S.block("HugFriend_03_last", *FRIEND_ITEMS[2][0], when=[FRIEND_PLAYED[2](ALFIRA, False), ~SAID_FRIEND(PLAYER)],
        set=[p(ALFIRA, False) for p in FRIEND_PLAYED[:2]], choices=MENU)


S.greeting("cold", voice("he46d9aaag48f9g4858ga58bg41dd1584a4b6"),          # N17: The sooner we go to sleep…
           when=[F.ApprovalAtLeast0_Sp1(ALFIRA, False)], choices=MENU)
# Главы разговоров (scenes/chNN_*.py): новая глава важнее ротации, но не холодной реплики —
# при одобрении ниже 0 глава ждёт. Вход — корень без текста и вложенный диалог главы.
S.chapter_entries()
S.greeting("first", voice("h8e9d685age2bdg4858g8c9bg8b45545d804f"),          # N5: I can't wait to hit the road…
           voice("h78247de5g47f4g491cga023g280acd8ebba5"),                     # N9: Hah, sorry - I'm getting ahead…
           when=[TALKED_1(ALFIRA, False)], set=[TALKED_1(ALFIRA)], choices=MENU)
S.greeting("second", voice("h94c66b2ag36cbg4fafg9decgbd3f033b843d"),         # N18: We should probably hit the hay…
           when=[TALKED_2(ALFIRA, False)], set=[TALKED_2(ALFIRA)], choices=MENU)
S.greeting("third", voice("hdb83bb64ga330g4966gabddg5ccd5448a7cd"),          # N13: …Thank you again for letting me stay.
           set=[TALKED_1(ALFIRA, False), TALKED_2(ALFIRA, False)], choices=MENU)

EXTRA_SCENES = [KISS_TRIAL] if KISS_CINEMATIC_TRIAL else []
