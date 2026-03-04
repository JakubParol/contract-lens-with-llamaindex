"""Generate synthetic agreement PDFs for testing the RAG pipeline.

Produces 5 agreements (3 EN, 2 PL) with tables, annexes, and signature blocks.
Output: data/agreements/*.pdf
"""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path

from fpdf import FPDF

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "agreements"
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")


class AgreementPDF(FPDF):
    """Helper for generating contract-style PDFs."""

    def __init__(self, title: str, lang: str = "en"):
        super().__init__()
        self.doc_title = title
        self.lang = lang
        self.set_auto_page_break(auto=True, margin=25)
        # Register DejaVu Sans for Unicode (Polish characters) support
        self.add_font("DejaVu", "", str(FONT_DIR / "DejaVuSans.ttf"))
        self.add_font("DejaVu", "B", str(FONT_DIR / "DejaVuSans-Bold.ttf"))
        # Map italic to regular (oblique not available on all systems)
        self.add_font("DejaVu", "I", str(FONT_DIR / "DejaVuSans.ttf"))

    def header(self):
        self.set_font("DejaVu", "B", 10)
        self.cell(0, 6, self.doc_title, align="C")
        self.ln(8)
        self.set_draw_color(0, 0, 0)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-20)
        self.set_font("DejaVu", "I", 8)
        page_label = "Strona" if self.lang == "pl" else "Page"
        self.cell(0, 10, f"{page_label} {self.page_no()}/{{nb}}", align="C")

    def add_heading(self, text: str, level: int = 1):
        sizes = {1: 16, 2: 13, 3: 11}
        self.set_font("DejaVu", "B", sizes.get(level, 11))
        self.ln(4)
        self.multi_cell(0, 7, text)
        self.ln(2)

    def add_paragraph(self, text: str):
        self.set_font("DejaVu", "", 10)
        self.multi_cell(0, 5, text)
        self.ln(3)

    def add_clause(self, number: str, text: str):
        self.set_font("DejaVu", "B", 10)
        self.cell(12, 5, number)
        self.set_font("DejaVu", "", 10)
        self.multi_cell(0, 5, text)
        self.ln(2)

    def add_table(self, headers: list[str], rows: list[list[str]], col_widths: list[int] | None = None):
        if col_widths is None:
            col_widths = [190 // len(headers)] * len(headers)
        # Header row
        self.set_font("DejaVu", "B", 9)
        self.set_fill_color(220, 220, 220)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 7, h, border=1, fill=True, align="C")
        self.ln()
        # Data rows
        self.set_font("DejaVu", "", 9)
        for row in rows:
            for i, cell in enumerate(row):
                self.cell(col_widths[i], 6, cell, border=1)
            self.ln()
        self.ln(4)

    def add_signature_block(self):
        self.ln(15)
        self.set_font("DejaVu", "", 10)
        labels = ("Zleceniodawca / Client", "Wykonawca / Provider") if self.lang == "pl" else ("Client", "Provider")
        self.cell(95, 5, "________________________", align="C")
        self.cell(95, 5, "________________________", align="C")
        self.ln(5)
        self.set_font("DejaVu", "I", 9)
        self.cell(95, 5, labels[0], align="C")
        self.cell(95, 5, labels[1], align="C")
        self.ln(5)
        date_label = "Data" if self.lang == "pl" else "Date"
        self.cell(95, 5, f"{date_label}: _______________", align="C")
        self.cell(95, 5, f"{date_label}: _______________", align="C")
        self.ln()


