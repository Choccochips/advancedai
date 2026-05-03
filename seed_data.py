# This file will be used 

import duckdb
from datetime import datetime

# connect to db 
con = duckdb.connect("keeb_data.duckdb")

# Clear tables so repeated tests dont build
con.execute("DELETE FROM raw_posts")
con.execute("DELETE FROM parsed_items")

posts = [
(
        "post_001",
        "[US-TX] [H] Paypal [W] Gateron Melodic Clicky, Gateron Type R, Keygeek Y2, AKKO Rosewood, INVYR Holy Panda, Cherry MX Black Switches",
        """Buying
Looking for these switches
Gateron Melodic Clicky
Gateron Type R
Keygeek Y2 (pref 53g Bottom out may consider others)
AKKO Rosewood
INVYR Holy Panda
Cherry MX Black"""
    ),

    (
        "post_002",
        "[US-CA][H] Dixie Bauer Gen 1, LZ Physix Poly (1/10), Nexus Primus Poly [W] PayPal, Local cash",
        """Reposting AGAIN with final lowered prices.
Bundle Deal: Take all three for $1,300 shipped.

Dixie Bauer (Gen 1) - $600
LZ Physix Poly - $600 (OBO)
Nexus Primus Poly - $400"""
    ),

    (
        "post_003",
        "[EU-SE] [H] Space65 CV cream [W] PayPal",
        """Selling
Looking to get 350 325 e, but open to offers.
Excellent condition, minor cosmetic scratch."""
    ),

    (
        "post_004",
        "[US-CA] [H] keyboards etc [W] Paypal",
        """Filco Majestouch Convertible 2 mx browns: $40
RealForce 106UB PJ0800: $50
Razer Blackwidow TE Chroma v2: $30
HHKB Pro 1 black: $310
LZ CLS SE built mx blacks: $650
drunkdeer G65: $40"""
    ),

    (
        "post_005",
        "[US-CA] [H] Machina Orbit R1 - Charcoal/Aluminum [W] PayPal",
        """Selling
400 - Shipped
Excellent condition, not built, no signs of wear."""
    ),

    (
        "post_006",
        "[US-NC] [H] SMKX Champagne Kohaku [W] keyboards, PayPal",
        """Buying
Looking for black kohaku or tofu60 or blackout board."""
    ),

    (
        "post_007",
        "[US-GA] [H] Unbuilt QK75 (Wired + Solder PCB) [W] PayPal",
        """Qwertykeys QK75 - $100 OBO + shipping -- SOLD
Anodized Grey shell
Solder PCB
Carrying case included"""
    ),

    (
        "post_008",
        "[US-TX] [H] Mode Envoy Full PC [W] PayPal",
        """Mode Envoy - $190 shipped
GMK Dualshot R2 - $80
Bundle for $230 shipped"""
    ),

    (
        "post_009",
        "[MA] [H] MoErgo Glove80 [W] PayPal",
        """Glove80 - $380 shipped
Basically new, used once."""
    ),

    (
        "post_010",
        "[US-TX] [H] Meletrix Zoom 98 + Awekeys Copper Eagle [W] Paypal",
        """Zoom 98 built - $550
Board only - $320
Keycaps - $270
GMK Parcel - $75"""
    ),

    (
        "post_011",
        "[US-CA][H] Built F2-84, Gok Venn, Tofu65 [W] Paypal",
        """F2-84 - $470
Gok Venn - $200 SOLD
Tofu65 - $100
Grab bag - $75"""
    ),

    (
        "post_012",
        "[US-FL] [H] Mercury65 E-white BNIB [W] PayPal",
        """Mercury65 - $400 shipped OBO"""
    ),

    (
        "post_013",
        "[HK][H] Matrix boards and GMK sets [W] Paypal",
        """Matrix 1.2OG - 520usd
Matrix NOOS - 520usd
Casper60 - 290usd
Leopold FC980C - 320usd"""
    ),

    (
        "post_014",
        "[US-NY] [H] Think6.5 v2, Iron160, GMK sets [W] PayPal",
        """Think6.5 v2.0 - $400
Iron160 - $550
Multiple GMK sets ranging $90–$350"""
    ),

    (
        "post_015",
        "[US-CA][H] Kalam Keycult No.2 TKL [W] PayPal",
        """Keycult No.2 TKL - $550"""
    ),

    (
        "post_016",
        "[US-CA] [H] Mode Envoy, Mode Sonnet, Duo40 [W] Paypal",
        """Mode Sonnet - $200
Mode Envoy - $130
Duo40 - $235
Realforce TKL - $150"""
    ),

    (
        "post_017",
        "[US-CA][H] RAMA U80-A, Wooting boards [W] PayPal",
        """RAMA U80-A - $400
Wooting 80HE - $400
Zoom TKL - $140
Womier SK75 - $150"""
    ),

    (
        "post_018",
        "[US-OR] [H] Mode Designs Encore Series 3 [W] PayPal",
        """Mode Encore Series 3 - $300 (SOLD $250)
PBTfans Tape set - $70"""
    ),

    (
        "post_019",
        "[US-IA] [H] Mode Loop [W] PayPal",
        """Mode Loop - $500 SOLD"""
    ),

    (
        "post_020",
        "[US-CA] [H] Mode Envoy, Bauer Lite, Osume Keycaps [W] PayPal",
        """Mode Envoy - $250
Bauer Lite - SOLD
Osume Sakura - $100"""
    ),

    (
        "post_021",
        "[US-MS] [H] Zephyr Z1, GMK Keycaps, Switches [W] Paypal",
        """
Looking to sell some stuff from the collection.

Keyboard
Zephyr Z1 $275

• Silver HHKB
• HS pcb, Alu Plate

Keycaps
GMK Night Runner $110
GMK Striker $90
GMK Panels $90
DCS Bowl Blanks $45

Switches - Take all switches for $120 shipped!
SW x Gateron Onyx $35
SWK Catmint $30
Keveek Intros $30
        """,
    ),

    (
        "post_022",
        "[US-FL] [H] Keyboards, Switches, Keycaps [W] PayPal",
        """
Keychron K6 (Black) - $30
Keychron Q4 (Black) $50
Womier SK75 (Green) $70

Luminkey60 (Brown) 120$
Elecfox Inky75 $70

GMK Minimal 2 Base $65
GMK Bento Revival R2 Base $65
Keytok Godzilla Black Classic $50
        """,
    ),

    (
        "post_023",
        "[US-VA] [H] Curve0, switches, artisans [W] PayPal",
        """
kbd0 curve0 $50 SOLD

switches:
gateron lanes x 70 - $45 SOLD
alexotos granites x108 $40
gateron longjing tea x70 - $30 SOLD

hmx macchiatos x90 - $20
akko creamy blue pro v3 x87 - $18

deskmat:
hibi parade desk mat - $20

artisans:
namong movie rudory pink - $60
jelly cap melon soda $30
        """,
    ),

    (
        "post_024",
        "[BH] [H] Plume65 [W] PayPal",
        """
Plume65 blue, brass

270$ With Free GMK set

Extra Aluminum plate
Extra daughterboard

Choose between:
GMK Hennessey
GMK Katana
        """,
    )
]

for i, (post_id, title, body) in enumerate(posts):
    con.execute("""
        INSERT INTO raw_posts (
            post_id, title, body, created_utc
        )
        VALUES (?, ?, ?, ?)
    """, [
        post_id,
        title,
        body,
        datetime.now()
    ])

print("Seeded raw_posts with data.")
