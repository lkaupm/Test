import asyncio
import os
from typing import Any

AGENT_SEQUENCE = {
    "intake": {"label": "Intake Agent", "icon": "🤖"},
    "dekkingscheck": {"label": "Dekkingscheck Agent", "icon": "🔍"},
    "juridisch": {"label": "Juridisch Beoordelingsagent", "icon": "⚖️"},
    "strategie": {"label": "Strategie Agent", "icon": "📋"},
    "communicatie": {"label": "Communicatie Agent", "icon": "✉️"},
    "afhandeling": {"label": "Afhandeling Agent", "icon": "📁"},
}

SYSTEM_PROMPTS = {
    "intake": "Je bent de Intake Agent van ARAG. Analyseer de binnengekomen claim en geef een gestructureerde intake-samenvatting. Bepaal: rechtsgebied, urgentie (laag/midden/hoog), volledigheid van informatie, eventuele ontbrekende gegevens.",
    "dekkingscheck": "Je bent de Dekkingscheck Agent van ARAG. Beoordeel of de beschreven situatie gedekt is onder een standaard ARAG rechtsbijstandsverzekering. Controleer: type geschil vs. polisdekking, wachttijden, uitsluitingen (medisch, straf, etc.), maximale vergoeding.",
    "juridisch": "Je bent de Juridisch Beoordelingsagent van ARAG. Beoordeel de juridische merites van de claim. Geef: kwalificatie van het rechtsprobleem, relevante wet- en regelgeving, inschatting slagingskans (%), complexiteit, risico's.",
    "strategie": "Je bent de Strategie Agent van ARAG. Stel een behandelstrategie op. Geef: aanbevolen aanpak (buitengerechtelijk/mediation/procedure), concrete actiestappen, realistische tijdlijn, kostenschatting.",
    "communicatie": "Je bent de Communicatie Agent van ARAG. Stel twee brieven op: 1) Ontvangstbevestiging aan klant met uitleg aanpak en verwachtingen. 2) Aanschrijving aan wederpartij. Gebruik professionele juridische taal.",
    "afhandeling": "Je bent de Afhandeling Agent van ARAG. Maak een dossiersamenvatting. Geef: dossiernummer, prioriteit, geschatte doorlooptijd, mijlpalen, aanbevolen behandelaar-profiel.",
}