def gen_it_service_agreement() -> Path:
    """IT Service Agreement (EN) with pricing table annex."""
    pdf = AgreementPDF("IT SERVICE AGREEMENT", lang="en")
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.add_heading("IT SERVICE AGREEMENT", 1)
    pdf.add_paragraph(
        f"This IT Service Agreement (the 'Agreement') is entered into as of {date(2025, 1, 15).isoformat()} "
        "between TechFlow Solutions Ltd., a company registered in London, United Kingdom "
        "('Provider'), and GlobalRetail Corp., a company registered in New York, USA ('Client')."
    )

    pdf.add_heading("1. Scope of Services", 2)
    pdf.add_clause("1.1", "The Provider shall deliver IT consulting services including system architecture review, "
                   "cloud migration planning, and implementation support for the Client's e-commerce platform.")
    pdf.add_clause("1.2", "Services shall be performed remotely unless on-site presence is specifically requested "
                   "and agreed upon in writing.")
    pdf.add_clause("1.3", "The Provider shall assign a dedicated team of no fewer than 3 senior consultants "
                   "to the engagement.")

    pdf.add_heading("2. Term and Termination", 2)
    pdf.add_clause("2.1", "This Agreement shall commence on January 15, 2025 and continue for a period of "
                   "12 months unless terminated earlier in accordance with this section.")
    pdf.add_clause("2.2", "Either party may terminate this Agreement with 30 days written notice.")
    pdf.add_clause("2.3", "In the event of material breach, the non-breaching party may terminate immediately "
                   "upon written notice.")

    pdf.add_heading("3. Payment Terms", 2)
    pdf.add_clause("3.1", "The Client shall pay the Provider in accordance with the pricing schedule set forth "
                   "in Annex A attached hereto.")
    pdf.add_clause("3.2", "Invoices shall be issued monthly and payment is due within 30 days of receipt.")
    pdf.add_clause("3.3", "Late payments shall accrue interest at a rate of 1.5% per month.")

    pdf.add_heading("4. Confidentiality", 2)
    pdf.add_clause("4.1", "Both parties agree to maintain the confidentiality of all proprietary information "
                   "disclosed during the term of this Agreement.")
    pdf.add_clause("4.2", "This obligation shall survive termination of the Agreement for a period of 3 years.")

    pdf.add_heading("5. Liability", 2)
    pdf.add_clause("5.1", "The Provider's total liability under this Agreement shall not exceed the total fees "
                   "paid by the Client in the 12 months preceding the claim.")
    pdf.add_clause("5.2", "Neither party shall be liable for indirect, consequential, or incidental damages.")

    pdf.add_signature_block()

    # Annex A - Pricing Table
    pdf.add_page()
    pdf.add_heading("ANNEX A - Pricing Schedule", 1)
    pdf.add_paragraph("The following rates apply to services rendered under this Agreement:")
    pdf.add_table(
        headers=["Service Category", "Rate (USD/hour)", "Min Hours/Month", "Monthly Cap"],
        rows=[
            ["Senior Architect", "$250", "40", "$12,000"],
            ["Cloud Engineer", "$200", "80", "$18,000"],
            ["DevOps Specialist", "$180", "60", "$12,500"],
            ["Project Manager", "$150", "20", "$4,000"],
            ["QA Engineer", "$140", "40", "$7,000"],
        ],
        col_widths=[55, 45, 45, 45],
    )
    pdf.add_paragraph("Additional services not listed above shall be quoted separately and require written approval.")
    pdf.add_paragraph("Travel expenses, if applicable, shall be reimbursed at cost with prior approval.")

    path = OUTPUT_DIR / "01_it_service_agreement_en.pdf"
    pdf.output(str(path))
    return path


