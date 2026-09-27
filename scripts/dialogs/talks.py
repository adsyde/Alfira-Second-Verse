"""Разговоры акта 1 по событиям и по месту — goal Osiris ALFSV_Talks.txt (генерируется build.py, руками не править).

Сценарии: design/dialogs/11_act1_events.md (С1–С7), design/dialogs/12_act1_local.md (Л1–Л8, К1–К15), сцены —
scripts/dialogs/scenes/events.py и local.py. Механизм по данным игры — docs/research/local-dialogs.md.

  * «!» — только ванильная PROC_RelationshipDialog (Patch8_HotFix9/…/_GLOBAL_Shared_RelationshipDialogs.txt), ванильные
    файлы не переопределяются. Разговоры по событиям — «в мире или в лагере» (DB_RelationshipDialog_WRD_TriggerInCamp)
    и не гаснут (DB_ExclamationDialog_NeverStop); локальные — только в мире, гаснут дальше 30 м.
  * Один раз за игру: DB_ALFSV_TalkQueued(ключ) + DB_RelationshipDialogsFinished игры. «Не сейчас» (флаг
    ALFSV_Talk_Postponed на ней) — знак ставится снова.
  * Сцены перед диалогами NPC (Л2–Л4) — PROC_DefineSingleOriginMoment(диалог NPC, тег ALFIRA, —, COM, —). Тега ALFIRA
    на её персонаже нет (ни в шаблоне, ни в Origins.lsx, ни в goals игры) — SetTag здесь.
  * К1–К15 — места ads.place с custom="talk": здесь только запуск PROC_ALFSV_Place_Request (goal ALFSV_World.txt).
"""
from __future__ import annotations

from dsl import new_flag
from reactions import G

A = "S_DEN_Bard_4a405fba-3000-4c63-97e5-a8001ebb883c"
NULL = "NULL_00000000-0000-0000-0000-000000000000"
KARLACH = "S_Player_Karlach_2c76687d-93a2-477b-8b18-8a14b549304c"
DAMMON = "S_DEN_Weaponsmith_e2ad06ec-8034-479a-9f69-b86faea6dc79"
ASHARAK = "S_DEN_Trainer_02025646-347a-4235-aef7-e46b7c94b435"
TAG_ALFIRA = "ALFIRA_c93d7c45-ff8f-4565-b4de-5b5eb48207bb"
INPARTY = "ALFSV_Alfira_InParty_b2950129-fdd2-4cda-8182-cf41cfd5d809"
DEN_SUB = "S_DEN_RangerDen_SUB_50062397-bf9c-4765-9cbc-e40b5148f211"

# диалоги NPC, на которые встают сцены Л2–Л4 (Act1_DEN_Training.txt:7, Act1_DEN_Misc.txt:294-295)
NPC_DIALOG = {"Asharak": "DEN_Thieflings_Trainer_f2596c8f-2b4f-0c9c-f371-e7940f4405d4",
              "Lakrissa": "DEN_General_TieflingGuard10_d43304e2-1268-7715-0d15-e28e52108970",
              "Dammon": "DEN_Weaponsmith_PostEA_f2e19bab-4804-9a49-c7ee-0a190f1fcafd"}

GAME = dict(
    RevealedTadpole="DEN_Apprentice_Event_RevealedTadpole_246e8df4-cd5d-da9f-7b19-cd8785478c6e",
    RaiderVictory="DEN_AttackOnDen_State_RaiderVictory_abe1bce8-c234-4afe-a490-76210d98a078",
    GnollsDead="PLA_ConflictedFlind_State_RegularGnollsDead_7415a408-ed52-4e7c-8a96-fe697647e24a",
    Cultists="PLA_KarlachRecruitmentTollhouse_Knows_RefugeesAreCultists_8b18c014-7558-4bab-aa35-37d135fc8630",
    VoloOnStage="GOB_VoloBallad_State_OnStage_0bc1d7d7-9129-4c6e-188d-054640cea3b9",
    TookGruel="DEN_Thieflings_Event_TookGruel_e9166e18-05a7-16da-0b43-dd1ff8674e0a",
    TookGruel2="DEN_Thieflings_Event_TookGruel2_cbf45767-7dac-0bdc-1f0f-8203b44798d9",
    Drums="GOB_Checkpoint_Event_ReactOnPlayerPerformingSong_fa4c345b-b443-4d6f-8ae7-51144b29f261",
    CelebrationNight="NIGHT_GoblinHunt_TieflingCelebration_1ad8c357-2695-4d5c-b5f9-8b8c07803121",
    CelebrationTonight="ALFSV_Celebration_Tonight_286ff093-d8b0-584d-9e8d-7c92853e9b5c",
)
OBJ = dict(
    ZevlorMap="S_DEN_TieflingLeaderMap_1ba813e9-28cc-4be2-96de-c7f50d2ee445",
    CampsiteBox="S_HAG_CampsiteBox_15dcab17-53d1-4290-913f-18f6a2ec03fc",
    KidsBox="S_FOR_KidsGameBox_f98642cb-31d9-4a61-8b7a-6e9d07059d54",
    HoleBook="S_FOR_HoleBook_da2a1502-399f-440d-93be-db6930231525",
    Tome="S_FOR_DangerousBook_Tome_73ea8888-ed82-4ca5-b9f9-0c9119873507",
    VoloArea="S_GOB_VoloBallad_FirstHeardArea_7d714a14-2d80-44d4-ba90-479e8510c024",
    Okta="S_DEN_Tiefling_FoodTrader_001_1b35671b-e5d7-4943-bbd0-4c816b69b7cb",
    UnderdarkSub="S_UND_Underdark_SUB_b379a862-a59f-4e52-9166-23fbe0e8976e",
    HideoutPos="S_DEN_AttackKidPos_011_653cf07f-e6ac-46eb-bb02-041ed278498e",   # место в убежище детей при налёте
)
VB = dict(
    Campsite="HAG_Campsite_VB_c34d5084-a2b4-63ec-9e03-75df85e54617",
    Hyena="PLA_DyingHyena_VB_HyenaRunning_d8cd0b3a-7a54-f0a5-765e-862974c6c438",
    KidsGame="FOR_KidsGame_VB_37723c9c-7012-7c11-7d53-64e736a8d75c",
    GithDummy="CRE_YouthTraining_VB_TrainingDummyComment_045d785a-5d7d-98d4-7760-4c9050d49244",
    GithSketches="CRE_YouthTraining_VB_AnatomicalSketchesComment_9fea9cc0-806f-3e73-f770-6d1454591f92",
)
DEFENSELESS = "ACT1_DEN_AttackOnDen_Defenseless_0d52984d-82c0-44b3-861c-5f8107982525"   # роль «Hideout» при налёте
NEAR_M = 15.0            # «она рядом»: в отряде и в 15 м от героя из диалога / от предмета

