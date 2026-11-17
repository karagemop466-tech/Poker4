#!/usr/bin/env python3
"""Build data/tournaments.json, data/rate-log.json, data/flagged.json for the Poker4 dashboard.

Every value below was read directly from an official operator document on 2026-11-17 UTC
(Venetian structure sheets 1-37, Venetian DSE IV schedule page, Wynn daily structures PDF,
Wynn daily poster PDF, Wynn WPT schedule PDF, WPT structures PDF chunks 0-3, TI homepage,
Venetian resort-fee page [2026-11-16]). Where an official value was not printed, the field
is None and the row is flagged unverified. Nothing is inferred.

Run: python3 tools/build_data.py
"""
import json, os

V = "https://www.venetianlasvegas.com"
VS = V + "/content/dam/vlvweb/casino/poker/deepstack/2026/structures"
SCHED = V + "/resort/casino/poker/deepstack-extravaganza-poker-tournament/dse-nov-2026.html"
W = "https://cdn.wynnresorts.com/image/upload"
DAILY = W + "/v1752011191/visitwynn_pdfs_files/Poker/Daily%20Tournaments/Poker-All_Daily_Structures.pdf"
POSTER = W + "/v1752011166/visitwynn_pdfs_files/Poker/Daily%20Tournaments/poker-daily-tournament-poster.pdf"
WPT_SCHED = W + "/v1757097329/visitwynn_pdfs_files/Poker/WPT/WPT_World_Championship_Schedule.pdf"
WPT_STRUCT = W + "/v1750864036/visitwynn_pdfs_files/Poker/WPT/WPT_World_Championship_Structures.pdf"
TI = "https://treasureisland.com/"
FEE = V + "/resort/resort-fee.html"
RET = "2026-11-17"
RET_FEE = "2026-11-16"

def src(skey, url, label, excerpt, retrieved=RET):
    return {"id": skey, "label": label, "url": url, "excerpt": excerpt, "retrieved": retrieved}