def gen_nda() -> Path:
    """Mutual NDA (EN)."""
    pdf = AgreementPDF("MUTUAL NON-DISCLOSURE AGREEMENT", lang="en")
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.add_heading("MUTUAL NON-DISCLOSURE AGREEMENT", 1)
    pdf.add_paragraph(
        f"This Mutual Non-Disclosure Agreement ('NDA') is entered into as of {date(2025, 3, 1).isoformat()} "
        "between DataVault Analytics Inc., registered in San Francisco, CA ('Party A'), "
        "and Quantum Insights GmbH, registered in Berlin, Germany ('Party B')."
    )

    pdf.add_heading("1. Purpose", 2)
    pdf.add_clause("1.1", "The parties wish to explore a potential business relationship concerning "
                   "joint development of AI-powered analytics solutions ('Purpose').")
    pdf.add_clause("1.2", "In connection with the Purpose, each party may disclose certain confidential "
                   "and proprietary information to the other party.")

    pdf.add_heading("2. Definition of Confidential Information", 2)
    pdf.add_clause("2.1", "'Confidential Information' means any non-public information disclosed by either party, "
                   "including but not limited to: technical data, trade secrets, business plans, customer lists, "
                   "financial information, source code, algorithms, and product roadmaps.")
    pdf.add_clause("2.2", "Confidential Information does not include information that: (a) is publicly available; "
                   "(b) was known prior to disclosure; (c) is independently developed; or "
                   "(d) is disclosed with written consent.")

    pdf.add_heading("3. Obligations", 2)
    pdf.add_clause("3.1", "Each receiving party shall: (a) hold Confidential Information in strict confidence; "
                   "(b) not disclose it to third parties without prior written consent; "
                   "(c) use it solely for the Purpose.")
    pdf.add_clause("3.2", "Each party shall limit access to Confidential Information to employees and contractors "
                   "who have a need to know and are bound by confidentiality obligations.")

    pdf.add_heading("4. Term", 2)
    pdf.add_clause("4.1", "This NDA shall remain in effect for 2 years from the date of execution.")
    pdf.add_clause("4.2", "Confidentiality obligations shall survive termination for an additional 3 years.")

    pdf.add_heading("5. Return of Materials", 2)
    pdf.add_clause("5.1", "Upon termination or request, each party shall promptly return or destroy all materials "
                   "containing Confidential Information and certify such destruction in writing.")

    pdf.add_heading("6. Governing Law", 2)
    pdf.add_clause("6.1", "This NDA shall be governed by the laws of the State of Delaware, USA.")

    pdf.add_signature_block()

    path = OUTPUT_DIR / "02_mutual_nda_en.pdf"
    pdf.output(str(path))
    return path


