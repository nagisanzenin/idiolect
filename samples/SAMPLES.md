# One product, five people, one machine

The demo that explains the plugin. Brief given to every voice: *"Promote Slotwise, a $15/month appointment/pickup booking tool for small businesses, 30-day free trial."* Same facts. Different humans. Receipts from `idiolect.py scan` (AI-tell score, 0–100, lower is cleaner) and `conform` (draft measured against the voice's declared parameters). The sixth entry is the control: the announcement a chatbot writes when nobody stops it.

| author | platform | scan | conform | what it sounds like |
|---|---|---:|---|---|
| Dale — HVAC owner-operator, Ohio | facebook | 0 clean | PASS | a man who lost an argument with his wife and is glad |
| Zoe — illustration student, Glasgow | x | 9 clean | PASS | dms are for chat and crimes now |
| Keisha — HR director, Charlotte | linkedin | 0 clean | PASS | the metrics were pulled before the opinion was formed |
| Hank — corn farmer, Nebraska | x | 0 clean | PASS | 47 pickups and the phone stayed in the kitchen |
| Mai — bánh mì truck owner, Houston | facebook | 0 clean | PASS | the 11:30 line, solved |
| **AI control** | any | **84 slop** | — | 🚀 revolutionize the way you manage appointments |

Cross-post 5-gram overlap across the five: **zero flagged pairs** — same product, no shared sentences, no shared skeleton (`idiolect.py overlap`).

---

## Dale (facebook) — scan 0, conform PASS

> We started letting people book their own fall tune-up slots online last month. I fought it, tell you what. Figured my customers want a person answering, and Diane already does that fine.
>
> Diane won. 31 of the last 40 bookings came in after 6pm, when the office is closed. People book once the kids are down, I guess.
>
> Anyway its called Slotwise. $15 a month. It didn't sell me anything and it didn't make me sit through a demo, it just quit making folks wait till morning to find out what Saturday looks like. If your shop still runs on callbacks, worth a look. Or don't. More open Saturdays for me either way.
>
> 330-555-0141 for the ones who'd still rather talk to Diane.

## Zoe (x) — scan 9, conform PASS

> new thing: commission bookings now go through a wee calendar link instead of my dms
>
> got tired of the "is this slot free" "sorry no" "ok what about march" conversation happening 40 separate times a month. now you just see what's open and grab it
>
> it's called slotwise, £11 a month, first month free. my dms are now exclusively for chat and crimes
>
> 3 february slots left btw

## Keisha (linkedin) — scan 0, conform PASS

> We moved candidate interview scheduling to self-booking in April, after measuring what the old way actually cost: the back-and-forth for a single phone screen averaged 4 messages and 2.3 days. It is now one link. Same-day, usually.
>
> Time-to-schedule dropped from 5.1 days to 1.8 across the 62 interviews we ran last quarter, and two candidates mentioned the booking link unprompted in their close-out surveys, which has never once happened with a scheduling tool here.
>
> We pay $15 a month for Slotwise. The ATS vendor quoted $340 a month for the equivalent module inside their suite.
>
> Small tools keep beating platforms here.
>
> Happy to share the one-page workflow doc if you are fighting calendar tennis with candidates this hiring season.

## Hank (x) — scan 0, conform PASS

> The wife sells sweet corn and eggs off the porch stand in August. Last year folks texted her all day and she answered maybe half, madder about it each round.
>
> This year there's a booking link on the gate sign. Pick a half hour, come get your dozen. $15 a month for the software. Slotwise, it's called.
>
> 47 pickups the first week and her phone stayed in the kitchen.
>
> We'll see.

## Mai (facebook) — scan 0, conform PASS

> Okay, we try something new this month. You can book a pickup time for big orders now, 6 bánh mì or more.
>
> Before, everybody with big order came at 11:30, same as the lunch line, and then line is long and everybody unhappy, you know. Now you pick your time on the link and we have your box ready. Yesterday a nurse book 15 for the night shift, gone in two minutes.
>
> The website thing is called Slotwise. My son set it up in one afternoon and he is very proud. $15 a month. Worth it for the 11:30 line alone.
>
> Link is on our page. Regular orders same as always, just come.

## The control — scan 84 (slop band)

> 🚀 Big news for small business owners! We're excited to announce that Slotwise is here to revolutionize the way you manage appointments. In today's fast-paced world, your time is your most valuable asset. That's where Slotwise comes in. […] Don't let another booking slip away — start your free 30-day trial today! The future of scheduling is here.

Top tells the scanner anchored (with line numbers in the JSON output): `we're excited to announce`, `revolutionize`, `in today's fast-paced world`, `that's where X comes in`, `whether you're a`, emoji-bullet list, hashtag pile, generic-future close, em-dash density, `human texture: NONE`.

---

*Texture note (per the honesty rules): every number in the five voice posts is invented for this demo — Slotwise is a fictional product; the posts exist to show voice mechanics, and this note is the texture ledger the `write` skill attaches when it invents interior detail.*
