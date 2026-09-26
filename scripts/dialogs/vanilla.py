"""Идентификаторы игры, на которые ссылаются сцены. Все взяты из данных Patch 8 Hotfix 9.

build.py при каждой сборке сверяет флаги и теги с файлами игры (Public/*/Flags, Public/*/Tags):
имя и тип должны совпасть с uuid, иначе сборка останавливается.
"""
from dsl import Flag

ALFIRA_TEMPLATE = "4a405fba-3000-4c63-97e5-a8001ebb883c"   # S_DEN_Bard, глобальный персонаж
PLAYER_SPEAKER = "e0d1ff71-04a8-4340-ae64-9684d846eb83"    # группа спикеров «игрок»
ALFIRA_ORIGIN = "38357c93-b437-4f03-88d0-a67bd4c0e3e9"     # Origin «Alfira» (GustavDev/Origins/Origins.lsx)


class F:
    """Ванильные флаги (Usage: 5 — глобальный, 4 — на объекте)."""
    FinishedSong = Flag("DEN_TieflingBard_State_FinishedSong", "Global", "e8ab958f-015b-f97d-5da4-c599b67e5ba0")
    ReturnedInstrument = Flag("DEN_TieflingBard_State_ReturnedInstrument", "Global", "03c9168b-079b-eff1-fbe4-9dcb4425c529")
    # ставит DEN_TieflingBard_Bard после удачного дуэта на лютне (на герое)
    GiveProficiency = Flag("DEN_TieflingBard_Event_GiveProficiency", "Object", "da7a54f9-091d-9276-2a76-3abec2b701a7")
    MaxPlayerCount = Flag("GEN_MaxPlayerCountReached", "Global", "823b5064-8aa4-c0b7-1b8c-657b46987ccd")
    OriginAddToParty = Flag("OriginAddToParty", "Object", "4870b2cd-210c-0fdc-9c58-4d0142bdae29")
    InvitedToCampWalk = Flag("GLO_ORI_Event_InvitedToCamp_Walk", "Object", "6dfae0e0-e6c4-4d4f-8979-df320356ea03")
    SwapToCamp = Flag("GLO_ND_CompanionSwap_ToCamp", "Object", "b0ad7652-77ee-c932-3440-922b6e1173aa")
    Recruited = Flag("ORI_State_Recruited", "Object", "e78c0aab-fb48-98e9-3ed9-773a0c39988d")
    BlockWaitInCamp = Flag("GLO_Origin_BlockWaitInCampOption", "Object", "a2cd0f8e-67c2-4294-8f5d-2d30f1acde38")
    RemoveFromParty = Flag("OriginRemoveFromPartyAfterDialog", "Object", "7a429beb-fbfb-fa8a-3a33-0349323ad11d")
    # порог одобрения ≥ 0 для героя-спикера 1; ставит на спутнике _GLO_Shared_Origins.txt
    # (PROC_ApprovalRating_SetThresholdEvents, DB_OriginRelationThresholdEventsPerSpeaker)
    ApprovalAtLeast0_Sp1 = Flag("Approval_AtLeast_0_For_Sp1", "Object", "80966819-5946-2be4-645c-809ecb253ed6")


class T:
    """Теги (Shared/Public/Shared/Tags)."""
    BARD = Flag("BARD", "Tag", "d93434bd-6b71-4789-b128-ee24156057cc")
    TIEFLING = Flag("TIEFLING", "Tag", "aaef5d43-c6f3-434d-b11e-c763290dbe0c")


class DC:
    """Классы сложности (Shared/Public/Shared/DifficultyClasses/DifficultyClasses.lsx)."""
    Act1_Easy = "31e92da6-bac9-46f7-af99-5f33d98fd4f0"     # 7
    Act1_Medium = "fa621d38-6f83-4e42-a55c-6aa651a75d46"   # 10


class NESTED:
    """Вложенные ванильные диалоги замены при полном отряде (ID ресурсов в банке игры)."""
    SwapRecruitment = "f02d36d9-1f59-33ee-b87d-82f4c13c501f"   # GLO_CompanionSwap_Recruitment (Уилл, Лаэ'зель)
    SwapCamp = "002e501b-6f1b-8357-1fde-20b1b4b7c1b9"          # GLO_CompanionSwap_Camp (Минск)