# ---------------------------------------------------------------- Venetian sheets
# Fields exactly as printed on each structure sheet. fee=house fee; pool=prize-pool contribution.
SHEETS = {
 1: dict(name="$200 No Limit Hold'em Bounty (1Day)", game="NLH", bounty=True, buyin=200, fee=40, pool=160,
         gtd=8000, gtd_basis="prize pool + total bounties", stack=25000, lvl=30, lr="8 levels + Break (9:40 PM)",
         payout="12.5% of the field", bounty_txt="$50 per elimination",
         ex="\"$40 of the $200 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $160 of every $200 Buy In.\" / \"Guarantee: $8,000 (prize pool + total bounties)\" / \"Players receive $50 bounty for each player they eliminate\""),
 2: dict(name="$400 No Limit Hold'em (Event 07, flights 1A/1B)", game="NLH", multi=True, buyin=400, fee=70, pool=330,
         gtd=75000, gtd_basis="prize pool", stack=40000, lvl=40, lr="9 levels + Break (5:55 PM)",
         ex="\"$70 of the $400 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $330 of every $400 Buy In.\" / \"Any player who bags chips for Day 2 may not play a subsequent flight.\""),
 3: dict(name="$400 No Limit Hold'em (Event 19, flights 1A/1B/1C)", game="NLH", multi=True, buyin=400, fee=70, pool=330,
         gtd=75000, gtd_basis="prize pool", stack=40000, lvl=40, lr="9 levels + Break (5:55 PM)",
         ex="\"$70 of the $400 Buy-In is withheld... prize pool consists of $330 of every $400 Buy In.\" / rule 08 bag/no-subsequent-flight"),
 4: dict(name="$600 No Limit Hold'em (Event 59, flights 1A/1B/1C)", game="NLH", multi=True, buyin=600, fee=95, pool=505,
         gtd=150000, gtd_basis="prize pool", stack=40000, lvl=40, lr="9 levels + Break (5:55 PM)",
         ex="\"$95 of the $600 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $505 of every $600 Buy In.\" / \"On Day 1A only, players who register before the start of the event (11:10 a.m.), will receive a $20 discount on house fees for a total buy in of $580 instead of $600.\""),
 5: dict(name="$300 No Limit Hold'em (1Day)", game="NLH", buyin=300, fee=58, pool=242, gtd=10000, gtd_basis="prize pool",
         stack=40000, lvl=30, lr="10 levels + Break (~4:55 PM)", payout="12.5% of the field",
         ex="\"$58 of the $300 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $242 of every $300 Buy In.\" / \"Late Registration: 10 levels + Break (~ 4:55 PM)\""),
 6: dict(name="$400 No Limit Hold'em (1Day)", game="NLH", buyin=400, fee=65, pool=335, gtd=15000, gtd_basis="prize pool",
         stack=40000, lvl=30, lr="10 levels + Break (~4:55 PM)", payout="12.5% of the field",
         ex="\"$65 of the $400 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $335 of every $400 Buy In.\""),
 7: dict(name="$600 No Limit Hold'em (1Day)", game="NLH", buyin=600, fee=90, pool=510, gtd={14:30000,28:40000,63:30000},
         gtd_basis="prize pool", stack=40000, lvl=30, lr="10 levels + Break (~4:55 PM)", payout="12.5% of the field",
         ex="\"$90 of the $600 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $510 of every $600 Buy In.\" / \"Guarantee: $30,000 for Event #14 and #63 / $40,000 for Event #28\""),
 8: dict(name="$200 NLH PokerAtlas Valuetown Bounty (1Day)", game="NLH", bounty=True, buyin=200, fee=40, pool=160,
         gtd=20000, gtd_basis="prize pool + total bounties", stack=25000, lvl=30, lr="8 levels + Break (9:40 PM)",
         payout="12.5% of the field", bounty_txt="$50 per elimination", discount="PokerAtlas PRO $20 rake discount on initial buy-in only (total $180)",
         ex="\"All subsequent buy in's after the initial buy in will be $200.\" / \"A Prize Pool of $20,000 is guaranteed... consists of the actual prize pool plus the total amount of $50 bounties\""),
 9: dict(name="$300 No Limit Hold'em (Event 01, flights 1B/1D)", game="NLH", multi=True, buyin=300, fee=60, pool=240,
         gtd=75000, gtd_basis="prize pool", stack=30000, lvl=30, lr="6 levels + Break (~8:40 PM)",
         ex="\"$60 of the $300 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $240 of every $300 Buy In.\" / \"Day B+D @ 5:10 PM with Day 2 @ 12:00 PM\""),
 10: dict(name="$300 No Limit Hold'em (Event 01, flights 1A/1C)", game="NLH", multi=True, buyin=300, fee=60, pool=240,
         gtd=75000, gtd_basis="prize pool", stack=30000, lvl=40, lr="6 levels + Break (~3:40 PM)",
         ex="\"Day A+C @ 11:10 AM with Day 2 @ 12:00 PM\" / \"$60 of the $300 Buy-In is withheld for house fees... prize pool consists of $240 of every $300 Buy In.\""),
 11: dict(name="$600 No Limit Hold'em Bounty (1Day)", game="NLH", bounty=True, buyin=600, fee=90, pool=510,
         gtd={16:30000,30:40000,54:50000}, gtd_basis="prize pool + total bounties", stack=40000, lvl=30,
         lr="10 levels + Break (4:55 PM)", payout="12.5% of the field", bounty_txt="$200 pre-money / $500 in the money",
         ex="\"Players receive $200 Bounty for each player they eliminate... Once we reach the money (posted payouts) - players receive a $500 Bounty\" / \"Guarantee: $30,000 (prize pool + total bounties) Event #16\""),
 12: dict(name="$800 No Limit Hold'em (Event 26, flights 1A/1C/1E)", game="NLH", multi=True, buyin=800, fee=110, pool=690,
         gtd=500000, gtd_basis="prize pool", stack=40000, lvl=40, lr="6 levels + Break (~3:40 PM)",
         ex="\"$110 of the $800 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $690 of every $800 Buy In.\" / rule 08 bag/no-subsequent-flight"),
 13: dict(name="$800 No Limit Hold'em (Event 26, flights 1B/1D)", game="NLH", multi=True, buyin=800, fee=110, pool=690,
         gtd=500000, gtd_basis="prize pool", stack=40000, lvl=30, lr="6 levels + Break (~8:40 PM)",
         ex="\"Day B+D @ 5:10 PM with Day 2 @ 12:00 PM\" / \"$110 of the $800 Buy-In is withheld for house fees...\""),
 14: dict(name="$800 No Limit Hold'em (Event 26, flight 1F Turbo)", game="NLH", multi=True, buyin=800, fee=110, pool=690,
         gtd=500000, gtd_basis="prize pool", stack=40000, lvl=20, lr="6 levels + Break (~7:25 PM)",
         ex="\"Day F (Turbo) @ 5:10 PM with Day 2 @ 12:00 PM\" / \"Level Duration: 20 minutes\""),
 15: dict(name="$300 No Limit Hold'em Bounty (1Day)", game="NLH", bounty=True, buyin=300, fee=50, pool=250,
         gtd=15000, gtd_basis="prize pool + total bounties", stack=25000, lvl=30, lr="8 levels + Break (9:40 PM)",
         payout="12.5% of the field", bounty_txt="$100 per elimination",
         ex="\"$50 of the $300 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $250 of every $300 Buy In.\" / \"Players receive $100 bounty for each player they eliminate\""),
 16: dict(name="$800 No Limit Hold'em Bounty (1Day)", game="NLH", bounty=True, buyin=800, fee=100, pool=700,
         gtd=75000, gtd_basis="prize pool + total bounties", stack=40000, lvl=30, lr="10 levels + Break (4:55 PM)",
         payout="12.5% of the field", bounty_txt="$200 pre-money / $500 in the money",
         ex="\"$100 of the $800 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $700 of every $800 Buy In.\""),
 17: dict(name="$600 No Limit Hold'em Seniors (1Day)", game="NLH", buyin=600, fee=90, pool=510, gtd=40000,
         gtd_basis="prize pool", stack=40000, lvl=30, lr="10 levels + Break (~3:55 PM)", payout="15% of the field",
         eligibility="Must be 50+ years of age",
         ex="\"MUST BE 50+ YEARS OF AGE TO PARTICPATE\" / \"$90 of the $600 Buy-In is withheld for house fees... prize pool consists of $510 of every $600 Buy In.\" / \"This event pays 15% of the field\""),
 18: dict(name="$200 NLH RaceDay Stack (1Day)", game="NLH", buyin=200, fee=35, pool=165, gtd=None, gtd_basis=None,
         stack=30000, lvl=20, lvl2=15, lr="6 levels + Break (~12:25 PM)", payout="12.5% of the field",
         ex="\"$35 of the $200 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $165 of every $200 Buy In.\" / No guarantee is printed anywhere on this sheet."),
 19: dict(name="$100 NLH LIPS Ladies Milestone Satellite (1Day)", game="NLH", satellite=True, buyin=100, fee=20, pool=80,
         gtd_txt="2 seats", gtd_basis="seats", stack=20000, lvl=20, lr="6 levels + Break (~6:25 PM)",
         eligibility="Open to Female players 21+",
         ex="\"Guarantee: 2 Seats\" / \"$20 of the $100 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $80 of every $100 Buy In.\" / Milestone: 200,000 chips = direct entry to Event #39"),
 20: dict(name="$1,100 No Limit Hold'em Seniors (Event 49, flights 1A/1B)", game="NLH", multi=True, buyin=1100, fee=140,
         pool=960, gtd=300000, gtd_basis="prize pool", stack=40000, lvl=40, lr="9 levels + Break (~4:55 PM)",
         eligibility="Must be 50+ years of age",
         ex="\"$140 of the $1,100 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $960 of every $1,100 Buy In.\" / flights play to ~15%"),
 21: dict(name="$2,200 NLH PokerAtlas Championship Title Event (Event 47, Day 1A)", game="NLH", multi=True, buyin=2200,
         fee=225, pool=1975, gtd=1000000, gtd_basis="prize pool", stack=40000, lvl=40, lr="9 levels + Break (~4:55 PM)",
         ex="\"$225 of the $2,200 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $1,975 of every $2,200 Buy In.\" / \"Day 1A @ 10:10 AM w/ Day 2 @ 1:00 PM @ Day 3 @ 11:00 AM\""),
 22: dict(name="$300 Pot Limit Omaha Double Board Bomb Pot (1Day)", game="PLO", buyin=300, fee=58, pool=242, gtd=10000,
         gtd_basis="prize pool", stack=30000, lvl=30, lr="8 levels + break (~4:40 PM)", payout="12.5% of the field",
         ex="\"$58 of the $300 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $242 of every $300 Buy In.\" / \"This event will play eight (8) handed and pay 12.5% of the field.\""),
 23: dict(name="$600 Pot Limit Omaha Double Board Bomb Pot (1Day)", game="PLO", buyin=600, fee=90, pool=510, gtd=25000,
         gtd_basis="prize pool", stack=30000, lvl=30, lr="8 levels + break (~4:40 PM)", payout="12.5% of the field",
         ex="\"$90 of the $600 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $510 of every $600 Buy In.\""),
 24: dict(name="$260 NLH Milestone Satellite (1Day)", game="NLH", satellite=True, buyin=260, fee=40, pool=220,
         gtd_txt="2 seats", gtd_basis="seats", stack=20000, lvl=20, lr="6 levels + Break (~6:25 PM)",
         ex="\"Guarantee: 2 Seats\" / \"$40 of the $260 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $220 of every $260 Buy In.\" / Milestone 200,000 = entry to Event #47"),
 25: dict(name="$260 NLH Turbo Milestone Satellite (1Day)", game="NLH", satellite=True, buyin=260, fee=35, pool=225,
         gtd_txt="2 seats", gtd_basis="seats", stack=20000, lvl=15, lr="6 levels",
         ex="\"$35 of the $260 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $225 of every $260 Buy In.\" / \"Event # 45 Start Time: 8:10 PM / Event # 46 Start Time: 9:10 AM / Event # 48 Start Time: 12:10 PM\""),
 26: dict(name="$400 Pot Limit Omaha Bounty (1Day)", game="PLO", bounty=True, buyin=400, fee=60, pool=340, gtd=15000,
         gtd_basis="prize pool + total bounties", stack=30000, lvl=30, lr="8 levels + break (~4:40 PM)",
         payout="12.5% of the field", bounty_txt="$100 per elimination", special="Call or Make It bet format",
         ex="\"$60 of the $400 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $340 of every $400 Buy In.\" / \"Players receive a $100 Bounty for each player they eliminate\""),
 27: dict(name="$600 PLO Bounty (1Day)", game="PLO", bounty=True, buyin=600, fee=90, pool=510, gtd=25000,
         gtd_basis="prize pool + total bounties", stack=30000, lvl=30, lr="8 levels + break (~4:40 PM)",
         payout="12.5% of the field", bounty_txt="$200 per elimination", special="Call or Make It bet format",
         ex="\"Players receive a $200 Bounty for each player they eliminate\" / \"A total prize pool of $25,000 is guaranteed... actual prize money plus the total amount of $200 bounties\""),
 28: dict(name="$600 BIG O (1Day)", game="Big O", buyin=600, fee=90, pool=510, gtd=25000, gtd_basis="prize pool",
         stack=30000, lvl=30, lr="8 levels + break (~4:40 PM)", payout="12.5% of the field", special="Call or Make It bet format",
         ex="\"$90 of the $600 Buy-In is withheld for house fees (Rake + Staff). Prize pool consists of $510 of every $600 Buy In.\""),
 29: dict(name="$200 No Limit Hold'em (1Day)", game="NLH", buyin=200, fee=40, pool=160, gtd=None, gtd_basis=None,
         stack=30000, lvl=30, lr="8 levels + Break (~3:40 PM)", payout="12.5% of the field",
         ex="\"$40 of the $200 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $160 of every $200 Buy In.\" / No guarantee is printed anywhere on this sheet."),
 30: dict(name="$200 No Limit Hold'em PKO (1Day)", game="NLH", bounty=True, buyin=200, fee=40, pool=160, gtd=8000,
         gtd_basis="prize pool + total bounties", stack=25000, lvl=30, lr="8 levels + Break (9:40 PM)",
         payout="12.5% of the field", bounty_txt="PKO: $50 start bounty, half kept / half carries",
         ex="\"Players start the event as a $50 bounty. For each player they eliminate... they will receive 1/2 of the other players bounty to keep as prize money\""),
 31: dict(name="$600 NLH LIPS Poker Jingle Tag Team (1Day)", game="NLH", team=True, buyin=600, fee=90, pool=510,
         gtd=10000, gtd_basis="prize pool", stack=40000, lvl=30, lr="8 levels + Break (~2:40 PM)",
         payout="12.5% of the field", special="Team event (players rotate every level)",
         ex="\"$80 of the $600 Buy-In is withheld for house fees (Rake + Staff). $10 of the $600 Buy In will be withheld as a flat fee for Vegas Connected, INC, DBA Ladies International Poker Series (LIPS). Prize pool consists of $510 of every $600 Buy In.\""),
 32: dict(name="$800 NLH LIPS Ladies (2Day)", game="NLH", multi=True, buyin=800, fee=110, pool=690, gtd=40000,
         gtd_basis="prize pool", stack=40000, lvl=40, lr="9 levels + Break (~4:55 PM)", eligibility="Female players 21+",
         ex="\"$90 of the $800 Buy-In is withheld for house fees (Rake + Staff). $20 of the $800 Buy In will be withheld as a flat fee for Vegas Connected, INC, DBA Ladies International Poker Series (LIPS). Prize pool consists of $690 of every $800 Buy In.\" / final table ~7:00 PM (PokerGO)"),
 33: dict(name="$600 NLH LIPS Kings and Queens Bounty (1Day)", game="NLH", bounty=True, buyin=600, fee=90, pool=510,
         gtd=30000, gtd_basis="prize pool + total bounties", stack=40000, lvl=30, lr="10 levels + Break (4:55 PM)",
         payout="12.5% of the field", bounty_txt="$200 per elimination",
         ex="\"$80 of the $600 Buy-In is withheld for house fees (Rake + Staff). $10 ... LIPS ... Prize pool consists of $510 of every $600 Buy In.\""),
 34: dict(name="$1,100 No Limit Hold'em PKO (1Day)", game="NLH", bounty=True, buyin=1100, fee=130, pool=970, gtd=75000,
         gtd_basis="prize pool + total bounties", stack=40000, lvl=30, lr="10 levels + Break (4:55 PM)",
         payout="12.5% of the field", bounty_txt="PKO: $200 start bounty",
         ex="\"$130 of the $1,100 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $970 of every $1,100 Buy In.\""),
 35: dict(name="$1,100 No Limit Hold'em (Event 56, flights 1A/1C/1E)", game="NLH", multi=True, buyin=1100, fee=140,
         pool=960, gtd=500000, gtd_basis="prize pool", stack=40000, lvl=40, lr="9 levels + Break (~4:55 PM)",
         ex="\"$140 of the $1,100 Buy-In is withheld... prize pool consists of $960 of every $1,100 Buy In. On Day 1A, players who register before the start of the event (10:10 a.m.) will receive a forty ($40) discount on house fees for a total buy in of $1,060 instead of $1,100.\""),
 36: dict(name="$1,100 No Limit Hold'em (Event 56, flights 1B/1D)", game="NLH", multi=True, buyin=1100, fee=140,
         pool=960, gtd=500000, gtd_basis="prize pool", stack=40000, lvl=30, lr="9 levels + Break (~11:10 PM)",
         ex="\"On Day 1B, players who register before the start of the event (6:10 PM.) will receive a forty ($40) discount on house fees for a total buy in of $1,060 instead of $1,100.\""),
 37: dict(name="$2,200 NLH PokerAtlas Championship Title Event (Event 47, Day 1B)", game="NLH", multi=True, buyin=2200,
         fee=225, pool=1975, gtd=1000000, gtd_basis="prize pool", stack=40000, lvl=30, lr="9 levels + Break (~11:10 PM)",
         ex="\"Day 1B @ 6:10 PM w/ Day 2 @ 1:00 PM @ Day 3 @ 11:00 AM\" / \"$225 of the $2,200 Buy-In is withheld for house fees...\""),
}

