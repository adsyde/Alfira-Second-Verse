"""Идентификаторы игры, на которые ссылаются сцены. Все взяты из данных Patch 8 Hotfix 9.

build.py при каждой сборке сверяет флаги и теги с файлами игры (Public/*/Flags, Public/*/Tags):
имя и тип должны совпасть с uuid, иначе сборка останавливается.
"""
from dsl import Flag

ALFIRA_TEMPLATE = "4a405fba-3000-4c63-97e5-a8001ebb883c"   # S_DEN_Bard, глобальный персонаж
PLAYER_SPEAKER = "e0d1ff71-04a8-4340-ae64-9684d846eb83"    # группа спикеров «игрок»
ALFIRA_ORIGIN = "38357c93-b437-4f03-88d0-a67bd4c0e3e9"     # Origin «Alfira» (GustavDev/Origins/Origins.lsx)
# рассказчик: speaker -666 в диалоге, актёр таймлайна с этим uuid (как в DEN_TieflingBard_Bard)
NARRATOR_SPEAKER = "a346318f-15b3-49ad-ab97-ddf8283dc339"
# Лакрисса (S_DEN_Tiefling_010): третий участник сцены «Лакрисса замечает героя» на празднике
LAKRISSA = "23129d6c-8d39-4a4c-a4f6-cfc6637b597c"