MOCK_RESPONSES = {
    "arbeidsrecht": {
        "intake": """**Intake Analyse — Arbeidsrecht**

**Rechtsgebied:** Arbeidsrecht – Ontslag op staande voet
**Urgentie:** HOOG ⚠️
**Volledigheid:** Voldoende voor eerste beoordeling

**Samenvatting:**
De heer/mevrouw [naam] stelt op onrechtmatige wijze op staande voet te zijn ontslagen door [wederpartij]. De werkgever beschuldigt de werknemer van diefstal, zonder aantoonbaar bewijs te verstrekken. Dit betreft een potentieel onregelmatig ontslag dat nietigverklaring of schadevergoeding rechtvaardigt.

**Actiepunten:**
- Arbeidsovereenkomst opvragen
- Ontslagbrief documenteren
- Bewijs van werkgever inzichtelijk maken
- Termijn: ontslag aanvechten binnen 2 maanden (art. 7:686a BW)""",

        "dekkingscheck": """**Dekkingscheck — Arbeidsrecht**

**Dekkingsstatus: ✅ GEDEKT**

**Beoordeling:**
- Rechtsgebied arbeidsrecht valt binnen standaard ARAG dekking
- Polis actief, geen lopende wachttijd van toepassing
- Geen uitsluitingsgronden geïdentificeerd
- Financieel belang (€45.000) binnen maximale vergoeding

**Polisdetails:**
- Module: Arbeidsrecht ✓
- Eigen risico: €250 (eerste zaak)
- Max. vergoeding: €250.000
- Wachttijd verstreken: Ja

**Conclusie:** Zaak is volledig gedekt. Behandeling kan starten.""",

        "juridisch": """**Juridische Beoordeling — Ontslag op Staande Voet**

**Kwalificatie:** Potentieel onregelmatig ontslag op staande voet (art. 7:677 jo. 7:678 BW)

**Juridische analyse:**
Ontslag op staande voet vereist een 'dringende reden' én onverwijlde mededeling. Beschuldiging van diefstal zonder bewijs is juridisch kwetsbaar. Werkgever draagt bewijslast.

**Slagingskans: 72%** 🟢

**Sterke punten:**
- Geen bewijs van diefstal → ontslag mogelijk nietig
- Werkgever moet dringende reden bewijzen
- Recht op transitievergoeding bij onregelmatig ontslag

**Risico's:**
- Werkgever kan aanvullend bewijs indienen
- Reputatieschade werknemer

**Relevante wetgeving:** Art. 7:677, 7:678, 7:681, 7:686a BW | WWZ 2015""",

        "strategie": """**Behandelstrategie — Ontslag op Staande Voet**

**Aanbevolen aanpak: Buitengerechtelijk (fase 1)**

**Actiestappen:**
1. Week 1-2: Bezwaarbrief aan werkgever + eis tot rectificatie
2. Week 2-3: Onderhandelingen over minnelijke schikking
3. Week 4-6: Mediationtraject (indien nodig)
4. Week 6+: Kantonrechter (indien geen schikking)

**Financieel scenario:**
- Minnelijke schikking: verwacht €25.000–€35.000
- Gerechtelijke procedure: verwacht €40.000–€50.000
- Kosten procedure: gedekt door ARAG

**Tijdlijn:** 6–12 weken (buitengerechtelijk) / 6–9 maanden (rechtbank)

**Aanbeveling:** Start met sterke bezwaarbrief om werkgever tot schikking te bewegen.""",

        "communicatie": """**Brief 1 — Ontvangstbevestiging aan klant**

Geachte [naam],

Hierbij bevestigen wij de ontvangst van uw claim inzake uw ontslag op staande voet. Wij hebben uw zaak in behandeling genomen en een juridisch dossier aangelegd.

Ons eerste advies: de beschuldiging van diefstal zonder bewijs maakt uw ontslag juridisch aanvechtbaar. Wij schatten uw kansen goed in.

**Onze aanpak:**
✓ Week 1: Bezwaarbrief aan uw werkgever
✓ Week 2–3: Onderhandelingen
✓ Indien nodig: procedure bij de kantonrechter

Vragen? Bel ons via 088-0200900.

Met vriendelijke groet,
ARAG Rechtsbijstand

---

**Brief 2 — Aanschrijving wederpartij**

Geachte heer/mevrouw,

Wij treden op als juridisch adviseur van [naam werknemer]. Wij stellen u in kennis dat het door u verleende ontslag op staande voet juridisch onhoudbaar is wegens het ontbreken van een aantoonbare dringende reden.

Wij sommeren u binnen 14 dagen:
1. Het ontslag in te trekken en werknemer te herplaatsen, óf
2. Een minnelijke regeling voor te stellen

Bij uitblijven van reactie zullen wij gerechtelijke stappen initiëren.

Hoogachtend,
ARAG Rechtsbijstand""",

        "afhandeling": """**Dossiersamenvatting**

**Dossiernummer:** ARG-2024-88123-AW
**Status:** Actief – In behandeling
**Prioriteit:** HOOG

**Behandelaar:** Senior jurist Arbeidsrecht

**Doorlooptijd schatting:**
- Buitengerechtelijk: 6–8 weken
- Met procedure: 6–9 maanden

**Mijlpalen:**
□ Week 1: Bezwaarbrief verzonden
□ Week 2–3: Reactie wederpartij afgewacht
□ Week 4: Evaluatie moment + eventueel mediation
□ Week 6: Go/no-go gerechtelijke procedure

**Financieel overzicht:**
- Claim waarde: €45.000
- Verwachte schikking: €25.000–€35.000
- ARAG kosten: gedekt

**Volgende actie:** Bezwaarbrief opstellen en versturen aan [wederpartij] binnen 5 werkdagen.""",
    },
    "huurrecht": {
        "intake": """**Intake Analyse — Huurrecht**

**Rechtsgebied:** Huurrecht – Gebreksverhelping woonruimte
**Urgentie:** HOOG ⚠️ (onbewoonbaarheid)
**Volledigheid:** Goed gedocumenteerd

**Samenvatting:**
Huurder meldt dat verhuurder al 3 maanden weigert de cv-ketel te repareren. De woning is daardoor in de winter onbewoonbaar. Dit is een ernstig gebrek dat verhuurder verplicht is te verhelpen op grond van art. 7:206 BW.

**Actiepunten:**
- Huurovereenkomst en correspondentie opvragen
- Gebrek officieel schriftelijk melden (indien nog niet gedaan)
- Foto's en tijdlijn van meldingen documenteren
- Mogelijkheid huurprijsvermindering onderzoeken (art. 7:207 BW)""",

        "dekkingscheck": """**Dekkingscheck — Huurrecht**

**Dekkingsstatus: ✅ GEDEKT**

**Beoordeling:**
- Huurrecht valt binnen standaard ARAG dekking
- Polis actief, geen uitsluitingen van toepassing
- Financieel belang (€8.000) ruim binnen maximale vergoeding

**Polisdetails:**
- Module: Huurrecht ✓
- Eigen risico: €250
- Max. vergoeding: €250.000
- Wachttijd verstreken: Ja

**Conclusie:** Zaak volledig gedekt. Spoedsituatie rechtvaardigt prioriteitsbehandeling.""",

        "juridisch": """**Juridische Beoordeling — Huurrecht**

**Kwalificatie:** Tekortkoming verhuurder in onderhoudsverplichting (art. 7:206 BW)

**Juridische analyse:**
Verhuurder is wettelijk verplicht gebreken aan de woning te verhelpen. Een defecte cv-ketel in de winter kwalificeert als ernstig gebrek. Huurder kan huurprijsvermindering eisen én verhelping via kort geding afdwingen.

**Slagingskans: 88%** 🟢

**Sterke punten:**
- Duidelijke onderhoudsverplichting verhuurder
- 3 maanden inactiviteit verhuurder = grove nalatigheid
- Kort geding mogelijk voor spoedeisende voorziening

**Risico's:**
- Verhuurder kan stellen gebrek pas recent gemeld te zijn

**Relevante wetgeving:** Art. 7:204, 7:206, 7:207 BW | Bouwbesluit 2012""",

        "strategie": """**Behandelstrategie — Huurrecht**

**Aanbevolen aanpak: Spoed + Buitengerechtelijk**

**Actiestappen:**
1. Direct: Ingebrekestelling verhuurder (14 dagen termijn)
2. Week 1: Aanvraag huurprijsvermindering bij Huurcommissie
3. Week 2: Kort geding indien geen actie verhuurder
4. Parallel: Claim schadevergoeding voor geleden schade

**Tijdlijn:** 2–4 weken (kort geding) / 3–6 maanden (bodemprocedure)

**Aanbeveling:** Directe ingebrekestelling + kort geding voorbereiding vanwege urgentie.""",

        "communicatie": """**Brief 1 — Ontvangstbevestiging aan klant**

Geachte [naam],

Wij bevestigen de ontvangst van uw klacht over de defecte cv-ketel. Gezien de urgentie pakken wij uw zaak met voorrang op.

**Onze aanpak:**
✓ Vandaag: Ingebrekestelling aan verhuurder
✓ Week 1-2: Aanvraag huurverlaging + druk op verhuurder
✓ Indien nodig: Kort geding voor onmiddellijke reparatie

Met vriendelijke groet,
ARAG Rechtsbijstand

---

**Brief 2 — Aanschrijving verhuurder**

Geachte heer/mevrouw,

Namens uw huurder [naam] stellen wij u formeel in gebreke wegens het niet verhelpen van een ernstig gebrek (defecte cv-ketel) gedurende meer dan 3 maanden.

U bent op grond van art. 7:206 BW verplicht dit gebrek binnen 14 dagen te verhelpen. Bij uitblijven van actie zullen wij een kort geding starten en huurprijsvermindering vorderen.

Hoogachtend,
ARAG Rechtsbijstand""",

        "afhandeling": """**Dossiersamenvatting**

**Dossiernummer:** ARG-2024-55234-HR
**Status:** Actief – Spoedsituatie
**Prioriteit:** HOOG

**Doorlooptijd:** 2–6 weken

**Mijlpalen:**
□ Dag 1: Ingebrekestelling verstuurd
□ Dag 14: Deadline verhuurder
□ Week 3: Kort geding indien nodig
□ Week 4-6: Huurcommissie procedure

**Financieel:** Claim €8.000 + huurverlaging terug te vorderen""",
    },
    "consumentenrecht": {
        "intake": """**Intake Analyse — Consumentenrecht**

**Rechtsgebied:** Consumentenrecht – Non-conformiteit (art. 7:17 BW)
**Urgentie:** MIDDEN
**Volledigheid:** Voldoende

**Samenvatting:**
Consument heeft een auto gekocht voor €18.500 die na 2 weken total loss is wegens motorschade. Dealer weigert aansprakelijkheid. Potentieel geval van non-conformiteit: de auto voldeed niet aan de redelijke verwachtingen bij aankoop.

**Actiepunten:**
- Koopovereenkomst en factuur opvragen
- Technisch rapport motorschade laten opstellen
- Correspondentie met dealer documenteren
- Termijn: klacht zo spoedig mogelijk (art. 7:23 BW)""",

        "dekkingscheck": """**Dekkingscheck — Consumentenrecht**

**Dekkingsstatus: ✅ GEDEKT**

**Beoordeling:**
- Consumentenrecht gedekt onder ARAG polis
- Belang €18.500 binnen polislimieten
- Geen uitsluitingen van toepassing

**Polisdetails:**
- Module: Consumentenrecht ✓
- Eigen risico: €250
- Max. vergoeding: €250.000

**Conclusie:** Zaak volledig gedekt.""",

        "juridisch": """**Juridische Beoordeling — Non-conformiteit**

**Kwalificatie:** Non-conformiteit bij consumentenkoop (art. 7:17 BW)

**Juridische analyse:**
Een auto die na 2 weken vastloopt wegens motorschade voldoet niet aan de overeenkomst. Wettelijk vermoeden van non-conformiteit binnen 6 maanden na levering (art. 7:18a BW). Dealer moet bewijzen dat gebrek niet aanwezig was bij levering.

**Slagingskans: 79%** 🟢

**Sterke punten:**
- Wettelijk vermoeden na 2 weken = gunstig
- Dealer draagt bewijslast
- Recht op herstel, vervanging of ontbinding + terugbetaling

**Relevante wetgeving:** Art. 7:17, 7:18a, 7:21, 7:22, 7:23 BW""",

        "strategie": """**Behandelstrategie — Consumentenrecht**

**Aanbevolen aanpak: Buitengerechtelijk eerst**

**Actiestappen:**
1. Week 1: Formele klachtbrief dealer (herstel/vervanging eisen)
2. Week 2-3: Indien geen reactie: ontbinding overeenkomst + terugbetaling
3. Week 3-4: Geschillencommissie Voertuigen (snel, laagdrempelig)
4. Week 6+: Kantonrechter indien nodig

**Tijdlijn:** 4–8 weken""",

        "communicatie": """**Brief 1 — Ontvangstbevestiging aan klant**

Geachte [naam],

Wij nemen uw klacht over de aangekochte auto in behandeling. Wij zijn van mening dat u sterke juridische gronden heeft.

**Aanpak:** Klachtbrief → Geschillencommissie → Kantonrechter indien nodig.

Met vriendelijke groet,
ARAG Rechtsbijstand

---

**Brief 2 — Aanschrijving dealer**

Geachte heer/mevrouw,

Namens [naam] sommeren wij u de non-conforme auto te herstellen of de koopsom van €18.500 terug te betalen binnen 14 dagen. Bij uitblijven starten wij een procedure bij de Geschillencommissie Voertuigen.

Hoogachtend,
ARAG Rechtsbijstand""",

        "afhandeling": """**Dossiersamenvatting**

**Dossiernummer:** ARG-2024-71892-CR
**Status:** Actief
**Prioriteit:** MIDDEN

**Doorlooptijd:** 4–12 weken

**Mijlpalen:**
□ Week 1: Klachtbrief dealer
□ Week 2-3: Reactie dealer afgewacht
□ Week 4: Geschillencommissie Voertuigen
□ Week 8+: Kantonrechter indien nodig

**Financieel:** Claim €18.500 terugbetaling + eventuele gevolgschade""",
    },
}


