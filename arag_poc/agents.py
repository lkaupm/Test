import asyncio
import json

PHASES = {
    "intake": {
        "label": "Fase 1: Intake",
        "color": "#fff8f0",
        "agents": ["transcription", "summary", "key_facts", "completeness", "coverage"]
    },
    "assessment": {
        "label": "Fase 2: Beoordeling",
        "color": "#f0f4ff",
        "agents": ["legal_analysis"]
    },
    "handling": {
        "label": "Fase 3: Afhandeling",
        "color": "#f0faf4",
        "agents": ["letter", "legal_drafting"]
    }
}

AGENTS = {
    "transcription": {
        "label": "Transcription Agent",
        "icon": "📝",
        "phase": "intake",
        "sub_agents": [],
        "system_prompt": "Je bent een transcriptie-agent die claimberichten verwerkt en documenteert."
    },
    "summary": {
        "label": "Summary Agent",
        "icon": "📋",
        "phase": "intake",
        "sub_agents": []
    },
    "key_facts": {
        "label": "Key Facts Agent",
        "icon": "🔑",
        "phase": "intake",
        "sub_agents": []
    },
    "completeness": {
        "label": "Completeness Check Agent",
        "icon": "✅",
        "phase": "intake",
        "sub_agents": []
    },
    "coverage": {
        "label": "Coverage Review Agent",
        "icon": "🔍",
        "phase": "intake",
        "sub_agents": []
    },
    "legal_analysis": {
        "label": "Legal Analysis Agent",
        "icon": "⚖️",
        "phase": "assessment",
        "sub_agents": ["legal_research", "similar_cases", "key_facts_refined", "next_best_action"]
    },
    "legal_research": {
        "label": "Legal Research Agent",
        "icon": "📚",
        "is_sub_agent": True,
        "phase": "assessment"
    },
    "similar_cases": {
        "label": "Similar Cases Agent",
        "icon": "🗂️",
        "is_sub_agent": True,
        "phase": "assessment"
    },
    "key_facts_refined": {
        "label": "Key Facts Agent (verfijning)",
        "icon": "🔑",
        "is_sub_agent": True,
        "phase": "assessment"
    },
    "next_best_action": {
        "label": "Next Best Action Agent",
        "icon": "🎯",
        "is_sub_agent": True,
        "phase": "assessment"
    },
    "letter": {
        "label": "Letter Agent",
        "icon": "✉️",
        "phase": "handling",
        "sub_agents": ["similar_cases_h", "summary_h", "key_facts_h", "legal_research_h"]
    },
    "similar_cases_h": {
        "label": "Similar Cases Agent",
        "icon": "🗂️",
        "is_sub_agent": True,
        "phase": "handling"
    },
    "summary_h": {
        "label": "Summary Agent",
        "icon": "📋",
        "is_sub_agent": True,
        "phase": "handling"
    },
    "key_facts_h": {
        "label": "Key Facts Agent",
        "icon": "🔑",
        "is_sub_agent": True,
        "phase": "handling"
    },
    "legal_research_h": {
        "label": "Legal Research Agent",
        "icon": "📚",
        "is_sub_agent": True,
        "phase": "handling"
    },
    "legal_drafting": {
        "label": "Legal Drafting Agent",
        "icon": "📄",
        "phase": "handling",
        "sub_agents": ["similar_cases_ld", "legal_analysis_ld"]
    },
    "similar_cases_ld": {
        "label": "Similar Cases Agent",
        "icon": "🗂️",
        "is_sub_agent": True,
        "phase": "handling"
    },
    "legal_analysis_ld": {
        "label": "Legal Analysis Agent",
        "icon": "⚖️",
        "is_sub_agent": True,
        "phase": "handling"
    }
}