def gen_lease_agreement_pl() -> Path:
    """Office Lease Agreement (PL) with asset inventory annex."""
    pdf = AgreementPDF("UMOWA NAJMU LOKALU BIUROWEGO", lang="pl")
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.add_heading("UMOWA NAJMU LOKALU BIUROWEGO", 1)
    pdf.add_paragraph(
        f"Umowa zawarta w dniu {date(2025, 2, 10).isoformat()} w Warszawie pomiedzy: "
        "Nieruchomosci Centrum Sp. z o.o. z siedziba w Warszawie, ul. Marszalkowska 100, "
        "NIP: 5271234567 ('Wynajmujacy'), a InnoTech Solutions Sp. z o.o. z siedziba w Warszawie, "
        "ul. Zlota 59, NIP: 5279876543 ('Najemca')."
    )

    pdf.add_heading("1. Przedmiot najmu", 2)
    pdf.add_clause("1.1", "Wynajmujacy oddaje Najemcy do uzywania lokal biurowy o powierzchni 250 m2, "
                   "znajdujacy sie na 5. pietrze budynku przy ul. Marszalkowskiej 100 w Warszawie.")
    pdf.add_clause("1.2", "Lokal wyposazony jest w elementy wymienione w Zalaczniku nr 1.")

    pdf.add_heading("2. Czas trwania umowy", 2)
    pdf.add_clause("2.1", "Umowa zostaje zawarta na czas okreslony 36 miesiecy, poczawszy od dnia 1 marca 2025 r.")
    pdf.add_clause("2.2", "Po uplywie okresu najmu umowa moze zostac przedluzona na podstawie pisemnego aneksu.")

    pdf.add_heading("3. Czynsz i oplaty", 2)
    pdf.add_clause("3.1", "Miesięczny czynsz najmu wynosi 25 000 PLN netto (plus VAT 23%).")
    pdf.add_clause("3.2", "Czynsz platny jest z gory do 10. dnia kazdego miesiaca na rachunek bankowy Wynajmujacego.")
    pdf.add_clause("3.3", "Najemca ponosi dodatkowo koszty mediow (energia, woda, ogrzewanie) wedlug zuzycia.")

    pdf.add_heading("4. Kaucja", 2)
    pdf.add_clause("4.1", "Najemca wplaci kaucje w wysokosci 75 000 PLN (rownowartość 3 miesiecy czynszu) "
                   "w terminie 7 dni od podpisania umowy.")
    pdf.add_clause("4.2", "Kaucja zostanie zwrocona w ciagu 30 dni od zakonczenia najmu, po potraceniu ewentualnych naleznosci.")

    pdf.add_heading("5. Obowiazki stron", 2)
    pdf.add_clause("5.1", "Wynajmujacy zobowiazuje sie do utrzymania budynku w nalezytym stanie technicznym.")
    pdf.add_clause("5.2", "Najemca zobowiazuje sie do uzywania lokalu zgodnie z przeznaczeniem i utrzymania go w dobrym stanie.")
    pdf.add_clause("5.3", "Wszelkie przerobki i adaptacje wymagaja pisemnej zgody Wynajmujacego.")

    pdf.add_heading("6. Wypowiedzenie", 2)
    pdf.add_clause("6.1", "Kazda ze stron moze wypowiedziec umowe z zachowaniem 3-miesiecznego okresu wypowiedzenia.")
    pdf.add_clause("6.2", "Wynajmujacy moze wypowiedziec umowe ze skutkiem natychmiastowym w przypadku zaleglosci "
                   "w oplatach przekraczajacych 2 miesiace.")

    pdf.add_signature_block()

    # Zalacznik 1 - asset inventory
    pdf.add_page()
    pdf.add_heading("ZALACZNIK NR 1 - Wykaz wyposazenia lokalu", 1)
    pdf.add_paragraph("Ponizszy wykaz stanowi liste wyposazenia przekazanego Najemcy wraz z lokalem:")
    pdf.add_table(
        headers=["Lp.", "Element wyposazenia", "Ilosc", "Stan"],
        rows=[
            ["1", "Biurko robocze 160x80cm", "20", "Dobry"],
            ["2", "Krzeslo biurowe ergonomiczne", "20", "Dobry"],
            ["3", "Szafa aktowa zamykana", "8", "Dobry"],
            ["4", "Stol konferencyjny 12-osobowy", "1", "Bardzo dobry"],
            ["5", "Krzeslo konferencyjne", "12", "Dobry"],
            ["6", "Projektor multimedialny Epson EB-2250U", "1", "Dobry"],
            ["7", "Tablica magnetyczna 200x100cm", "2", "Dobry"],
            ["8", "Klimatyzator scienny", "4", "Bardzo dobry"],
            ["9", "Drukarka sieciowa HP LaserJet Pro", "2", "Dobry"],
            ["10", "Ekspres do kawy DeLonghi Magnifica", "1", "Dobry"],
        ],
        col_widths=[15, 95, 25, 55],
    )
    pdf.add_paragraph("Stan wyposazenia potwierdzony przez obie strony w dniu przekazania lokalu.")

    path = OUTPUT_DIR / "03_lease_agreement_pl.pdf"
    pdf.output(str(path))
    return path