SHEET_URL = lambda n: f"{VS}/dse_nov_2026-structure_{n}.pdf"
def vsrc(n): return src(f"V_S{n}", SHEET_URL(n), f"Venetian official structure sheet #{n}", SHEETS[n]["ex"])

# ---------------------------------------------------------------- Venetian events (all 64)
# [event_no, sheet, start_time, flights/dates, extra]
E = [
 [1,[9,10],"11:10 AM / 5:10 PM",[["1A","2026-11-16","11:10 AM"],["1B","2026-11-16","5:10 PM"],["1C","2026-11-17","11:10 AM"],["1D","2026-11-17","5:10 PM"],["Day 2","2026-11-18","12:00 PM"]],None],
 [2,5,"11:10 AM",[["Single day","2026-11-18","11:10 AM"]],None],
 [3,18,"10:10 AM",[["Single day","2026-11-19","10:10 AM"]],None],
 [4,18,"10:10 AM",[["Single day","2026-11-20","10:10 AM"]],None],
 [5,18,"10:10 AM",[["Single day","2026-11-21","10:10 AM"]],None],
 [6,29,"11:10 AM",[["Single day","2026-11-22","11:10 AM"]],None],
 [7,2,"11:10 AM / 5:10 PM",[["1A","2026-11-23","11:10 AM"],["1B","2026-11-23","5:10 PM"],["Day 2","2026-11-25","11:00 AM"]],None],
 [8,30,"5:10 PM",[["Single day","2026-11-23","5:10 PM"]],None],
 [9,1,"5:10 PM",[["Single day","2026-11-24","5:10 PM"]],None],
 [10,6,"11:10 AM",[["Single day","2026-11-25","11:10 AM"]],None],
 [11,1,"5:10 PM",[["Single day","2026-11-25","5:10 PM"]],None],
 [12,5,"11:10 AM",[["Single day","2026-11-26","11:10 AM"]],None],
 [13,1,"5:10 PM",[["Single day","2026-11-26","5:10 PM"]],None],
 [14,7,"11:10 AM",[["Single day","2026-11-27","11:10 AM"]],None],
 [15,1,"5:10 PM",[["Single day","2026-11-27","5:10 PM"]],None],
 [16,11,"11:10 AM",[["Single day","2026-11-28","11:10 AM"]],None],
 [17,26,"12:10 PM",[["Single day","2026-11-28","12:10 PM"]],None],
 [18,8,"5:10 PM",[["Single day","2026-11-28","5:10 PM"]],None],
 [19,3,"11:10 AM",[["1A","2026-11-29","11:10 AM"],["1B","2026-11-30","11:10 AM"],["1C","2026-12-01","11:10 AM"],["Day 2","2026-12-02","11:00 AM"]],None],
 [20,22,"12:10 PM",[["Single day","2026-11-29","12:10 PM"]],None],
 [21,1,"5:10 PM",[["Single day","2026-11-29","5:10 PM"]],None],
 [22,1,"5:10 PM",[["Single day","2026-11-30","5:10 PM"]],None],
 [23,1,"5:10 PM",[["Single day","2026-12-01","5:10 PM"]],None],
 [24,17,"10:10 AM",[["Single day","2026-12-02","10:10 AM"]],None],
 [25,1,"5:10 PM",[["Single day","2026-12-02","5:10 PM"]],None],
 [26,[12,13,14],"11:10 AM / 5:10 PM",[["1A","2026-12-03","11:10 AM"],["1B","2026-12-03","5:10 PM"],["1C","2026-12-04","11:10 AM"],["1D","2026-12-04","5:10 PM"],["1E","2026-12-05","11:10 AM"],["1F (Turbo)","2026-12-05","5:10 PM"],["Day 2","2026-12-06","12:00 PM"]],None],
 [27,28,"12:10 PM",[["Single day","2026-12-03","12:10 PM"]],None],
 [28,7,"11:10 AM",[["Single day","2026-12-06","11:10 AM"]],None],
 [29,15,"5:10 PM",[["Single day","2026-12-06","5:10 PM"]],None],
 [30,11,"11:10 AM",[["Single day","2026-12-07","11:10 AM"]],None],
 [31,15,"5:10 PM",[["Single day","2026-12-07","5:10 PM"]],None],
 [32,17,"10:10 AM",[["Single day","2026-12-08","10:10 AM"]],None],
 [33,19,"4:10 PM",[["Single day","2026-12-08","4:10 PM"]],None],
 [34,15,"5:10 PM",[["Single day","2026-12-08","5:10 PM"]],None],
 [35,31,"10:10 AM",[["Single day","2026-12-09","10:10 AM"]],None],
 [36,16,"11:10 AM",[["Single day","2026-12-09","11:10 AM"]],None],
 [37,19,"4:10 PM",[["Single day","2026-12-09","4:10 PM"]],None],
 [38,15,"5:10 PM",[["Single day","2026-12-09","5:10 PM"]],None],
 [39,32,"10:10 AM",[["Day 1","2026-12-10","10:10 AM"],["Day 2","2026-12-11","10:00 AM"],["Final Table","2026-12-11","7:00 PM"]],None],
 [40,27,"12:10 PM",[["Single day","2026-12-10","12:10 PM"]],None],
 [41,24,"4:10 PM",[["Single day","2026-12-10","4:10 PM"]],None],
 [42,15,"5:10 PM",[["Single day","2026-12-10","5:10 PM"]],None],
 [43,33,"11:10 AM",[["Single day","2026-12-11","11:10 AM"]],None],
 [44,24,"4:10 PM",[["Single day","2026-12-11","4:10 PM"]],None],
 [45,25,"8:10 PM",[["Single day","2026-12-11","8:10 PM"]],None],
 [46,25,"9:10 AM",[["Single day","2026-12-12","9:10 AM"]],None],
 [47,[21,37],"10:10 AM / 6:10 PM",[["1A","2026-12-12","10:10 AM"],["1B","2026-12-12","6:10 PM"],["Day 2","2026-12-13","1:00 PM"],["Day 3 / Final Table","2026-12-14","11:00 AM"]],None],
 [48,25,"12:10 PM",[["Single day","2026-12-12","12:10 PM"]],None],
 [49,20,"10:10 AM",[["1A","2026-12-13","10:10 AM"],["1B","2026-12-14","10:10 AM"],["Day 2","2026-12-15","10:00 AM"]],None],
 [50,15,"5:10 PM",[["Single day","2026-12-13","5:10 PM"]],None],
 [51,15,"5:10 PM",[["Single day","2026-12-14","5:10 PM"]],None],
 [52,34,"11:10 AM",[["Single day","2026-12-15","11:10 AM"]],None],
 [53,15,"5:10 PM",[["Single day","2026-12-15","5:10 PM"]],None],
 [54,11,"11:10 AM",[["Single day","2026-12-16","11:10 AM"]],None],
 [55,15,"5:10 PM",[["Single day","2026-12-16","5:10 PM"]],None],
 [56,[35,36],"10:10 AM / 6:10 PM",[["1A","2026-12-17","10:10 AM"],["1B","2026-12-17","6:10 PM"],["1C","2026-12-18","10:10 AM"],["1D","2026-12-18","6:10 PM"],["1E","2026-12-19","10:10 AM"],["Day 2","2026-12-20","11:00 AM"]],None],
 [57,23,"12:10 PM",[["Single day","2026-12-17","12:10 PM"]],None],
 [58,8,"5:10 PM",[["Single day","2026-12-19","5:10 PM"]],None],
 [59,4,"11:10 AM",[["1A","2026-12-20","11:10 AM"],["1B","2026-12-21","11:10 AM"],["1C","2026-12-22","11:10 AM"],["Day 2","2026-12-23","11:00 AM"]],None],
 [60,1,"5:10 PM",[["Single day","2026-12-20","5:10 PM"]],None],
 [61,1,"5:10 PM",[["Single day","2026-12-21","5:10 PM"]],None],
 [62,1,"5:10 PM",[["Single day","2026-12-22","5:10 PM"]],None],
 [63,7,"11:10 AM",[["Single day","2026-12-23","11:10 AM"]],None],
 [64,1,"5:10 PM",[["Single day","2026-12-23","5:10 PM"]],None],
]

