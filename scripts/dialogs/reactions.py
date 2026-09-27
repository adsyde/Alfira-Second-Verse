"""Реакции Альфиры на поступки, акт 1 — design/reactions/01_act1.md (согласовано 2026-09-27).

Генерирует goal Osiris Mods/_MOD_/Story/RawFiles/Goals/ALFSV_Reactions.txt (руками не править) и флаги
«уже было» ALFSV_React_* (глобальные: одна реакция за игру). Флаги и события игры, способы «рядом»
A/B/C — design/reactions/01_act1.md «Для сборки» и docs/research/act1-flags.md.

  A — флаг из диалога + DB_DialogSpeakers(_Inst, Альфира, _)  (как Act1_ORI_Gale.txt:326-355);
  B — QRY_DEN_IsInDen / DB_InRegion / DB_Players (она в отряде);
  C — только «она спутница».

Одобрение — PROC_ChangeApprovalRatingForAllAvatars (_GLO_Shared_Origins.txt), как у ванильных спутников.
Реплики над головой (№1, 2/4, 5/7, 18) — места с custom="reaction" в scenes/places.py; запуск —
PROC_ALFSV_Place_Request(ключ) из goal ALFSV_World.txt (одна AD за раз, ждёт до 60 с).
"""
from __future__ import annotations

from dsl import new_flag

A = "S_DEN_Bard_4a405fba-3000-4c63-97e5-a8001ebb883c"
NULL = "NULL_00000000-0000-0000-0000-000000000000"
DEN = "S_DEN_RangerDen_SUB_50062397-bf9c-4765-9cbc-e40b5148f211"
MAYRINA = "S_HAG_Hagspawn_SurrogateMother_08c970d7-3138-45e8-8965-68eadf4b07cd"
GRYMFORGE = "S_UND_DuergarCamp_SUB_05c3bf1f-29a6-437c-9a98-c1ff0ec53a53"
PERFORM_MAX = 5          # №19: не больше +5 за акт

