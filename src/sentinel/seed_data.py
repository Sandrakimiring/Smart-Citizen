"""
Seed data generator for Nyayo Sentinel.

Generates realistic Kenyan citizen questions with pre-defined
topics, tension levels, and counties. Used to populate the dashboard
for demo/testing without needing the live Haki engine.

Usage: python -m src.sentinel.seed_data
"""

import random

from .database import init_db, insert_signal
from .models import Signal, KENYA_COUNTIES

# ── Realistic question templates by topic ─────────────────────────────
QUESTIONS = {
    "tax": [
        ("Is the housing levy mandatory?", 0.65, "Nairobi"),
        ("What tax changes are in the finance bill?", 0.50, None),
        ("Why was VAT increased on fuel?", 0.72, "Mombasa"),
        ("How much PAYE should I pay on 80,000 KES salary?", 0.35, None),
        ("Is the digital services tax legal?", 0.60, "Nairobi"),
        ("Will the new tax affect small businesses in Kisumu?", 0.68, "Kisumu"),
        ("This housing levy is theft!", 0.88, "Nairobi"),
        ("How do I file my KRA returns?", 0.25, None),
        ("Are pensions taxable under the new bill?", 0.55, None),
        ("Why are we being double-taxed on M-Pesa transactions?", 0.82, "Nairobi"),
        ("What is the turnover tax rate for small traders?", 0.30, "Nakuru"),
        ("The Finance Bill will destroy our businesses!", 0.90, "Kisumu"),
        ("How is the affordable housing levy calculated?", 0.45, "Kiambu"),
        ("Is there tax relief for people with disabilities?", 0.40, None),
        ("Why are matatu operators being taxed more?", 0.70, "Nairobi"),
        ("What happened to the tax amnesty program?", 0.50, None),
        ("Are boda boda riders supposed to pay taxes?", 0.55, "Bungoma"),
        ("The government keeps adding new taxes every year!", 0.85, None),
        ("What does the excise duty on betting mean?", 0.45, "Nairobi"),
        ("How do I apply for a tax compliance certificate?", 0.20, None),
    ],
    "land": [
        ("Why are land rates increasing in Eldoret?", 0.75, "Uasin Gishu"),
        ("How do I get a title deed in Kajiado?", 0.40, "Kajiado"),
        ("What is the process for land succession?", 0.35, None),
        ("Can the government take my ancestral land?", 0.80, "Kilifi"),
        ("How do I verify a title deed is genuine?", 0.45, "Nairobi"),
        ("Land grabbers are taking community land in Lamu!", 0.90, "Lamu"),
        ("What are the new rules on foreign land ownership?", 0.50, None),
        ("Why is the land commission not resolving disputes?", 0.72, "Kwale"),
        ("How much does land transfer cost in Kiambu?", 0.30, "Kiambu"),
        ("Our community land was taken without compensation!", 0.92, "Tana River"),
        ("What is the minimum plot size allowed under subdivision?", 0.35, "Nakuru"),
        ("How long does a land search take at the registry?", 0.40, "Nairobi"),
        ("The county is charging illegal land rates!", 0.78, "Mombasa"),
        ("Can I build on agricultural land?", 0.30, "Murang'a"),
        ("What rights do squatters have?", 0.65, "Mombasa"),
        ("How do I convert leasehold to freehold?", 0.40, None),
        ("Is the National Land Commission doing anything about IDPs?", 0.70, "Uasin Gishu"),
        ("Why are surveyors so expensive?", 0.50, "Machakos"),
    ],
    "employment": [
        ("What is the current minimum wage?", 0.30, None),
        ("Can my employer fire me without notice?", 0.65, "Nairobi"),
        ("How do I report labour violations?", 0.60, None),
        ("Are interns entitled to payment under the law?", 0.50, "Nairobi"),
        ("Youth unemployment is getting worse every year!", 0.85, "Nairobi"),
        ("What are my rights as a domestic worker?", 0.55, "Nairobi"),
        ("How do I register for NHIF as self-employed?", 0.35, None),
        ("My employer hasn't paid NSSF for 6 months!", 0.80, "Mombasa"),
        ("What does the Employment Act say about maternity leave?", 0.40, None),
        ("Are there any government programs for youth employment?", 0.45, "Kisumu"),
        ("Can a company make you work on public holidays without pay?", 0.70, None),
        ("How do I apply for the Kazi Mtaani program?", 0.30, "Nairobi"),
    ],
    "education": [
        ("Is CBC being abolished?", 0.55, None),
        ("What are the university admission requirements?", 0.25, None),
        ("Why are school fees increasing in private schools?", 0.65, "Nairobi"),
        ("How does the new education funding model work?", 0.50, None),
        ("Teachers are not being paid on time!", 0.78, "Turkana"),
        ("What happened to the laptop project for schools?", 0.60, None),
        ("Can a school deny admission because of fees?", 0.55, "Kiambu"),
        ("How do I apply for HELB loan?", 0.30, None),
        ("The CBC curriculum is confusing parents!", 0.72, "Nakuru"),
        ("Are there scholarships for students from Marsabit?", 0.40, "Marsabit"),
    ],
    "security": [
        ("What does the anti-terrorism act say?", 0.40, None),
        ("How do I report cybercrime?", 0.35, None),
        ("Is the police allowed to search my phone?", 0.60, "Nairobi"),
        ("Why are there so many extrajudicial killings?", 0.85, "Nairobi"),
        ("What are my rights when arrested?", 0.55, None),
        ("The security situation in Baringo is terrible!", 0.88, "Baringo"),
        ("How does the computer misuse act affect bloggers?", 0.50, None),
        ("Can CCTV footage be used as evidence in court?", 0.35, None),
        ("What is the National Security Council's role?", 0.30, None),
        ("Police brutality during protests must stop!", 0.92, "Nairobi"),
    ],
    "health": [
        ("What happened to NHIF? Is SHA better?", 0.55, None),
        ("Why are hospital bills so expensive?", 0.70, "Nairobi"),
        ("How do I register for SHA?", 0.35, None),
        ("Are county hospitals supposed to be free?", 0.50, "Kisumu"),
        ("There are no drugs in Garissa hospital!", 0.85, "Garissa"),
        ("What does the mental health bill cover?", 0.40, None),
        ("How do I access reproductive health services?", 0.45, None),
        ("The health system in Turkana is collapsing!", 0.88, "Turkana"),
        ("Can a hospital refuse emergency treatment?", 0.65, None),
        ("What is the government doing about cancer treatment costs?", 0.60, "Nairobi"),
        ("Why did they remove dental from SHA coverage?", 0.70, None),
        ("How do I access mental health support in Nyeri?", 0.50, "Nyeri"),
    ],
    "governance": [
        ("What are the qualifications to be president?", 0.20, None),
        ("How does impeachment of a governor work?", 0.45, None),
        ("Why is the Senate not passing the revenue bill?", 0.60, "Nairobi"),
        ("What powers does the county assembly have?", 0.30, None),
        ("Corruption in government is out of control!", 0.88, None),
        ("How do I access the county budget?", 0.35, "Meru"),
        ("What is the role of the ombudsman?", 0.25, None),
        ("Our ward representative has disappeared!", 0.72, "Homa Bay"),
        ("How do citizens participate in budget making?", 0.30, None),
        ("Why are MCAs increasing their salaries?", 0.80, "Nairobi"),
    ],
    "rights": [
        ("What are my constitutional rights?", 0.30, None),
        ("Can the government spy on my communications?", 0.65, "Nairobi"),
        ("Is peaceful protest legal in Kenya?", 0.55, None),
        ("What does the Data Protection Act cover?", 0.35, None),
        ("Police are violating our right to protest!", 0.85, "Nairobi"),
        ("How do I access information from government?", 0.40, None),
        ("Can a landlord evict me without a court order?", 0.70, "Nairobi"),
        ("What rights do refugees have in Kenya?", 0.45, "Garissa"),
        ("Freedom of expression is being suppressed!", 0.82, None),
        ("How do I report human rights violations?", 0.50, None),
    ],
    "environment": [
        ("Is the Nairobi expressway affecting air quality?", 0.50, "Nairobi"),
        ("What are the penalties for illegal logging?", 0.40, None),
        ("Why is Lake Nakuru drying up?", 0.65, "Nakuru"),
        ("How do I report illegal dumping in Kisumu?", 0.55, "Kisumu"),
        ("The Mau Forest is being destroyed!", 0.80, "Narok"),
        ("What does NEMA do about factory pollution?", 0.50, "Nairobi"),
        ("Are there policies for climate change adaptation?", 0.35, None),
        ("Flooding in Budalangi happens every year!", 0.85, "Busia"),
        ("What are the rules for sand harvesting?", 0.45, "Machakos"),
        ("Why is Nairobi river still polluted?", 0.70, "Nairobi"),
    ],
    "infrastructure": [
        ("When will the Nairobi-Mombasa highway be finished?", 0.45, None),
        ("Why are the roads in Isiolo so bad?", 0.72, "Isiolo"),
        ("How much did the SGR cost?", 0.55, None),
        ("Why is there no clean water in Turkana?", 0.85, "Turkana"),
        ("The bridge in Siaya collapsed and nobody fixed it!", 0.82, "Siaya"),
        ("When will rural areas get electricity?", 0.60, "West Pokot"),
        ("How do I apply for water connection from NAIROBI Water?", 0.35, "Nairobi"),
        ("Why is KenGen not expanding electricity to the north?", 0.65, "Samburu"),
        ("The dam project in Makueni stalled!", 0.75, "Makueni"),
        ("What is the status of the Lamu port project?", 0.50, "Lamu"),
    ],
}

