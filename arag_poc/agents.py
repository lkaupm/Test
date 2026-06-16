import asyncio
import os
from typing import AsyncGenerator

AGENT_LABELS = {
    "intake": "🤖 Intake Agent",
    "dekkingscheck": "🔍 Dekkingscheck Agent",
    "juridisch": "⚖️ Juridisch Beoordelaar",
    "strategie": "📋 Strategie Agent",
    "communicatie": "✉️ Communicatie Agent",
    "afhandeling": "📁 Afhandeling Agent",
}

SYSTEM_PROMPTS = {
    "intake": """Je bent de Intake Agent van ARAG Rechtsbijstand. Analyseer de binnengekomen claim en geef een gestructureerde intake-samenvatting.
Bepaal: rechtsgebied, urgentie (laag/midden/hoog), volledigheid van informatie, eventuele ontbrekende gegevens.
Schrijf beknopt maar volledig. Gebruik kopjes met **vet** voor structuur. Max 200 woorden.""",

    "dekkingscheck": """Je bent de Dekkingscheck Agent van ARAG Rechtsbijstand. Beoordeel of de beschreven situatie gedekt is onder een standaard ARAG rechtsbijstandsverzekering.
Controleer: type geschil vs. polisdekking, wachttijden (3 maanden standaard), uitsluitingen (straf, medisch, opzet), maximale vergoeding (€250.000).
Geef een duidelijke dekkingsstatus: GEDEKT / MOGELIJK GEDEKT / NIET GEDEKT. Max 200 woorden.""",

    "juridisch": """Je bent de Juridisch Beoordelingsagent van ARAG Rechtsbijstand. Beoordeel de juridische merites van de claim.
Geef: kwalificatie van het rechtsprobleem, relevante wet- en regelgeving (artikel nummers), inschatting slagingskans (%), complexiteit (laag/midden/hoog), risico's.
Wees specifiek met wetsartikelen. Max 250 woorden.""",

    "strategie": """Je bent de Strategie Agent van ARAG Rechtsbijstand. Stel een behandelstrategie op na de juridische beoordeling.
Geef: aanbevolen aanpak (buitengerechtelijk/mediation/procedure), concrete actiestappen met tijdlijn, verwacht financieel resultaat, kostenschatting.
Gebruik een stappenplan. Max 200 woorden.""",

    "communicatie": """Je bent de Communicatie Agent van ARAG Rechtsbijstand. Stel twee brieven op:
1) Ontvangstbevestiging aan klant: professioneel, empathisch, heldere uitleg aanpak en verwachtingen.
2) Aanschrijving aan wederpartij: formeel juridisch, sommatie met termijn.
Gebruik [naam] als placeholder voor namen. Max 350 woorden totaal.""",

    "afhandeling": """Je bent de Afhandeling Agent van ARAG Rechtsbijstand. Maak een definitieve dossiersamenvatting.
Geef: dossiernummer (genereer format ARG-YYYY-XXXXX-XX), prioriteit, aanbevolen behandelaar-profiel, geschatte doorlooptijd, concrete mijlpalen, financieel overzicht.
Sluit af met directe volgende actie voor de behandelend jurist. Max 200 woorden.""",
}