class F:
    """Ванильные флаги (Usage: 5 — глобальный, 4 — на объекте)."""
    FinishedSong = Flag("DEN_TieflingBard_State_FinishedSong", "Global", "e8ab958f-015b-f97d-5da4-c599b67e5ba0")
    ReturnedInstrument = Flag("DEN_TieflingBard_State_ReturnedInstrument", "Global", "03c9168b-079b-eff1-fbe4-9dcb4425c529")
    # ставит DEN_TieflingBard_Bard после удачного дуэта на лютне (на герое)
    GiveProficiency = Flag("DEN_TieflingBard_Event_GiveProficiency", "Object", "da7a54f9-091d-9276-2a76-3abec2b701a7")
    # на герое: он играл дуэт на лютне Лихейлы (DEN_TieflingBard_Bard N4659 «Hand me that lute»), после чего
    # лютня остаётся у него во всех ветках («Keep the lute», N2541/N4534). TransferInstrument не годится:
    # это событие «передать предмет от Альфиры тому, на ком флаг» (Act1_DEN_TieflingBard.txt:45-49),
    # его ставят и возврат украденной лютни, и отказ от помощи.
    PlayWithInstrument = Flag("DEN_TieflingBard_Event_PlayWithInstrument", "Object", "b063223a-761a-fae0-e766-f76a53b78b81")
    MaxPlayerCount =Flag("GEN_MaxPlayerCountReached", "Global", "823b5064-8aa4-c0b7-1b8c-657b46987ccd")
    OriginAddToParty = Flag("OriginAddToParty", "Object", "4870b2cd-210c-0fdc-9c58-4d0142bdae29")
    InvitedToCampWalk = Flag("GLO_ORI_Event_InvitedToCamp_Walk", "Object", "6dfae0e0-e6c4-4d4f-8979-df320356ea03")
    SwapToCamp = Flag("GLO_ND_CompanionSwap_ToCamp", "Object", "b0ad7652-77ee-c932-3440-922b6e1173aa")
    Recruited = Flag("ORI_State_Recruited", "Object", "e78c0aab-fb48-98e9-3ed9-773a0c39988d")
    BlockWaitInCamp = Flag("GLO_Origin_BlockWaitInCampOption", "Object", "a2cd0f8e-67c2-4294-8f5d-2d30f1acde38")
    RemoveFromParty = Flag("OriginRemoveFromPartyAfterDialog", "Object", "7a429beb-fbfb-fa8a-3a33-0349323ad11d")
    # порог одобрения ≥ 0 для героя-спикера 1; ставит на спутнике _GLO_Shared_Origins.txt
    # (PROC_ApprovalRating_SetThresholdEvents, DB_OriginRelationThresholdEventsPerSpeaker)
    ApprovalAtLeast0_Sp1 = Flag("Approval_AtLeast_0_For_Sp1", "Object", "80966819-5946-2be4-645c-809ecb253ed6")
    # вечер в лагере (после «Завершить день», до сна): GLO_Camp.txt, PROC_Camp_SetModeToNight/ToDay
    CampNight = Flag("GLO_CAMP_State_NightMode", "Global", "fb53edc2-9a89-4ad2-af83-20b5fe425cdd")
    # Астарион в лагере и он спутник, а не аватар (DB_OriginCampFlags, GLO_CampNights.txt «Camp Flags»)
    AstarionCompanionInCamp = Flag("ASTARIONCOMPANION", "Global", "9fa6b609-3ba0-43ed-a95b-82304f7b8dac")
    # «Первая крупная победа» акта 1 (глава 3): вожаки гоблинов убиты — все три из DB_GOB_GoblinLeaders
    # (Act1_GOB_GoblinHunt.txt, PROC_GLO_DefeatCounter_AllDefeated("GOB_GoblinHunt_Leaders"));
    # налёт на Рощу отбит — «Raiders defeated!» (Act1_DEN_AttackOnDen.txt, SetFlag после DebugBreak).
    # Третья победа — спасена Майрина — это запись журнала HAG_HagSpawn/SavedMayrina, не флаг (см. ch03).
    GoblinLeadersDead = Flag("GOB_State_LeadersAreDead", "Global", "a1c5b01f-4b7f-47ab-82b0-d24d9c6d8bc6")
    GroveRaidRepelled = Flag("DEN_AttackOnDen_State_DenVictory", "Global", "71c7f23e-3ff1-c9b8-3ef5-d75fa1b42c8d")
    # праздник тифлингов (CAMP_GoblinHuntCelebration_Bard): флаги диалога на герое
    CelebrationHasMetBard = Flag("CAMP_GoblinHuntCelebration_HasMet_Bard", "Dialog", "21639b69-57a6-8baf-165f-5633f74a65ae")
    RefusedBardSong = Flag("CAMP_GoblinHuntCelebration_Event_RefusedBardSong", "Dialog", "d3939955-5d61-ad2d-d406-1ebc0753c139")
    # герой обещал Лакриссе выпить с ней (её «Heh. Lakrissa would approve» на празднике)
    LakrissaPromisedDrink = Flag("DEN_General_TieflingGuard10_PromisedDrink", "Dialog", "f8a1e851-679e-cf93-69ed-148230c22395")


# Пороги одобрения для героя-спикера 1: Approval_AtLeast_N_For_Sp1 на спутнике
# (_GLO_Shared_Origins.txt, DB_OriginRelationThresholdEventsPerSpeaker). Uuid — Gustav/Public/Gustav/Flags.
APPROVAL_SP1 = {n: Flag(f"Approval_AtLeast_{n}_For_Sp1", "Object", u) for n, u in {
    -40: "b5ab9ca2-f6cd-aefc-5a2d-7d64f5d3f705", -30: "8f9363d0-7072-bbac-3615-7ede8167786e",
    -20: "209202b4-2d23-0c5f-9437-8cae49ef1a36", -10: "487684c1-c443-51f9-2b5a-605e1d744164",
    0: "80966819-5946-2be4-645c-809ecb253ed6", 5: "7468e995-931a-454f-9b2d-0facc6e81ee1",
    10: "2a7380a2-da28-7741-a065-fd118fdd9a92", 20: "f262956a-153c-91bd-4d7c-9a8e5e11119e",
    30: "55081005-8df3-62e5-60d9-971a0439947e", 35: "662a12ed-c01d-4af2-9510-d18bf5005c29",
    40: "50cd7894-b71c-adf0-7476-48b94c42be43", 50: "31d32c7a-52bc-62fc-38a7-15277f3b46fb",
    60: "4445984d-56f3-0e7c-25d5-cf5cca2a5642", 70: "2fb2abfb-5445-5419-6de4-77380dbf6265",
    80: "c014f892-8450-7821-8936-f862cc67654e", 90: "1b98e5dd-064f-a93b-fcb0-23cd1c55671f",
    100: "20293b72-864b-f8c7-605b-500e5a9fffd1"}.items()}