SCHED_SRC = src("V_SCHED", SCHED, "Venetian official DSE IV schedule page",
                "\"DeepStack Extravaganza - November 16 - December 23, 2026\" ... \"More than $3.6 Million in guaranteed tournament prize pools\" (page H1/series line)")

events = []
for no, sheets, start, flights, extra in E:
    if isinstance(sheets, int): sheets = [sheets]
    s = SHEETS[sheets[0]]
    gtd = s.get("gtd")
    if isinstance(gtd, dict): gtd = gtd.get(no)
    gtd_txt = s.get("gtd_txt") if gtd is None else gtd
    row = {
        "id": f"VEN-{no:02d}", "venue": "Venetian", "room": "Venetian Poker Room",
        "event_no": no, "name": s["name"].replace("(Event 07, flights 1A/1B)", f"(Event #{no})").replace("(Event 19, flights 1A/1B/1C)", f"(Event #{no})").replace("(Event 59, flights 1A/1B/1C)", f"(Event #{no})").replace("(Event 01, flights 1B/1D)", f"(Event #{no})").replace("(Event 01, flights 1A/1C)", f"(Event #{no})").replace("(Event 26, flights 1A/1C/1E)", f"(Event #{no})").replace("(Event 26, flights 1B/1D)", f"(Event #{no})").replace("(Event 26, flight 1F Turbo)", f"(Event #{no})").replace("(Event 49, flights 1A/1B)", f"(Event #{no})").replace("(Event 47, Day 1A)", f"(Event #{no})").replace("(Event 47, Day 1B)", f"(Event #{no})").replace("(Event 56, flights 1A/1C/1E)", f"(Event #{no})").replace("(Event 56, flights 1B/1D)", f"(Event #{no})"),
        "game": s["game"], "start_time": start, "sessions": flights,
        "buyin": s["buyin"], "house_fee": s["fee"], "pool_contribution": s["pool"],
        "guarantee": gtd_txt, "guarantee_basis": s["gtd_basis"],
        "guarantee_per_buyin": (round((gtd_txt or 0) / s["buyin"], 2) if isinstance(gtd_txt, (int, float)) and s["buyin"] else None),
        "starting_stack": s["stack"], "level_minutes": f"{s['lvl']}/{s.get('lvl2')}" if s.get("lvl2") else s["lvl"],
        "late_registration": s["lr"], "payout": s.get("payout"),
        "flags": [k for k, on in (("bounty", s.get("bounty")), ("multi-flight/multi-day", s.get("multi")),
                                  ("satellite", s.get("satellite")), ("team event", s.get("team"))) if on],
        "bounty_text": s.get("bounty_txt"), "discount_official": s.get("discount"),
        "special": s.get("special"), "eligibility": s.get("eligibility"),
        "single_entry_confirmed": False,
        "single_entry_status": "unverified — no official sheet states max entries, no re-entry, freezeout, or add-on policy; sheets 8 and the multi-flight sheets reference subsequent buy-ins/re-entry by structure",
        "reentry_official": None, "addon_official": None,
        "structure_read": True,
        "sources": [vsrc(n) for n in sheets] + [SCHED_SRC],
        "last_checked": RET,
    }
    if extra: row.update(extra)
    events.append(row)