MOCK_RESPONSES = {
    "intake": {
        "arbeidsrecht": """**Intake Analyse — Arbeidsrecht**

**Rechtsgebied:** Arbeidsrecht – Ontslag op staande voet
**Urgentie:** ⚠️ HOOG
**Volledigheid:** Voldoende voor eerste beoordeling

**Samenvatting:**
Klant stelt op onrechtmatige wijze op staande voet te zijn ontslagen door de werkgever. De werkgever beschuldigt de werknemer van diefstal, zonder aantoonbaar bewijs te verstrekken. Dit betreft een potentieel onregelmatig ontslag dat nietigverklaring of schadevergoeding rechtvaardigt.

**Actiepunten intake:**
- Arbeidsovereenkomst en ontslagbrief documenteren
- Bewijs van werkgever inzichtelijk maken
- Termijn: ontslag aanvechten binnen 2 maanden (art. 7:686a BW)
- Salaris en ancienniteit vaststellen voor berekening schadevergoeding

**Financieel belang:** €45.000 — rechtvaardigt volledige behandeling""",

        "huurrecht": """**Intake Analyse — Huurrecht**

**Rechtsgebied:** Huurrecht – Gebrekkige woning / onderhoudsplicht verhuurder
**Urgentie:** ⚠️ HOOG (winterperiode, onbewoonbaarheid)
**Volledigheid:** Voldoende

**Samenvatting:**
Klant ondervindt al 3 maanden ernstige gebreken aan de huurwoning (cv-ketel defect). Verhuurder verzuimt zijn wettelijke onderhoudsplicht. Situatie is verergerd door het seizoen en raakt de bewoonbaarheid.

**Actiepunten intake:**
- Schriftelijke communicatie met verhuurder documenteren
- Foto/video bewijs van gebrek verzamelen
- Huurprijscontrole: mogelijkheid huurverlaging wegens gebreken
- Eventuele klacht bij Huurcommissie

**Financieel belang:** €8.000 — behandeling proportioneel""",

        "consumentenrecht": """**Intake Analyse — Consumentenrecht**

**Rechtsgebied:** Consumentenrecht – Non-conformiteit bij koop (art. 7:17 BW)
**Urgentie:** MIDDEN
**Volledigheid:** Voldoende

**Samenvatting:**
Klant heeft een auto gekocht voor €18.500 die na 2 weken een ernstig motordefect vertoont. De verkoper weigert aansprakelijkheid. Er is sprake van non-conformiteit: de zaak beantwoordt niet aan de koopovereenkomst.

**Actiepunten intake:**
- Koopovereenkomst/factuur opvragen
- Technisch rapport motorschade laten opstellen
- Communicatie met dealer documenteren
- Ingebrekestelling versturen

**Financieel belang:** €18.500 — behandeling proportioneel""",
    },

    "dekkingscheck": {
        "arbeidsrecht": """**Dekkingscheck — Arbeidsrecht**

**Dekkingsstatus: ✅ GEDEKT**

**Beoordeling:**
- Rechtsgebied arbeidsrecht valt binnen standaard ARAG dekking
- Polis actief, wachttijd verstreken
- Geen uitsluitingsgronden geïdentificeerd
- Financieel belang (€45.000) ruim binnen maximale vergoeding

**Polisdetails:**
| Onderdeel | Status |
|-----------|--------|
| Module Arbeidsrecht | ✓ Actief |
| Wachttijd (3 mnd) | ✓ Verstreken |
| Uitsluitingen | ✓ Geen van toepassing |
| Max. vergoeding | ✓ €250.000 |
| Eigen risico | €250 (eerste zaak) |

**Conclusie:** Zaak is volledig gedekt. Behandeling kan direct starten.""",

        "huurrecht": """**Dekkingscheck — Huurrecht**

**Dekkingsstatus: ✅ GEDEKT**

**Beoordeling:**
- Huurrecht is gedekt onder standaard ARAG polis
- Wachttijd verstreken (polis >3 maanden actief)
- Gebrek aan huurwoning = geen uitsluitingsgrond
- Belang €8.000 binnen maximale vergoeding

**Polisdetails:**
| Onderdeel | Status |
|-----------|--------|
| Module Huurrecht | ✓ Actief |
| Wachttijd | ✓ Verstreken |
| Uitsluitingen | ✓ Geen |
| Max. vergoeding | ✓ €250.000 |

**Conclusie:** Volledig gedekt. Behandeling kan starten.""",

        "consumentenrecht": """**Dekkingscheck — Consumentenrecht**

**Dekkingsstatus: ✅ GEDEKT**

**Beoordeling:**
- Consumentenrecht (koop particulier) gedekt onder ARAG polis
- Geschil ontstaan na afsluiten polis, wachttijd verstreken
- Geen uitsluitingen van toepassing
- Belang €18.500 binnen polislimieten

**Polisdetails:**
| Onderdeel | Status |
|-----------|--------|
| Module Consumentenrecht | ✓ Actief |
| Wachttijd | ✓ Verstreken |
| Uitsluitingen | ✓ Geen |
| Max. vergoeding | ✓ €250.000 |

**Conclusie:** Volledig gedekt. Behandeling kan starten.""",
    },

    "juridisch": {
        "arbeidsrecht": """**Juridische Beoordeling — Ontslag op Staande Voet**

**Kwalificatie:** Potentieel onregelmatig ontslag op staande voet (art. 7:677 jo. 7:678 BW)

**Juridische analyse:**
Ontslag op staande voet vereist een 'dringende reden' én onverwijlde mededeling. Beschuldiging van diefstal zonder bewijs is juridisch uiterst kwetsbaar. De werkgever draagt de volledige bewijslast (art. 7:678 BW).

**Slagingskans: 72%** 🟢

**Sterke punten:**
- Geen bewijs van diefstal → ontslag mogelijk nietig (art. 7:681 BW)
- Recht op transitievergoeding bij onregelmatig ontslag (art. 7:673 BW)
- Mogelijk recht op billijke vergoeding (ernstig verwijtbaar handelen werkgever)

**Risico's:**
- Werkgever kan aanvullend bewijs indienen
- Reputatieschade werknemer in arbeidsmarkt

**Relevante wetgeving:**
Art. 7:677, 7:678, 7:681, 7:673 BW | Wet Werk en Zekerheid (WWZ) 2015
Jurisprudentie: HR 12 februari 1999, NJ 1999/643""",

        "huurrecht": """**Juridische Beoordeling — Gebreken Huurwoning**

**Kwalificatie:** Tekortkoming in de nakoming onderhoudsplicht verhuurder (art. 7:204 jo. 7:206 BW)

**Juridische analyse:**
Verhuurder is wettelijk verplicht de woning in goede staat te onderhouden. Een defecte cv-ketel in winterperiode kwalificeert als ernstig gebrek. Na 3 maanden is er sprake van structureel verzuim.

**Slagingskans: 85%** 🟢

**Mogelijke rechtsmiddelen:**
- Huurverlaging via Huurcommissie (art. 7:207 BW)
- Schadevergoeding voor extra stookkosten
- Machtiging rechter voor herstel op kosten verhuurder (art. 7:206 lid 3 BW)
- In uiterst geval: ontbinding huurovereenkomst

**Relevante wetgeving:**
Art. 7:204, 7:206, 7:207, 7:208 BW | Besluit kleine herstellingen""",

        "consumentenrecht": """**Juridische Beoordeling — Non-conformiteit Voertuig**

**Kwalificatie:** Non-conformiteit bij consumentenkoop (art. 7:17 BW) — motorschade binnen 6 maanden vermoeden non-conformiteit

**Juridische analyse:**
Bij een defect binnen 6 maanden na aankoop geldt het wettelijk vermoeden dat de zaak bij aflevering al non-conform was (art. 7:18a BW). De dealer moet het tegendeel bewijzen.

**Slagingskans: 80%** 🟢

**Rechtsmiddelen:**
- Gratis herstel of vervanging (primair)
- Prijsvermindering of ontbinding (subsidiair, art. 7:22 BW)
- Schadevergoeding gevolgschade

**Relevante wetgeving:**
Art. 7:17, 7:18a, 7:21, 7:22 BW | EU Richtlijn 2019/771 (Consumenten Kooprichtlijn)""",
    },

    "strategie": {
        "arbeidsrecht": """**Behandelstrategie — Ontslag op Staande Voet**

**Aanbevolen aanpak: Buitengerechtelijk (fase 1) → Kantonrechter (fase 2 indien nodig)**

**Actiestappen:**

**Fase 1 — Buitengerechtelijk (week 1–4):**
1. ✉️ Week 1: Bezwaarbrief aan werkgever + eis tot rectificatie + bewijs opvragen
2. 📞 Week 2: Telefonisch overleg / onderhandelingen
3. 🤝 Week 3–4: Minnelijke schikking proberen

**Fase 2 — Mediaton/Rechtbank (week 5+):**
4. ⚖️ Week 5–6: Mediation (indien vastgelopen)
5. 📋 Week 7+: Verzoekschrift kantonrechter

**Financieel scenario:**
- Minnelijke schikking: €25.000–€35.000 + referentie
- Gerechtelijke procedure: €40.000–€50.000
- Kosten procedure: volledig gedekt door ARAG

**Tijdlijn:** 6–8 weken (buitengerechtelijk) | 6–9 maanden (rechtbank)

**Aanbeveling:** Start met krachtige bezwaarbrief. Werkgever heeft zwakke positie zonder bewijs.""",

        "huurrecht": """**Behandelstrategie — Gebrekkige Huurwoning**

**Aanbevolen aanpak: Parallel spoor (Huurcommissie + directe sommatie)**

**Actiestappen:**

**Spoor 1 — Direct (week 1–2):**
1. ✉️ Week 1: Ingebrekestelling verhuurder, termijn 14 dagen voor herstel
2. 📸 Week 1: Bewijs verzamelen (foto's, temperatuurmetingen)

**Spoor 2 — Huurcommissie (week 2–6):**
3. 📋 Week 2: Klacht Huurcommissie indienen (huurverlaging + gebrekenherstel)
4. 🏛️ Week 4–6: Zitting Huurcommissie

**Spoor 3 — Rechtbank (indien nodig):**
5. ⚖️ Week 6+: Kort geding voor onmiddellijke herstelplicht

**Verwacht resultaat:**
- Huurverlaging 40% tot herstel
- Schadevergoeding extra stookkosten
- Herstelplicht verhuurder

**Tijdlijn:** 3–6 weken""",

        "consumentenrecht": """**Behandelstrategie — Non-conformiteit Voertuig**

**Aanbevolen aanpak: Buitengerechtelijk + Geschillencommissie Voertuigen**

**Actiestappen:**

**Fase 1 — Buitengerechtelijk (week 1–3):**
1. ✉️ Week 1: Ingebrekestelling dealer (herstel/vervanging binnen 14 dagen)
2. 🔧 Week 1: Onafhankelijk technisch rapport laten opstellen (bewijs)
3. 📞 Week 2: Onderhandelingen over oplossing

**Fase 2 — Geschillencommissie (week 3–8):**
4. 📋 Week 3: Klacht Geschillencommissie Voertuigen (goedkoop, bindend advies)
5. 🏛️ Week 6–8: Zitting en uitspraak

**Fase 3 — Rechtbank (indien nodig):**
6. ⚖️ Week 8+: Dagvaarding bij rechtbank

**Verwacht resultaat:** Terugbetaling €18.500 of gratis herstel
**Tijdlijn:** 6–10 weken""",
    },

    "communicatie": {
        "arbeidsrecht": """**Brief 1 — Bevestiging aan klant**

Geachte heer/mevrouw [naam],

Hierbij bevestigen wij de ontvangst van uw claim inzake uw ontslag op staande voet bij [wederpartij]. Wij hebben uw zaak in behandeling genomen en aangemeld onder dossiernummer ARG-2024-88123-AW.

Na eerste beoordeling concluderen wij dat uw positie juridisch sterk is. De beschuldiging van diefstal zonder bewijs maakt uw ontslag aanvechtbaar.

**Onze aanpak:**
→ Week 1: Bezwaarbrief aan werkgever
→ Week 2–3: Onderhandelingen minnelijke schikking
→ Indien nodig: procedure kantonrechter

Voor vragen: 088-020 09 00 | mijn.arag.nl

Met vriendelijke groet,
ARAG Rechtsbijstand

---

**Brief 2 — Aanschrijving wederpartij**

Geachte heer/mevrouw,

Wij treden op als juridisch adviseur van [naam werknemer]. Wij stellen u in kennis dat het door u verleende ontslag op staande voet d.d. [datum] juridisch onhoudbaar is wegens het ontbreken van een aantoonbare dringende reden als bedoeld in art. 7:678 BW.

Wij sommeren u hierbij het ontslag in te trekken en werknemer per direct te herplaatsen, dan wel binnen **14 dagen** een minnelijke regeling voor te stellen.

Bij uitblijven van een reactie zullen wij zonder nadere aankondiging gerechtelijke stappen initiëren.

Hoogachtend,
ARAG Rechtsbijstand""",

        "huurrecht": """**Brief 1 — Bevestiging aan klant**

Geachte heer/mevrouw [naam],

Wij bevestigen ontvangst van uw claim inzake gebreken aan uw huurwoning. Uw zaak is in behandeling genomen onder dossiernummer ARG-2024-55234-HR.

Uw situatie (defecte cv-ketel, 3 maanden onopgelost) is ernstig en juridisch sterk. Wij handelen met prioriteit.

**Aanpak:** Ingebrekestelling verhuurder + Huurcommissie klacht deze week.

Met vriendelijke groet, ARAG Rechtsbijstand

---

**Brief 2 — Aanschrijving verhuurder**

Geachte heer/mevrouw,

Namens uw huurder [naam] stellen wij vast dat u ernstig tekortschiet in uw wettelijke onderhoudsplicht (art. 7:206 BW). De cv-ketel is al 3 maanden defect ondanks herhaalde verzoeken.

Wij sommeren u de cv-ketel binnen **7 dagen** volledig te herstellen of te vervangen. Tevens vorderen wij schadevergoeding voor de periode van het gebrek.

Bij niet-nakoming starten wij een kort geding procedure.

Hoogachtend, ARAG Rechtsbijstand""",

        "consumentenrecht": """**Brief 1 — Bevestiging aan klant**

Geachte heer/mevrouw [naam],

Wij bevestigen ontvangst van uw claim inzake de non-conforme auto. Dossiernummer: ARG-2024-71892-CR.

Uw rechtspositie is sterk: een motordefect na 2 weken valt onder het wettelijk vermoeden van non-conformiteit. De dealer moet het tegendeel bewijzen.

**Aanpak:** Ingebrekestelling + onafhankelijk technisch rapport deze week.

Met vriendelijke groet, ARAG Rechtsbijstand

---

**Brief 2 — Aanschrijving dealer**

Geachte heer/mevrouw,

Namens de heer/mevrouw [naam] stellen wij vast dat het door u geleverde voertuig [merk/type] niet beantwoordt aan de koopovereenkomst (art. 7:17 BW). Het motordefect na 2 weken gebruik kwalificeert als non-conformiteit; het wettelijk vermoeden van art. 7:18a BW is van toepassing.

Wij vorderen binnen **14 dagen**: kosteloos herstel of vervanging, bij gebreke waarvan wij ontbinding van de koopovereenkomst en terugbetaling van €18.500 eisen.

Hoogachtend, ARAG Rechtsbijstand""",
    },

    "afhandeling": {
        "arbeidsrecht": """**Dossiersamenvatting — ARG-2024-88123-AW**

**Status:** ✅ Actief — Behandeling gestart
**Prioriteit:** 🔴 HOOG
**Behandelaar:** Senior Jurist Arbeidsrecht (5+ jaar ervaring ontslagrecht)

**Doorlooptijd:**
- Buitengerechtelijk: **6–8 weken**
- Met kantonprocedure: **6–9 maanden**

**Mijlpalen:**
□ Dag 1–3: Bezwaarbrief opstellen en verzenden
□ Week 2: Reactie wederpartij afwachten
□ Week 3: Onderhandelingen / schikkingsvoorstel
□ Week 4: Evaluatiemoment — doorgaan of escaleren?
□ Week 6: Go/no-go rechtbankprocedure

**Financieel overzicht:**
| Post | Bedrag |
|------|--------|
| Claim waarde | €45.000 |
| Verwachte schikking | €25.000–€35.000 |
| ARAG behandelkosten | Gedekt |
| Kans op succes | 72% |

**⚡ Directe actie jurist:** Bezwaarbrief opstellen en verzenden aan Bouwbedrijf De Vries BV binnen **3 werkdagen**.""",

        "huurrecht": """**Dossiersamenvatting — ARG-2024-55234-HR**

**Status:** ✅ Actief — Spoedbehandeling
**Prioriteit:** 🔴 HOOG (onbewoonbaarheid)
**Behandelaar:** Jurist Huurrecht

**Doorlooptijd:** 3–6 weken

**Mijlpalen:**
□ Dag 1: Ingebrekestelling verhuurder (7 dagen termijn)
□ Week 1: Klacht Huurcommissie indienen
□ Week 2: Bewijs verzamelen met klant
□ Week 4–6: Zitting Huurcommissie

**Financieel overzicht:**
| Post | Bedrag |
|------|--------|
| Claim waarde | €8.000 |
| Verwachte huurverlaging | 40% tijdelijk |
| Schadevergoeding | €500–€1.500 |

**⚡ Directe actie jurist:** Ingebrekestelling verhuurder **vandaag** verzenden — winterperiode = spoedsituatie.""",

        "consumentenrecht": """**Dossiersamenvatting — ARG-2024-71892-CR**

**Status:** ✅ Actief — Standaard behandeling
**Prioriteit:** 🟡 MIDDEN
**Behandelaar:** Jurist Consumentenrecht

**Doorlooptijd:** 6–10 weken

**Mijlpalen:**
□ Week 1: Ingebrekestelling dealer + technisch rapport opdracht
□ Week 2: Onderhandelingen
□ Week 3: Geschillencommissie Voertuigen indienen
□ Week 6–8: Zitting en uitspraak

**Financieel overzicht:**
| Post | Bedrag |
|------|--------|
| Claim waarde | €18.500 |
| Verwacht resultaat | Herstel of terugbetaling €18.500 |
| Kans op succes | 80% |

**⚡ Directe actie jurist:** Ingebrekestelling dealer opstellen + onafhankelijk expertise bureau inschakelen binnen **2 werkdagen**.""",
    },
}