# Флаги игры (имя_uuid, как в goals Larian)
G = dict(
    AttackStart="DEN_AttackOnDen_Event_Start_c641da6a-b3f5-4873-bd34-c53768d30d6f",
    DenVictory="DEN_AttackOnDen_State_DenVictory_71c7f23e-3ff1-c9b8-3ef5-d75fa1b42c8d",
    HostileTieflings="DEN_AttackOnDen_State_HostileTieflings_c5641caa-4409-4739-a1fe-8263b8271f4e",
    Denouncing="DEN_ShadowDruid_Event_StartDenouncingScene_e01769d4-9ac4-17a0-584e-ceb26e4bc384",
    DenouncingInProgress="DEN_ShadowDruid_State_DenouncingInProgress_3143a5ba-c508-4a32-a2f1-8091731d83e0",
    LeadersDead="GOB_State_LeadersAreDead_a1c5b01f-4b7f-47ab-82b0-d24d9c6d8bc6",
    Lockdown="DEN_Lockdown_State_Active_0b54c7d2-b7b1-4d0f-b8e4-0cf1ee32b1eb",
    FreedChild="DEN_ShadowDruid_State_FreedChild_e0db3e8d-497d-33bb-ce67-91dff9fb1c67",
    KidFreed="DEN_ShadowDruid_State_KidFreed_8d9e9065-7bb5-a516-15c3-c9d8c1f4f5e2",
    KidDied="DEN_ShadowDruid_State_KidDied_5b5de896-e733-47ae-81df-85a4b25ebfd1",
    HelpedSaveVictim="DEN_HarpyMeal_State_HelpedSaveVictim_13491e5a-6381-2d8d-e015-5aae3948b794",
    RescuedChild="DEN_HarpyMeal_State_RescuedChild_7a90f576-f762-4710-aa4d-9a81905bd971",
    SurrogateReleased="HAG_HagSpawn_Quest_SurrogateReleased_dafa0dd7-c2bb-be04-6881-ed81a87373fd",
    HagDead="HAG_Hag_State_IsDead_781391e2-7d33-642d-28c0-e9b06cde32bb",
    HagTookMother="HAG_Hag_State_HagTookMother_38dc6752-5ab3-e108-64ed-fe63971d69fd",
    HelpingKarlach="PLA_KarlachRecruitment_State_HelpingKarlach_b7cd48bc-b9e3-419e-8ad0-c4837bc0cec0",
    AgreedToHelpKarlach="ORI_Karlach_Quest_AgreedToHelpNotRecruited_f08dc12e-cb2e-e373-e2eb-b0d2c7b0d7dc",
    KarlachHostile="PLA_KarlachRecruitment_Event_KarlachHostile_cb16919b-08da-485c-a9df-7911ba1572d1",
    KilledKarlach="PLA_KarlachRecruitment_State_KilledKarlach_ee2f4a40-6290-4a2b-ba3a-54da7dc3f69f",
    VoloEscaped="GOB_VoloBallad_State_VoloEscaped_13ae819f-b0b7-434d-9ebb-cee412b1a407",
    PlayersMetVolo="GOB_VoloBallad_State_PlayersMetVolo_0c341094-ae74-4a72-b2b6-3cd98a43ae11",
    GnomesFreed="UND_State_LeaderFreedGnomes_49acb531-d0c4-d3d1-6af4-c79e246e4327",
    GnomesLeave="UND_GnomeWorkers_Event_Leave_ad897c6f-87d5-4a30-88f0-41c92b965bc8",
    GnomesExecuted="UND_TheDrowNere_State_GnomesExecuted_7f3f882c-40fb-430e-8df6-c1d6e450aebd",
    GnomesHostile="UND_DuergarCamp_State_GnomesHostile_53aab2ec-c119-b4ed-c3b2-7181e4ecbaf7",
    Torture="GOB_Torturers_Assisted_aee96e28-e049-0e55-b5d8-c001580de642",
    ThrewRock="GOB_WolfPens_Event_ThrewRock_9af39233-b6e9-4279-b3ca-d68163b240bc",
    Crossbow="DEN_CapturedGoblin_State_SteppedInfrontOfCrossbow_dff39def-ac63-8851-1330-239b310f090f",
)

# Флаги мода «реакция уже была» (одна за игру). Имя → описание.
ONCE = {
    "GroveDefended": "Reaction 1: the Grove held against Minthara's attack",
    "GatesOpened": "Reaction 2: the hero opened the Grove gates to the goblins",
    "GroveSaved": "Reactions 3 / 3b: the Grove saved (Kagha exposed or the goblin leaders killed) - one of the two",
    "TieflingsExpelled": "Reaction 4: the ritual went ahead, the tieflings were driven out",
    "Arabella": "Reaction 5: Arabella saved",
    "ArabellaDied": "Reaction 6: Arabella died",
    "Mirkon": "Reaction 7: Mirkon saved from the harpies",
    "Mayrina": "Reaction 8: Mayrina freed / Auntie Ethel dead, Mayrina alive",
    "MayrinaToHag": "Reaction 9: Mayrina given to Auntie Ethel for power",
    "KarlachHelped": "Reaction 10: agreed to help Karlach",
    "KarlachAttacked": "Reaction 11: attacked or killed Karlach",
    "Volo": "Reaction 12: Volo freed from the goblin camp",
    "GnomesFreed": "Reaction 13: the deep gnomes of Grymforge freed",
    "GnomesHarmed": "Reaction 14: the deep gnomes executed or attacked",
    "Torture": "Reaction 15: the prisoner tortured in the goblin camp",
    "RockAtBear": "Reaction 16: rocks thrown at the bear in the goblin pens",
    "Sazza": "Reaction 17: Sazza shielded from the crossbow",
}
FLAGS = {k: new_flag(f"ALFSV_React_{k}", "Global", v) for k, v in ONCE.items()}