# ---------------------------------------------------------------- Wynn dailies (recurring)
wynn_daily = [
 dict(id="WYNN-DAILY-MTH", name="$200 NLH Monday-Thursday", weekdays=["Mon","Tue","Wed","Thu"], start="12:00 PM",
      buyin=200, fee=38, pool=162, gtd=10000, gtd_basis="prize pool", stack=25000, lvl=30, lr="Registration and re-entries until start of level 9 (approximately 4:30 p.m.)",
      reentry="RE-ENTRY CONFIRMED ALLOWED — \"The Tournament entry fee, as well as the re-entry fee, is $200\"; \"Registration and re-entries will be available until the start of level 9\"",
      addon=None, fee_split="$26 tournament fee + $12 poker staff + $162 prize pool",
      ex="\"This $200 NLH $10,000 Guarantee poker tournament ... is a Single Day No Limit Hold'em event beginning at 12 p.m.\" / \"Registration and re-entries will be available until the start of level 9 (approximately 4:30 p.m.)\""),
 dict(id="WYNN-DAILY-FRI", name="$240 NLH Rebuy & Add-on Friday", weekdays=["Fri"], start="12:00 PM",
      buyin=240, fee=50, pool=190, gtd=40000, gtd_basis="prize pool", stack=25000, lvl=30,
      lr="Registration, rebuys and add-ons until start of level 9 (~4:30 p.m.)",
      reentry="RE-ENTRY CONFIRMED NOT ALLOWED — \"Re-entry is NOT allowed.\" Unlimited $200 rebuys at 15,000 chips or less + one $100 add-on instead",
      addon="Unlimited $200 rebuys (at ≤15,000 chips) + one $100 add-on — both confirmed by official text",
      fee_split="$35 tournament fee + $15 staff + $190 prize pool (entry); $10 staff + $5 fee per $200 rebuy; $5 fee + $5 staff per add-on",
      ex="\"Re-entry is NOT allowed. All rebuys must be done immediately from the player's original seat.\" / \"Unlimited $200 rebuys for 25,000 tournament chips are available any time a player is at 15,000 chips or less.\""),
 dict(id="WYNN-DAILY-SS", name="$200 NLH Saturday & Sunday", weekdays=["Sat","Sun"], start="12:00 PM",
      buyin=200, fee=38, pool=162, gtd=25000, gtd_basis="prize pool", stack=25000, lvl=30,
      lr="Registration, re-entries, and one add-on per entry until start of level 11 (~5:30 p.m.)",
      reentry="RE-ENTRY CONFIRMED ALLOWED — \"Registration, re-entries, and one (1) add-on per entry will be available until the start of level 11 (approximately 5:30 p.m.)\"",
      addon="One (1) $100 add-on for 25,000 tournament chips per entry — confirmed by official text",
      fee_split="$26 tournament fee + $12 poker staff + $162 prize pool; $5 fee + $5 staff per $100 add-on",
      ex="\"$200 NLH $25,000 Guarantee ... Single Day No Limit Hold'em event beginning at 12 p.m.\" / \"Registration, re-entries, and one (1) add-on per entry will be available until the start of level 11\""),
 dict(id="WYNN-DAILY-NIGHT", name="$160 NLH Nightly (Mon-Sun)", weekdays=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"], start="6:00 PM",
      buyin=160, fee=30, pool=130, gtd=10000, gtd_basis="prize pool", stack=25000, lvl=20,
      lr="Registration, re-entries, and one add-on per entry until start of level 9 (~9:00 p.m.)",
      reentry="RE-ENTRY CONFIRMED ALLOWED — \"The Tournament entry fee, as well as the re-entry fee, is $160\"; \"Registration, re-entries, and one (1) add-on per entry will be available until the start of level 9 (approximately 9:00 p.m.)\"",
      addon="One (1) $100 add-on for 25,000 tournament chips per entry — confirmed by official text",
      fee_split="$20 tournament fee + $10 poker staff + $130 prize pool",
      ex="\"$160 NLH $10,000 Guarantee ... Single Day No Limit Hold'em event beginning at 6 p.m.\" / 20-minute levels, 10-minute breaks"),
]
for r in wynn_daily:
    r.update(dict(venue="Wynn", room="Wynn Poker Room (in Encore)", event_no=None, game="NLH",
        sessions=None, guarantee_per_buyin=round(r["gtd"]/r["buyin"], 2),
        late_registration=r["lr"], payout=None, flags=["recurring weekly"], bounty_text=None,
        discount_official=None, special=None, eligibility=None, single_entry_confirmed=False,
        single_entry_status="re-entry/add-on CONFIRMED by official text — not a single-entry event",
        structure_read=True,
        sources=[src("W_STRUCTS", DAILY, "Wynn official daily structures + terms PDF", r.pop("ex")),
                 src("W_POSTER", POSTER, "Wynn official daily tournament poster PDF", "Daily schedule grid: Mon-Thu $200 NLH 12 p.m.; Fri $240 NLH Rebuy 12 p.m.; Sat/Sun $200 NLH 12 p.m.; Nightly $160 NLH 6 p.m.")],
        last_checked=RET, notes="Official terms: events 'may be suspended during Seniors Events, Classic Events, or other Tournament Series' (e.g., WPT series). Confirm same-day running before travel."))

# ---------------------------------------------------------------- Wynn WPT series
wsrc_sched = src("W_WPT", WPT_SCHED, "Wynn official WPT World Championship schedule PDF",
                 "Series grid November 27 - December 21, 2026 with buy-ins, guarantees, chips, levels")
def wrow(id_, name, game, buyin, gtd, basis, dates, stack=None, lvl=None, reentry=None, flags=None, ex=None, disc=None, eligibility=None):
    return dict(id=id_, venue="Wynn", room="Wynn Poker Room (in Encore)", event_no=None, name=name, game=game,
        start_time="see sessions", sessions=dates, buyin=buyin, house_fee=None, pool_contribution=None,
        guarantee=gtd, guarantee_basis=basis, guarantee_per_buyin=(round(gtd/buyin, 2) if isinstance(gtd, int) and buyin else None),
        starting_stack=stack, level_minutes=lvl, late_registration=None, payout=None,
        flags=flags or [], bounty_text=None, discount_official=disc, special=None, eligibility=eligibility,
        single_entry_confirmed=False,
        single_entry_status=("re-entry CONFIRMED ALLOWED by official structure text" if reentry else
                             "unverified — structure sheet exists in official structures PDF but was not read line-by-line in this pass (chunks 0-3 of 8 read)"),
        reentry_official=reentry, addon_official=None, structure_read=bool(reentry),
        sources=[src("W_WPT", WPT_SCHED, "Wynn official WPT schedule PDF", "Schedule row: " + (ex or name))]
                + ([src("W_WPT_STRUCT", WPT_STRUCT, "Wynn official WPT structures PDF", reentry)] if reentry else []),
        last_checked=RET)