def gen_sla_agreement() -> Path:
    """Cloud SLA Agreement (EN) with metrics table annex."""
    pdf = AgreementPDF("SERVICE LEVEL AGREEMENT", lang="en")
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.add_heading("SERVICE LEVEL AGREEMENT", 1)
    pdf.add_paragraph(
        f"This Service Level Agreement ('SLA') is entered into as of {date(2025, 4, 1).isoformat()} "
        "between CloudNine Infrastructure Ltd., registered in Dublin, Ireland ('Provider'), "
        "and MegaBank Financial Services Plc., registered in London, UK ('Client')."
    )

    pdf.add_heading("1. Service Description", 2)
    pdf.add_clause("1.1", "The Provider shall deliver managed cloud infrastructure services including "
                   "compute, storage, networking, and database services on the Provider's platform.")
    pdf.add_clause("1.2", "Services are provided on a 24/7/365 basis with support available through "
                   "the Provider's support portal, email, and phone.")

    pdf.add_heading("2. Service Levels", 2)
    pdf.add_clause("2.1", "The Provider commits to the service levels defined in Annex A.")
    pdf.add_clause("2.2", "Service levels are measured on a calendar month basis.")
    pdf.add_clause("2.3", "Scheduled maintenance windows (communicated 5 business days in advance) "
                   "are excluded from availability calculations.")

    pdf.add_heading("3. Service Credits", 2)
    pdf.add_clause("3.1", "If the Provider fails to meet the guaranteed service levels, "
                   "the Client shall be entitled to service credits as specified in Annex A.")
    pdf.add_clause("3.2", "Service credits shall be applied to the next monthly invoice.")
    pdf.add_clause("3.3", "Total service credits in any calendar month shall not exceed 30% of that month's fees.")

    pdf.add_heading("4. Incident Management", 2)
    pdf.add_clause("4.1", "Incidents shall be classified as P1 (Critical), P2 (High), P3 (Medium), P4 (Low).")
    pdf.add_clause("4.2", "Response and resolution targets per priority are defined in Annex A.")

    pdf.add_heading("5. Reporting", 2)
    pdf.add_clause("5.1", "The Provider shall deliver monthly service reports including uptime statistics, "
                   "incident summaries, and SLA compliance metrics.")

    pdf.add_signature_block()

    # Annex A - SLA Metrics
    pdf.add_page()
    pdf.add_heading("ANNEX A - Service Level Metrics", 1)

    pdf.add_heading("Availability Targets", 3)
    pdf.add_table(
        headers=["Service Tier", "Monthly Uptime SLA", "Credit (< SLA)", "Credit (< 99%)"],
        rows=[
            ["Platinum", "99.99%", "10% monthly fee", "25% monthly fee"],
            ["Gold", "99.95%", "10% monthly fee", "20% monthly fee"],
            ["Silver", "99.9%", "5% monthly fee", "15% monthly fee"],
        ],
        col_widths=[40, 45, 50, 55],
    )

    pdf.add_heading("Incident Response Targets", 3)
    pdf.add_table(
        headers=["Priority", "Description", "Response Time", "Resolution Target"],
        rows=[
            ["P1 - Critical", "Service down, all users affected", "15 minutes", "4 hours"],
            ["P2 - High", "Major feature degraded", "30 minutes", "8 hours"],
            ["P3 - Medium", "Minor feature issue", "2 hours", "24 hours"],
            ["P4 - Low", "Cosmetic or informational", "8 hours", "5 business days"],
        ],
        col_widths=[35, 65, 40, 50],
    )

    pdf.add_heading("Penalty Matrix", 3)
    pdf.add_table(
        headers=["SLA Breach Count (Quarter)", "Action"],
        rows=[
            ["1-2 breaches", "Service credits applied automatically"],
            ["3-4 breaches", "Escalation to VP level, remediation plan required within 5 days"],
            ["5+ breaches", "Client may terminate with 30 days notice without penalty"],
        ],
        col_widths=[60, 130],
    )

    path = OUTPUT_DIR / "04_cloud_sla_en.pdf"
    pdf.output(str(path))
    return path