class T:
    """Теги (Public/<Shared|Gustav|GustavDev>/Tags)."""
    BARD = Flag("BARD", "Tag", "d93434bd-6b71-4789-b128-ee24156057cc")
    TIEFLING = Flag("TIEFLING", "Tag", "aaef5d43-c6f3-434d-b11e-c763290dbe0c")
    FEMALE = Flag("FEMALE", "Tag", "3806477c-65a7-4100-9f92-be4c12c4fa4f")
    # герой — Темный Соблазн (GustavDev/Tags; в диалогах игры 327 проверок против 34 у DARK_URGE).
    # Не путать с глобальным флагом лагеря DARKURGE («Соблазн в отряде»).
    REALLY_DARK_URGE = Flag("REALLY_DARK_URGE", "Tag", "cd611d7d-b67d-42b4-a75c-a0c6091ef8a2")
    # герой-ориджин и раса/класс — варианты героя на празднике (CAMP_GoblinHuntCelebration_Bard)
    REALLY_ASTARION = Flag("REALLY_ASTARION", "Tag", "ffd08582-7396-4cac-bcd4-8f9cd0fd8ef3")
    REALLY_SHADOWHEART = Flag("REALLY_SHADOWHEART", "Tag", "642d2aee-e3df-47e3-9f47-bbcd441bb9e0")
    REALLY_LAEZEL = Flag("REALLY_LAEZEL", "Tag", "b5682d1d-c395-489c-9675-1f9b0c328ea5")
    REALLY_WYLL = Flag("REALLY_WYLL", "Tag", "5f40def5-d3ec-4698-a367-01a339888956")
    REALLY_GALE = Flag("REALLY_GALE", "Tag", "9b0354c0-56d9-4723-8034-918ac9abab19")
    REALLY_KARLACH = Flag("REALLY_KARLACH", "Tag", "1a2f70d6-8ead-4eb5-a824-79ee1971764a")
    REALLY_TIEFLING = Flag("REALLY_TIEFLING", "Tag", "7bf7207f-7406-49c0-b501-eaaa2bb4efd7")
    REALLY_DUERGARDWARF = Flag("REALLY_DUERGARDWARF", "Tag", "45b007f7-f4f6-46e2-9480-395a49b87ef3")
    REALLY_LOLTHDROWELF = Flag("REALLY_LOLTHDROWELF", "Tag", "c71eb8de-74e3-4d70-9826-22da7e2dc607")
    FIGHTER = Flag("FIGHTER", "Tag", "1ae7017c-4884-4a43-bc4a-742fa0d201c0")
    BARBARIAN = Flag("BARBARIAN", "Tag", "02913f9a-f696-40cf-acdf-32032afab32c")


class DC:
    """Классы сложности (Shared/Public/Shared/DifficultyClasses/DifficultyClasses.lsx)."""
    Act1_Easy = "31e92da6-bac9-46f7-af99-5f33d98fd4f0"     # 7
    Act1_Medium = "fa621d38-6f83-4e42-a55c-6aa651a75d46"   # 10


class NESTED:
    """Вложенные ванильные диалоги замены при полном отряде (ID ресурсов в банке игры)."""
    SwapRecruitment = "f02d36d9-1f59-33ee-b87d-82f4c13c501f"   # GLO_CompanionSwap_Recruitment (Уилл, Лаэ'зель)
    SwapCamp = "002e501b-6f1b-8357-1fde-20b1b4b7c1b9"          # GLO_CompanionSwap_Camp (Минск)
