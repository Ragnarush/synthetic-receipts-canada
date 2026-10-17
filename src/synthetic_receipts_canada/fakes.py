"""Fictitious merchants, addresses, people and tax numbers.

Everything here is invented. Guard rails that keep it that way:
- merchant names are assembled from parts and never match a real chain or trademark;
- phone numbers sit in the 555-01XX block, reserved for fiction by the NANP;
- GST (BN) and QST numbers have the right shape but deliberately FAIL the Luhn check,
  so the generator can never emit a number that belongs to a real registrant.
"""

import random
from dataclasses import dataclass

RESTAURANT_PREFIXES = [
    "Resto", "Bistro", "Café", "Casse-croûte", "Pizzeria", "Cantine", "Brasserie",
    "Rôtisserie", "Taverne", "Restaurant", "Crêperie", "Grill", "Buffet", "Sushi",
]
RESTAURANT_SUFFIXES = [
    "Chez Doh", "du Coin", "La Marmite", "Le Pélican", "Les Trois Érables", "du Vieux-Quai",
    "L'Assiette carrée", "Chez Mireille", "Le Fictif", "La Belle Fourchette", "du Moulin",
    "Chez Jean Doh", "La Cabane à Pignon", "Le Petit Mousse", "Les Deux Cuillères",
    "Au Fourneau d'Antan", "La Toque Rouge", "Le Bedon Rond", "Chez Thérèse Doh",
]
STREETS = [
    "rue Principale", "rue Saint-Joseph", "boulevard des Pins", "avenue des Érables",
    "chemin de la Montagne", "rue du Moulin", "rue Notre-Dame", "boul. de la Rivière",
    "rue des Bouleaux", "avenue du Quai", "rue de l'Église", "chemin du Lac",
]
# Real cities, with the first letter of a Québec postal code that fits each one.
CITIES = [
    ("Montréal", "H"), ("Québec", "G"), ("Laval", "H"), ("Gatineau", "J"), ("Sherbrooke", "J"),
    ("Trois-Rivières", "G"), ("Lévis", "G"), ("Saguenay", "G"), ("Longueuil", "J"),
    ("Rimouski", "G"), ("Drummondville", "J"), ("Saint-Jérôme", "J"), ("Terrebonne", "J"),
    ("Granby", "J"), ("Shawinigan", "G"), ("Rouyn-Noranda", "J"), ("Sept-Îles", "G"),
]
AREA_CODES = ["514", "438", "418", "581", "450", "579", "819", "873", "367"]
FIRST_NAMES = [
    "Julie", "Marc", "Sophie", "Étienne", "Nadia", "Karim", "Mélanie", "Simon", "Jade",
    "Olivier", "Camille", "Gabriel", "Léa", "Hugo", "Émilie", "Thomas", "Rosalie", "Félix",
]
# Letters a Canadian postal code may use in positions 1, 3 and 5 (no D, F, I, O, Q, U).
POSTAL_LETTERS = "ABCEGHJKLMNPRSTVWXYZ"


@dataclass(frozen=True)
class Merchant:
    name: str
    street: str
    city: str
    province_label: str
    postal_code: str
    phone: str
    gst_number: str  # 9 digits + RT0001
    qst_number: str  # 10 digits + TQ0001

    @property
    def address_lines(self) -> list[str]:
        return [self.street, f"{self.city} ({self.province_label})  {self.postal_code}"]


def luhn_is_valid(digits: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def _digits_failing_luhn(rng: random.Random, length: int) -> str:
    while True:
        digits = "".join(rng.choice("0123456789") for _ in range(length))
        if digits[0] != "0" and not luhn_is_valid(digits):
            return digits


def fake_gst_number(rng: random.Random) -> str:
    return _digits_failing_luhn(rng, 9) + "RT0001"


def fake_qst_number(rng: random.Random) -> str:
    return _digits_failing_luhn(rng, 10) + "TQ0001"


def fake_phone(rng: random.Random) -> str:
    return f"{rng.choice(AREA_CODES)} 555-{rng.randint(100, 199):04d}"


def fake_postal_code(rng: random.Random, first_letter: str) -> str:
    return (
        f"{first_letter}{rng.randint(0, 9)}{rng.choice(POSTAL_LETTERS)} "
        f"{rng.randint(0, 9)}{rng.choice(POSTAL_LETTERS)}{rng.randint(0, 9)}"
    )


def fake_restaurant(rng: random.Random) -> Merchant:
    city, letter = rng.choice(CITIES)
    name = f"{rng.choice(RESTAURANT_PREFIXES)} {rng.choice(RESTAURANT_SUFFIXES)}"
    return Merchant(
        name=name,
        street=f"{rng.randint(10, 9999)}, {rng.choice(STREETS)}",
        city=city,
        province_label="Québec",
        postal_code=fake_postal_code(rng, letter),
        phone=fake_phone(rng),
        gst_number=fake_gst_number(rng),
        qst_number=fake_qst_number(rng),
    )


def fake_first_name(rng: random.Random) -> str:
    return rng.choice(FIRST_NAMES)