MOCK_RESPONSES = {
    "arbeidsrecht": {
        "transcription": """📝 Transcriptie voltooid — Mijn ARAG digitale intake

Ontvangst: maandag 09:42 via Mijn ARAG portaal
Klant: Piet Janssen, polisnummer ARAG-2024-88123

Verbatim samenvatting klant:
"Ik werk al 8 jaar bij Bouwbedrijf De Vries BV en ben afgelopen vrijdag op staande voet ontslagen. Mijn leidinggevende beschuldigde mij van het stelen van gereedschap ter waarde van €300. Ik heb dit niet gedaan en er is geen bewijs. Ik heb geen ontslagbrief ontvangen met onderbouwing."

Kanaal: Mijn ARAG (tekst)
Status: Volledig gedocumenteerd""",
        "summary": """**Samenvatting Claim**

**Situatie:** Werknemer (8 jaar in dienst) op staande voet ontslagen wegens beschuldiging diefstal gereedschap (€300). Geen bewijs geleverd door werkgever.

**Kernvraag:** Is het ontslag op staande voet rechtsgeldig gegeven de afwezigheid van bewijs?

**Gewenste uitkomst:** Ontslag aanvechten, herplaatsing of schadevergoeding.

**Tijdlijn:** Ontslag gegeven op vrijdag, eerste contact ARAG maandag. Urgentie hoog: aanvechttermijn loopt.""",
        "key_facts": """**Geëxtraheerde Sleutelfeiten**

1. Dienstverband: 8 jaar bij Bouwbedrijf De Vries BV
2. Ontslaggrond: beschuldiging diefstal gereedschap €300
3. Bewijs: geen bewijs verstrekt door werkgever
4. Procedure: geen formele ontslagbrief met onderbouwing ontvangen
5. Tijdstip ontslag: vrijdag (recent)
6. Klant ontkent beschuldiging uitdrukkelijk
7. Geen eerdere disciplinaire maatregelen bekend
8. Financieel belang klant: maandsalaris + eventuele transitievergoeding""",
        "completeness": """**Volledigheidscheck**

✓ Aanwezig:
- Naam klant en polisnummer
- Beschrijving ontslaggrond
- Naam werkgever
- Tijdstip ontslag

✗ Ontbreekt / Nog op te vragen:
- Kopie arbeidsovereenkomst
- Eventuele ontslagbrief / aangetekende brief
- CAO-informatie (van toepassing?)
- Salarisstrook (berekening transitievergoeding)

**Actie jurist:** Klant verzoeken documenten te uploaden via Mijn ARAG vóór juridische analyse""",
        "coverage": """**Coverage Review — Arbeidsrecht**

✅ **GEDEKT**

- Module Arbeidsrecht: actief ✓
- Wachttijd: verstreken (polis >3 maanden) ✓
- Uitsluitingen: geen van toepassing ✓
- Max. vergoeding: €250.000 ✓
- Eigen risico: €250

Bijzonderheden: ontslag op staande voet valt expliciet onder de arbeidsrechtmodule. Geen strafrecht-component geïdentificeerd.""",
        "legal_research": """Relevante wet- en regelgeving:
• Art. 7:677 BW — onverwijld ontslag op staande voet
• Art. 7:678 BW — dringende reden, bewijslast werkgever
• Art. 7:681 BW — vernietigbaarheid onregelmatig ontslag
• Art. 7:673 BW — transitievergoeding
Jurisprudentie: HR 12 feb 1999 (diefstal zonder bewijs onvoldoende)""",
        "similar_cases": """Vergelijkbare ARAG-zaken:
1. Zaak HR-2022-4471: Ontslag staande voet beschuldiging diefstal, geen camerabeelden. Uitkomst: nietig verklaard, €28.000 schikking.
2. Zaak HR-2023-0892: Bewijs achteraf geleverd. Ontslag in stand. Les: snel documenteren.""",
        "key_facts_refined": """Verfijnde sleutelfeiten (juridisch geprioriteerd):
✓ Bewezen: 8 jaar dienstverband, geen ontslagbrief
? Onbewezen: diefstal (bewijslast bij werkgever)
⚠️ Kritisch: termijn aanvechting (2 maanden)""",
        "next_best_action": """Aanbevolen acties:
1. ✅ Bezwaarbrief + schikkingspoging — 68% kans, 6-8 weken
2. ⚖️ Kantonrechter — 72% kans, 6-9 maanden
3. 🤝 Mediation — 55% kans, 4-6 weken""",
        "legal_analysis": """**Juridische Analyse — Ontslag op Staande Voet**

**Kwalificatie:** Potentieel onregelmatig ontslag op staande voet (art. 7:677 jo. 7:678 BW)

**Beoordeling:** Werkgever heeft geen aantoonbaar bewijs van diefstal. De bewijslast ligt bij de werkgever (art. 7:678 BW). Zonder bewijs is de dringende reden niet vast te stellen.

**Slagingskans: 72%** 🟢

**Risico's:** Werkgever kan alsnog bewijs aanleveren. Loondoorbetalingsverplichting kan complex zijn.

**Aanbeveling:** Start buitengerechtelijk traject met bezwaarbrief aan werkgever. Deadline aanvechten: binnen 2 maanden na ontslagdatum.""",
        "similar_cases_h": "Brief-precedent: Zaak HR-2022-4471 — aanschrijving leidde tot schikking binnen 3 weken.",
        "summary_h": "Kernboodschap brief: werknemer (8jr) ontslagen zonder bewijs diefstal. Verzoek om ontslag terug te draaien of schikking.",
        "key_facts_h": "Kernfeiten voor brief: 8jr dienstverband, geen bewijs, geen formele ontslagbrief ontvangen.",
        "legal_research_h": "Juridische grondslag brief: art. 7:677 + 7:678 BW. Eis: onderbouwing dringende reden binnen 5 werkdagen.",
        "letter": """**Brief 1 — Ontvangstbevestiging aan klant Piet Janssen**

Geachte heer Janssen,

Wij bevestigen de ontvangst van uw rechtshulpverzoek d.d. heden. Uw zaak betreft het ontslag op staande voet door Bouwbedrijf De Vries BV.

Wij hebben uw dossier in behandeling genomen. Op basis van onze eerste analyse zien wij goede mogelijkheden om uw ontslag aan te vechten. Uw toegewezen jurist neemt binnen 1 werkdag contact met u op.

Met vriendelijke groet,
ARAG Rechtsbijstand

---

**Brief 2 — Aanschrijving aan Bouwbedrijf De Vries BV**

Geachte directie,

Wij vertegenwoordigen de heer P. Janssen (hierna: cliënt) inzake het op [datum] verleende ontslag op staande voet.

Namens cliënt betwisten wij de rechtsgeldigheid van dit ontslag. Op grond van artikel 7:678 BW dient u een dringende reden aan te tonen. Tot op heden heeft u geen enkel bewijs van de beweerde diefstal overlegd.

Wij sommeren u hierbij:
1. Het ontslag schriftelijk in te trekken binnen 5 werkdagen
2. Het achterstallig salaris te voldoen
3. Cliënt toe te laten tot zijn werk

Bij gebreke hiervan zullen wij rechtsmaatregelen treffen.

Met vriendelijke groet,
Mr. [Naam], ARAG Rechtsbijstand""",
        "similar_cases_ld": "Processtuk-precedent: Verweer HR-2022-4471 succesvol ingediend bij Rechtbank Rotterdam.",
        "legal_analysis_ld": "Juridische verdieping processtuk: bewijslast-probleem werkgever centraal; art. 7:678 BW vereist objectief aantoonbare dringende reden.",
        "legal_drafting": """**CONCEPT VERWEERSCHRIFT**

Aan: Kanton rechtbank [Stad]
Inzake: Bouwbedrijf De Vries BV vs. P. Janssen
Datum: [datum]

**VERWEER**

Conclusie van antwoord, tevens houdende eis in reconventie

**1. INLEIDING**
Verweerder, de heer Piet Janssen, betwist met klem de rechtmatigheid van het hem op [datum] verleende ontslag op staande voet.

**2. FEITEN**
- 8 jaar onberispelijk dienstverband
- Geen voorafgaande disciplinaire maatregelen
- Ontslag gebaseerd op ongefundeerde beschuldiging diefstal
- Geen bewijs overlegd door werkgever

**3. JURIDISCH KADER**
Op grond van art. 7:678 BW dient de werkgever de dringende reden onomstotelijk aan te tonen. Verweerder verwijst naar HR 12 februari 1999 waaruit volgt dat een beschuldiging zonder bewijs onvoldoende grondslag is voor ontslag op staande voet.

**4. CONCLUSIE**
Verweerder verzoekt de rechtbank:
1. Het ontslag nietig te verklaren
2. Werkgever te veroordelen tot loondoorbetaling
3. Werkgever te veroordelen in proceskosten

Alternatief: toekenning billijke vergoeding + transitievergoeding.

[Handtekening Jurist ARAG]"""
    },
    "huurrecht": {
        "transcription": """📝 Transcriptie voltooid — Telefoongesprek

Ontvangst: dinsdag 14:15 via ARAG Servicedesk
Klant: Maria de Boer, polisnummer ARAG-2023-55441

Verbatim samenvatting klant:
"Mijn verhuurder heeft mijn huur per 1 april verhoogd van €875 naar €1.050 per maand. Dat is een verhoging van €175, ruim 20%. Ik huur al 6 jaar dit appartement in Amsterdam. Mijn vrienden zeggen dat dit wettelijk niet mag. Ik heb een brief van de verhuurder ontvangen maar geen toelichting op de berekening."

Kanaal: Telefoon (inkomend)
Status: Volledig gedocumenteerd""",
        "summary": """**Samenvatting Claim**

**Situatie:** Huurster (6 jaar, Amsterdam) geconfronteerd met huurverhoging van 20% (€875 → €1.050). Wettelijk maximum is voor sociale huur 5,5% in 2024.

**Kernvraag:** Is de huurverhoging van 20% rechtmatig?

**Gewenste uitkomst:** Huurverhoging terugdraaien naar wettelijk maximum.

**Tijdlijn:** Verhoging per 1 april, huidig contact april. Bezwaartermijn: tot 1 juli.""",
        "key_facts": """**Geëxtraheerde Sleutelfeiten**

1. Huurperiode: 6 jaar, Amsterdam
2. Huidige huur: €875/maand
3. Nieuwe huur: €1.050/maand (+€175, +20%)
4. Huurtype: vermoedelijk sociale huur (te verifiëren)
5. Ingangsdatum verhoging: 1 april
6. Geen onderbouwing berekening ontvangen
7. Wettelijk maximum 2024: max 5,5% sociale huur
8. Financieel belang: €175/maand = €2.100/jaar""",
        "completeness": """**Volledigheidscheck**

✓ Aanwezig:
- Naam klant en polisnummer
- Huurprijzen (oud en nieuw)
- Adres en stad
- Huurperiode

✗ Ontbreekt:
- Huurcontract (sociaal of vrije sector?)
- Brief verhuurder met aankondiging
- Puntentelling woning (bepaalt huurklasse)
- WOZ-waarde woning

**Actie jurist:** Huurcontract en verhuurbrief opvragen bij klant""",
        "coverage": """**Coverage Review — Huurrecht**

✅ **GEDEKT**

- Module Huurrecht: actief ✓
- Wachttijd: verstreken (polis >1 jaar) ✓
- Uitsluitingen: geen van toepassing ✓
- Max. vergoeding: €50.000 ✓

Bijzonderheden: huurrechtgeschillen vallen volledig onder de polis. Sprongcassatie bij Hoge Raad niet gedekt.""",
        "legal_research": """Relevante wetgeving:
• Art. 7:250 BW — huurprijswijziging
• Uitvoeringswet huurprijzen woonruimte (UHW)
• Besluit huurprijzen woonruimte 2024: max 5,5% sociaal
• Art. 7:253 BW — huurcommissie procedure""",
        "similar_cases": """Vergelijkbare zaken:
1. Zaak HC-2023-1182: Verhoging 18%, teruggedraaid naar 5,5%. Huurcommissie uitspraak 6 weken.
2. Zaak HC-2022-0034: Vrije sectorwoning, verhoging toegestaan. Les: huurklasse bepalen is cruciaal.""",
        "key_facts_refined": """Verfijnde feiten:
✓ Bewezen: 20% verhoging, 6jr huur Amsterdam
? Kritisch: huurtype (sociaal vs vrij) — bepalend voor procedure
⚠️ Deadline: bezwaar vóór 1 juli indienen""",
        "next_best_action": """Aanbevolen acties:
1. ✅ Huurcommissie procedure — 85% kans, 6-8 weken, gratis
2. ⚖️ Kantonrechter — 70% kans, 6 maanden
3. ✉️ Bezwaarbrief verhuurder — 40% kans, 2 weken""",
        "legal_analysis": """**Juridische Analyse — Illegale Huurverhoging**

**Kwalificatie:** Waarschijnlijk onrechtmatige huurverhoging in sociale sector (art. 7:250 BW jo. UHW)

**Beoordeling:** Een verhoging van 20% overschrijdt het wettelijk maximum van 5,5% (2024) ruimschoots. Mits de woning kwalificeert als sociale huur (huurprijs onder liberalisatiegrens €879/maand), is de verhoging aanvechtbaar.

**Slagingskans: 85%** 🟢

**Risico's:** Indien vrije sector: verhoging mogelijk wel toegestaan. Puntentelling woning moet worden opgevraagd.

**Aanbeveling:** Direct huurcommissie inschakelen. Snelste en goedkoopste route. Deadline: vóór ingangsdatum + 3 maanden.""",
        "similar_cases_h": "Brief-precedent: Aanschrijving verhuurder in HC-2023-1182 leidde tot vrijwillige correctie nog vóór huurcommissiezitting.",
        "summary_h": "Kernboodschap: huurverhoging 20% overschrijdt wettelijk max (5,5%). Verzoek tot correctie binnen 14 dagen.",
        "key_facts_h": "Kernfeiten brief: €875→€1.050, +20%, wettelijk max 5,5%, ingangsdatum 1 april.",
        "legal_research_h": "Grondslag: art. 7:250 BW + Besluit huurprijzen 2024. Max toegestaan: €875 × 1,055 = €922,63/maand.",
        "letter": """**Brief 1 — Bevestiging aan mevrouw De Boer**

Geachte mevrouw De Boer,

Wij bevestigen uw rechtshulpverzoek inzake de huurverhoging van uw woning te Amsterdam.

Op basis van onze eerste analyse is de huurverhoging van 20% zeer waarschijnlijk in strijd met de wettelijke maximering. Wij nemen uw zaak met prioriteit in behandeling.

Uw jurist neemt binnen 1 werkdag contact op voor verdere actie.

Met vriendelijke groet,
ARAG Rechtsbijstand

---

**Brief 2 — Aanschrijving aan verhuurder**

Geachte verhuurder,

Wij vertegenwoordigen mevrouw M. de Boer, huurster van het pand aan [adres] te Amsterdam.

U heeft per 1 april de huurprijs verhoogd van €875 naar €1.050 per maand (+20%). Op grond van het Besluit huurprijzen woonruimte 2024 bedraagt het wettelijk maximum voor sociale huurwoningen 5,5%. De maximaal toegestane huur bedraagt derhalve €922,63 per maand.

Wij verzoeken u de huurverhoging binnen 14 dagen te corrigeren naar maximaal €922,63. Bij uitblijven van reactie zullen wij een procedure bij de Huurcommissie starten.

Met vriendelijke groet,
Mr. [Naam], ARAG Rechtsbijstand""",
        "similar_cases_ld": "Processtuk-precedent: Verzoekschrift HC-2023-1182 succesvol, huurcommissie uitspraak in 6 weken.",
        "legal_analysis_ld": "Juridische verdieping: art. 7:250 BW vereist schriftelijke onderbouwing + wettelijk maximum. Beide vereisten geschonden.",
        "legal_drafting": """**VERZOEKSCHRIFT HUURCOMMISSIE**

Aan: De Huurcommissie
Datum: [datum]
Betreft: Verzoek tot toetsing huurverhoging

**Verzoeker:** Mevrouw M. de Boer
**Verhuurder:** [Naam verhuurder]
**Adres woning:** [adres], Amsterdam

**VERZOEK**

Verzoeker verzoekt de Huurcommissie de voorgestelde huurverhoging van €875 naar €1.050 (20%) te toetsen en te verlagen naar het wettelijk maximum.

**GRONDEN**

1. De verhoging van 20% overschrijdt het wettelijk maximum van 5,5% (Besluit huurprijzen woonruimte 2024) ruimschoots.
2. De woning kwalificeert als sociale huurwoning (huurprijs < liberalisatiegrens).
3. Verhuurder heeft geen inhoudelijke onderbouwing van de berekening verstrekt.

**VERZOEK HUURCOMMISSIE**

De Huurcommissie te verzoeken:
1. De huurverhoging te toetsen
2. De maximale huurprijs vast te stellen op €922,63/maand
3. De teveel betaalde huur terug te vorderen

Bijlagen: huurcontract, aankondigingsbrief verhuurder

[Handtekening Jurist ARAG]"""
    },
    "consumentenrecht": {
        "transcription": """📝 Transcriptie voltooid — Mijn ARAG digitale intake

Ontvangst: woensdag 11:20 via Mijn ARAG portaal
Klant: Ahmed El-Masri, polisnummer ARAG-2024-12034

Verbatim samenvatting klant:
"Ik heb 4 maanden geleden een wasmachine gekocht bij MediaMarkt voor €649. Na 3 maanden stopte het apparaat met werken. De winkel weigert reparatie of vervanging en zegt dat ik zelf maar een reparateur moet bellen. De fabrikant (Bosch) zegt dat het buiten garantie is, maar dat kan toch niet na 3 maanden?"

Kanaal: Mijn ARAG (tekst)
Status: Volledig gedocumenteerd""",
        "summary": """**Samenvatting Claim**

**Situatie:** Consument kocht wasmachine (€649) bij MediaMarkt. Na 3 maanden defect. Zowel winkel als fabrikant weigeren service.

**Kernvraag:** Heeft klant recht op gratis reparatie/vervanging onder wettelijke garantie?

**Gewenste uitkomst:** Reparatie of vervanging van de wasmachine, kosteloos.

**Tijdlijn:** Aankoop 4 maanden geleden, defect 1 maand geleden. Wettelijke garantietermijn: 2 jaar.""",
        "key_facts": """**Geëxtraheerde Sleutelfeiten**

1. Product: wasmachine Bosch, aankoopprijs €649
2. Verkoper: MediaMarkt
3. Aankoopdatum: ca. 4 maanden geleden
4. Defect opgetreden: na 3 maanden gebruik
5. Weigeringen: zowel verkoper als fabrikant
6. Wettelijke garantie: 2 jaar (conformiteitseis art. 7:17 BW)
7. Fabrieksgarantie: door fabrikant betwist
8. Financieel belang: €649 (vervanging) of reparatiekosten""",
        "completeness": """**Volledigheidscheck**

✓ Aanwezig:
- Beschrijving probleem
- Naam verkoper en fabrikant
- Aankoopbedrag
- Tijdlijn

✗ Ontbreekt:
- Aankoopbon / factuur
- Correspondentie met MediaMarkt/Bosch
- Exacte foutmelding / defect beschrijving
- Model- en serienummer wasmachine

**Actie jurist:** Aankoopbon en correspondentie opvragen""",
        "coverage": """**Coverage Review — Consumentenrecht**

✅ **GEDEKT**

- Module Consumentenrecht: actief ✓
- Wachttijd: verstreken ✓
- Uitsluitingen: geen van toepassing ✓
- Max. vergoeding: €25.000 ✓

Bijzonderheden: consumentenrechtgeschillen inclusief non-conformiteit volledig gedekt.""",
        "legal_research": """Relevante wetgeving:
• Art. 7:17 BW — conformiteitseis
• Art. 7:21 BW — herstel of vervanging
• Art. 7:18 BW — bewijsvermoeden 12 maanden
• EU Richtlijn 2019/771 — 2 jaar wettelijke garantie""",
        "similar_cases": """Vergelijkbare zaken:
1. Zaak CR-2023-2210: Wasmachine defect na 5 maanden. MediaMarkt veroordeeld tot vervanging. Rechtbank Utrecht.
2. Zaak CR-2022-1105: Elektronisch apparaat, fabrikant aansprakelijk naast verkoper. Schikking €580.""",
        "key_facts_refined": """Verfijnde feiten:
✓ Bewezen: aankoop ~4 maanden, defect na 3 maanden
✓ Wettelijk: conformiteitseis geldt 2 jaar
⚠️ Voordeel: bewijsvermoeden in eerste 12 maanden (art. 7:18 BW lid 2)""",
        "next_best_action": """Aanbevolen acties:
1. ✅ Ingebrekestelling MediaMarkt — 80% kans, 2-4 weken
2. ⚖️ Geschillencommissie Thuiswinkel — 75% kans, 8 weken
3. 🏛️ Kantonrechter — 85% kans, 4 maanden""",
        "legal_analysis": """**Juridische Analyse — Non-conformiteit Consumentenkoop**

**Kwalificatie:** Non-conform product (art. 7:17 BW), verkoper aansprakelijk

**Beoordeling:** Een wasmachine die na 3 maanden defect raakt voldoet niet aan de conformiteitseis. Op grond van art. 7:18 lid 2 BW geldt een bewijsvermoeden: het defect wordt geacht bij levering aanwezig te zijn geweest. MediaMarkt (als verkoper) is primair aansprakelijk, ongeacht de fabrieksgarantie.

**Slagingskans: 88%** 🟢

**Risico's:** Minimaal. Wet staat duidelijk aan kant van consument.

**Aanbeveling:** Ingebrekestelling aan MediaMarkt met eis tot reparatie/vervanging binnen 14 dagen. Daarna Geschillencommissie of rechter.""",
        "similar_cases_h": "Brief-precedent: Ingebrekestelling CR-2023-2210 leidde tot vervanging binnen 10 dagen, zonder procedure.",
        "summary_h": "Kernboodschap: wasmachine defect na 3 maanden, non-conform, MediaMarkt aansprakelijk. Eis: vervanging of reparatie binnen 14 dagen.",
        "key_facts_h": "Kernfeiten brief: €649 wasmachine, defect na 3 maanden, wettelijke garantie 2 jaar, bewijsvermoeden van toepassing.",
        "legal_research_h": "Grondslag: art. 7:17 + 7:21 BW. Klant heeft recht op herstel of vervanging. Kosten voor rekening verkoper.",
        "letter": """**Brief 1 — Bevestiging aan de heer El-Masri**

Geachte heer El-Masri,

Wij bevestigen uw rechtshulpverzoek inzake de defecte wasmachine aangeschaft bij MediaMarkt.

Op basis van onze analyse staat de wet duidelijk aan uw kant. Een wasmachine die na 3 maanden stopt te werken is niet conform, en MediaMarkt is als verkoper verplicht dit kosteloos te herstellen of vervangen.

Uw jurist neemt binnen 1 werkdag contact op.

Met vriendelijke groet,
ARAG Rechtsbijstand

---

**Brief 2 — Ingebrekestelling aan MediaMarkt**

Geachte directie MediaMarkt,

Wij vertegenwoordigen de heer A. El-Masri inzake een bij u aangeschafte wasmachine (Bosch, €649, aankoopdatum [datum]).

Het product is na 3 maanden gebruik defect geraakt en voldoet derhalve niet aan de conformiteitseis van artikel 7:17 BW. Op grond van artikel 7:18 lid 2 BW wordt het defect vermoed reeds bij levering aanwezig te zijn geweest.

U bent als verkoper verplicht over te gaan tot gratis herstel of vervanging (art. 7:21 BW).

Wij sommeren u binnen 14 dagen:
1. De wasmachine kosteloos te repareren of vervangen
2. Een bevestiging van uw actie schriftelijk aan ons toe te sturen

Bij uitblijven starten wij een procedure bij de Geschillencommissie.

Met vriendelijke groet,
Mr. [Naam], ARAG Rechtsbijstand""",
        "similar_cases_ld": "Processtuk-precedent: Verzoekschrift Geschillencommissie CR-2023-2210, oordeel: vervanging verplicht.",
        "legal_analysis_ld": "Juridische verdieping: non-conformiteit + bewijsvermoeden 12 maanden combinatie maakt verweer verkoper vrijwel kansloos.",
        "legal_drafting": """**VERZOEKSCHRIFT GESCHILLENCOMMISSIE ELEKTRO**

Aan: Geschillencommissie Electro
Datum: [datum]
Betreft: Klacht non-conform product

**Verzoeker:** De heer A. El-Masri
**Verweerder:** MediaMarkt Nederland BV
**Aankoop:** Bosch wasmachine, €649, [datum]

**FEITEN**

1. Verzoeker heeft op [datum] een wasmachine (Bosch) gekocht bij verweerder voor €649.
2. Na 3 maanden gebruik is het apparaat defect geraakt.
3. Verweerder heeft geweigerd het product te repareren of vervangen.
4. Fabrikant heeft verwezen naar verweerder.

**JURIDISCHE GRONDSLAG**

Het product voldoet niet aan de conformiteitseis (art. 7:17 BW). Op grond van art. 7:18 lid 2 BW geldt het bewijsvermoeden dat het gebrek reeds bij aflevering aanwezig was (defect < 12 maanden na aankoop).

**VERZOEK**

De Geschillencommissie te verzoeken:
1. Vast te stellen dat de wasmachine non-conform is
2. Verweerder te verplichten tot gratis vervanging of restitutie €649
3. Verweerder te veroordelen in de behandelingskosten

Bijlagen: aankoopbon, foto's defect, correspondentie MediaMarkt/Bosch

[Handtekening Jurist ARAG]"""
    }
}