def gen_employment_contract_pl() -> Path:
    """Employment Contract (PL) with compensation table."""
    pdf = AgreementPDF("UMOWA O PRACE", lang="pl")
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.add_heading("UMOWA O PRACE", 1)
    pdf.add_paragraph(
        f"Umowa zawarta w dniu {date(2025, 5, 1).isoformat()} w Krakowie pomiedzy: "
        "AI Systems Poland Sp. z o.o. z siedziba w Krakowie, ul. Mogilska 43, "
        "NIP: 6793456789, reprezentowana przez Jana Kowalskiego - Prezesa Zarzadu ('Pracodawca'), "
        "a Anną Nowak, zamieszkala w Krakowie, PESEL: 90010112345 ('Pracownik')."
    )

    pdf.add_heading("1. Warunki zatrudnienia", 2)
    pdf.add_clause("1.1", "Pracodawca zatrudnia Pracownika na stanowisku: Senior Data Scientist.")
    pdf.add_clause("1.2", "Wymiar czasu pracy: pelny etat (40 godzin tygodniowo).")
    pdf.add_clause("1.3", "Miejsce wykonywania pracy: siedziba Pracodawcy oraz praca zdalna (model hybrydowy, "
                   "minimum 2 dni w tygodniu w biurze).")
    pdf.add_clause("1.4", "Umowa zawarta na czas nieokreslony z 3-miesiecznym okresem wypowiedzenia.")

    pdf.add_heading("2. Wynagrodzenie", 2)
    pdf.add_clause("2.1", "Wynagrodzenie zasadnicze oraz dodatkowe skladniki okreslone sa w Zalaczniku nr 1.")
    pdf.add_clause("2.2", "Wynagrodzenie wyplacane jest do ostatniego dnia roboczego kazdego miesiaca "
                   "na wskazany rachunek bankowy Pracownika.")

    pdf.add_heading("3. Obowiazki Pracownika", 2)
    pdf.add_clause("3.1", "Pracownik zobowiazuje sie do sumiennego i starannego wykonywania powierzonych obowiazkow.")
    pdf.add_clause("3.2", "Do obowiazkow nalezy w szczegolnosci: projektowanie i implementacja modeli ML/AI, "
                   "analiza danych, przygotowywanie raportow, mentoring juniorskich czlonkow zespolu.")

    pdf.add_heading("4. Zakaz konkurencji", 2)
    pdf.add_clause("4.1", "W czasie trwania umowy Pracownik zobowiazuje sie do niepodejmowania dzialalnosci "
                   "konkurencyjnej wobec Pracodawcy.")
    pdf.add_clause("4.2", "Zakaz konkurencji obowiazuje rowniez przez 12 miesiecy po ustaniu stosunku pracy, "
                   "za co Pracownikowi przysluguje odszkodowanie w wysokosci 25% wynagrodzenia zasadniczego.")

    pdf.add_heading("5. Urlop", 2)
    pdf.add_clause("5.1", "Pracownikowi przysluguje 26 dni urlopu wypoczynkowego rocznie.")
    pdf.add_clause("5.2", "Dodatkowo Pracodawca przyznaje 3 dni urlopu na cele rozwoju zawodowego (konferencje, szkolenia).")

    pdf.add_signature_block()

    # Zalacznik - compensation
    pdf.add_page()
    pdf.add_heading("ZALACZNIK NR 1 - Wynagrodzenie i swiadczenia", 1)
    pdf.add_table(
        headers=["Skladnik", "Kwota/Opis", "Czestotliwosc"],
        rows=[
            ["Wynagrodzenie zasadnicze", "22 000 PLN brutto", "Miesieczne"],
            ["Premia uznaniowa", "Do 20% wynagrodzenia zasadniczego", "Kwartalne"],
            ["Premia roczna", "Do 2 wynagrodzen zasadniczych", "Roczne"],
            ["Pakiet medyczny (LuxMed)", "Wariant rodzinny", "Miesieczne"],
            ["Karta sportowa (MultiSport)", "Wariant Plus", "Miesieczne"],
            ["Budzet szkoleniowy", "10 000 PLN rocznie", "Roczne"],
            ["Sprzet sluzbowy", "MacBook Pro 16\" + monitor 4K", "Jednorazowo"],
            ["Dodatek za prace zdalna", "500 PLN", "Miesieczne"],
        ],
        col_widths=[65, 80, 45],
    )
    pdf.add_paragraph(
        "Kwoty wynagrodzen podlegaja corocznej waloryzacji na podstawie oceny okresowej Pracownika "
        "oraz sytuacji finansowej Pracodawcy."
    )

    path = OUTPUT_DIR / "05_employment_contract_pl.pdf"
    pdf.output(str(path))
    return path


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    generators = [
        ("IT Service Agreement (EN)", gen_it_service_agreement),
        ("Mutual NDA (EN)", gen_nda),
        ("Lease Agreement (PL)", gen_lease_agreement_pl),
        ("Cloud SLA (EN)", gen_sla_agreement),
        ("Employment Contract (PL)", gen_employment_contract_pl),
    ]

    for name, gen_fn in generators:
        path = gen_fn()
        print(f"  Generated: {path.name} ({name})")

    print(f"\nAll {len(generators)} agreements generated in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