wpt = [
 wrow("WPT-600", "$600 No Limit Hold'em $400K GTD (Day 1A-1F)", "NLH", 600, 400000, "prize pool",
      [["1A","2026-11-27","11:00 AM"],["1B","2026-11-27","5:00 PM"],["1C","2026-11-28","11:00 AM"],["1D","2026-11-28","5:00 PM"],["1E","2026-11-29","11:00 AM"],["1F","2026-11-29","6:00 PM"],["Day 2","2026-11-30","1:00 PM"]],
      40000, "30/40 (1F 20)",
      reentry="\"Unlimited re-entry for each starting flight will be available until the start of level 9. A player who advances to Day 2 is prohibited from entering a subsequent starting flight.\" Fee split: $600 = $510 pool + $65 fee + $25 staff.",
      ex="$600 NLH $400,000 GTD, 40,000 chips, 30/40-min levels"),
 wrow("WPT-TORSE", "$600 TORSE", "Mixed (T-O-R-S-E)", 600, None, None,
      [["Single day","2026-11-27","12:00 PM"]], 35000, 30,
      reentry="\"Unlimited re-entry will be available until the start of level 9.\" $600 = $510 pool + $65 fee + $25 staff.", ex="$600 TORSE 12 p.m."),
 wrow("WPT-PLO400", "$400 Pot Limit Omaha", "PLO", 400, None, None,
      [["Single day","2026-11-27","1:00 PM"]], 30000, 30,
      reentry="\"Unlimited re-entry will be available until the start of level 9 (approximately 5:30 p.m.).\" $400 = $337 pool + $45 fee + $18 staff.", ex="$400 PLO 1 p.m."),
 wrow("WPT-MTD", "$600 Mixed Triple Draw (A-5, 2-7, Badugi)", "Mixed Triple Draw", 600, None, None,
      [["Single day","2026-11-28","12:00 PM"],["Single day","2026-12-20","1:00 PM"]], 35000, 30,
      reentry="\"Unlimited re-entry will be available until the start of level 9.\" $600 = $510 pool + $65 fee + $25 staff.", ex="$600 Mixed Triple Draw"),
 wrow("WPT-800", "$800 No Limit Hold'em $1M GTD (Day 1A-1F)", "NLH", 800, 1000000, "prize pool",
      [["1A","2026-11-30","11:00 AM"],["1B","2026-11-30","5:00 PM"],["1C","2026-12-01","11:00 AM"],["1D","2026-12-01","5:00 PM"],["1E","2026-12-02","11:00 AM"],["1F","2026-12-02","6:00 PM"],["Day 2","2026-12-03","1:00 PM"],["Final Table","2026-12-04","1:00 PM"]],
      40000, "30/40 (1F 20)",
      reentry="\"Unlimited re-entry for each starting flight will be available until the start of level 9.\" $800 = $695 pool + $72 fee + $33 staff.",
      ex="$800 NLH $1,000,000 GTD, 40,000 chips"),
 wrow("WPT-L08", "$600 Limit Omaha 8", "Limit Omaha 8", 600, None, None,
      [["Single day","2026-11-30","12:00 PM"]], 35000, 30,
      reentry="\"Unlimited re-entry will be available until the start of level 9.\" $600 = $510 pool + $65 fee + $25 staff.", ex="$600 Limit Omaha 8 12 p.m."),
 wrow("WPT-1600", "$1,600 No Limit Hold'em $1M GTD (Day 1A/1B)", "NLH", 1600, 1000000, "prize pool",
      [["1A","2026-12-03","11:00 AM"],["1B","2026-12-04","11:00 AM"],["Day 2","2026-12-05","11:00 AM"]], 40000, 40,
      ex="$1,600 NLH $1,000,000 GTD, Day 1A Thu 11 a.m. / 1B Fri 11 a.m."),
 wrow("WPT-PRIME", "WPT Prime Championship $1,100 $5M GTD", "NLH", 1100, 5000000, "prize pool",
      [["1A","2026-12-05","11:00 AM"],["1B","2026-12-06","11:00 AM"],["1C","2026-12-07","11:00 AM"],["1D","2026-12-08","11:00 AM"],["Day 2","2026-12-09","12:00 PM"],["Day 3","2026-12-10","12:00 PM"],["Day 4","2026-12-11","12:00 PM"],["Final Table","2026-12-12","2:00 PM"]],
      40000, "40/60",
      ex="WPT Prime Championship $1,100 $5,000,000 GTD, 40,000 chips, 40/60-min levels"),
 wrow("WPT-SGMB", "Super Gold Million Mystery Bounty $400 $3M GTD", "NLH Mystery Bounty", 400, 3000000, "prize pool (includes $1,000,000 added in cash prizes by ClubWPT Gold — ClubWPT Gold is not available in Nevada; printed footnote)",
      [["1A","2026-12-10","10:00 AM"],["1B","2026-12-10","6:00 PM"],["1C","2026-12-11","10:00 AM"],["1D","2026-12-11","6:00 PM"],["Day 2","2026-12-12","2:00 PM"],["Day 3","2026-12-13","1:00 PM"],["Final Table","2026-12-14","2:00 PM"]],
      30000, "30/40 (1B/1D 20/40)", flags=["mystery bounty"],
      ex="$400 buy-in / $3,000,000 GTD / 30,000 chips"),
 wrow("WPT-800-100K", "$800 NLH $100K GTD", "NLH", 800, 100000, "prize pool",
      [["Single day","2026-12-12","10:00 AM"]], 30000, 30, ex="$800 NLH $100,000 GTD 10 a.m., 30,000 chips, 30-min levels"),
 wrow("WPT-PLO3000", "$3,000 PLO $250K GTD", "PLO", 3000, 250000, "prize pool",
      [["Single day","2026-12-12","1:00 PM"]], 30000, 30, ex="$3,000 PLO $250,000 GTD 1 p.m."),
 wrow("WPT-800-500K", "$800 NLH $500K GTD (Day 1A/1B)", "NLH", 800, 500000, "prize pool",
      [["1A","2026-12-13","11:00 AM"],["1B","2026-12-14","11:00 AM"],["Day 2","2026-12-15","11:00 AM"]], 40000, 40,
      ex="$800 NLH $500,000 GTD, 40,000 chips"),
 wrow("WPT-PLO1600-1M", "$1,600 PLO $1M GTD (Day 1A/1B)", "PLO", 1600, 1000000, "prize pool",
      [["1A","2026-12-13","12:00 PM"],["1B","2026-12-14","12:00 PM"],["Day 2","2026-12-15","12:00 PM"]], 40000, 40,
      ex="$1,600 PLO $1,000,000 GTD, 40,000 chips"),
 wrow("WPT-MTD-2DAY", "$1,100 Mixed Triple Draw (2 Day)", "Mixed Triple Draw", 1100, None, None,
      [["Day 1","2026-12-14","12:00 PM"]], 40000, 40, ex="$1,100 Mixed Triple Draw (A-5, 2-7, Badugi) (2 Day) 12 p.m."),
 wrow("WPT-BIGO", "$1,100 Big O", "Big O", 1100, None, None,
      [["Single day","2026-12-15","12:00 PM"]], 30000, 30, ex="$1,100 Big O 12 p.m., 30,000 chips"),
 wrow("WPT-PKOPLO3000", "$3,000 PLO Progressive Bounty (PKO) $250K GTD", "PLO PKO", 3000, 250000, "prize pool",
      [["Single day","2026-12-15","1:00 PM"]], 30000, 30, flags=["bounty"], ex="$3,000 PLO Progressive Bounty $250,000 GTD 1 p.m."),
 wrow("WPT-1600-500T", "$1,600 NLH $500 Bounty Turbo $100K GTD", "NLH Bounty Turbo", 1600, 100000, "prize pool",
      [["Single day","2026-12-15","7:00 PM"]], 30000, 20, flags=["bounty","turbo"], ex="$1,600 NLH $500 Bounty Turbo $100,000 GTD 7 p.m."),
 wrow("WPT-SENIORS", "Seniors NLH Championship $1,100 $500K GTD (3 Day)", "NLH", 1100, 500000, "prize pool",
      [["Day 1","2026-12-17","11:00 AM"]], 40000, 40, eligibility="Seniors (see official structures for age rule)",
      ex="Seniors NLH Championship (3 Day) $1,100 $500,000 GTD 11 a.m."),
 wrow("WPT-MIXED-CH", "Wynn Mixed Championship $1,600 (2 Day)", "Mixed", 1600, None, None,
      [["Day 1","2026-12-17","11:00 AM"]], 40000, "40/60", ex="Wynn Mixed Championship (2 Day) $1,600 11 a.m."),
 wrow("WPT-3000", "$3,000 NLH $2M GTD (Day 1A/1B)", "NLH", 3000, 2000000, "prize pool",
      [["1A","2026-12-17","12:00 PM"],["1B","2026-12-18","12:00 PM"],["Day 2","2026-12-19","12:00 PM"]], 40000, 40,
      ex="$3,000 NLH $2,000,000 GTD, 40,000 chips (schedule rows; see flagged date-typo note for adjacent rows)"),
 wrow("WPT-HR25800", "NLH High Roller $25,800 (2 Day)", "NLH High Roller", 25800, None, None,
      [["Day 1","2026-12-17","1:00 PM"]], 200000, "40/60",
      disc="Early-registration discounted entry available (printed footnote *****); see structures",
      ex="NLH High Roller (2 Day) $25,800 1 p.m., 200,000 chips"),
 wrow("WPT-1100-1M", "$1,100 NLH $1M GTD (Day 1A/1B)", "NLH", 1100, 1000000, "prize pool",
      [["1A","2026-12-16 (printed 'Dec. 18 Wednesday' — official PDF date typo; see Flagged page)","11:00 AM"],["1B","2026-12-16 (printed 'Dec. 18 Wednesday' — official PDF date typo; see Flagged page)","7:00 PM"],["Day 2","2026-12-20","11:00 AM (printed schedule)"]], 40000, "40 (1B 20/40)",
      ex="$1,100 NLH $1,000,000 GTD, 40,000 chips — rows printed under 'Dec. 18 Wednesday', an impossible weekday for 2026 (flagged)"),
 wrow("WPT-PLO-BBP", "$800 PLO Double Board Bomb Pot", "PLO", 800, None, None,
      [["Single day","2026-12-16 (printed 'Dec. 18 Wednesday' — official PDF date typo; see Flagged page)","12:00 PM"]], 30000, 30,
      ex="$800 PLO Double Board Bomb Pot 12 p.m."),
 wrow("WPT-600-100K", "$600 NLH $100K GTD", "NLH", 600, 100000, "prize pool",
      [["Single day","2026-12-18","12:00 PM"]], 30000, 30, ex="$600 NLH $100,000 GTD 12 p.m., 30,000 chips"),
 wrow("WPT-1600MB", "$1,600 NLH Mystery Bounty $1M GTD (Day 1A-1D)", "NLH Mystery Bounty", 1600, 1000000, "prize pool",
      [["1A","2026-12-19","11:00 AM"],["1B","2026-12-19","7:00 PM"],["1C","2026-12-20","11:00 AM"],["1D","2026-12-20","7:00 PM"],["Day 2","2026-12-21","1:00 PM"]], 40000, "40 (1B/1D 20/40)",
      flags=["mystery bounty"], ex="$1,600 NLH Mystery Bounty $1,000,000 GTD, 40,000 chips"),
 wrow("WPT-6MAX3000", "$3,000 NLH 6-Max $500K GTD", "NLH 6-Max", 3000, 500000, "prize pool",
      [["Single day","2026-12-19","1:00 PM"]], 30000, 30, ex="$3,000 NLH 6-Max $500,000 GTD 1 p.m."),
 wrow("WPT-600-50K", "$600 NLH $50K GTD", "NLH", 600, 50000, "prize pool",
      [["Single day","2026-12-20","12:00 PM"]], 30000, 30, ex="$600 NLH $50,000 GTD 12 p.m., 30,000 chips"),
 wrow("WPT-1100-100K", "$1,100 NLH $100K GTD", "NLH", 1100, 100000, "prize pool",
      [["Single day","2026-12-21","12:00 PM"]], 30000, 30, ex="$1,100 NLH $100,000 GTD 12 p.m., 30,000 chips"),
 wrow("WPT-TURBO600", "$600 NLH Turbo $50K GTD", "NLH Turbo", 600, 50000, "prize pool",
      [["Single day","2026-12-05/06/07/08/09/12 (schedule rows)","9:00 PM"],["Single day","2026-12-21","8:00 PM"],["6-Max Turbo variant","2026-12-19","6:00 PM"],["5-Card PLO Turbo variant","2026-12-20","6:00 PM"]], 30000, 20,
      ex="$600 NLH Turbo $50,000 GTD 9 p.m. (multiple dates), 30,000 chips, 20-min levels"),
]
# satellites (separate section)
sats = [
 wrow("WPT-SAT-DP", "$400 Double Play Milestone Satellite (2 x $1,100 tickets)", "Satellite", 400, "25 prizes", "seats",
      [["2026-12-03","7:00 PM"],["2026-12-04","7:00 PM"],["2026-12-06","7:00 PM"]], 20000, 20,
      ex="Winners receive two prizes valued at $1,100 each (printed footnote *)"),
 wrow("WPT-SAT-PRIME", "$200 Milestone Satellite to $1,100 Prime Championship", "Satellite", 200, "50 seats", "seats",
      [["2026-12-06","12:00 PM"]], 20000, 20, ex="Milestone Satellite to $1,100 Prime Championship, 50 seats"),
 wrow("WPT-SAT-WC1100", "$1,100 Milestone Satellites to $10,400 World Championship", "Satellite", 1100, "25 seats per flight", "seats",
      [["2026-12-08","7:00 PM"],["2026-12-09","2:00 PM / 7:00 PM"],["2026-12-12","2:00 PM / 7:00 PM"],["2026-12-13","12:00 PM / 6:00 PM"],["2026-12-14","12:00 PM / 6:00 PM"],["2026-12-15","11:00 AM / 6:00 PM"]], 20000, 25,
      ex="Milestone Satellite to $10,400 World Championship, 25 seats per flight"),
 wrow("WPT-SAT-3000", "$400 Milestone Satellites to $3,000 NLH", "Satellite", 400, "25 seats per flight", "seats",
      [["2026-12-17","2:00 PM / 7:00 PM"],["2026-12-18 (printed 'Dec. 18 Wednesday' — date typo; flagged)","10:00 AM / 6:00 PM"]], 20000, "20/25",
      ex="Milestone Satellite to $3,000 NLH, 25 seats"),
 wrow("WPT-SAT-1600MB", "$300 Milestone Satellites to $1,600 Mystery Bounty", "Satellite", 300, "10 seats per flight", "seats",
      [["2026-12-19","12:00 PM / 5:00 PM"]], 20000, 20, ex="Milestone Satellite to $1,600 Mystery Bounty, 10 seats"),
 wrow("WPT-SAT-LADIES", "$200 Milestone Satellite to $10,400 Ladies NLH Championship", "Satellite", 200, "10 seats", "seats",
      [["2026-12-12","4:00 PM"]], 20000, 20, ex="Milestone Satellite to $10,400 Ladies NLH Championship, 10 seats"),
 wrow("WPT-SAT-PKG", "$1,600 Milestone Satellite Package to Prime and World Championship", "Satellite", 1600, "25 prizes", "seats",
      [["2026-12-07","7:00 PM"]], 20000, 25, ex="Milestone Satellite Package to Prime and World Championship, 25 prizes"),
]
for r in wpt + sats:
    if r.get("flags") is None: r["flags"] = []
    if "satellite" in r["id"].lower() or "SAT" in r["id"]:
        r["flags"] = list(set((r.get("flags") or []) + ["satellite"]))
    if r.get("bounty_text") is None and any("bounty" in f for f in r["flags"]): r["bounty_text"] = "Mystery/progressive bounty format — prize pool includes bounties (see official structures)"
    r.setdefault("notes", None)