def _get_mock_response(agent_name: str, claim_data: dict) -> str:
    claim_type = claim_data.get("type_claim", "").lower()
    
    type_map = {
        "arbeidsrecht": "arbeidsrecht",
        "huurrecht": "huurrecht",
        "consumentenrecht": "consumentenrecht",
    }
    
    mock_key = type_map.get(claim_type, "arbeidsrecht")
    return MOCK_RESPONSES.get(mock_key, MOCK_RESPONSES["arbeidsrecht"]).get(agent_name, f"Mock response voor {agent_name}")


async def run_agent(agent_name: str, claim_data: dict, context: dict, queue: asyncio.Queue, use_mock: bool = False) -> str:
    if use_mock:
        mock_text = _get_mock_response(agent_name, claim_data)
        full_text = ""
        for char in mock_text:
            full_text += char
            await queue.put({"type": "agent_chunk", "agent": agent_name, "text": char})
            await asyncio.sleep(0.01)
        return full_text
    else:
        import anthropic
        
        client = anthropic.AsyncAnthropic()
        
        user_message = f"""Claim gegevens:
- Naam klant: {claim_data.get('naam', '')}
- Polisnummer: {claim_data.get('polisnummer', '')}
- Type claim: {claim_data.get('type_claim', '')}
- Omschrijving: {claim_data.get('omschrijving', '')}
- Financieel belang: {claim_data.get('belang', '')}
- Wederpartij: {claim_data.get('wederpartij', '')}

Vorige agentresultaten:
{chr(10).join(f"- {k}: {v[:500]}" for k, v in context.items() if k not in ['jurist_decision', 'jurist_note'])}

Jurist beslissing: {context.get('jurist_decision', 'N.v.t.')}
Jurist notitie: {context.get('jurist_note', '')}
"""
        
        full_text = ""
        async with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=SYSTEM_PROMPTS[agent_name],
            messages=[{"role": "user", "content": user_message}],
        ) as stream:
            async for text in stream.text_stream:
                full_text += text
                await queue.put({"type": "agent_chunk", "agent": agent_name, "text": text})
        
        return full_text