def goal(ids) -> str:
    def rf(k):
        f = FLAGS[k]
        return f"(FLAG){f.name}_{ids.flag(f)}"

    def react(k, value, ad=""):
        return f'PROC_ALFSV_React({rf(k)}, {value}, "{ad}");'

    def rule(head, conds, then):
        return ["IF" if head == "IF" else head] + _and(conds) + ["THEN"] + then + [""]

    def _and(conds):
        out = []
        for i, c in enumerate(conds):
            if i:
                out.append("AND")
            out.append(c)
        return out

    speakers = f"DB_DialogSpeakers(_Inst, {A}, _)"
    comp = "DB_ALFSV_IsCompanion(1)"
    o = ["Version 1", "SubGoalCombiner SGC_AND", "INITSECTION",
         "// GENERATED by scripts/dialogs/build.py from scripts/dialogs/reactions.py (design/reactions/01_act1.md).",
         "// Do not edit: change reactions.py and rebuild. Alfira's reactions to the hero's deeds, act 1.",
         "// A save where she is already a companion: the goal is new there, INIT runs on story patching and",
         "// only registers the cared-for tieflings (no retroactive approval).",
         "PROC_ALFSV_React_CaredFaction();",
         "KBSECTION", "//REGION One reaction: once per game (ALFSV_React_* flag), approval for every avatar, overhead line", "",
         "PROC", "PROC_ALFSV_React((FLAG)_Once, (INTEGER)_Value, (STRING)_AD)", "AND", comp, "AND",
         "NOT DB_GlobalFlag(_Once)", "THEN", "PROC_GlobalSetFlagAndCache(_Once);",
         f"PROC_ChangeApprovalRatingForAllAvatars({A}, _Value);", "PROC_ALFSV_React_AD(_AD);", "",
         "PROC", "PROC_ALFSV_React_AD((STRING)_AD)", "AND", '_AD != ""', "THEN", "PROC_ALFSV_Place_Request(_AD);", "",
         "//END_REGION", "", "//REGION Grove (1-7)", ""]
    # 1. Нападение Минтары отбито: Event_Start И DenVictory (DenVictory ставит и охота на гоблинов)
    o += ["// 1. Minthara's attack repelled: DenVictory after DEN_AttackOnDen_Event_Start (Act1_DEN_AttackOnDen.txt:456-465).",
          "// In the Grove +10 and a line; elsewhere (camp) +5"]
    o += rule("IF", [f"FlagSet((FLAG){G['DenVictory']}, {NULL}, _)", f"DB_GlobalFlag((FLAG){G['AttackStart']})",
                     f"QRY_DEN_IsInDen({A})"], [react("GroveDefended", 10, "React_GroveHeld")])
    o += rule("IF", [f"FlagSet((FLAG){G['DenVictory']}, {NULL}, _)", f"DB_GlobalFlag((FLAG){G['AttackStart']})",
                     f"NOT QRY_DEN_IsInDen({A})"], [react("GroveDefended", 5)])
    o += ["// 2. The gates opened to the goblins - she was there (in the party or in the Grove)"]
    o += rule("IF", [f"FlagSet((FLAG){G['HostileTieflings']}, {NULL}, _)", f"DB_Players({A})"],
              [react("GatesOpened", -10, "React_TieflingsOut")])
    o += rule("IF", [f"FlagSet((FLAG){G['HostileTieflings']}, {NULL}, _)", f"QRY_DEN_IsInDen({A})"],
              [react("GatesOpened", -10, "React_TieflingsOut")])
    o += ["// 3. Kagha exposed, the ritual stopped (Act1_DEN_ShadowDruid.txt:958-965): in the denouncing scene or in the Grove.",
          "// 3b. The goblin leaders killed - the Grove saved too. One reaction for both (ALFSV_React_GroveSaved)."]
    o += rule("IF", [f"FlagSet((FLAG){G['Denouncing']}, {NULL}, _Inst)", speakers], [react("GroveSaved", 5)])
    o += rule("PROC", [f'PROC_State_Changed({DEN}, "DEN", "DEN_State_RitualStopped")', f"QRY_DEN_IsInDen({A})"],
              [react("GroveSaved", 5)])
    o += rule("IF", [f"FlagSet((FLAG){G['LeadersDead']}, {NULL}, _)"], [react("GroveSaved", 5)])
    o += ["// 4. The ritual went ahead: the vines close the Grove, the tieflings are out (Act1_DEN_Lockdown.txt:120-140)"]
    o += rule("IF", [f"FlagSet((FLAG){G['Lockdown']}, {NULL}, _)"], [react("TieflingsExpelled", -10, "React_TieflingsOut")])
    o += ["// 5. Arabella freed - she was in the snake court dialog"]
    o += rule("IF", [f"FlagSet((FLAG){G['FreedChild']}, _, _Inst)", speakers], [react("Arabella", 5, "React_Children")])
    o += ["// 6. Arabella died - she will hear of it"]
    o += rule("IF", [f"FlagSet((FLAG){G['KidDied']}, {NULL}, _)"], [react("ArabellaDied", -3)])
    o += ["// 7. Mirkon saved: the game sets HelpedSaveVictim on every player in the cove (Act1_DEN_HarpyMeal.txt:770-776)"]
    o += rule("IF", [f"FlagSet((FLAG){G['HelpedSaveVictim']}, {A}, _)"], [react("Mirkon", 5, "React_Children")])
    o += ["//END_REGION", "", "//REGION Before recruitment: 3, 5, 6, 7 count once, when she joins", "",
          "// a PROC, not DB rules: later changes of these flags go through the rules above (with 'near')",
          "IF", comp, "THEN", "PROC_ALFSV_React_BeforeRecruitment();", ""]
    retro = "PROC_ALFSV_React_BeforeRecruitment()"
    for flag in ("Denouncing", "DenouncingInProgress"):
        o += rule("PROC", [retro, f"DB_GlobalFlag((FLAG){G[flag]})"], [react("GroveSaved", 5)])
    o += rule("PROC", [retro, f"DB_GlobalFlag((FLAG){G['KidFreed']})"], [react("Arabella", 5)])
    o += rule("PROC", [retro, f"DB_GlobalFlag((FLAG){G['KidDied']})"], [react("ArabellaDied", -3)])
    for flag in ("RescuedChild", "HelpedSaveVictim"):
        o += rule("PROC", [retro, "DB_Avatars(_Avatar)", f"GetFlag((FLAG){G[flag]}, _Avatar, 1)"], [react("Mirkon", 5)])
    o += ["//END_REGION", "", "//REGION The wilds (8-12)", ""]
    o += ["// 8. Mayrina freed (Auntie Ethel's plea, in the dialog) or Ethel dead and Mayrina alive (she was in the party)"]
    o += rule("IF", [f"FlagSet((FLAG){G['SurrogateReleased']}, _, _Inst)", speakers], [react("Mayrina", 5)])
    o += rule("IF", [f"FlagSet((FLAG){G['HagDead']}, _, _)", f"NOT DB_Dead({MAYRINA})",
                     f"NOT DB_GlobalFlag((FLAG){G['HagTookMother']})", f"DB_Players({A})"], [react("Mayrina", 5)])
    o += ["// 9. Mayrina left to Ethel for power"]
    o += rule("IF", [f"FlagSet((FLAG){G['HagTookMother']}, _, _Inst)", speakers], [react("MayrinaToHag", -5)])
    o += ["// 10. Agreed to help Karlach (her dialog takes everyone in the trigger)"]
    for flag in ("HelpingKarlach", "AgreedToHelpKarlach"):
        o += rule("IF", [f"FlagSet((FLAG){G[flag]}, _, _Inst)", speakers], [react("KarlachHelped", 5)])
    o += ["// 11. Attacked or killed Karlach"]
    o += rule("IF", [f"FlagSet((FLAG){G['KarlachHostile']}, _, _Inst)", speakers], [react("KarlachAttacked", -5)])
    o += rule("IF", [f"FlagSet((FLAG){G['KilledKarlach']}, _, _)", f"DB_Players({A})"], [react("KarlachAttacked", -5)])
    o += ["// 12. Volo freed from the goblin camp (he comes to camp; guard against the debug teleport)"]
    o += rule("IF", [f"FlagSet((FLAG){G['VoloEscaped']}, _, _)", f"DB_GlobalFlag((FLAG){G['PlayersMetVolo']})"],
              [react("Volo", 2)])
    o += ["//END_REGION", "", "//REGION Underdark and the goblin camp (13-17)", ""]
    o += ["// 13-14. Grymforge deep gnomes: freed / executed or attacked - she was in the duergar camp"]
    for flag in ("GnomesFreed", "GnomesLeave"):
        o += rule("IF", [f"FlagSet((FLAG){G[flag]}, _, _)", f"DB_InRegion({A}, {GRYMFORGE})"], [react("GnomesFreed", 5)])
    for flag in ("GnomesExecuted", "GnomesHostile"):
        o += rule("IF", [f"FlagSet((FLAG){G[flag]}, _, _)", f"DB_InRegion({A}, {GRYMFORGE})"], [react("GnomesHarmed", -5)])
    o += ["// 15-17. In the dialog with her present: torture, rocks at the bear, Sazza shielded from the crossbow"]
    o += rule("IF", [f"FlagSet((FLAG){G['Torture']}, _, _Inst)", speakers], [react("Torture", -5)])
    o += rule("IF", [f"FlagSet((FLAG){G['ThrewRock']}, _, _Inst)", speakers], [react("RockAtBear", -2)])
    o += rule("IF", [f"FlagSet((FLAG){G['Crossbow']}, _, _Inst)", speakers], [react("Sazza", 2)])
    o += ["//END_REGION", "",
          "//REGION 18. Killing tieflings: -10 for each, like Wyll (Act1_OriginMoments_Wyll.txt:4-6, _GLO_Shared_Origins.txt 'Killing NPCs')", "",
          "PROC", "PROC_ALFSV_React_CaredFaction()", "AND", comp, "THEN",
          f"DB_CompanionCaredFaction((CHARACTER){A}, (FACTION)ACT1_DEN_Tieflings_ca9de2d9-9022-9215-6d9b-676d916dcb5a, -10, 1, 0);",
          f"DB_CompanionCaredFaction((CHARACTER){A}, (FACTION)ACT1_DEN_AttackOnDen_NPC_08f28bce-a261-35e2-9914-6aa8b3eea155, -10, 1, 0);",
          "", "IF", comp, "THEN", "PROC_ALFSV_React_CaredFaction();", "",
          "// the first such death: her line (the game inserts this fact on every reaction; it triggers once)",
          "IF", f"DB_CompanionReactedToFactionMemberDeath({A}, _Faction)", "THEN",
          'PROC_ALFSV_React_AD("React_TieflingKilled");', "", "//END_REGION", "",
          f"//REGION 19. A good performance near her (PERFORM_POSITIVE, _CRIME_BardReactions.txt): +1, at most +{PERFORM_MAX} in act 1", "",
          "IF", 'StatusApplied(_Performer, "PERFORM_POSITIVE", _, _)', "AND", "DB_PartyMembers((CHARACTER)_Performer)", "AND",
          f"_Performer != {A}", "AND", comp, "AND", f"DB_Players({A})", "AND", "IsInCombat(_Performer, 0)", "AND",
          f"QRY_SpeakerIsInDialogRange(_Performer, {A})", "AND", "QRY_ALFSV_Chapters_InAct(1)", "THEN",
          "PROC_ALFSV_React_Perform();", "",
          "PROC", "PROC_ALFSV_React_Perform()", "AND", "NOT DB_ALFSV_React_Performed(_)", "THEN",
          "DB_ALFSV_React_Performed(0);", "",
          "PROC", "PROC_ALFSV_React_Perform()", "AND", "DB_ALFSV_React_Performed(_N)", "AND", f"_N < {PERFORM_MAX}", "AND",
          "IntegerSum(_N, 1, _Next)", "THEN", "NOT DB_ALFSV_React_Performed(_N);", "DB_ALFSV_React_Performed(_Next);",
          f"PROC_ChangeApprovalRatingForAllAvatars({A}, 1);", "", "//END_REGION", "EXITSECTION", "", "ENDEXITSECTION", ""]
    return "\n".join(o)