# ladies + LIPS eligibility notes for review page
events += wynn_daily + wpt

satellites = sats

# ---------------------------------------------------------------- assemble JSON
data = {
 "meta": {
   "built": RET,
   "source_of_truth": "Official operator documents only (Venetian structure sheets 1-37 + DSE IV schedule page; Wynn daily structures/poster PDFs; Wynn WPT schedule + structures PDFs). Every row links its sources with excerpts and retrieval dates.",
   "single_entry_rule": "A row is single_entry_confirmed=true ONLY if an official document explicitly states no re-entry / one entry / freezeout. No such statement exists for any Venetian event (sheets 1-37) or any WPT event read (structures chunks 0-3). Wynn daily events officially ALLOW re-entry/add-ons. The 'single-entry / freezeout confirmed' filter therefore currently returns zero rows — displayed honestly rather than filled by inference.",
   "ranking_rule": "Rows are ranked by guarantee_per_buyin only when both guarantee (prize-pool basis) and buy-in are officially printed. guaranteed pool / entry fee is a descriptive ratio, not a forecast of value. Bounty events, satellites, team events and high rollers are labeled and kept in their own sections.",
   "finish_times": "No official document publishes estimated finish times. Overlap analysis uses start times + late-registration cutoffs + structure length only, and is labeled 'possible overlap', never 'confirmed impossible'.",
   "coverage_note": "WPT structures PDF chunks 0-3 of 8 were read line-by-line; chunks 4-7 (some December events) are linked but their re-entry rules are marked unverified. See Flagged for Review.",
 },
 "venues": {
   "Venetian": {"poker_room": "Venetian Poker Room", "official": SCHED, "series": "DeepStack Extravaganza IV, Nov 16 - Dec 23, 2026", "series_gtd_line": "More than $3.6 Million in guaranteed tournament prize pools"},
   "Wynn": {"poker_room": "Wynn Poker Room (located in Encore at Wynn Las Vegas — printed in official terms)", "official": "https://wynnpoker.com/", "series": "WPT World Championship, Nov 27 - Dec 21, 2026; daily tournaments year-round"},
 },
 "events": events,
 "satellites": satellites,
 "separate_section_note": "Re-entry / rebuy / add-on events: Wynn dailies (re-entry confirmed), Friday Wynn rebuy event (rebuys+add-on confirmed, re-entry prohibited), all WPT-series events read so far (unlimited re-entry confirmed), Valuetown events 18/58 (subsequent buy-ins printed), all Venetian multi-flight events (bag-players-excluded rule implies re-entry into later flights), all bounty/PKO events (money-for-elimination advantage), satellites, and team events.",
}

with open("data/tournaments.json", "w") as f: json.dump(data, f, indent=1)

# ---------------------------------------------------------------- rate log
rate_log = {
 "meta": {"rule": "Rates are a dated log, never a single value. Each entry: date recorded, property, item, value as printed, official source URL, retrieval method. Room rates are dynamic booking-engine values; when a rate is captured (manually from the official booking page), append a dated entry — do not overwrite old ones.",
          "tax_note": "True nightly cost formula used by the calculator: nightly rate + mandatory resort fee + Clark County room tax. The 13.38% tax rate was provided by the site owner and is NOT yet verified against an official government page — see Flagged for Review."},
 "entries": [
  {"date": "2026-11-16", "property": "The Venetian Resort (incl. Palazzo)", "item": "Mandatory resort fee", "value": "$55 per room per night + tax", "source": FEE, "retrieved": RET_FEE, "method": "Official Venetian resort-fee page"},
  {"date": "2026-11-16", "property": "The Venetian Resort (incl. Palazzo)", "item": "Conditional poker-rate program (not a date quote)", "value": "$119 / $209 conditional poker-rate starts (requires qualifying play); recorded by session 60fb62da — re-verify on the official page before relying", "source": V + "/resort/casino/poker/suite-rates.html", "retrieved": "2026-11-16", "method": "Official Venetian poker suite-rates page (session 60fb62da capture, shared board)"},
  {"date": "2026-11-16", "property": "Treasure Island", "item": "Optional resort fee", "value": "$49.95 per day + tax (optional/opt-in fee) — recorded by session 60fb62da from official TI tower-suite/fee + offer-terms pages; homepage package headlines \"NO RESORT FEE\" (fee is optional)", "source": "https://treasureisland.com/hotel/tower-suite", "retrieved": "2026-11-16", "method": "Official TI pages (session 60fb62da capture, shared board)"},
  {"date": "2026-11-17", "property": "Treasure Island", "item": "Package headline (not a booked rate)", "value": "\"$69* NIGHT + NO RESORT FEE**\" package; \"Always Free Parking\"; footnotes * / ** not visible in fetched extract — confirm on official booking page", "source": TI, "retrieved": RET, "method": "Official TI homepage"},
 ],
}
with open("data/rate-log.json", "w") as f: json.dump(rate_log, f, indent=1)

