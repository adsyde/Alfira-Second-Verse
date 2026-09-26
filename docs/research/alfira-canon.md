# Альфира: канон по данным игры

Библия персонажа для мода, который делает Альфиру полноценным спутником. Источник только данные Baldur's Gate 3 версии Patch 8 Hotfix 9: распакованные диалоги (`.lsj`), Osiris-цели (`Story/RawFiles/Goals/*.txt`), локализация EN/RU, VoiceMeta, статы и шаблоны. Всё, что не подтверждено файлами, помечено как _интерпретация_ или вынесено в «Открытые вопросы».

Полные тексты сцен лежат в `reports/dialogs/*.md` (34 файла, генерирует `scripts/dialog_dump.py --all-alfira`). Здесь даны только короткие цитаты: EN, затем официальный RU.

---

## 1. Идентификаторы

| Что | Значение | Где найдено |
|---|---|---|
| Глобальный персонаж | `S_DEN_Bard_4a405fba-3000-4c63-97e5-a8001ebb883c`, `IsGlobal=True`, уровень размещения `WLD_Main_A` | `Gustav/Mods/Gustav/Globals/WLD_Main_A/Characters/_merged.lsx` |
| Имя | «Alfira» / «Альфира» (`ha56e1454g5433g4c27ga904g78df82805018`) | там же |
| Корневой шаблон | `9103fce3-…` = **`Tieflings_Female_Asmodeus_Civilian`** (тифлинг-женщина, линия Асмодея, «гражданская») | `Shared/Public/Shared/RootTemplates/_merged.lsx` |
| Статы | `DEN_Refugees_Tiefling_Bard` → `Tiefling_Bard` → `Tiefling_Caster` → `_Tiefling`. Vitality 20. Характеристики наследуются от `Tiefling_Caster`: СИЛ 12, ЛОВ 10, ТЕЛ 12, ИНТ 16, МДР 12, ХАР 12. `SpellCastingAbility` = Charisma. Владение: простое оружие, ручные арбалеты, длинные луки, рапиры, короткие мечи, **музыкальные инструменты**. Класса и уровня нет: это NPC-статблок | `Stats/Generated/Data/Character.txt` (Shared + Gustav) |
| Снаряжение | `EQP_Unarmed_Lute`; в инвентаре `S_DEN_BardMandolin`, `S_SCE_AlfiraLute` | `_merged.lsx` |
| Фракция | `082ce2e1-e636-4a56-817c-af798bdc59d8`; при найме в сюжете Тёмного соблазна выставляется `ACT1_DEN_TieflingBard` | `_merged.lsx`, `Act1_ORI_DarkUrge.txt` |
| Anubis-конфиги по актам | `DEN_Bard` → `HAV_Bard` → `LOW_Alfira` | `Act*_GLO_LevelTravelers.txt` |
| Теги | `ALFIRA` (`c93d7c45-…`, категории Code/Dialog/**Origin**/DialogHidden/CharacterSheet) и `REALLY_ALFIRA` (`0c8221b4-…`) | `Gustav/Public/GustavDev/Tags/` |
| Флаг «в команде» | `GLO_Origin_PartOfTheTeam_Alfira` | `GLO_Origin_DarkUrge.txt` |
| Банк озвучки | `Localization_VoiceMeta/Mods/Gustav/Localization/English/Soundbanks/4a405fba30004c6397e5a8001ebb883c.lsx`, файлы `v4a405fba30004c6397e5a8001ebb883c_<handle>.wem` | VoiceMeta.pak |
| Двойник для ночи Тёмного соблазна | `S_DEN_Bard_Backup` = **Квил Грутсланг** (Quil Grootslang), бард-драконорождённая | `Act1_ORI_DarkUrge.txt`, синопсис `CAMP_DarkUrge_MurderOfAlfira_CFM_BardBackupArrives` |

Существенный для мода факт: в игре уже есть инфраструктура Альфиры как члена отряда. Она используется в сцене с Тёмным соблазном (`Act1_ORI_DarkUrge.txt`): `DB_OriginInPartyDialog(S_DEN_Bard, DEN_Bard_InParty)`, `DB_OriginNPCAlignment`, `DB_OriginPartOfTheTeamFlag(..., ORI_Alfira_ControlledByUser)`, `DB_OriginKickFromPartyFlags(..., ORI_Alfira_Event_KickCompanion, ORI_Alfira_State_CanBeKicked)`, `PROC_GLO_PartyMembers_Initialize`, `DB_GLO_Playable`, флаг `OriginAddToParty`. Меню смены состава уже умеет говорить «You can take Alfira's place» / «Ты можешь занять место Альфиры» (`GLO_CompanionSwap_*`, найм Астариона, Гейла, Карлах, Уилла, Минска) и «I'll leave Alfira here in camp».

---

## 2. Кто она: факты из текста игры

### Происхождение
- **Тифлинг-беженка из Элтуриэля.** «I've been running since Elturel» / «Я бежала из Элтуриэля…» (CFM). Своему собрату-тифлингу на празднике она говорит «After Elturel…» / «После Элтуриэля…». В газете эпилога она входит в `DB_EPI_Epilogue_ElturelSurvivors`.
- **Мать сгорела в Аверно.** Воло спрашивает про пламя Аверно, она огрызается: «They were hot enough to burn my mother alive. Does that help?» / «Оно было достаточно жарким, чтобы сжечь мою мать заживо. Так считается?» и сразу извиняется (`CAMP_Bard_AD_Volo`).
- **Родных и друзей в городе нет.** Лакрисса спрашивает, есть ли у неё кто-то во Вратах, она отвечает: «None. You?» / «Никого. А у тебя?».
- **Линия Асмодея** видна только по имени корневого шаблона (`Tieflings_Female_Asmodeus_Civilian`). В репликах её родословная не упоминается.

