// This Day in the Pacific War — entry dataset
// Vol. I scope: 07 December 1941 — 01 September 1942
// "actual" = CINCPAC running-summary voice (Dec 7 1941 is the user-provided sample).
// "note"   = historian's interpretation, structured in three parts:
//              knew      — what the fleet commander knew on this date
//              didntKnow — what he did not yet know
//              coming    — what was about to happen
//            (Used as placeholder AND as the fallback if live AI generation fails.)
// "command" names the officer holding CINCPAC on this date — note the change of
//            command on 31 Dec 1941 from Kimmel (via acting CINCPAC Pye) to Nimitz.

window.WAR_TIMELINE = { start: "1941-12-07", end: "1942-09-01" };

window.ENTRIES = [
  {
    date: "1941-12-07",
    event: "Pearl Harbor",
    place: "PEARL HARBOR — OAHU, T.H.",
    command: "ADM. H. E. KIMMEL, CINCPAC",
    page: 4,
    actual: [
      "Japanese attack on Pearl Harbor. At 0755 local time, the first wave of Japanese aircraft struck the Pacific Fleet at anchor. ARIZONA, OKLAHOMA, CALIFORNIA, NEVADA, and WEST VIRGINIA were hit.",
      "Task forces at sea — including those carrying Marine reinforcements to Midway and Wake — were undamaged. Search for enemy carriers underway; direction of withdrawal unknown.",
    ],
    note: {
      knew: "By midday Admiral Kimmel knew the battle line had been gutted at its moorings — ARIZONA destroyed, OKLAHOMA capsized, the better part of five battleships out of action — and that the enemy had achieved complete surprise against the fleet's main anchorage.",
      didntKnow: "He did not yet grasp that the carriers' absence was the day's saving grace, nor that Nagumo had already turned for home, declining the strike against the fuel farms and repair basins that would let Pearl Harbor still serve as a fleet base. The location and intentions of the enemy striking force were a blank; phantom contacts would send ships chasing shadows for days.",
      coming: "Within three weeks Kimmel would be relieved. On 31 December, Chester Nimitz would raise his flag over a command in ruins and inherit the truth this entry only gestures toward — that the war would now be carried by the carriers still at sea.",
    },
  },
  {
    date: "1941-12-08",
    event: "War declared · fleet sorties",
    place: "AT SEA / PEARL HARBOR",
    command: "ADM. H. E. KIMMEL, CINCPAC",
    page: 9,
    actual: [
      "United States in state of war with Japan. Fleet units sortieing to seaward; ENTERPRISE group searching south and west of Oahu for reported enemy surface forces. Several contacts investigated; none confirmed.",
      "Guam under air attack. Wake garrison reports bombing of Marine air detachment. Cavite and Manila areas struck; condition of Asiatic Fleet air strength reduced.",
    ],
    note: {
      knew: "Kimmel knew the nation was now at war and that the fleet had to get to sea; ENTERPRISE was already searching to the south and west of Oahu for a surface force reported closing the islands.",
      didntKnow: "He did not know that the contacts driving those searches were phantoms while the true carrier force steamed away untouched, nor that MacArthur's air power was being destroyed on the ground at Clark Field hours after Hawaii's warning reached Luzon.",
      coming: "The reflex to sortie and hunt would harden over the coming months into the doctrine of the fast carrier task force — but first came weeks of chasing ghosts, friendly aircraft shot down over Oahu by nervous gunners, and a slow reckoning with how little anyone yet knew.",
    },
  },
  {
    date: "1941-12-10",
    event: "Force Z lost · Wake holds",
    place: "PACIFIC / SOUTH CHINA SEA",
    command: "ADM. H. E. KIMMEL, CINCPAC",
    page: 21,
    actual: [
      "British capital ships PRINCE OF WALES and REPULSE reported sunk by Japanese air attack off Malaya. No carrier support present.",
      "Wake Island holds. Marine defenders repel landing attempt, sinking destroyer HAYATE and damaging others by shore battery and air. First enemy warships sunk by U.S. forces in the war.",
    ],
    note: {
      knew: "Kimmel knew two things at once: that the British had lost PRINCE OF WALES and REPULSE to air attack with no carrier cover, and that the Marines on Wake had thrown back a landing and sunk the first enemy warships of the war.",
      didntKnow: "He could not yet weigh how completely the loss of Force Z had ended the battleship's reign at sea, nor that Wake's defiance had set in motion a relief expedition that would become his successor's first agonizing decision.",
      coming: "The same week that proved capital ships were now prey would force the Navy to rebuild its thinking around the carrier — and Wake, the war's lone bright spot, was already living on borrowed time.",
    },
  },
  {
    date: "1941-12-23",
    event: "Wake Island falls",
    place: "WAKE ISLAND / PEARL HARBOR",
    command: "VICE ADM. W. S. PYE, ACTING CINCPAC",
    page: 58,
    actual: [
      "Wake Island fallen. Second Japanese landing supported by carrier aircraft from KAGA and SORYU overwhelms garrison. Relief expedition (SARATOGA group) recalled approximately 425 miles from objective.",
      "Acting command directs withdrawal to preserve carrier strength. Decision under review pending arrival of relief of CINCPAC.",
    ],
    note: {
      knew: "Admiral Pye, holding the command for a matter of days, knew Wake had fallen and that the relief force built around SARATOGA was still hundreds of miles short of the island.",
      didntKnow: "What he could not know was how bitterly the recall would be judged — by the men on the beach who watched rescue turn away, and by a history weighing one irreplaceable carrier against a lost garrison.",
      coming: "Nimitz, days from taking command, would inherit and ratify the same cold arithmetic again and again: with only three carriers in the Pacific, none could be spent on a position already lost. Wake taught a generation the difference between courage and recklessness.",
    },
  },
  {
    date: "1942-02-01",
    event: "Marshalls–Gilberts raids",
    place: "MARSHALL & GILBERT ISLANDS",
    command: "ADM. C. W. NIMITZ, CINCPAC",
    page: 142,
    actual: [
      "Carrier task forces strike Marshall and Gilbert Islands. ENTERPRISE group (Halsey) raids Kwajalein, Wotje, Maloelap; YORKTOWN group (Fletcher) strikes Jaluit, Makin, Mili.",
      "Shipping and aircraft destroyed; installations bombarded. Own losses light. Forces retiring eastward at high speed.",
    ],
    note: {
      knew: "A month into his command, Nimitz knew his raiders had struck the Marshalls and Gilberts and retired intact — the first time the United States had carried the war into Japanese-held territory.",
      didntKnow: "He did not yet know how badly his own intelligence had overstated the damage done, nor that the true value of the raids lay not in tonnage sunk but in hard lessons banked for battles still months away.",
      coming: "The hit-and-run doctrine blooded here would be paid forward at Coral Sea and Midway; more immediately, it served notice to a stunned fleet that the Pacific war could be taken to the enemy.",
    },
  },
  {
    date: "1942-04-18",
    event: "Doolittle Raid",
    place: "OFF THE COAST OF JAPAN",
    command: "ADM. C. W. NIMITZ, CINCPAC",
    page: 268,
    actual: [
      "Army B-25 aircraft launched from HORNET (Task Force 16, Halsey) against Tokyo, Nagoya, Kobe. Sixteen aircraft airborne after force sighted by enemy picket; launch advanced approximately 170 miles.",
      "Aircraft proceeding to China fields after attack. Task force retiring at high speed. Material results secondary to effect on enemy disposition.",
    ],
    note: {
      knew: "Nimitz knew sixteen Army bombers had launched from HORNET against the Japanese home islands — early and at the limit of their range after the force was sighted by a picket boat.",
      didntKnow: "He did not yet know the fate of the crews scattering toward China, nor that the raid's true effect would register not in Tokyo's rubble but in the mind of the Japanese high command.",
      coming: "Stung by the violation of the homeland, Yamamoto would win approval for the operation he had wanted all along — the destruction of the American carriers at Midway. The raid launched here led straight to the trap Nimitz would spring seven weeks later.",
    },
  },
  {
    date: "1942-05-08",
    event: "Battle of the Coral Sea",
    place: "CORAL SEA",
    command: "ADM. C. W. NIMITZ, CINCPAC",
    page: 331,
    actual: [
      "Carrier engagement in Coral Sea concluded. LEXINGTON lost to fire and explosion following torpedo and bomb hits; YORKTOWN damaged but operational. Enemy light carrier SHOHO sunk 7 May; fleet carrier SHOKAKU heavily damaged, ZUIKAKU air group gutted.",
      "Port Moresby invasion convoy turned back. First check to Japanese advance in the Southwest Pacific.",
    ],
    note: {
      knew: "Nimitz knew he had traded the fleet carrier LEXINGTON for the light carrier SHOHO and heavy damage to SHOKAKU, and that the Port Moresby invasion had been turned back — the first Japanese advance ever halted.",
      didntKnow: "He could not yet be certain how badly SHOKAKU was hurt or that ZUIKAKU's air group had been gutted — that two enemy fleet carriers would therefore be absent from the battle already forming around Midway.",
      coming: "The wounded YORKTOWN would limp into Pearl and be patched for sea in seventy-two hours. Three Japanese carriers neutralized against one American carrier resurrected — a ledger that would decide the month to come.",
    },
  },
  {
    date: "1942-06-04",
    event: "Battle of Midway",
    place: "VICINITY OF MIDWAY",
    command: "ADM. C. W. NIMITZ, CINCPAC",
    page: 388,
    actual: [
      "Major engagement off Midway. Carrier aircraft from ENTERPRISE, HORNET, and YORKTOWN attack enemy carrier force. AKAGI, KAGA, SORYU set ablaze in morning strikes; HIRYU disabled in afternoon. YORKTOWN hit, dead in water, under tow.",
      "Enemy invasion of Midway not pressed. Forces being ordered to exploit advantage without undue risk to remaining carriers.",
    ],
    note: {
      knew: "Forewarned by his codebreakers of the date and the place, Nimitz knew by nightfall that AKAGI, KAGA, SORYU, and HIRYU were burning or sunk and that the Midway invasion had been broken.",
      didntKnow: "He did not yet know the full scale of what had happened in six minutes near 1020, nor that the loss of four fleet carriers and their irreplaceable aircrews had permanently stripped Japan of the initiative.",
      coming: "Midway did not end the war, but it ended Japan's freedom to choose where the war would be fought. The next move would be American — and it was already being drafted for the Solomons.",
    },
  },
  {
    date: "1942-08-07",
    event: "Guadalcanal landings",
    place: "GUADALCANAL — SOLOMON ISLANDS",
    command: "ADM. C. W. NIMITZ, CINCPAC",
    page: 502,
    actual: [
      "Operation WATCHTOWER commenced. First Marine Division landed Guadalcanal, Tulagi, Gavutu-Tanambogo. Airfield on Guadalcanal seized largely intact; renamed for Major Henderson.",
      "Landings against light initial opposition ashore. Enemy air reaction from Rabaul heavy. Naval covering forces remaining in area to support consolidation.",
    ],
    note: {
      knew: "Nimitz knew the First Marine Division was ashore on Guadalcanal and Tulagi and that the airfield — the whole point of the operation — had been taken nearly intact.",
      didntKnow: "He did not yet know that the easy landing was the prelude to a six-month campaign of attrition, nor how swiftly and savagely the Japanese would answer at sea.",
      coming: "The contest for that airfield would consume both navies through the rest of 1942. The bill for committing to a campaign before its supply lines were secure would come due within forty-eight hours.",
    },
  },
  {
    date: "1942-08-09",
    event: "Battle of Savo Island",
    place: "SAVO ISLAND — SOLOMON SEA",
    command: "ADM. C. W. NIMITZ, CINCPAC",
    page: 511,
    actual: [
      "Night surface action off Savo Island. Allied cruiser force surprised by enemy column under Mikawa. ASTORIA, QUINCY, VINCENNES, and HMAS CANBERRA lost; CHICAGO damaged. Enemy retired before dawn without engaging transports.",
      "Amphibious shipping withdrawn ahead of schedule. Marines ashore on Guadalcanal left without full supply or naval cover.",
    ],
    note: {
      knew: "Nimitz knew the worst: four heavy cruisers lost in under an hour off Savo Island, and the amphibious shipping pulled out ahead of schedule, leaving the Marines ashore exposed.",
      didntKnow: "He did not yet know that Mikawa's failure to press on and destroy the transports had spared the landing from outright catastrophe, nor how long the perimeter would have to hold on captured supplies and nerve.",
      coming: "Savo opened the long, grinding fight for Guadalcanal that would run into 1943. The calculated risk had nearly come apart on its second night — and the campaign that defined the road back had only begun.",
    },
  },
];