# ---------------------------------------------------------------- flagged
flagged = {
 "meta": {"updated": RET, "rule": "Irregularities and unverified items are published here with sources. None of these block publication."},
 "items": [
  {"id": "F1", "severity": "important", "title": "No Venetian event is officially single-entry (yet)",
   "detail": "All 37 official DSE IV structure sheets were read line-by-line. None states a maximum number of entries, 'no re-entry', 'freezeout', or any add-on policy. Sheet 8 (Events 18/58) prints \"All subsequent buy in's after the initial buy in will be $200\", implying re-entry is allowed there, and every multi-flight sheet prints \"Any player who bags chips for Day 2 may not play a subsequent flight\", implying re-entry into later flights is otherwise permitted. Per the site rules, no event is labeled confirmed single-entry without explicit wording.",
   "sources": [SHEET_URL(n) for n in range(1, 38)], "action": "Ask the Venetian poker room (or check registration terms) for written single-entry/no-re-entry policy per event before paying non-refundable travel."},
  {"id": "F2", "severity": "important", "title": "All Wynn daily tournaments officially allow re-entry and/or add-ons",
   "detail": "Official structures PDF: Mon-Thu $200 and Nightly $160 print re-entry explicitly ('entry fee, as well as the re-entry fee, is ...'); Sat/Sun $200 allows re-entries + one $100 add-on; Friday $240 is a rebuy/add-on event with unlimited rebuys (re-entry explicitly NOT allowed). None qualifies as a single-entry event.",
   "sources": [DAILY], "action": None},
  {"id": "F3", "severity": "important", "title": "Wynn dailies may be suspended during the WPT series",
   "detail": "Each Wynn daily structure states the event 'may be suspended during Seniors Events, Classic Events, or other Tournament Series.' During the WPT World Championship (Nov 27 - Dec 21), the usual dailies may not run as printed.",
   "sources": [DAILY, WPT_SCHED], "action": "Confirm the daily calendar for your exact dates on wynnpoker.com before booking."},
  {"id": "F4", "severity": "moderate", "title": "Official WPT schedule PDF prints impossible weekday: 'Dec. 18 Wednesday'",
   "detail": "Six schedule rows (incl. $1,100 NLH $1M GTD Day 1A/1B, $800 PLO Double Board Bomb Pot, PLO 6-Max, HORSE, two satellite rows) are printed under 'Dec. 18 Wednesday'. In 2026, December 18 is a Friday and December 16 is the Wednesday. The adjacent rows print 'Dec. 17 Thursday' and 'Dec. 18 Friday' correctly. The dates for the mislabeled rows are ambiguous as printed and are NOT guessed on this site.",
   "sources": [WPT_SCHED], "action": "Verify intended dates with the Wynn poker room before registering."},
  {"id": "F5", "severity": "moderate", "title": "Four Venetian events list no guarantee anywhere",
   "detail": "Events #3, #4, #5 ($200 NLH RaceDay Stack, structure sheet 18) and #6 ($200 NLH 1Day, structure sheet 29) print no guarantee on their sheets, and the schedule page shows none for them. Guarantee fields are left blank and these rows are excluded from ratio ranking.",
   "sources": [SHEET_URL(18), SHEET_URL(29)], "action": None},
  {"id": "F6", "severity": "moderate", "title": "Bounty-event guarantees include bounty money",
   "detail": "Venetian bounty sheets print the guarantee as 'prize pool + total bounties' (e.g., $8,000 for $200 bounties, $15,000 for $300 bounties). The displayed ratio (guarantee / buy-in) therefore mixes bounty and prize-pool money; bounty rows are labeled and ranked separately.",
   "sources": [SHEET_URL(1), SHEET_URL(15), SHEET_URL(11)], "action": None},
  {"id": "F7", "severity": "moderate", "title": "WPT structures PDF chunks 4-7 not yet read line-by-line",
   "detail": "Structures for $1,600 NLH $1M, WPT Prime $5M, Super Gold Million Mystery Bounty $400 $3M, $800 NLH $500K, $1,600 PLO $1M, Seniors, $3,000 NLH $2M, $1,100 NLH $1M, $1,600 Mystery Bounty, high rollers, Ladies, and remaining satellites were not read in this pass (chunks 0-3 of 8 were). Their re-entry rules are marked unverified. Every event whose structure WAS read states 'Unlimited re-entry ... until the start of level 9.'",
   "sources": [WPT_STRUCT], "action": "Read remaining chunks before relying on re-entry policy for those events."},
  {"id": "F8", "severity": "moderate", "title": "Hotel room rates cannot be statically verified",
   "detail": "Strip hotels publish rates through dynamic booking engines (dates/occupancy-specific). No durable official static rate page exists. Room-rate fields are left blank; the site provides official booking links and a dated rate log. Logged dated items so far: Venetian resort fee $55/night + tax (official page, 2026-11-16); Venetian conditional poker-rate program $119/$209 starts (official suite-rates page, session 60fb62da); TI optional resort fee $49.95 + tax (official TI pages, session 60fb62da); TI \"$69 NIGHT + NO RESORT FEE\" package headline (official homepage, 2026-11-17; footnotes not visible in extract).",
   "sources": [FEE, TI, "https://www.venetianlasvegas.com/book", "https://www.venetianlasvegas.com/resort/casino/poker/suite-rates.html", "https://treasureisland.com/hotel/tower-suite"], "action": "Capture itemized checkout totals for exact dates/occupancy from the official booking engine and append to the rate log before paying."},
  {"id": "F9", "severity": "moderate", "title": "13.38% room-tax rate is corroborated but not yet independently re-verified this session",
   "detail": "The calculator applies 13.38% because the site owner specified it. The shared board records that session 60fb62da verified 13.38% Clark County room tax from official Treasure Island offer-terms pages (2026-11-16); no official government page was reachable from this session's build environment to re-confirm.",
   "sources": ["https://treasureisland.com/deals-offers/buy-1-get-1-bogo-free-fine-print"], "action": "Verify the tax line on your actual booking checkout (it is printed there) and correct the constant in app.js if it differs."},
  {"id": "F10", "severity": "moderate", "title": "Walking minutes are mapping estimates — no property publishes official walk times",
   "detail": "Each hotel-venue row links Google Maps directions between the two official properties and shows a straight-line-distance-based estimate. No casino publishes an official walking-time figure. The ≤30-minute walk filter applies to these labeled estimates only.",
   "sources": [], "action": "Open the Maps links and confirm a route you would actually walk, at the time of day you would walk it."},
  {"id": "F11", "severity": "moderate", "title": "Caesars / Bellagio / ARIA official pages unreachable from the build environment",
   "detail": "caesars.com and mgmresorts.com pages did not load during this build (consistent with earlier sessions). Those rooms' tournaments are listed on this site only as pointers to their official pages, without values.",
   "sources": ["https://www.caesars.com/caesars-palace/casino", "https://bellagio.mgmresorts.com/en/casino/poker.html", "https://aria.mgmresorts.com/en/casino/poker.html"], "action": None},
  {"id": "F12", "severity": "info", "title": "No 8:00 AM start exists on any official schedule checked",
   "detail": "The requested 8 AM day-start cannot be met officially: earliest Venetian starts are 9:10 AM (Turbo satellite #46) and 10:10 AM (RaceDay/Seniors/1A flights); Wynn dailies start at 12 PM and WPT morning flights at 10-11 AM. The schedule page builds the earliest possible day honestly instead of inventing an 8 AM event.",
   "sources": [SCHED, WPT_SCHED], "action": None},
  {"id": "F13", "severity": "info", "title": "Official-page typos preserved, not corrected",
   "detail": "Venetian schedule page prints 'No LImit Hold'em' for events 2, 6, 10, 12; Wynn daily poster headline pairs are read from a two-column layout. Site rows use the official text; where layout pairing was ambiguous, the structures PDF (which is definitive) was used.",
   "sources": [SCHED, POSTER], "action": None},
  {"id": "F14", "severity": "info", "title": "Eligibility restrictions apply to some events",
   "detail": "Venetian Seniors events (#24, #32, #49) require age 50+; LIPS Ladies events require female players; the LIPS tag team event requires teams; Wynn/WPT requires 21+ and venue rewards membership (Venetian Rewards card printed on every Venetian sheet; Wynn Rewards membership printed in Wynn terms).",
   "sources": [SHEET_URL(17), SHEET_URL(19), SHEET_URL(32), DAILY], "action": None},
  {"id": "F15", "severity": "info", "title": "Discounted buy-ins exist and change the true entry cost",
   "detail": "Official discounts printed: Venetian Event #59 1A pre-registration $20 off ($580), Event #56 1A/1B pre-registration $40 off ($1,060), PokerAtlas PRO $20 off first entry of Events 18/58 ($180), WPT pre-registration discount footnote (*****), Ladies Championship $11,100 entry with ladies discount. The table shows the standard buy-in; discounts are in each row's notes.",
   "sources": [SHEET_URL(4), SHEET_URL(35), SHEET_URL(8), WPT_SCHED], "action": None},
 ],
}
with open("data/flagged.json", "w") as f: json.dump(flagged, f, indent=1)

print(f"events={len(data['events'])} satellites={len(satellites)}")