# Some questions that Haki can't answer (for knowledge gaps)
UNANSWERABLE = [
    ("When will the president visit Mandera?", "governance", 0.55, "Mandera"),
    ("How much money did the county governor steal?", "governance", 0.90, "Nairobi"),
    ("What will happen to fuel prices next month?", "tax", 0.65, None),
    ("Why did my HELB application get rejected?", "education", 0.70, None),
    ("Where can I find a job in Eldoret?", "employment", 0.50, "Uasin Gishu"),
    ("Who will win the next election?", "governance", 0.40, None),
    ("Why is my village chief so corrupt?", "governance", 0.82, "Vihiga"),
    ("Can you help me write a letter to my MP?", "governance", 0.30, None),
    ("What is the price of maize today?", "infrastructure", 0.45, "Trans-Nzoia"),
    ("How do I get a passport quickly?", "governance", 0.50, "Nairobi"),
    ("Will there be a drought this year?", "environment", 0.60, "Wajir"),
    ("My neighbor stole my cow, what do I do?", "rights", 0.65, "Baringo"),
]


def seed(count: int = 200):
    """Generate and insert seed signals."""
    init_db()

    inserted = 0
    all_questions = []

    for topic, questions in QUESTIONS.items():
        for q_text, tension, county in questions:
            all_questions.append(Signal(
                question=q_text,
                answer=f"[Simulated answer for: {q_text[:50]}...]",
                topic=topic,
                tension_score=tension,
                county=county,
                supported=True,
                language="en",
            ))

    for q_text, topic, tension, county in UNANSWERABLE:
        all_questions.append(Signal(
            question=q_text,
            answer=None,
            topic=topic,
            tension_score=tension,
            county=county,
            supported=False,
            language="en",
        ))

    random.shuffle(all_questions)
    for signal in all_questions[:count]:
        insert_signal(signal)
        inserted += 1

    print(f"[OK] Inserted {inserted} seed signals into Sentinel database")
    return inserted


if __name__ == "__main__":
    seed()