LEFT_FOR_GROVE = new_flag("ALFSV_LeftForGrove", "Global",
                          "S2b: after the gates were opened Alfira left the party for good, went to the Grove and died in the raid")
FLAGS = [LEFT_FOR_GROVE]


def goal(ids) -> str:
    from scenes import events as ev, local as lo
    from scenes.places import PLACES as WORLD_PLACES

    def fl(f):
        return f"(FLAG){f.name}_{ids.flag(f)}"

    def dlg(s):
        return f"(DIALOGRESOURCE){s.name}_{s.dialog_id}"

    def place_dlg(key, places):
        s = next(p.scene for p in places if p.key == key)
        return dlg(s)

    def rule(head, conds, then):
        out = [head]
        for i, c in enumerate(conds):
            out += (["AND"] if i else []) + [c]
        return out + ["THEN"] + then + [""]

    POST = fl(ev.POSTPONED)
    o = ["Version 1", "SubGoalCombiner SGC_AND", "INITSECTION",
         "// GENERATED by scripts/dialogs/build.py from scripts/dialogs/talks.py (design/dialogs/11_act1_events.md,",
         "// 12_act1_local.md). Do not edit: change talks.py / scenes/events.py / scenes/local.py and rebuild.",
         "// Alfira's act 1 talks: '!' over her (vanilla PROC_RelationshipDialog), scenes before NPC dialogs (origin",
         "// moments on the ALFIRA tag), overhead lines K1-K15 (places of ALFSV_World.txt). A save where she is already a",
         "// companion: the goal is new there, INIT runs on story patching - tag and origin moments are set up.",
         "PROC_ALFSV_Talks_Data();", "PROC_ALFSV_Talks_Init();", "KBSECTION",
         "//REGION Data (re-inserted at every level start, so new talks reach existing saves)", "",
         "IF", "LevelGameplayStarted(_, _)", "THEN", "PROC_ALFSV_Talks_Data();", "PROC_ALFSV_Talks_Init();", "",
         "PROC", "PROC_ALFSV_Talks_Data()", "THEN"]
    for key, s in ev.TALKS.items():
        o.append(f'DB_ALFSV_Talk("{key}", {dlg(s)}, "event");')
    for key, s in lo.TALKS.items():
        o.append(f'DB_ALFSV_Talk("{key}", {dlg(s)}, "local");')
    o.append("// events: the mark shows in the world or in camp (not at night) and does not go out when you walk away")
    for s in ev.TALKS.values():
        o.append(f"DB_RelationshipDialog_WRD_TriggerInCamp({dlg(s)}, (FLAG){NULL});")
        o.append(f"DB_ExclamationDialog_NeverStop({dlg(s)}, (FLAG){NULL});")
    o.append("// S2b, the farewell: try to start it at once (then the usual mark)")
    o.append(f"DB_RelationshipDialog_AutostartTryOnce({dlg(ev.C2B)}, (FLAG){NULL});")
    o += ["", "//END_REGION", "",
          "//REGION The ALFIRA tag (origin moments look for it, QRY_IsTaggedForOM) and the origin moments", "",
          "IF", "DB_ALFSV_IsCompanion(1)", "THEN", "PROC_ALFSV_Talks_Init();", ""]
    o += rule("PROC", ["PROC_ALFSV_Talks_Init()", "DB_ALFSV_IsCompanion(1)", f"IsTagged({A}, (TAG){TAG_ALFIRA}, 0)"],
              [f"SetTag({A}, (TAG){TAG_ALFIRA});"])
    o += rule("PROC", ["PROC_ALFSV_Talks_Init()", "DB_ALFSV_IsCompanion(1)"], ["PROC_ALFSV_Talks_DefineOMs();"])
    # Л2 Ашарак, Л3 Лакрисса (до праздника): один раз — OM сам снимается после сцены (_GLO_Shared_OriginMoments.txt)
    for key in ("Asharak", "Lakrissa"):
        conds = ["PROC_ALFSV_Talks_DefineOMs()", f'NOT DB_ALFSV_OM("{key}")']
        if key == "Lakrissa":
            conds += [f"NOT DB_CampNight_Completed((FLAG){GAME['CelebrationNight']})",
                      f"NOT DB_GlobalFlag((FLAG){GAME['CelebrationTonight']})"]
        o += [f"// L{2 if key == 'Asharak' else 3}: {key} - the scene before the NPC's own dialog (COM only)"]
        o += rule("PROC", conds, [f'DB_ALFSV_OM("{key}");',
                                  f"PROC_DefineSingleOriginMoment((DIALOGRESOURCE){NPC_DIALOG[key]}, (TAG){TAG_ALFIRA}, "
                                  f"(DIALOGRESOURCE){NULL}, {dlg(lo.OMS[key])}, (DIALOGRESOURCE){NULL});"])
    o += ["// L3 only before the celebration: the night starts - the scene is no longer offered"]
    o += rule("PROC", ["PROC_CAMP_GoblinHuntCelebration_SetupTieflings()"],
              [f"PROC_ClearOriginMoment({dlg(lo.L3)});"])
    o += ["// L4: Dammon - only while Karlach is not in the party (her own origin moment is on his dialog,",
          "// Act1_OriginMoments_Karlach.txt:64); with Karlach - the same scene as a '!' after his dialog (below)"]
    o += rule("PROC", ["PROC_ALFSV_Talks_DefineOMs()", 'NOT DB_ALFSV_OM("Dammon")'],
              ['DB_ALFSV_OM("Dammon");', 'DB_ALFSV_OMWanted("Dammon");'])
    o += rule("IF", ['DB_ALFSV_OMWanted("Dammon")', f"NOT DB_Players({KARLACH})", 'NOT DB_ALFSV_OMDefined("Dammon")'],
              ['DB_ALFSV_OMDefined("Dammon");',
               f"PROC_DefineSingleOriginMoment((DIALOGRESOURCE){NPC_DIALOG['Dammon']}, (TAG){TAG_ALFIRA}, "
               f"(DIALOGRESOURCE){NULL}, {dlg(lo.L4)}, (DIALOGRESOURCE){NULL});"])
    o += rule("IF", ['DB_ALFSV_OMDefined("Dammon")', f"DB_Players({KARLACH})"],
              ['NOT DB_ALFSV_OMDefined("Dammon");', f"PROC_ClearOriginMoment({dlg(lo.L4)});"])
    for key, s in lo.OMS.items():
        o += rule("IF", [f"DialogEnded({dlg(s)}, _)"], [f'DB_ALFSV_OMPlayed("{key}");'])
    o += rule("IF", [f"DialogEnded({dlg(lo.L4)}, _)", 'DB_ALFSV_OMWanted("Dammon")'],
              ['NOT DB_ALFSV_OMWanted("Dammon");', f"PROC_ClearOriginMoment({dlg(lo.L4)});"])
    o += rule("PROC", ["PROC_ALFSV_Talks_ClearOMs()"],
              [f"PROC_ClearOriginMoment({dlg(s)});" for s in lo.OMS.values()] + ['NOT DB_ALFSV_OMWanted("Dammon");'])
    o += ["//END_REGION", "",
          "//REGION '!' over her: queue once, the vanilla relationship dialog system shows it", "",
          "// she is with us: in the active party, or in camp as a companion (then the mark shows in camp)"]
    o += rule("QRY", ["QRY_ALFSV_Talk_WithUs()", f"DB_Players({A})"], ["DB_NOOP(1);"])
    o += rule("QRY", ["QRY_ALFSV_Talk_WithUs()", f"NOT DB_Players({A})", f"DB_PartOfTheTeam({A})"], ["DB_NOOP(1);"])
    o += ["// she was near the event: a speaker of that dialog, or in the party within 15 m of its hero"]
    o += rule("QRY", ["QRY_ALFSV_Talk_Near((INTEGER)_Inst)", f"DB_DialogSpeakers(_Inst, {A}, _)"], ["DB_NOOP(1);"])
    o += rule("QRY", ["QRY_ALFSV_Talk_Near((INTEGER)_Inst)", f"DB_Players({A})", "DB_DialogPlayers(_Inst, _Player, _)",
                      f"GetDistanceTo({A}, _Player, _Dist)", f"_Dist < {NEAR_M}"], ["DB_NOOP(1);"])
    o += rule("QRY", ["QRY_ALFSV_Talk_NearObject((GUIDSTRING)_Object)", f"DB_Players({A})",
                      f"GetDistanceTo({A}, _Object, _Dist)", f"_Dist < {NEAR_M}"], ["DB_NOOP(1);"])
    o += rule("PROC", ["PROC_ALFSV_Talk_Event((STRING)_Key)", "QRY_ALFSV_Talk_WithUs()"], ["PROC_ALFSV_Talk_Queue(_Key);"])
    o += rule("PROC", ["PROC_ALFSV_Talk_Local((STRING)_Key)", f"DB_Players({A})"], ["PROC_ALFSV_Talk_Queue(_Key);"])
    o += rule("PROC", ["PROC_ALFSV_Talk_Queue((STRING)_Key)", "DB_ALFSV_IsCompanion(1)", f"NOT DB_Dead({A})",
                       "NOT DB_ALFSV_TalkQueued(_Key)", "DB_ALFSV_Talk(_Key, _, _)"],
              ["DB_ALFSV_TalkQueued(_Key);", "PROC_ALFSV_Talk_Start(_Key);"])
    o += rule("PROC", ["PROC_ALFSV_Talk_Start((STRING)_Key)", "DB_ALFSV_Talk(_Key, _Dialog, _)"],
              [f"PROC_RelationshipDialog((CHARACTER){A}, _Dialog, (FLAG){NULL}, {A}, 0, -100);"])
    o += ["// 'Not now': the game has marked it finished - put the mark up again, same talk"]
    o += rule("IF", [f"DB_RelationshipDialogsFinished((CHARACTER){A}, _Dialog, _Flag)", "DB_ALFSV_Talk(_Key, _Dialog, _)",
                     f"GetFlag({POST}, {A}, 1)"],
              [f"ClearFlag({POST}, {A}, 0);", f"NOT DB_RelationshipDialogsFinished({A}, _Dialog, _Flag);",
               "PROC_ALFSV_Talk_Start(_Key);"])
    o += ["//END_REGION", "", "//REGION Events S1-S7 (the same game flags as the reactions, design/reactions/01_act1.md)", ""]
    o += ["// S1: the Grove held - Minthara's attack repelled (reaction 1) or the goblin leaders dead, tieflings not expelled (3b)"]
    o += rule("IF", [f"FlagSet((FLAG){G['DenVictory']}, {NULL}, _)", f"DB_GlobalFlag((FLAG){G['AttackStart']})"],
              ['PROC_ALFSV_Talk_Event("GroveHeld");'])
    o += rule("IF", [f"FlagSet((FLAG){G['LeadersDead']}, {NULL}, _)", f"NOT DB_GlobalFlag((FLAG){G['Lockdown']})",
                     f"NOT DB_GlobalFlag((FLAG){G['HostileTieflings']})"], ['PROC_ALFSV_Talk_Event("GroveHeld");'])
    o += ["// S2a: the ritual went ahead, the tieflings are driven out (reaction 4) - she hears of it wherever she is"]
    o += rule("IF", [f"FlagSet((FLAG){G['Lockdown']}, {NULL}, _)"], ['PROC_ALFSV_Talk_Event("RoadExpelled");'])
    o += ["// S2b: the gates opened to the goblins (reaction 2) - in the party or in camp"]
    o += rule("IF", [f"FlagSet((FLAG){G['HostileTieflings']}, {NULL}, _)"], ['PROC_ALFSV_Talk_Event("GatesOpened");'])
    o += ["// S3: Kagha exposed, the ritual stopped (reaction 3) - she was there"]
    o += rule("IF", [f"FlagSet((FLAG){G['Denouncing']}, {NULL}, _Inst)", "QRY_ALFSV_Talk_Near(_Inst)"],
              ['PROC_ALFSV_Talk_Event("Kagha");'])
    o += rule("PROC", [f'PROC_State_Changed({DEN_SUB}, "DEN", "DEN_State_RitualStopped")', f"QRY_DEN_IsInDen({A})"],
              ['PROC_ALFSV_Talk_Event("Kagha");'])
    o += ["// S4: Arabella (reaction 5) or Mirkon (reaction 7) saved - one talk, about the first one (Mirkon: flag on her)"]
    o += rule("IF", [f"FlagSet((FLAG){G['FreedChild']}, _, _Inst)", "QRY_ALFSV_Talk_Near(_Inst)"],
              ['PROC_ALFSV_Talk_Event("Children");'])
    o += rule("IF", [f"FlagSet((FLAG){G['HelpedSaveVictim']}, {A}, _)", "DB_ALFSV_IsCompanion(1)",
                     'NOT DB_ALFSV_TalkQueued("Children")'],
              [f"SetFlag({fl(ev.MIRKON)}, {A}, 0);", 'PROC_ALFSV_Talk_Event("Children");'])
    o += ["// S5: agreed to help Karlach (reaction 10) - she was there"]
    for flag in ("HelpingKarlach", "AgreedToHelpKarlach"):
        o += rule("IF", [f"FlagSet((FLAG){G[flag]}, _, _Inst)", "QRY_ALFSV_Talk_Near(_Inst)"],
                  ['PROC_ALFSV_Talk_Event("Karlach");'])
    o += ["// S6: Nettie finds the tadpole and explains ceremorphosis (DEN_Apprentice, Act1_DEN_Apprentice.txt:114-120) -",
          "// the first talk about it with her there. (GLO_Tadpole_TrueSoulCorpse is a dialog with a corpse, often",
          "// without her, and it is not about ceremorphosis.) Alfira has no tadpole: ILLITHID is set only on the",
          "// starting players (GLO_Tadpole.txt:17-21)."]
    o += rule("IF", [f"FlagSet((FLAG){GAME['RevealedTadpole']}, _, _Inst)", "QRY_ALFSV_Talk_Near(_Inst)"],
              ['PROC_ALFSV_Talk_Event("Tadpole");'])
    o += ["// S7: the first tiefling killed (reaction 18; the game inserts the fact once per faction) - once, wherever she is"]
    o += rule("IF", [f"DB_CompanionReactedToFactionMemberDeath((CHARACTER){A}, _Faction)"], ['PROC_ALFSV_Talk_Event("Blood");'])
    o += ["//END_REGION", "",
          "//REGION S2a: below 20 approval she leaves with the refugees (ALFSV_LeftWithRefugees, she returns in act 2)", ""]
    o += rule("IF", [f"DialogEnded({dlg(ev.C2A)}, _)", f"DB_GlobalFlag({fl(ev.LEFT_WITH_REFUGEES)})", "DB_ALFSV_IsCompanion(1)"],
              ["PROC_ALFSV_Talk_LeaveWithRefugees();"])
    o += ["// Out of the party like a companion leaving (the approval and the in-party dialog stay for act 2), and she walks",
          "// away after the refugees. DB_ALFSV_Left blocks recruitment in act 1 (ALFSV_Companion.txt)."]
    o += rule("PROC", ["PROC_ALFSV_Talk_LeaveWithRefugees()"],
              ["NOT DB_ALFSV_IsCompanion(1);", 'DB_ALFSV_Left("Refugees");', "PROC_ALFSV_Talks_ClearOMs();",
               f'PROC_Origins_CompanionLeaveTemporarily((CHARACTER){A}, "ALFSV_LeftWithRefugees");',
               f'PROC_DisappearOutOfSight({A}, "Walk", 1, "ALFSV_Talk_LeftWithRefugees");'])
    o += ["//END_REGION", "",
          "//REGION S2b: after the farewell she leaves for good, goes to the Grove and dies in the raid, as without recruitment", "",
          "// the farewell said (flag on its last line)"]
    o += rule("IF", [f"DialogEnded({dlg(ev.C2B)}, _)", f"DB_GlobalFlag({fl(ev.GATES_FAREWELL)})"],
              ["PROC_ALFSV_Talk_GoToGrove();"])
    o += ["// failsafe: the raid is over or a long rest, and the farewell was never clicked - she leaves without it"]
    o += rule("IF", [f"FlagSet((FLAG){GAME['RaiderVictory']}, {NULL}, _)", 'DB_ALFSV_TalkQueued("GatesOpened")'],
              ["PROC_ALFSV_Talk_GoToGrove();"])
    o += rule("PROC", ["PROC_LongRest()", 'DB_ALFSV_TalkQueued("GatesOpened")'], ["PROC_ALFSV_Talk_GoToGrove();"])
    o += rule("PROC", ["PROC_ALFSV_Talk_GoToGrove()", "DB_ALFSV_IsCompanion(1)"],
              [f"PROC_CancelRelationshipDialog((CHARACTER){A}, {dlg(ev.C2B)}, (FLAG){NULL});",
               "NOT DB_ALFSV_IsCompanion(1);", 'DB_ALFSV_Left("GatesOpened");', f"PROC_GlobalSetFlagAndCache({fl(LEFT_FOR_GROVE)});",
               "PROC_ALFSV_Talks_ClearOMs();",
               f'PROC_Origins_CompanionLeavePermanently((CHARACTER){A}, "ALFSV_GatesOpened");',
               f'PROC_DisappearOutOfSight({A}, "Run", 1, "ALFSV_Talk_GoneToGrove");',
               f'ObjectTimerLaunch({A}, "ALFSV_Talk_ToGrove", 20000);'])
    o += rule("IF", [f'EntityEvent({A}, "ALFSV_Talk_GoneToGrove")'], ["PROC_ALFSV_Talk_DieInGrove();"])
    o += rule("IF", [f'ObjectTimerFinished({A}, "ALFSV_Talk_ToGrove")'], ["PROC_ALFSV_Talk_DieInGrove();"])
    o += ["// In the children's hideout, where the raid finds her in the game (DB_DEN_NPC role \"Hideout\", Act1_DEN_Misc.txt:197)"]
    o += rule("PROC", ["PROC_ALFSV_Talk_DieInGrove()", "NOT DB_ALFSV_Talk_InHideout(1)", f"NOT DB_Dead({A})"],
              ["DB_ALFSV_Talk_InHideout(1);", f'ObjectTimerCancel({A}, "ALFSV_Talk_ToGrove");', f"SetOnStage({A}, 1);",
               f"SetFaction({A}, (FACTION){DEFENSELESS});", f'TeleportTo({A}, {OBJ["HideoutPos"]}, "");',
               "PROC_ALFSV_Talk_HideoutFate();"])
    o += ["// The hideout massacre has not happened yet: the game kills her itself (PROC_DEN_AttackOnDen_KillKids: Die(S_DEN_Bard),",
          "// Act1_DEN_AttackOnDen.txt:3128-3133). Already happened, or the raid is over: now, the way KillKids does it."]
    o += rule("PROC", ["PROC_ALFSV_Talk_HideoutFate()", 'DB_OnlyOnce("DEN_AttackOnDen_KidsDieOrRun")'],
              ["PROC_ALFSV_Talk_DieNow();"])
    o += rule("PROC", ["PROC_ALFSV_Talk_HideoutFate()", f"DB_GlobalFlag((FLAG){GAME['RaiderVictory']})"],
              ["PROC_ALFSV_Talk_DieNow();"])
    o += rule("IF", [f"FlagSet((FLAG){GAME['RaiderVictory']}, {NULL}, _)", "DB_ALFSV_Talk_InHideout(1)"],
              ["PROC_ALFSV_Talk_DieNow();"])
    o += rule("PROC", ["PROC_ALFSV_Talk_DieNow()", f"NOT DB_Dead({A})"],
              [f"Die({A}, DEATHTYPE.DoT, 1);", f'CreatePuddle({A}, "SurfaceBlood", 10, 15, 10, 20, 1.0);'])
    o += ["//END_REGION", "", "//REGION Local '!' L1, L5-L8 and L4 with Karlach (design/dialogs/12_act1_local.md)", ""]
    o += ["// L1: someone in the party studies Zevlor's map (Act1_DEN_TieflingRefugees.txt:190-204), she is next to it"]
    o += rule("IF", [f"UseStarted(_Player, {OBJ['ZevlorMap']})", "DB_Players(_Player)",
                     f"QRY_ALFSV_Talk_NearObject({OBJ['ZevlorMap']})"], ['PROC_ALFSV_Talk_Local("ZevlorMap");'])
    o += ["// L5: the gnoll pack is dead (Act1_PLA_ConflictedFlind.txt:1167-1174)"]
    o += rule("IF", [f"FlagSet((FLAG){GAME['GnollsDead']}, {NULL}, _)"], ['PROC_ALFSV_Talk_Local("Gnolls");'])
    o += ["// L6: the 'refugees' in the Tollhouse are Zariel's cultists (Act1_PLA_KarlachRecruitment.txt:560-575)"]
    o += rule("IF", [f"FlagSet((FLAG){GAME['Cultists']}, {NULL}, _)"], ['PROC_ALFSV_Talk_Local("Tollhouse");'])
    o += ["// L7: after the vanilla line at the ravaged campsite (Act1_HAG_Boosters.txt:14)"]
    for ev_name in ("VoiceBarkEnded((VOICEBARKRESOURCE){vb}, _)", "VoiceBarkFailed((VOICEBARKRESOURCE){vb})"):
        o += rule("IF", [ev_name.format(vb=VB["Campsite"]), f"QRY_ALFSV_Talk_NearObject({OBJ['CampsiteBox']})"],
                  ['PROC_ALFSV_Talk_Local("Campsite");'])
    k10 = place_dlg("Talk_K10_Volo", lo.PLACES)
    o += ["// L8: Volo sings to the goblins - first her overhead line K10, then the '!'"]
    o += rule("IF", [f"AutomatedDialogEnded({k10}, _)"], ['PROC_ALFSV_Talk_Local("Volo");'])
    o += rule("IF", [f"EnteredTrigger({A}, {OBJ['VoloArea']})", f"DB_GlobalFlag((FLAG){GAME['VoloOnStage']})",
                     'DB_ALFSV_PlaceDone("Talk_K10_Volo")'], ['PROC_ALFSV_Talk_Local("Volo");'])
    o += ["// L4 with Karlach in the party: no scene before Dammon's dialog (hers plays), a '!' after it - same text"]
    o += rule("IF", [f"DialogEnded((DIALOGRESOURCE){NPC_DIALOG['Dammon']}, _)", f"DB_Players({KARLACH})",
                     'NOT DB_ALFSV_OMPlayed("Dammon")', f"QRY_ALFSV_Talk_NearObject({DAMMON})"],
              ['PROC_ALFSV_Talk_Local("Dammon");'])
    o += ["// Clicking her with that '!': the scene needs Dammon as a speaker (QRY_SelectCustomDialog goes before the",
          "// relationship dialog, __GLOBAL_Dialogs.txt); if he is not in range - her usual talk, the mark stays"]
    o += rule("QRY", [f"QRY_SelectCustomDialog({A}, _Player)", "DB_Avatars((CHARACTER)_Player)",
                      f"DB_HandlingRelationshipDialog({A}, {dlg(lo.L4)}, _, _, _, _)",
                      f"QRY_SpeakerIsAvailableAndInDialogRange({DAMMON}, _Player)"],
              [f"DB_SelectedDialog({dlg(lo.L4)}, {DAMMON}, {A}, _Player);"])
    o += rule("QRY", [f"QRY_SelectCustomDialog({A}, _Player)", "DB_Avatars((CHARACTER)_Player)",
                      f"DB_HandlingRelationshipDialog({A}, {dlg(lo.L4)}, _, _, _, _)",
                      f"NOT QRY_SpeakerIsAvailableAndInDialogRange({DAMMON}, _Player)"],
              [f"DB_SelectedDialog((DIALOGRESOURCE){INPARTY}, {A}, _Player);"])
    o += ["//END_REGION", "", "//REGION Overhead lines K1-K15: events -> PROC_ALFSV_Place_Request (K1, K3, K9 - game flags,",
          "// ALFSV_World.txt); one AD at a time, waits up to 60 s", ""]
    o += ["// K2: in combat - straight away, without the wait for a free moment (QRY_SpeakerIsAvailable is false in combat)"]
    o += rule("IF", [f"VoiceBarkStarted((VOICEBARKRESOURCE){VB['Hyena']}, _)", f"DB_Players({A})",
                     'QRY_ALFSV_Place_Wanted("Talk_K02_Hyena")', 'DB_ALFSV_Place("Talk_K02_Hyena", _Dialog)',
                     "NOT DB_ALFSV_AD_Playing(_)"],
              ['DB_ALFSV_AD_Requested(_Dialog, "Talk_K02_Hyena");', "PROC_ALFSV_AD_SetMood();", f"PROC_TryStartAD(_Dialog, {A});"])
    o += ["// K4: Okta's gruel (as Karlach's reaction, Act1_OriginMoments_Karlach.txt:603-624)"]
    for flag in ("TookGruel", "TookGruel2"):
        o += rule("PROC", [f"PROC_FlagReactionAfterDialog(_, (FLAG){GAME[flag]})",
                           f"QRY_SpeakerIsAvailableAndInDialogRange({A}, {OBJ['Okta']})"],
                  ['PROC_ALFSV_Place_Request("Talk_K04_Gruel");'])
    o += ["// K5: a ritual druid's dialog at the Sacred Pool is over (Act1_DEN_SacredPond.txt:268-281, hotfix)"]
    o += rule("IF", ["DialogEnded(_Dialog, _Inst)", "DB_DEN_RitualDialogs(_Dialog)", "QRY_ALFSV_Talk_Near(_Inst)"],
              ['PROC_ALFSV_Place_Request("Talk_K05_Ritual");'])
    o += ["// K6: the children's game on the floor in the Blighted Village (Act1_FOR_Misc.txt:7)"]
    o += rule("IF", [f"VoiceBarkEnded((VOICEBARKRESOURCE){VB['KidsGame']}, _)", f"QRY_ALFSV_Talk_NearObject({OBJ['KidsBox']})"],
              ['PROC_ALFSV_Place_Request("Talk_K06_KidsGame");'])
    o += ["// K7: the wine hidden in a hollow book (Act1_FOR_Boosters.txt:733-741)"]
    o += rule("IF", [f"UseStarted(_Char, {OBJ['HoleBook']})", "DB_Players(_Char)", f"QRY_ALFSV_Talk_NearObject({OBJ['HoleBook']})"],
              ['PROC_ALFSV_Place_Request("Talk_K07_HoleBook");'])
    o += ["// K8: the dangerous book destroyed (FOR_DangerousBook.txt:145-165: a companion within 12 m)"]
    o += rule("IF", [f"DestroyedBy({OBJ['Tome']}, _, _, _)", f"QRY_ALFSV_Talk_NearObject({OBJ['Tome']})"],
              ['PROC_ALFSV_Place_Request("Talk_K08_DangerousBook");'])
    o += ["// K10: Volo on stage (Act1_GOB_VoloBallad.txt:5,145-152: the trigger is registered for the players)"]
    o += rule("IF", [f"EnteredTrigger({A}, {OBJ['VoloArea']})", f"DB_GlobalFlag((FLAG){GAME['VoloOnStage']})"],
              ['PROC_ALFSV_Place_Request("Talk_K10_Volo");'])
    o += ["// K11: the hero played the drums at the goblin checkpoint (Act1_GOB_Checkpoint.txt:234-244)"]
    o += rule("PROC", [f"PROC_FlagReactionAfterDialog(_Player, (FLAG){GAME['Drums']})", f"_Player != {A}",
                       f"QRY_SpeakerIsAvailableAndInDialogRange({A}, _Player)"],
              ['PROC_ALFSV_Place_Request("Talk_K11_Drums");'])
    o += ["// K12: the poems in the Arcane Tower read (Act1_UND_ArcaneTower.txt:702-714)"]
    o += rule("IF", ["GameBookInterfaceClosed(_Book, _Player)", "DB_UND_ArcaneTower_Poems(_Book, _)",
                     "QRY_ALFSV_Talk_NearObject(_Player)"], ['PROC_ALFSV_Place_Request("Talk_K12_Poems");'])
    o += ["// K13: Lathander's statue at the Creche recognised (Religion; Act1b_CRE_Exterior.txt:355,362)"]
    for check in ("CRE_Exterior_ArrivalStatuePlaque_Religion", "CRE_Exterior_CourtyardStatue_Religion"):
        o += rule("PROC", [f'PROC_GLO_KnowledgeCheckSuccess(_Player, "{check}", _)', "QRY_ALFSV_Talk_NearObject(_Player)"],
                  ['PROC_ALFSV_Place_Request("Talk_K13_Lathander");'])
    o += ["// K14: the gith youth training hall (Act1b_CRE_Creche_Misc.txt:139-142)"]
    for vb in ("GithDummy", "GithSketches"):
        o += rule("IF", [f"VoiceBarkStarted((VOICEBARKRESOURCE){VB[vb]}, _)"], ['PROC_ALFSV_Place_Request("Talk_K14_GithYouth");'])
    und = place_dlg("UnderdarkFirst", WORLD_PLACES)
    o += ["// K15: the first time in the Underdark - right after her place line UnderdarkFirst (same trigger);",
          "// if that line was said before this version - on the next entry"]
    o += rule("IF", [f"AutomatedDialogEnded({und}, _)"], ['PROC_ALFSV_Place_Request("Talk_K15_Underdark");'])
    o += rule("IF", [f"EnteredTrigger({A}, {OBJ['UnderdarkSub']})", 'DB_ALFSV_PlaceDone("UnderdarkFirst")'],
              ['PROC_ALFSV_Place_Request("Talk_K15_Underdark");'])
    o += ["//END_REGION", "",
          "//REGION Debug (Script Extender console)",
          "// Osi.PROC_ALFSV_Debug_Talk(\"GroveHeld\") - put the '!' up again (ignores 'once'; she must be a companion)",
          "// Osi.PROC_ALFSV_Debug_TalkNow(\"Kagha\") - start the talk right now with the host (no mark)",
          "// Osi.PROC_ALFSV_Debug_TalkMirkon() - S4 starts with Mirkon (otherwise Arabella)",
          "// Osi.PROC_ALFSV_Debug_OM(\"Asharak\") - the scene before the NPC dialog is offered again (then talk to him)",
          "// Osi.PROC_ALFSV_Debug_OMNow(\"Dammon\") - the three-way scene right now (the NPC must be near)",
          "// Keys: " + ", ".join(list(ev.TALKS) + list(lo.TALKS)) + "; OM: " + ", ".join(lo.OMS), ""]
    o += rule("PROC", ["PROC_ALFSV_Debug_Talk((STRING)_Key)", "DB_ALFSV_Talk(_Key, _Dialog, _)",
                       f"DB_RelationshipDialogsFinished((CHARACTER){A}, _Dialog, _Flag)"],
              [f"NOT DB_RelationshipDialogsFinished({A}, _Dialog, _Flag);"])
    o += rule("PROC", ["PROC_ALFSV_Debug_Talk((STRING)_Key)", "DB_ALFSV_TalkQueued(_Key)"], ["NOT DB_ALFSV_TalkQueued(_Key);"])
    o += rule("PROC", ["PROC_ALFSV_Debug_Talk((STRING)_Key)"], ["PROC_ALFSV_Talk_Queue(_Key);"])
    npc = {"Dammon": DAMMON, "Asharak": ASHARAK, "Lakrissa": "S_DEN_Tiefling_010_23129d6c-8d39-4a4c-a4f6-cfc6637b597c"}
    o += rule("PROC", ["PROC_ALFSV_Debug_TalkNow((STRING)_Key)", 'DB_ALFSV_Talk(_Key, _Dialog, "event")', "GetHostCharacter(_Host)",
                       f"QRY_StartDialog_Fixed(_Dialog, {A}, _Host)"], ["DB_NOOP(1);"])
    o += rule("PROC", ["PROC_ALFSV_Debug_TalkNow((STRING)_Key)", 'DB_ALFSV_Talk(_Key, _Dialog, "local")', '_Key != "Dammon"',
                       "GetHostCharacter(_Host)", f"QRY_StartDialog_Fixed(_Dialog, {A}, _Host)"], ["DB_NOOP(1);"])
    o += rule("PROC", ["PROC_ALFSV_Debug_TalkMirkon()"], [f"SetFlag({fl(ev.MIRKON)}, {A}, 0);"])
    for key, s in lo.OMS.items():
        o += rule("PROC", [f'PROC_ALFSV_Debug_OM("{key}")'],
                  [f'NOT DB_ALFSV_OM("{key}");', f'NOT DB_ALFSV_OMPlayed("{key}");', f'NOT DB_ALFSV_OMDefined("{key}");',
                   "PROC_ALFSV_Talks_DefineOMs();"])
        o += rule("PROC", [f'PROC_ALFSV_Debug_OMNow("{key}")', "GetHostCharacter(_Host)",
                           f"QRY_StartDialog_Fixed({dlg(s)}, {npc[key]}, {A}, _Host)"], ["DB_NOOP(1);"])
    o += rule("PROC", ['PROC_ALFSV_Debug_TalkNow("Dammon")'], ['PROC_ALFSV_Debug_OMNow("Dammon");'])
    o += ["//END_REGION", "EXITSECTION", "", "ENDEXITSECTION", ""]
    return "\n".join(o)