async def run_agent(agent_id: str, claim_data: dict, previous_results: dict, queue: asyncio.Queue) -> str:
    agent = AGENTS.get(agent_id, {})
    claim_type = claim_data.get("claim_type", "arbeidsrecht")
    phase = agent.get("phase", "intake")

    # Handle sub-agents first
    sub_agents = agent.get("sub_agents", [])
    sub_results = {}

    for sub_id in sub_agents:
        sub_agent = AGENTS.get(sub_id, {})
        await queue.put({
            "type": "sub_agent_start",
            "agent_id": sub_id,
            "parent_id": agent_id,
            "label": sub_agent.get("label", sub_id),
            "icon": sub_agent.get("icon", "🔧"),
            "phase": phase
        })

        # Get mock response for sub-agent
        mock_text = MOCK_RESPONSES.get(claim_type, {}).get(sub_id, f"Analyse voltooid voor {sub_agent.get('label', sub_id)}.")

        # Stream word by word
        words = mock_text.split(" ")
        for i, word in enumerate(words):
            chunk = word + (" " if i < len(words) - 1 else "")
            await queue.put({
                "type": "sub_agent_chunk",
                "agent_id": sub_id,
                "parent_id": agent_id,
                "chunk": chunk,
                "phase": phase
            })
            await asyncio.sleep(0.03)

        await queue.put({
            "type": "sub_agent_complete",
            "agent_id": sub_id,
            "parent_id": agent_id,
            "result": mock_text,
            "phase": phase
        })
        sub_results[sub_id] = mock_text

    # Now run the main agent
    await queue.put({
        "type": "agent_start",
        "agent_id": agent_id,
        "label": agent.get("label", agent_id),
        "icon": agent.get("icon", "🤖"),
        "phase": phase
    })

    # Get mock response
    mock_response = MOCK_RESPONSES.get(claim_type, {}).get(agent_id,
        f"Verwerking voltooid voor {agent.get('label', agent_id)}. Geen specifieke mock beschikbaar voor dit claim type.")

    # Add context from sub-agents if any
    if sub_results:
        context_note = f"\n\n[Gebaseerd op {len(sub_results)} sub-agent analyses]"
        mock_response = mock_response + context_note

    # Stream word by word
    words = mock_response.split(" ")
    for i, word in enumerate(words):
        chunk = word + (" " if i < len(words) - 1 else "")
        await queue.put({
            "type": "agent_chunk",
            "agent_id": agent_id,
            "chunk": chunk,
            "phase": phase
        })
        await asyncio.sleep(0.03)

    await queue.put({
        "type": "agent_complete",
        "agent_id": agent_id,
        "result": mock_response,
        "phase": phase
    })

    return mock_response
