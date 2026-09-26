"""Разговор с Альфирой в отряде и в лагере (минимальный, до глав этапа 4).

Приветствия — её озвученные реплики из ванильного DEN_Bard_InParty (там она спутница
Темного Соблазна на одну ночь): голос и постановка Larian. Холодная реплика — только при
одобрении ниже 0 (флаг порога игры Approval_AtLeast_0_For_Sp1). Остальные идут по кругу.
Новые тексты — только ответы на «пойдём» и «жди в лагере» (черновик).
"""
from dsl import ALFIRA, Join, Scene, new_flag, opt, say, voice
from vanilla import F, NESTED

SCENE = Scene(
    name="ALFSV_Alfira_InParty",
    dialog_id="b2950129-fdd2-4cda-8182-cf41cfd5d809",      # ID из этапа 2 (DB_OriginInPartyDialog)
    base="DEN_Bard_InParty",
    voice_from=["DEN_Bard_InParty"],
    nested=[NESTED.SwapCamp],
    status="черновик",
)
S = SCENE

TALKED_1 = new_flag("ALFSV_InParty_Greeting1", "Dialog", "In-party greeting rotation: first greeting played")
TALKED_2 = new_flag("ALFSV_InParty_Greeting2", "Dialog", "In-party greeting rotation: second greeting played")

MENU = [
    opt("Пойдём со мной.", "Come with me.", when=[F.Recruited(ALFIRA, False)],
        join=Join(nested=NESTED.SwapCamp,
                  reply=say("Right behind you.", "Я за тобой.", emo="happy", note="черновик"))),
    opt("Жди меня в лагере.", "Wait for me at camp.",
        when=[F.BlockWaitInCamp(ALFIRA, False), F.Recruited(ALFIRA)],
        reply=[say("I'll keep the fire going.", "Буду поддерживать костёр.", emo="happy>thinking", note="черновик")],
        set=[F.RemoveFromParty(ALFIRA)], end=True),
    opt("*Уйти.*", "*Leave.*", end=True),
]

S.greeting("cold", voice("he46d9aaag48f9g4858ga58bg41dd1584a4b6"),          # N17: The sooner we go to sleep…
           when=[F.ApprovalAtLeast0_Sp1(ALFIRA, False)], choices=MENU)
S.greeting("first", voice("h8e9d685age2bdg4858g8c9bg8b45545d804f"),          # N5: I can't wait to hit the road…
           voice("h78247de5g47f4g491cga023g280acd8ebba5"),                     # N9: Hah, sorry - I'm getting ahead…
           when=[TALKED_1(ALFIRA, False)], set=[TALKED_1(ALFIRA)], choices=MENU)
S.greeting("second", voice("h94c66b2ag36cbg4fafg9decgbd3f033b843d"),         # N18: We should probably hit the hay…
           when=[TALKED_2(ALFIRA, False)], set=[TALKED_2(ALFIRA)], choices=MENU)
S.greeting("third", voice("hdb83bb64ga330g4966gabddg5ccd5448a7cd"),          # N13: …Thank you again for letting me stay.
           set=[TALKED_1(ALFIRA, False), TALKED_2(ALFIRA, False)], choices=MENU)
