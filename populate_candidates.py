"""
Populate all 267 candidates with realistic biographical data.
Run from inside the Online-Voting-main directory:
    python populate_candidates.py
"""

import sqlite3, random, textwrap

DB = "db.sqlite3"

# ── Party profiles ────────────────────────────────────────────────────────────
PARTY_DATA = {
    "BNP": {
        "slogans": [
            "Democracy First, Bangladesh Always",
            "Restore the People's Voice",
            "Unity, Progress, Freedom",
            "Building a Democratic Bangladesh",
            "Justice for Every Citizen",
            "Strong Nation, Strong People",
            "The People's Choice for Change",
            "Freedom Through Democracy",
        ],
        "manifesto_lines": [
            "Restore full democratic rights and free press",
            "Ensure judicial independence and rule of law",
            "Combat corruption at every level of government",
            "Boost private sector investment and job creation",
            "Modernise infrastructure across rural Bangladesh",
            "Guarantee free and fair elections under a neutral caretaker",
            "Strengthen local government and decentralise power",
            "Expand social safety nets for vulnerable communities",
            "Increase education budget to 20% of national expenditure",
            "Develop export-oriented industries beyond garments",
        ],
        "occupations": [
            "Advocate, Supreme Court of Bangladesh",
            "Businessman and Community Leader",
            "Former Civil Servant",
            "Agricultural Entrepreneur",
            "Retired Army Officer",
            "Industrialist",
            "Former District Commissioner",
            "Chartered Accountant",
        ],
        "bio_templates": [
            "{name} has served the {region} constituency for over {years} years, championing democratic values and grassroots development. A prominent figure in the Bangladesh Nationalist Party, {pronoun} has led campaigns for government accountability and infrastructure development. {name} has dedicated {pronoun_pos} career to public service, fighting against authoritarian governance and standing firmly for the rights of ordinary citizens.",
            "Born and raised in {region}, {name} rose through the ranks of BNP's local chapter to become one of the most respected voices in the constituency. With a background in {occ_short}, {pronoun} has championed economic development, rural electrification, and farmers' rights. {name}'s {years}-year political career is defined by {pronoun_pos} unwavering commitment to democratic governance.",
            "{name} is a seasoned politician and community advocate from {region}. As a BNP stalwart, {pronoun} has consistently fought against political repression and for the restoration of democratic norms. {name} brings both professional expertise and deep local roots to the National Assembly. {pronoun_cap} campaign focuses on economic recovery, job creation, and transparent governance.",
        ],
    },
    "NCP": {
        "slogans": [
            "New Vision, New Bangladesh",
            "People Power, People Progress",
            "Youth, Change, Future",
            "Clean Politics for a Bright Future",
            "Reform Bangladesh from the Ground Up",
            "Progress Through Participation",
            "A Nation Built on Justice",
            "Change That Communities Can Trust",
        ],
        "manifesto_lines": [
            "Reform the electoral system for genuine representation",
            "Invest in renewable energy and green infrastructure",
            "Create one million youth employment opportunities in five years",
            "Digitalise all government services to reduce corruption",
            "Provide universal healthcare coverage for every citizen",
            "Reform land ownership and protect farmers' rights",
            "Strengthen women's political and economic participation",
            "Build world-class technical education institutions",
            "Decentralise development funding to district level",
            "Negotiate equitable trade and water-sharing agreements",
        ],
        "occupations": [
            "University Professor",
            "Physician and Public Health Advocate",
            "NGO Director and Social Activist",
            "Software Engineer and Tech Entrepreneur",
            "Journalist and Media Professional",
            "Development Economist",
            "Environmental Activist",
            "Microfinance and Rural Development Expert",
        ],
        "bio_templates": [
            "{name} is a reform-minded leader from {region} who joined the National Citizens' Party to bring fresh ideas and progressive governance to Bangladesh. With a background in {occ_short}, {pronoun} has spent {years} years advocating for digital inclusion, healthcare access, and youth empowerment. {name}'s campaign is built on transparency, civic engagement, and evidence-based policymaking.",
            "A native of {region}, {name} founded local community organisations before entering electoral politics with NCP. {pronoun_cap} brings an analytical, reform-driven approach to constituency representation. {name} is particularly passionate about women's rights, rural health infrastructure, and creating sustainable economic opportunities for the youth of Bangladesh.",
            "{name} represents the new generation of Bangladeshi leadership. After spending {years} years in {occ_short}, {pronoun} channelled {pronoun_pos} expertise into public service through the National Citizens' Party. {name} believes that accountable institutions and citizen-centred governance are the only path to lasting development in {region} and across Bangladesh.",
        ],
    },
    "Daripalla": {
        "slogans": [
            "Harmony, Heritage, Hope",
            "United Communities, Shared Future",
            "Culture, Dignity, Progress",
            "Voice of the Marginalised",
            "Inclusive Growth for Every Community",
            "Protecting Our Roots, Building Our Future",
            "Every Voice Counts",
            "Bridge the Divide, Build the Nation",
        ],
        "manifesto_lines": [
            "Protect the rights and cultural identity of all ethnic minorities",
            "Ensure equal access to education and health in remote areas",
            "Create community-managed development funds at the union level",
            "Promote agro-based industries and fair trade for smallholders",
            "Build flood-resilient infrastructure in vulnerable regions",
            "Guarantee fair distribution of national development funds",
            "Strengthen community policing and local dispute resolution",
            "Develop eco-tourism as an alternative livelihood",
            "Secure river and water rights for fishing communities",
            "Expand mobile connectivity and digital literacy in rural areas",
        ],
        "occupations": [
            "Community Development Worker",
            "Teacher and Education Advocate",
            "Farmer and Agricultural Leader",
            "Local Business Owner",
            "Trade Union Organiser",
            "Cultural Preservation Activist",
            "Former Union Parishad Chairman",
            "Healthcare Worker and Social Activist",
        ],
        "bio_templates": [
            "{name} has been a tireless advocate for the marginalised communities of {region} throughout {pronoun_pos} {years}-year career in civil society and politics. As a Daripalla candidate, {pronoun} stands for equitable development, cultural preservation, and giving every community a seat at the table. With a background in {occ_short}, {name} understands the everyday struggles of ordinary Bangladeshis.",
            "Born into a farming family in {region}, {name} witnessed firsthand the inequalities that define rural Bangladesh. After years in {occ_short}, {pronoun} joined Daripalla to fight for inclusive policies that reach the last mile. {name} has been instrumental in securing clean water, school buildings, and road connectivity for underserved union councils in {pronoun_pos} constituency.",
            "{name} is a grassroots leader known throughout {region} for {pronoun_pos} dedication to community welfare. As a Daripalla candidate, {pronoun} champions the rights of small farmers, fishermen, and artisans who are often overlooked by mainstream political parties. With {years} years of social work and a background in {occ_short}, {name} brings genuine community knowledge to the legislature.",
        ],
    },
}