def _get_claim_type_key(claim_type: str) -> str:
    mapping = {
        "Arbeidsrecht": "arbeidsrecht",
        "Huurrecht": "huurrecht",
        "Consumentenrecht": "consumentenrecht",
    }
    return mapping.get(claim_type, "arbeidsrecht")


async def run_agent(agent_name: str, claim_data: dict, context: dict, queue: asyncio.Queue):
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    claim_type_key = _get_claim_type_key(claim_data.get("claim_type", "Arbeidsrecht"))

    await queue.put({"type": "agent_start", "agent": agent_name, "label": AGENT_LABELS[agent_name]})

    if not api_key or api_key == "":
        # Mock mode: stream character by character
        mock_text = MOCK_RESPONSES.get(agent_name, {}).get(claim_type_key, "")
        if not mock_text:
            # Fallback to arbeidsrecht mock
            mock_text = MOCK_RESPONSES.get(agent_name, {}).get("arbeidsrecht", f"[Mock] {agent_name} analyse voltooid.")

        full_text = ""
        for char in mock_text:
            full_text += char
            await queue.put({"type": "agent_chunk", "agent": agent_name, "text": char})
            await asyncio.sleep(0.008)

        await queue.put({"type": "agent_complete", "agent": agent_name, "result": full_text})
        return full_text

    # Real API mode
    try:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=api_key)

        context_text = "\n\n".join([
            f"**{k.upper()} BEVINDINGEN:**\n{v}" for k, v in context.items()
        ])

        user_message = f"""**CLAIM GEGEVENS:**
Naam klant: {claim_data.get('naam', 'Onbekend')}
Polisnummer: {claim_data.get('polisnummer', 'Onbekend')}
Type claim: {claim_data.get('claim_type', 'Onbekend')}
Omschrijving: {claim_data.get('omschrijving', '')}
Geschat belang: €{claim_data.get('belang', '0')}
Wederpartij: {claim_data.get('wederpartij', 'Onbekend')}

{f"**VORIGE AGENT BEVINDINGEN:**{chr(10)}{context_text}" if context_text else ""}

Voer uw analyse uit."""

        full_text = ""
        async with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=600,
            system=SYSTEM_PROMPTS[agent_name],
            messages=[{"role": "user", "content": user_message}]
        ) as stream:
            async for text in stream.text_stream:
                full_text += text
                await queue.put({"type": "agent_chunk", "agent": agent_name, "text": text})

        await queue.put({"type": "agent_complete", "agent": agent_name, "result": full_text})
        return full_text

    except Exception as e:
        error_msg = f"[Fout bij uitvoeren agent: {str(e)}]"
        await queue.put({"type": "agent_chunk", "agent": agent_name, "text": error_msg})
        await queue.put({"type": "agent_complete", "agent": agent_name, "result": error_msg})
        return error_msg
