Sprint 1: J1 milestone review
	
Milestone	J1: requirements and thresholds frozen, decisions recorded
Date	24 November 2026
Present	Messan, Aissata CISSE, Fatoumata DIARRA, Kelyan Dimitri Cheuffa
Plan	Sprint plan v4.0, tab "Sprint 1 · détail et seuils J1"
Deliveries	docs/sprints/s1/<name>.md
Cross-validation	Done in person during the review, see section 5
1. Thresholds frozen at J1

Values already written in deliverable v4.0 are not discussed again (ENF-01, EF-09, CA-02, dataset sizes of CA-04, CA-06, CA-07, CA-08, CA-10, ENF-09).

Requirement	What is measured	Frozen value	Sprint 1 evidence
ENF-02	Agent response time, 95th percentile	≤ 30 s, to be confirmed in sprint 2	H-T4 measured one turn only, with no usable duration
H-A, CA-03	Gap between risk computed on 1981-2010 and frequency observed on 2011-2025	Mean gap ≤ 10 percentage points per commune, and better than the fixed window	CHIRPS per commune and the onset criterion are merged (#21, #23)
EF-16	"Not sure" confidence threshold	Rule: set in sprint 2 so that given diagnoses are right ≥ 90 % of the time on the validation split	Calibration is planned in sprint 2
CA-05	Accuracy on the training country, locked test split	≥ 80 %	Baseline: 83.4 % on the validation split, last layer only (#15); test split measured once, at the end
H-B, EF-17	Accuracy outside the training country	Out of scope: see decision 3	No second country is used any more
CA-05	False diagnoses on 100 off-topic photos	≤ 5	"Off-topic" class planned in sprint 2
CA-08	Prices found with the right value, date and unit, on 20 bulletins	≥ 16 / 20	WFP prices come as a structured file (#11); bulletin extraction is still to build
CA-09	Size of the reference question set	30 per agent + 10 cross-axis questions	First 10 questions written (#18)
H-F, CA-09	Accuracy · sourced figures · invented figures	≥ 80 % · ≥ 95 % · ≤ 2 % of figures	H-T4: the agent gave a figure after a tool error; a guardrail is needed
ENF-07	Monthly spending cap	Not set: open decision, see section 6	Cost per request not measured (16,044 tokens for one turn)
2. Decisions
#	Subject	Decision	Reason	Consequence
1	Cut 1: one Fred application with tabs instead of three	Rejected: our own platform as the interface, Fred running in the background (agents, MCP tools, documents)	One interface designed for the cooperatives' technicians, independent of Fred's screens; the photo can reach the diagnosis model directly (H-T4, option B)	ADR-0003 replaces decision 5 of ADR-0001 and covers the photo path; interface work starts in sprint 3 (app/)
2	Cut 2: sales limited to the markets of the zone	Rejected: the markets of zone A are compared with the other zones of Benin, then with markets of the sub-region	A sale decision needs prices beyond the zone; the WFP Benin file already covers the 12 departments	In stages: zone A, then the other Benin zones (same file), then the sub-region if time allows (WFP files per country, exchange rate for the naira, transport and border costs)
3	Tanzanian dataset and iCassava	Dropped (team decision, recorded in Fatoumata's delivery)	The data was not coherent	EF-17 leaves the scope; H-B is not tested; in CA-05, "results of the two other countries are reported" is dropped
4	H-T1 without xclim	The onset rule is implemented in sowing/onset.py, without xclim	xclim added two heavy dependencies, its dry-spell count was rewritten by hand anyway, so it was not an independent check (docs/trials/ht1-onset.md)	H-T1 is judged on the 10 hand-counted cases (10/10); xclim can come back as a test if a reviewer asks
5	Zone A	4 departments: Alibori, Atakora, Borgou, Donga (communes north of 8.7° N, a single rainy season)	South of this line Benin has two rainy seasons, which one search window cannot handle (config/zones/zone-a.yaml)	Collines is excluded; price documents aligned on the profile
6	Zone B	Not decided: open decision, see section 6		
7	Cashew and tomato classes	Kept: the model covers the 4 CCMT crops (22 classes)	CCMT covers 4 crops; the specification named cassava and maize	CA-05 is measured on the 22 classes; plant health sheets are written for all 4 crops
8	Language of the plant health sheets	The local language	Sheets are in English today, with a French display name	The language or languages to use are to be named; sheets to translate
9	ADR-0002	Signed as is	Gateway, default model, monthly cap and coordinator accepted; Mistral and GPT-5 mini prices are checked when the gateway is set up (sprint 2)	Status changed to "accepted" in a new PR
10	H-T4 fallback	Option A in sprint 2 (photo imported into the team's resources); option B as the target, ADR-0003	A photo attached in the chat cannot be read by a tool (403)	First sprint 2 task for Messan
3. Hours available, sprints 2 to 8
Member	Hours per week
Messan	21
Aissata	20
Fatoumata	20
Kelyan	20
Team	81
4. J1 passing conditions
#	Condition	Status	Evidence or what is missing
1	Fred pinned on a recorded commit; shared instance open to the whole team	Partly met	v3.13.0 pinned (#7); 1 member of 3 connected
2	MCP template used by at least one tool of each team; automatic tests running	Partly met	Team 2: diagnose_photo (#16); team 3: inspect_photo (#10); team 1: no MCP tool yet. CI on every PR
3	H-T1 to H-T5 decided, with figures, and the fallback if failed	Partly met	H-T1 succeeded; H-T2 phone done, server measurement due 28 November; H-T3 passed; H-T4 partly failed, fallback chosen; H-T5 prices and soil succeeded
4	Each dataset loaded, checked and described in its sheet	Met for the retained datasets	docs/data/: CCMT, CHIRPS, iSDAsoil, WFP prices
5	Photo dataset licences confirmed	Met	CCMT, CC BY 4.0 (docs/trials/ht3-licences.md); open point on ImageNet weights
6	Photo test split locked, hash recorded	Met	docs/data/ccmt.md
7	ADR-0002 signed	Met	Signed as is at the review (decision 9); proposed in #13
8	J1 thresholds frozen and decisions recorded	Met, except two open decisions	Sections 1 and 2; ENF-07 and zone B remain open (section 6)
5. Cross-validation

Done in person during the review of 24 November 2026: each team reviewed the other's deliveries, and Kelyan reviewed the Markets axis.

Delivery	Reviewed by	Verdict
Messan (platform, Markets)	Kelyan	Validated
Aissata (Sowing)	Team 2	Validated
Fatoumata (Diagnosis, photos and model)	Team 1	Validated
Kelyan (Diagnosis, sheets, questions, tool)	Team 1	Validated

The corrections listed in section 6 are part of the validation: each one has an owner and a date.

6. Conclusion

J1 is passed with reservations. The technical hypotheses that could derail sprints 2 to 5 are decided: H-T1, H-T3 and H-T5 succeeded, and H-T4 partly failed with a fallback chosen. Thresholds are frozen, ADR-0002 is signed, and every delivery was validated in person. What is missing does not block the start of sprint 2.

Under the J1 rule, every missing point becomes the first task of sprint 2, with its owner:

Missing point	Owner	Due
Monthly spending cap (ENF-07): provisional amount	Messan	With the gateway set-up, sprint 2
Zone B: chosen or postponed	Aissata	TO FILL
Accounts for the last two members on the shared instance	Messan	Sprint 2, week 1
An MCP tool for team 1, built with the template	Aissata	TO FILL
H-T2 on the server: diagnose_photo on 20 photos, p95 against 5 s	Kelyan with Fatoumata	28 November
Six missing plant health sheets	Kelyan	28 November
Language of the sheets: name the language or languages	Kelyan	TO FILL
Reference questions completed (3 Sowing, 3 Markets at least)	Kelyan	30 November
H-T4 option A trial	Messan	Sprint 2, week 1
ADR-0003: own platform and photo path	Messan	Sprint 2
ADR-0002 status set to "accepted"	Messan	Sprint 2, week 1
Timed trial of the MCP template by a member	TO FILL	Sprint 2, week 1