OCC_SHORT = {
    "Advocate, Supreme Court of Bangladesh": "law",
    "Businessman and Community Leader": "business",
    "Former Civil Servant": "civil service",
    "Agricultural Entrepreneur": "agriculture",
    "Retired Army Officer": "the military",
    "Industrialist": "industry",
    "Former District Commissioner": "civil administration",
    "Chartered Accountant": "finance and accounting",
    "University Professor": "academia",
    "Physician and Public Health Advocate": "medicine",
    "NGO Director and Social Activist": "NGO and development work",
    "Software Engineer and Tech Entrepreneur": "technology",
    "Journalist and Media Professional": "journalism",
    "Development Economist": "economics and development",
    "Environmental Activist": "environmental advocacy",
    "Microfinance and Rural Development Expert": "rural development",
    "Community Development Worker": "community development",
    "Teacher and Education Advocate": "education",
    "Farmer and Agricultural Leader": "agriculture",
    "Local Business Owner": "local business",
    "Trade Union Organiser": "labour rights",
    "Cultural Preservation Activist": "cultural advocacy",
    "Former Union Parishad Chairman": "local government",
    "Healthcare Worker and Social Activist": "healthcare",
}

# Female names in the dataset (detected manually)
FEMALE_NAMES = {
    "Sabira Sultana", "Arifa Akter", "Dilshana Parul",
    "Tanjila Ahmed", "Jui Chakma", "Tahsina Rushdir",
}

def get_pronouns(name):
    if name in FEMALE_NAMES:
        return "she", "her", "her", "She"
    return "he", "his", "him", "He"

def pick(lst, seed):
    random.seed(seed)
    return random.choice(lst)

def build_record(cid, name, party, region):
    random.seed(cid * 17 + 3)
    pd = PARTY_DATA[party]

    occ = pick(pd["occupations"], cid + 1)
    occ_short = OCC_SHORT.get(occ, "public service")
    slogan = pick(pd["slogans"], cid + 2)
    years = random.randint(8, 28)
    age = random.randint(38, 65)
    pronoun, pronoun_pos, pronoun_obj, pronoun_cap = get_pronouns(name)

    template = pick(pd["bio_templates"], cid + 3)
    bio = template.format(
        name=name, region=region, years=years,
        occ_short=occ_short,
        pronoun=pronoun, pronoun_pos=pronoun_pos,
        pronoun_obj=pronoun_obj, pronoun_cap=pronoun_cap,
    )

    # Pick 5 manifesto lines
    random.seed(cid + 99)
    lines = random.sample(pd["manifesto_lines"], 5)
    manifesto = "\n".join(lines)

    return {
        "id": cid,
        "bio": bio,
        "age": age,
        "occupation": occ,
        "slogan": slogan,
        "manifesto": manifesto,
    }


def run():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # Fetch all candidates
    cur.execute("""
        SELECT c.id, c.name, c.party, r.name
        FROM voting_candidate c
        JOIN voting_region r ON c.region_id = r.id
    """)
    candidates = cur.fetchall()
    print(f"Found {len(candidates)} candidates. Populating...")

    updated = 0
    for cid, name, party, region in candidates:
        if party not in PARTY_DATA:
            print(f"  SKIP {name} ({party}) — unknown party")
            continue

        rec = build_record(cid, name, party, region)

        cur.execute("""
            UPDATE voting_candidate
            SET bio=?, age=?, occupation=?, slogan=?, manifesto=?
            WHERE id=?
        """, (
            rec["bio"], rec["age"],
            rec["occupation"], rec["slogan"], rec["manifesto"],
            rec["id"],
        ))
        updated += 1

    conn.commit()
    conn.close()
    print(f"Done. Updated {updated} candidates.")


if __name__ == "__main__":
    run()