### Лихейла (Lihala) — наставница
- «apprenticed to a woman called Lihala» (синопсис `DEN_TieflingBard_Bard`). Для Альфиры она «Teacher... friend... everything to me» / «Наставница... друг... она всё для меня» (Разговор с мертвым).
- **Погибла от гноллов по дороге в рощу.** «She was playing her lute. We... didn't hear the gnolls coming.» / «Она играла на лютне. Мы... не услышали гноллов.» Там же: «There was so much blood. I - I can still smell it.» Альфира спаслась бегством: «Run when they... shriek. They call... for others...» (Разговор с мертвым).
- **Какой была Лихейла:** любила танцевать, хотя танцевала неуклюже: «She loved dancing. Had two left feet, mind.» / «Она любила танцевать. Хотя обе ноги у нее были левые». Была строгой: «She'd yell at me for that clunky verse. And make me play 'til my fingers were raw.» Не разрешала ученице пить вино (праздник в лагере). Её максимы Альфира постоянно цитирует (см. §4).
- **После гибели Лихейлы Альфира не играла:** «I haven't finished a song since Lihala died. Haven't played at all, if I'm honest.» / «…По правде говоря, я всё это время вообще не играла». Пока игрок не помог ей, она не могла смотреть на лютню, не слыша криков наставницы.
- **Лютни.** У Альфиры есть своя лютня и лютня Лихейлы («It was my teacher's. And it's - it's all I have left.»). В предметах есть строки «Lihala's Lute / Лютня Лихейлы» и «Alfira's Lute / Лютня Альфиры». В третьем акте она дарит игроку «my very first lute». Какой предмет-объект соответствует какой строке, в данных не проверено: предметы уровней не распакованы.

### Цель и мечта
- В рощу она пришла с намерением петь в «Эльфийской песни»: «Elfsong Tavern... Baldur's Gate...» и «To perform there... to sing... for Lihala...» (Разговор с мертвым). Лакриссе говорит: «I've always wanted to sing at the Elfsong Tavern.» / «Я всегда хотела петь в таверне „Эльфийская песнь“.»
- В третьем акте цель меняется: **школа бардов**. «I'm going to open up a school of bards - the best in the Realms!» / «Я собираюсь открыть школу бардов – лучшую во всем свете!»

### Песня «The Weeping Dawn» / «Плач рассвета»
Реквием по Лихейле, который Альфира сочиняет в роще. Полный текст звучит в `DEN_TieflingBard_AD_FullSong` (читать в `reports/dialogs/`). Это прощание с наставницей: танец среди звёзд, благодарность за любовь, которую уже не вернуть, обещание помнить. Официальный RU-вариант переведён вольно. Одна из строк («…the last light down») перекликается с названием таверны «Последний свет» во втором акте. _Интерпретация:_ вероятно, случайное совпадение, в данных связь никак не обозначена.

### Характер по ремаркам и синопсисам
Ремарки для актрисы (`NodeContext`) почти прямо описывают персонажа:
- «Music is what she loves the most in life. It inspires her and gives her hope.»
- Синопсис Разговора с мертвым: «She is quiet and determined».
- Альфира не боец и знает это: «Hardly going to be much use in a battle, am I?» / «В бою от меня проку мало, согласись» (ремарка: «knows her own strengths»). При нападении готова умереть за детей: «She isn't a fighter but is prepared to lay down her life to protect them.» (`DEN_DruidAttack_Bard`).
- Она склонна к самоуничижению («I'm an <i>idiot</i>» / «Вот же я <i>дура</i>»; «Even animals think I'm terrible») и забегает вперёд («As usual, getting ahead of myself»; «Let's take it one note at a time, as my teacher would say»).
- Не держит зла, но и не прощает сразу. Тому, кто разбил лютню, в третьем акте: «I've forgiven you for that - just about.» / «Я тебе это простила – хоть и с трудом.»
- Ей не стыдно, что она сбежала: «I know what I am and what I'm not - and I'm not ashamed of running.» (HAV)
- Любит кошек: ремарка «alfira LOVES cats» в сцене с Тарой, которая на неё шипит («Lucky Gale.» / «Счастливчик Гейл...»).
- Заботится о других через действие: «my instinct is to rush in and try to make everything better, you know?» / «я всегда рвусь немедленно что-то сделать, чтобы исправить положение...» (SCE).
- Молодая и неопытная. Вина впервые попробовала на празднике («My teacher never let me have any»). Спутники называют её «girl», «waif», «gentle young soul, slain in her prime». Возраст нигде не указан.
- Со злыми и грубыми бывает резкой: «You horrid, horrid beast», «Get the hells away from me» / «Уйди с глаз моих и провались пропадом», «you lute-breaking arsehole», «I've met steaming piles of excrement more pleasant than you».

_Интерпретация:_ ядро образа — горе, которое переходит в творчество, и вера, что песня помогает живым. Храбрость у неё «тыловая»: рассказывать сказки детям под звуки боя. Юмор она использует как защиту. Самооценка хрупкая и сильно зависит от поддержки, поэтому ветка «уговорить бросить музыку» работает так жестоко.

---

## 3. Манера речи

**Междометия и ругательства:** «Urgh» / «Тьфу», «Damn it» / «Проклятье», «Gods» / «Боги», «Godsdammit», «Heh» / «Хм»/«Ха», «Hah!», «Stars, you hadn't heard?» / «Звезды, так ты не в курсе?», «Stars above...» / «Звезды всевышние...», «the hells», «bloody song», «arsehole», «bastard».

**Вербальные тики:**
- «…nothing fits, you know?» / «…всё не ладится, понимаешь?» повторяется в нескольких ветках.
- Цитирует наставницу, всегда с отсылкой «my teacher always said» / «моя наставница говорила»:
  - «the dead deserve to be remembered» / «Усопшие заслуживают, чтобы о них помнили»;
  - «a good musician never demands a solo»;
  - «eulogies… were for the living as well as the dead» / «погребальные песни нужны и живым, и усопшим»;
  - «emotions are to be felt - not feared» / «эмоции надо проживать, а не страшиться их»;
  - «Now's a time for cheerful lies» / «Сейчас время для веселого вранья»;
  - «one note at a time» / «по одной ноте за раз».
- Мыслит музыкальными метафорами: «Violence doesn't fix everything… Music can help in ways a <i>silly blade</i> can't.» / «Музыка помогает там, где <i>дурацкий меч</i> бесполезен.»
- Постоянно обещает написать песню о герое: «I'm going to have to write a song about you now, aren't I?», «an entire <i>catalogue</i> of songs about you» / «целый <i>список</i> песен».

**Юмор.** Самоирония и «юмор висельника», чаще всего в сцене с детьми во время осады:
- «They're cute but deadly. Like the Realms' most terrifying bunny rabbits.» / «Эти милахи просто смертоносны. Как опаснейшие кролики-убийцы.»
- «I'm pretty certain if I stop for too long they will actually <i>eat</i> me.»
- О собственной песне: «It sounded like a cat being strangled.» / «Не музыка, а кошачьи вопли.»
- Подыгрывает шутке про лютню: «Yes, it's led quite a life of crime. I'm simply putting it out of its misery... by slowly killing it with this song.»
- Дразнит игрока в третьем акте и во втором: «brainy-breeches» / «умняшка», «grumpypants» / «брюзга», «Har, har», «Oh, hush - I know you love me really.» / «Ой, прекрати... я знаю, ты на самом деле меня любишь.», «the clouds have been most appreciative of my performance».

**Регистр.** Разговорный британский английский: «mind», «bloody», «arsehole», «I've a long way to go», «Thanks ever so much», «gonna», «erm». Официальный RU передаёт это просторечием и эмоцией («сикось-накось», «треклятой», «забацаем», «Вот же я дура»).

**Динамика тона по актам.** В первом акте голос надломленный: горе, фрустрация, выплески. На празднике — хмельная и воодушевлённая. Во втором акте — уставшая, на пределе («I feel like I'm at the end of my rope»), но благодарная. В третьем акте она «the happiest and most confident we've ever seen her» (ремарка в `LOW_Elfsong_Alfira`), а журнал называет её «unflappable» / «невозмутимой».

**Шпаргалка для сценариста.** Короткие рваные фразы с тире («I - I can still smell it»). Самоперебивание. Смех перед серьёзным («Heh. She'd have said the same thing.»). Благодарит даже тех, кто ей неприятен («still, because she's lovely, feels the need to say thank you»).

---

## 4. Отношения

### Лакрисса (`S_DEN_Tiefling_010`, внутреннее имя «FlirtyTiefling», стражница из рощи)
Это канонический **романтический интерес** Альфиры.
- Празднику в лагере посвящена отдельная сцена `CAMP_GoblinHuntCelebration_AD_Bard_Flirty`. Синопсис: «warm and flirtatious back and forth… quickly realise how much they enjoy the others company». Лакрисса зовёт её «Alfie» / «Альфи», Альфира придумывает строку «two tiefling queens, frightful and fierce» / «две леди тифлингов». Лакрисса предлагает познакомить её с сестрой и племянниками, Альфира отвечает «I'd like that».
- Во втором акте Лакриссу угоняют в Лунные Башни. Там она говорит: «When I saw Alfira disappear into the darkness, my heart just about stopped.» Если игрок её спасает, происходит воссоединение (`HAV_AlfiraTale_ReunionWithFlirty`, «We're 'two tiefling queens', remember?»). После этого идут AD с планами: «We'll have a little house, maybe a garden?» / «У нас будет свой домик, может быть, даже с садом».
- В третьем акте ремарка говорит прямо: «shy smile (her and lakrissa are a thing)». Лакрисса называет её «my girl, Alfira… sweetie pie» / «моей крошке Альфире… бусинка». Они живут вместе: Лакрисса берёт лишние смены, чтобы Альфира занималась музыкой.
- В эпилоге Лакрисса дарит ей дом-школу с табличкой, где стоят имена игрока и Лихейлы (письмо).
- Если Лакрисса погибла, на празднике её место занимает «Zae» (`S_CAMP_TieflingBackup_002`, AD `…_Bard_Backup02`, без флирта). В эпилоге тогда приходит другое письмо, от одной Альфиры (см. §6).

### Тифлинги и дети
- С детьми она сидит в убежище во время налёта и атаки друидов, рассказывает им сказки (история Балдурана в детской версии). В эпилоге второго акта она присматривает за Маттисом, Уми и Иде и пишет с ними песню. Спрашивает про Мол: «Gods, I hope Mol is all right.» Дети её помнят: «When Alfira sang us that song? I think of it every day.» (лагерь беженцев, третий акт).
- Из погибших при засаде она описывает Ашарака, который учил детей деревянным мечам, и Икарона («quiet… heart of gold»). Кого именно казнили, зависит от того, кто выжил в первом акте. Ролан спас её и детей, если остался в роще. Кэл и Лия увезены.
- **Зевлор, Арабелла:** в её собственных репликах их нет. Арабелла отправляет игрока в «Последний свет» словами «Alfira's there - you'll be safe.» _Интерпретация:_ Альфира к этому моменту — узнаваемое «лицо» лагеря беженцев.

### Игрок
- Отношение определяется первым актом: помог с песней, отговорил от музыки, украл или разбил лютню.
- Помог с песней: благодарность и дружба. В третьем акте прощается словами «Take care, my friend. Thank you for helping a stumbling bard in a druids' grove find her spark again.»
- Флирт с игроком только лёгкий и шутливый: «I know you love me really» с подмигиванием. В ветке Тёмного соблазна: «I want to make my own stories. And I can't think of anyone else I'd rather share that with.» / «И больше всего на свете мне хотелось бы разделить их с тобой». Флаги с `WithFlirty` / `Flirty` относятся к Лакриссе, а не к игроку.

### Спутники (только ветка Тёмного соблазна, AD в лагере)
- **Астарион** предлагает «начать экскурсию» с его палатки. Она пугается: «Oh - OH. I, ah, I'm quite all right». На издёвку отвечает: «a lute to the skull would fell a mouthy elf pretty easily».
- **Уилл**: «are you the <i>real</i> 'Blade of Frontiers'?». Любимая песня о нём — «Endless Blade» / «Бесконечный клинок». Узнаёт, что есть и непристойная версия.
- **Гейл/Тара:** хочет погладить кошку, та шипит.
- **Воло** путает её имя («Amira») и неловко спрашивает про Аверно.
- **Карлах** за неё: «Bad luck to turn a bard away from a campfire.» **Лаэ'зель** против песен. **Шэдоухарт** прагматична.
- После её убийства спутники реагируют. Уилл: «Alfira wouldn't have harmed a housefly. A gentle young soul, slain in her prime.» Карлах: «whoever did kill her will pay for it». Хальсин и Лаэ'зель тоже. Отдельные реплики есть в `CAMP_DarkUrge_MurderOfAlfira_GD_MorningAfter` и `CAMP_DarkUrge_SparedIsobel_SD`.

---

## 5. Что она знает, мировоззрение
- Историю Балдурана и корабля «Wandering Eye» / «Глаз скитальца». Детям рассказывает её в приглаженном виде; игрок-бард или балдурец может заметить, что это не настоящая версия.
- Милила, бога песни («a tale worthy of Milil»), знает. О Влаакит не слышала. Баллад о Мистре не знает, но готова написать.
- Песни о Клинке Фронтира. Легенду/песню «Heart's Requiem» / «Погребальная песнь сердца»: «The hero survives a war and rebuilds her life - stronger than ever».
- Тифлингов в сказаниях видит так: «Plenty with tiefling villains... but not so many heroes». Хочет, чтобы «Faerûn… see us as we <i>really</i> are».
- Знает, что в «Эльфийской песни» выступать может только сама «Эльфийская песнь» (призрак).
- О богах отзывается скептически: «The gods have enough people singing about them.»
- Мечтает о Глубоководье и Невервинтере («Can we go to Waterdeep?»).

---

## 6. Сюжетная машина состояний

### 6.1. Ключевые флаги

| Флаг | Тип | Смысл |
|---|---|---|
| `DEN_TieflingBard_HasMet` | Dialog | Знакомство состоялось |
| `DEN_TieflingBard_State_SpokeToAnimals` | Global | Игрок поговорил с белками (`DEN_TieflingBard_Animals`, «Разговор с животными»), которые высмеивают её пение |
| `DEN_TieflingBard_Event_Helped` | Dialog | Игрок взялся помогать |
| **`DEN_TieflingBard_State_FinishedSong`** | Global | **Песня закончена** (благодаря Выступлению, барду или подсказке «что бы ты сказала наставнице»). Основная «хорошая» ветка; цепляет цель предыстории Entertainer `Act1_Entertainer_Alfira` |
| `DEN_TieflingBard_Event_GiveProficiency` | Object | После дуэта игрок получает статус `DEN_ALFIRA_PROFICIENCY` «An Unlikely Tutor» / «Неожиданная наставница», владение музыкальными инструментами |
| `DEN_TieflingBard_Event_PlayWithInstrument`, `…_TransferInstrument` | Object | Игрок играл на лютне Лихейлы. В хорошем исходе Альфира оставляет её игроку: «Keep the lute. Please. You've earned it.» |
| `DEN_TieflingBard_State_TrashedSong` | Global | Игрок уговорил начать заново (AD `StartingOver`) |
| **`DEN_TieflingBard_State_ConvincedToQuit`** | Global | **Игрок убедил бросить музыку.** Меняет реплики во всех актах; с этим флагом Лакрисса не флиртует на празднике |
| `DEN_TieflingBard_State_StoleInstrument` / `_Event_StoleInstrument` / `_Event_LostInstrument` | Global/Dialog | Лютня Лихейлы украдена (открыто или тайно). Альфира ищет её (AD `LookingForInstrument`, `Dejected`) |
| `DEN_TieflingBard_State_ReturnedInstrument` | Global | Лютню вернули |
| **`DEN_TieflingBard_Event_SmashedLute`** / `_State_SmashedLute` | Dialog/Global | Игрок разбил её лютню (проверка Ловкости). Последствия видны во всех актах |
| `DEN_TieflingBard_State_Sulking` | — | Стоп-флаг музыки; где ставится, не найдено |
| `DEN_TieflingBard_State_Unavailable` | — | `DB_DefeatedStateFlag` |
| `DEN_Bard_HasMet_User` | User | Игрок уже разговаривал с ней |
| `CAMP_GoblinHuntCelebration_HasMet_Bard`, `…_Event_RefusedBardSong` | Dialog | Праздник в лагере; игрок отказался от песни о себе |
| `CAMP_DarkUrge_Event_RecruitAlfira` + `CAMP_DarkUrge_Event_AlfiraJoined` | Global | Тёмный соблазн взял её в отряд (всегда ставятся вместе, `DB_GLO_CompoundFlag`) |
| `CAMP_DarkUrge_Event_AlfiraHappy` / `…AlfiraUpset` | Dialog | Настроение в ночь убийства |
| `ORI_DarkUrge_MurderOfAlfira_Requirement` | — | Ставится при входе в `S_FOR_AreaTrigger`; условие ночи убийства |
| `ORI_DarkUrge_MurderOfAlfira_State_InGoblinCamp` | Global | Лагерь игрока в лагере гоблинов (другие реплики) |
| `ORI_DarkUrge_MurderOfAlfira_Alternative` | Global | Жертвой стала Квил, а не Альфира |
| `ORI_DarkUrge_State_MurderedAlfiraOrAlternative(InSleep)`, `ORI_DarkUrge_Event_HideAlfiraCorpse`, `ORI_DarkUrge_State_CleanedBlood`, `ORI_DarkUrge_State_AlfiraMurderWokeParty` | Global | Исход ночи убийства |
| `HAV_SavingPrisoners_Knows_CapturedTieflings` | Global | Игрок узнал о засаде (часто от неё) |
| `HAV_SavingPrisoners_Event_AlfiraAskedForHelp` | Global | Она попросила спасти пленных из Лунных Башен (журнал `HAV_SaveTieflingPrisoners`) |
| `HAV_AlfiraTale_State_AsharakWasAlive` / `…IkaronWasAlive` | Global | Кого казнили в засаде |
| `HAV_AlfiraTale_Knows_SavedByRolan`, `…Knows_ProdigySiblingsFate` | Global | Ролан спас её и детей; судьба Кэла и Лии |
| `HAV_AlfiraTale_HasMet_Upset` | Dialog | Игрок её обидел. Без этого флага по окончании диалога засчитывается цель Folk Hero `Act2_FolkHero_LastLightAlfiraReunion` |
| `HAV_SavingPrisoners_State_(All)TieflingsReturned`, `MOO_Jailbreak_State_AllPrisonersDied` | Global | Итог спасения пленных |
| `HAV_AlfiraTale_Event_SmallReward` (`1182ce42`) / `…_BigReward` (`7016a73a`) | Global | Её награды игроку (малая или большая) |
| `HAV_AlfiraTale_State_ReunionDone` | Global | Воссоединение с Лакриссой |
| `SCE_Alfira_State_RequestedBard`, `SCE_Alfira_Event_GaveShiningDawn` / `…RefusedShiningDawn` | Global/Dialog | Эпилог второго акта: игрок-бард играет с ней и получает `Target_SCE_TieflingFollowup_BardicInspiration` «Improved Bardic Inspiration» / «Улучшенное бардовское вдохновение» (1d12, раз за отдых) |
| `SCE_TieflingFollowUp_Alfira_AskedAboutKids` | — | Обновляет квест «LOW_FindMol» |
| `LOW_Elfsong_Alfira_HasMet` | Dialog/Char | Встреча на крыше «Эльфийской песни»; цели Entertainer и Folk Hero третьего акта |
| `LOW_Elfsong_State_HasAlfiraLute` → `LOW_Elfsong_Event_GivingAlfiraLute` | Object | Она дарит «my very first lute» (`S_LOW_Elfsong_Rooftop_AlfiraFirstLute`). Если лютню украли: «Kindly imagine I've given it to you, yeah?» |
| `LOW_Elfsong_Event_AlfiraPerformance` | Global | Отряд в зоне крыши: она играет |
| `LOW_Elfsong_State_LakrissaWithAlfira`, `…TalkWithAlfiraLakrissaRooftopOnce`, `…LakrissaPermaDefeated`, `…AlfiraPermaDefeated` | Global | Сцены третьего акта и выбор письма эпилога |

### 6.2. Акт 1: Изумрудная роща
**Где она:** сидит на камне у `S_DEN_BardSeat` рядом с логовом рейнджеров (`S_DEN_RangerDen_SUB`), вокруг белки. Когда игрок входит в `S_DEN_BardSingArea`, она начинает петь (`DEN_TieflingBard_StartSinging`).

**Квест песни** (`DEN_TieflingBard_Bard`, 122 реплики) даёт четыре исхода:
1. **Песня закончена** (`FinishedSong`). Варианты: дуэт на лютне Лихейлы с двумя проверками Выступления (Charisma/Performance); пропеть строку, если игрок бард; разговорить её вопросом «что бы ты сказала наставнице». Итог — синематик песни и слёзы. Она рассказывает о гноллах, называет песню «The Weeping Dawn» / «Плач рассвета». Может оставить игроку лютню Лихейлы и дать владение инструментом. После этого в роще играет AD `FullSong`.
2. **Начать заново** (`TrashedSong`): неуверенность, AD `StartingOver`.
3. **Бросить музыку** (`ConvincedToQuit`): «I'm not cut out to be a bard. Or much else, if I'm honest.» AD `QuitComposing`: «If not a bard, then an adventurer? No, I don't have the stomach for it.»
4. **Лютня украдена или разбита** (`StoleInstrument`/`SmashedLute`): ненависть к игроку. Разбитая лютня: «My teacher gave me that! And she - and she's <i>dead</i>, you bastard.»

Неудачная попытка вырвать лютню: «You horrid, horrid beast.» С игроком-Тёмным соблазном рассказчик комментирует её «приторную доброту» (`REALLY_DARK_URGE`).

**Атака друидов** (`DEN_DruidAttack`, роль «Cower»). Если друиды нападают на тифлингов, она прячет детей в убежище: «Keep them away from the kids - <i>please.</i>» После боя: «That's twice you saved us now.» Если игрок украл или разбил лютню: «You're a person with many faces.»

**Налёт гоблинов** (`DEN_AttackOnDen`, роль «Hideout»). Она рассказывает детям сказку, пока идёт бой.
- **Тифлинги побеждают** (`DEN_AttackOnDen_State_DenVictory`): «I'm going to have to write a song about you now, aren't I?» / «It's nice to be done with the sad songs, for a time.»
- **Игрок на стороне гоблинов** (`RaidersInDen` + `HostileTieflings`). Если игрока нет в зоне убежища, скрипт `PROC_DEN_AttackOnDen_KillKids` убивает детей и **Альфиру** (`Die(S_DEN_Bard)`). Если игрок входит в убежище, дети разбегаются, а Альфира принимает последний бой: «N-no. Not again. Not. <i>Again.</i>» (синопсис связывает это с гибелью Лихейлы). После победы гоблинов её окровавленную лютню можно найти на их празднике: «you realise the lute belonged to Alfira». Её труп попадает и в `DB_FOR_SlaughteredTieflingTriggers`. Если Альфира и зачарованный ребёнок убиты до налёта, ставится `DEN_AttackOnDen_State_NoStoryteller`.

**Праздник в лагере** (`CAMP_GoblinHuntCelebration`, ночь `NIGHT_GoblinHunt_TieflingCelebration`, после победы над вожаками гоблинов). Она пьяна от первого в жизни вина и хочет написать песню о герое. Реакции зависят от происхождения и класса игрока (Астарион, Лаэ'зель, Уилл, Гейл, Карлах, тифлинг, полудроу, дуэргар, бард, воин, варвар). С Лакриссой идёт флирт; если та мертва — AD с Зай.

**Разговор с мертвым** (`DEN_TieflingBard_Dead`): «Alfira... apprentice... bard...». Убийце она не отвечает.

### 6.3. Ночь убийства (только для Тёмного соблазна)
- **Условия** (`Act1a_Camp_PostEA.txt`, `Act1_ORI_DarkUrge.txt`): игрок — Тёмный соблазн (тег `DARKURGE`), выставлен `ORI_DarkUrge_MurderOfAlfira_Requirement`. Ночь эксклюзивная, приоритет 6200. Отменяется, если уже наступила стадия Изобель (`ORI_DarkUrge_KilledIsobel/SparedIsobel_Requirement`). Может сработать в лагерях первого акта и во втором акте (SCLMAIN, SHARTEMPLE, MOONRISE, HAVEN). Принудительно включается при переходах `ToCreche…` / `ToSCLFromUnderdark` (`GLO_FallbackCamp_Gustav.txt`).
- **Сцена `CAMP_DarkUrge_MurderOfAlfira_CFM_AlfiraArrives`** (85 реплик) приходит в трёх вариантах:
  - **Песня закончена:** «You've, well, inspired me. I want to stand on my own two feet, to prove that I can be half the bard Lihala was. I want to join you - to fight by your side.» / «…Я хочу присоединиться к тебе, сражаться бок о бок с тобой». В этой же сцене звучит «But I can fight! I won't hold you back, I swear it.»
  - **Отговорили или разбили лютню:** ищет ночлег, холодна, игрок может извиниться (Убеждение).
  - **Игрок не был в роще:** просит о помощи тифлингам и рассказывает о друидах: «If we leave, we're dead. If we stay, we're dead.»
- Игрок может принять её в отряд (`OriginAddToParty`). Тогда она ненадолго становится членом группы (`DEN_Bard_InParty`, AD `CAMP_Bard_AD*`) и рада дороге: «Can we go to Waterdeep?»
- **Сон `…SD_BloodOnHands`:** игрок просыпается над её изуродованным телом. Варианты: спрятать тело, отмыться, признаться. Утром `…GD_MorningAfter` — реакции спутников. Ставится `PROC_Origins_CompanionLeavePermanently(_, "CompanionMurdered")`. Упоминается в финале («Her death weighs upon you still»), у Джергала («Please bring her back»), в эпилоге Божественного барда («She deserves remembering»). Дворецкий Бога Убийств говорит, что сам всё устроил: «the sweet little girl Alfira was to place herself in your knife's way».
- **Замена жертвы** (`QRY_ORI_DarkUrge_ReplaceAlfira`). Если Альфира в момент подготовки «не может говорить» (`DB_CantTalk`) или игрок уже в SCL_Main_A и ни разу не входил в рощу, вместо неё приходит и погибает **Квил Грутсланг** (`S_DEN_Bard_Backup`, флаг `…_Alternative`). Только так Альфира переживает сюжет Тёмного соблазна. Тогда в эпилоге может прийти письмо `S_EPI_Letter_AlfiraDUSaved`, а газетной статьи о школе не будет: по комментарию в скрипте «She is keeping a super low profile».

### 6.4. Акт 2: «Последний свет» и эпилог акта
- Появляется в `HAV_TieflingSurvivors` (категория «Base», точка `S_HAV_EnteringHaven_AlfiraPoint`), если тифлинги ушли из рощи живыми.
- **Засада сектантов по дороге** (`HAV_AlfiraTale_Bard`, 80 реплик). Их окружили, выстроили «like dogs», Ашарака или Икарона ослепили и лишили языка. Альфира сбежала: «All I could do was run.» Её спас Ролан, если остался в роще. Остальных увели в Лунные Башни. Она просит игрока их спасти: «If they're not dead, they're in Moonrise. And gods have mercy on anyone in that hellspit.» Этот разговор открывает журнал `HAV_SaveTieflingPrisoners`.
- Пока лагерь «на взводе» (после истории с Огненным Кулаком-предателем): «Can't we trust anyone?». После освобождения Ночной песни: «I'd forgotten what light, true blazing light, felt like.»
- **Итог спасения:**
  - все спасены — «You actually did it», большая награда;
  - часть спасена — «Our group grows smaller and smaller», малая награда;
  - все погибли — «They were good people - they deserved to die old and happy.»
  - Если вернулась Лакрисса, играется воссоединение (`AlfiraBigReward`): «One last favour? Take this off my hands - it suits you better.» Какие предметы выдаются, в данных не найдено.
- **Опасности:** она в списке участников осады «Последнего света» (`DB_HAV_Siege_NPCs`, `DB_HAV_Siege_Undead_Swarms`) и участников нападения на трактир при похищении Изобель (`DB_HAV_TakingIsobel_KOParticipants`). _Интерпретация:_ если защита «Последнего света» падает, она может погибнуть вместе с остальными; точный механизм смерти не проверялся.
- **Эпилог второго акта** (`SCE_Alfira`, `SCE_AD_Alfira`, после победы над Кетериком). Она присматривает за детьми, пока Мол пропала, и сочиняет с ними песню. Игроку-барду предлагает дуэт «bard to bard» и дарит улучшенное вдохновение: «Yes! I've missed this.» Не-барду говорит, что поищет барда в городе. При `ConvincedToQuit` просто сторожит детей.

### 6.5. Акт 3: Врата Балдура
- `PROC_LOW_AlfiraSetup` срабатывает, если она не `PermaDefeated` и есть `DEN_TieflingRefugees_State_LeftDen`. Её телепортируют на **крышу «Эльфийской песни»**, выдают диалог `LOW_Elfsong_Alfira` и кладут в инвентарь «первую лютню».
- **Обычный вариант:** «We made it to <i>the</i> Elfsong Tavern.» Лакрисса пускает её репетировать на крыше. Альфира «отчитывает» игрока и объявляет о школе бардов «because of <i>you</i>», дарит лютню. Если игрок шутит «назови школу в мою честь»: «You and Lihala's names in bold? Hm - I like it. Deal.»
- **При `ConvincedToQuit`:** она потеряна: «I'm not a bard - not anymore… I just feel more lost.» В AD думает о сменах в таверне, а не об уличных выступлениях.
- С Лакриссой: AD на крыше («We made it, Lakrissa.» — «Only because I had you.»), общая сцена `LOW_Elfsong_Alfira_Lakrisssa` (планы на школу, Лакрисса её дразнит).
- В лагере беженцев у Драконьего перекрестка тифлинги говорят, что «Alfira made her way into the city».

### 6.6. Эпилог (`Act3c_EPI_Letters.txt`, `Act3c_EPI_Gazettes.txt`; хотфикс 9 переопределяет Gazettes, но строки про Альфиру не меняет)

| Письмо или статья | Условие | Содержание |
|---|---|---|
| `S_EPI_Letter_AlfiraAndLakrissa` | Альфира жива, Лакрисса жива, игрок не Тёмный соблазн | Лакрисса дарит ей дом с табличкой, где имена игрока и Лихейлы и надпись «School of Music». Ученики «from Candlekeep to Waterdeep», Лакрисса ушла из таверны помогать. «And I've never been happier.» |
| `S_EPI_Letter_AlfiraAtElfsong` | Альфира жива, Лакрисса мертва, игрок не Тёмный соблазн | Сама купила ветхий дом в Нижнем городе, сама чинила («quite handy with a hammer and nail»), очередь учеников «almost went to Rivington». Какое письмо какому тексту соответствует, установлено по содержанию, _интерпретация_ |
| `S_EPI_Letter_AlfiraDUSaved` | Альфира жива, игрок Тёмный соблазн | «I saw murder in your eyes when you looked at me - but you stayed your hand… I'm not going to tell you where I am… With love and forgiveness» |
| Газета `EPI_AlfiraMusicSchool` (Gazette_001) | Не мертва, игрок не Тёмный соблазн | Текст статьи в распакованных данных не найден: книги не распакованы |

Замечание: письма и статья не проверяют `ConvincedToQuit`. В эпилоге она открывает школу, даже если в третьем акте «больше не бард». Это канон, противоречие есть в самой игре.

### 6.7. Сводка судеб
1. Погибает при налёте гоблинов, если игрок на стороне гоблинов (скрипт или бой).
2. Убита игроком или в бою в первом акте. Разговор с мертвым.
3. Убита Тёмным соблазном в ночь `NIGHT_DarkUrge_MurderOfAlfira` (первый акт или ранний второй).
4. Выживает при Тёмном соблазне только через подмену Квил: письмо «DUSaved».
5. Выживает до «Последнего света», но может погибнуть в осаде или при падении защиты.
6. Доживает до третьего акта, крыша «Эльфийской песни»: бард с мечтой о школе или потерянная и «бросившая».
7. Эпилог: школа бардов, с Лакриссой или одна.

Сама Альфира никогда не попадает в плен в Лунные Башни. Туда уводят Лакриссу и других.

---

## 7. Каталог сцен

Отчёты: `reports/dialogs/<файл>.md`. Число — реплики Альфиры с озвучкой и секунды.

**Акт 1, роща (`Gustav/…/Dialogs/Act1/DEN/`)**
- `DEN_TieflingBard_Bard` (122 / 660 с): основной квест песни, все четыре исхода.
- `DEN_TieflingBard_AD_ComposingSong` (9): сочиняет вслух, обрывки строк.
- `DEN_TieflingBard_AD_FullSong` (12): поёт готовую песню целиком.
- `DEN_TieflingBard_AD_StartingOver` (3): «Nope. I hate it all.»
- `DEN_TieflingBard_AD_QuitComposing` (3): после отказа от музыки.
- `DEN_TieflingBard_AD_LookingForInstrument` (3): ищет лютню.
- `DEN_TieflingBard_AD_Dejected` (3): лютню украли или разбили.
- `DEN_TieflingBard_AD_InstrumentStolen` (1), `…_InstrumentBroken` (2, включая рыдание «*Sob.*»).
- `DEN_TieflingBard_Animals` (без её реплик): белки высмеивают её пение.
- `DEN_SpeakWithDead/DEN_TieflingBard_Dead` (7): Разговор с мертвым.
- `DEN_DruidAttack_Bard` (5), `DEN_DruidAttack_AD_BardAndKidAfterAttack` (4, с Заки): атака друидов.
- `DEN_AttackOnDen_Bard` (24), `DEN_AttackOnDen_AD_KidStory` (6, сказка о Балдуране), `DEN_AttackOnDen_AD_BardDefendsKids` (1): налёт гоблинов.

**Лагерь**
- `Camp/NPCs/CAMP_GoblinHuntCelebration_Bard` (31): праздник, песня о герое.
- `…/ADs/CAMP_GoblinHuntCelebration_AD_Bard_Flirty` (11): флирт с Лакриссой.
- `…/ADs/CAMP_GoblinHuntCelebration_AD_Bard_Backup02` (5): с Зай, если Лакриссы нет.
- `Camp/Campfire_Moments/CAMP_DarkUrge_MurderOfAlfira_CFM_AlfiraArrives` (85): приход в лагерь Тёмного соблазна.
- `Camp/DEN_Bard_InParty` (5): реплики в отряде.
- `Camp/CAMP_Bard_AD` (8), `…_AD_Astarion` (4), `…_AD_GaleTressym` (4), `…_AD_Volo` (5), `…_AD_Wyll` (5): AD в лагере Тёмного соблазна.
- `Camp/SoloDreams/CAMP_DarkUrge_MurderOfAlfira_SD_BloodOnHands` (0): пробуждение над телом.
- Связанные сцены без её GUID: `…_CFM_BardBackupArrives` (Квил), `Companions/Group_Discussions/CAMP_DarkUrge_MurderOfAlfira_GD_MorningAfter` (утро).

**Акт 2 (`GustavDev/…/Act2/`)**
- `Haven/HAV_AlfiraTale_Bard` (80): рассказ о засаде, просьба спасти пленных, итог.
- `Haven/HAV_AlfiraTale_ReunionWithFlirty` (11): воссоединение с Лакриссой. Скрипт ссылается на ресурс `HAV_SavingPrisoners_BardAndFlirtyReunion`.
- `Haven/HAV_AlfiraTale_AD_WithFlirty` (6): нежные AD после воссоединения.
- `Epilogue/SCE_Alfira` (32), `Epilogue/SCE_AD_Alfira` (8): эпилог акта, дети и дуэт.

**Акт 3 (`GustavDev/…/Act3/LowerCity/`)**
- `LOW_Elfsong_Alfira` (32): финал её арки на крыше.
- `LOW_Elfsong_Alfira_Lakrisssa` (3): вдвоём с Лакриссой (три «s» в имени файла — так в игре).
- `LOW_Elfsong_AD_Lakrissa_Alfira` (8): быт, аренда, смены.

**Реплики других о ней** (без её голоса): `MOO_Jailbreak_FlirtyTiefling`, `HAV_SavingPrisoners_FlirtyTiefling`, `LOW_Elfsong_Lakrissa`, `HAV_ProdigyLament_Rolan`, `SCE_Ide`, `SCE_Umi`, `SCE_Mattis`, `TWN_ArabellasPowers_TownIntroduction`, `WYR_RefugeeCamp_AD_TieflingRefugees`, `WYR_RefugeeCamp_AD_TraineeKids`, `*_InParty*` (Уилл, Карлах, Хальсин, Лаэ'зель, Гейл, Шэдоухарт, Астарион), `CAMP_DarkUrge_SparedIsobel_SD`, `CAMP_DarkUrge_IsobelKillOrder_SD`, `CAMP_Jergal`, `END_GameFinale_SoloFates_CustomAvatar`, `EPI_Epilogue_DivineBard`, `GLO_CompanionSwap_*`.

---

## 8. Озвучка (для датасета клонирования голоса)

Источник — её банк VoiceMeta. Поле `Length` содержит длительность каждой `.wem`. Все 548 записей банка совпали с 548 уникальными `TaggedText`, которые в диалогах произносит её индекс спикера. Потерянных строк нет.

- **548 строк, 2842 с (около 47 минут).** Медиана 4,8 с, минимум 0,78 с, максимум 20,3 с.
- Приоритеты: `P1_StoryDialog` 437, `P4_RepeatingDialog_AD` 100, `P3_StoryDialog_AD` 11.
- По актам:

| Блок | Строк | Секунд |
|---|---|---|
| Акт 1, роща (DEN_*) | 205 | 1048 |
| Праздник в лагере | 47 | 205 |
| Ветка Тёмного соблазна (CFM, InParty, CAMP_Bard_AD*) | 116 | 605 |
| Акт 2 (HAV + SCE) | 137 | 732 |
| Акт 3 (LOW) | 43 | 252 |

- **Пение:**
  - Чистое пение — **25 строк, около 176 с**: 12 в `DEN_TieflingBard_AD_FullSong`, 3 в `…_AD_ComposingSong`, 10 в `DEN_TieflingBard_Bard`. Самые длинные — `hf7c28a17…` (20,3 с) и `h8ca2cd99…` (19,0 с).
  - Смешанные строки — **3 шт., около 31 с**: пение переходит в речь (`hd99e112c…` 18,8 с «Dance upon the stars tonight… - no. <i>Become</i> - ugh.», `h7eeb0097…`, `he4c8a05a…`).
  - Декламация стихов внутри речи на празднике (`h8f83a60d…`, `had48b82b…`, `h894acf1e…`, `h59f26c5a…`, `h25c154c1…`): это речь, не пение.
  - Сама синематик-песня (узел `N4555`, «Cue cinematic of her singing») не содержит `TaggedText`. _Интерпретация:_ полная исполненная версия, вероятно, лежит в музыкальных ассетах, а не в её банке.
- **Что пометить или исключить в датасете:**
  - 7 строк Разговора с мертвым (50 с): «мёртвая» подача с паузами, в игре возможна обработка.
  - Рыдание «*Sob.*» и короткие выкрики.
  - 9 повторяющихся текстов (10 лишних записей, около 50 с). Три из них с идентичной длиной — вероятно, копии одного аудио: две пары «Moon. Sun…» / «Faith. Care…» в FullSong и «No pressure, kin» в двух вариантах для Карлах.
- Список «handle → файл/длина/пение» можно пересобрать скриптом по банку. Промежуточный результат лежал в scratchpad (`vo.json`); в репозиторий он не сохранён.

---

## 9. Крючки для мода

### 9.1. Что уже есть в движке
- Механика «Альфира в отряде» из ветки Тёмного соблазна (см. §1): флаги `CAMP_DarkUrge_Event_RecruitAlfira`/`AlfiraJoined`, `OriginAddToParty`, диалог `DEN_Bard_InParty`, `ORI_Alfira_ControlledByUser`, `ORI_Alfira_Event_KickCompanion`/`State_CanBeKicked`, тег `ALFIRA` категории Origin, строки смены состава. Это основа для найма вне ветки Тёмного соблазна.
- Озвученные реплики найма уже есть, их можно переиспользовать или взять как образец. «I want to join you - to fight by your side. I want to help people - as you've helped me.» (`CAMP_DarkUrge_MurderOfAlfira_CFM_AlfiraArrives`, узел N58). «I'd rather face it head on - with you.» «I won't let you down - I promise.» Лагерные AD: «Should I write a song? No, they'd probably find it annoying.»

### 9.2. Естественные точки найма

| Точка | Почему не противоречит канону | Цена |
|---|---|---|
| **A. После `FinishedSong` в роще** | Её собственная речь в CFM показывает, что она хочет «stand on my own two feet… fight by your side». Мотив дан игрой | Если она уходит из рощи, выпадают сцены второго акта (рассказ о засаде, просьба о Лунных Башнях, воссоединение). Ветка Лакриссы теряет опору: флирт на празднике |
| **B. Праздник в лагере** | Она уже в лагере, пьяна и «feeling inspired», хочет песню о герое | Флирт с Лакриссой в ту же ночь. Если нанимать тут, Лакрисса остаётся фактором |
| **C. «Последний свет» после спасения пленных** | Она на пределе и ищет, как «keep going». Если лагерь «становится всё меньше», мотив «делать больше, чем петь о чужих подвигах» из CFM звучит органично | Если Лакрисса спасена, самый логичный ответ Альфиры — остаться с ней. Найм здесь естественнее, если Лакрисса погибла |
| **D. Эпилог второго акта (SCE)** | Пик уверенности после дуэта: «I hope we get to play again sometime soon.» | Дети без Мол держат её рядом («the kids need me») |
| **E. Крыша «Эльфийской песни»** | «You and I are going to take this city by storm» — готовая фраза-крючок. Её арка закрыта, она уверена в себе | Мечта о школе и Лакрисса. Спутница третьего акта может «открыть школу после Мозгового ядра», и это совпадает с эпилогом |

_Рекомендация (интерпретация):_ меньше всего канона ломает C или E. Сцены первого и второго актов остаются нетронутыми, а личный квест продолжает её арку: школа, память о Лихейле, песня об игроке. Если нужен найм в первом акте (A), придётся написать замену HAV-сценам: например, она путешествует с игроком, узнаёт о засаде вместе с ним, и чувство вины «меня не было с ними» становится сюжетным ядром.

### 9.3. Материал для личного квеста
- **Лихейла:** гноллы, лютня, «The Weeping Dawn», ни одна песня не закончена после её смерти. Можно найти место гибели, остатки каравана, песни Лихейлы.
- **Элтуриэль и мать, сгоревшая в Аверно.** В игре это одна строка — большой неразработанный пласт.
- **«Песня о герое»:** она всю игру обещает её написать. Кульминацией может стать её исполнение.
- **Школа бардов с именами игрока и Лихейлы** — эпилог уже задан игрой.
- **Страх и бегство:** «I'm not ashamed of running». Арка храбрости без ломки характера: стать смелой, не перестав быть собой.

### 9.4. Роман — осторожно
- В каноне **её пара — Лакрисса** (ремарка «her and lakrissa are a thing», общий дом в эпилоге). Роман с игроком при живой Лакриссе прямо противоречит данным.
- Варианты без противоречия:
  1. роман доступен только если Лакрисса `PermaDefeated` (у игры на этот случай есть своё письмо);
  2. с живой Лакриссой — только дружба или наставничество;
  3. отдельная ветка, где Альфира сама выбирает и честно говорит о Лакриссе.
- Флирт с игроком в каноне шутливый («I know you love me really») и сдержанный. Ухаживание Астариона она неловко отклоняет.

### 9.5. Чего писатель не должен противоречить
1. Тифлинг, беженка из Элтуриэля, мать сгорела в Аверно. Линия Асмодея — только по имени шаблона.
2. Наставница Лихейла (RU: **Лихейла**) погибла от гноллов по дороге в рощу. Альфира выжила, потому что убежала.
3. После смерти Лихейлы Альфира не играла, пока не встретила игрока. Песня — «The Weeping Dawn» / «Плач рассвета».
4. Мечта — «Эльфийская песнь», позже школа бардов. Выступать в «Эльфийской песни» может только она сама.
5. Альфира — не воин и сама это признаёт. В бою её роль — защищать детей и поддерживать дух. Единственное «But I can fight!» — порыв в ветке Тёмного соблазна.
6. В городе нет родни. Лакрисса — её близкая, потом возлюбленная.
7. Шрамы от поступков игрока в первом акте переходят во все акты: украденная или разбитая лютня, `ConvincedToQuit`. Мод обязан учитывать эти флаги.
8. У Тёмного соблазна она канонически убита, если её не подменили на Квил. Спасённая, она живёт скрытно и не открывает школу публично.
9. Терминология RU из официального перевода: «Альфира», «Лихейла», «Лакрисса», «Плач рассвета», «Эльфийская песнь», «Последний свет», «Лунные Башни», «Изумрудная роща», «Элтуриэль», «Аверно», «Милил».

---

## 10. Открытые вопросы
- Какие предметы выдаются в `HAV_AlfiraTale_Event_SmallReward` / `BigReward` и при воссоединении («Take this off my hands»)? Нужно распаковать `Levels/*/Items` и Treasure.
- Соответствие `S_DEN_BardInstrument` / `S_DEN_BardMandolin` / `S_SCE_AlfiraLute` / `S_LOW_Elfsong_Rooftop_AlfiraFirstLute` строкам «Lihala's Lute» / «Alfira's Lute».
- Текст газетной статьи `EPI_AlfiraMusicSchool`: нужны книги (`Localization/*/Books` или `Content/*/Books`).
- Где ставится `DEN_TieflingBard_State_Sulking`.
- Точные условия гибели в осаде «Последнего света».
- Не переопределяет ли хотфикс 9 что-то кроме Gazettes: в `Patch8_HotFix9` её GUID нашёлся только в `Act3c_EPI_Gazettes.txt`.
