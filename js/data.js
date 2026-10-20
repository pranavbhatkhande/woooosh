export const profile = {
  prepared: "Prepared for Pranav Bhatkhande",
  date: "October 20, 2026",
  line: "36 years old. Goals: lose 5–10% of body weight, get stronger, substantially improve metabolic and vascular health. Budget: 4–5 h/week of exercise, 80–95% adherence, no prescription drugs, sensible supplements. Sex, weight, and medical history were unknown when this was written, so targets are per kg of body weight or as % changes.",
};

export const bigIdea =
  "For a 36-year-old, “metabolism” is mostly about how much muscle you carry, how fit your heart and lungs are, how well your muscles handle glucose, and how much you move. It is not about speeding up a sluggish engine. Your RMR is not falling with age yet: it is stable from 20 to 60 [1]. Lift heavy, do some genuinely hard cardio, walk a lot, eat in a modest deficit with plenty of protein, and protect your sleep. Everything else is a rounding error.";

export const outcome =
  "Realistic 12-week outcome at about 85% adherence: body weight down ~5–8% (that is 0.5–0.7%/wk), waist noticeably smaller, main lifts up meaningfully, VO2max up roughly 5 mL/kg/min (about 1.5 METs, the average trial gain), resting BP a few mmHg lower, and better insulin sensitivity. The 10% end of the goal is usually a 16–24-week project.";

export const grades =
  "Evidence: Strong = several meta-analyses/RCTs or a position stand agree. Moderate = RCTs with some inconsistency, or strong mechanism plus decent trials. Weak/emerging = small or short trials, or mostly observational data. Anecdotal = practitioner experience, labeled as such. Impact: High / Medium / Low = expected effect on your goals at realistic adherence.";

export const levers = [
  { n: 1, name: "Modest calorie deficit", target: "~300–500 kcal/day below maintenance; lose ~0.5–0.7% of body weight per week", evidence: "Strong", cites: "9, 30", impact: "High" },
  { n: 2, name: "Progressive resistance training", target: "Every major muscle 2×/wk, ~10+ hard sets per muscle per week, RPE 7–9", evidence: "Strong", cites: "10, 11, 16", impact: "High" },
  { n: 3, name: "High protein", target: "1.6–2.2 g/kg/day in 3–5 feedings of ~0.4 g/kg", evidence: "Strong", cites: "12, 13, 14", impact: "High" },
  { n: 4, name: "Hard cardio 1–2×/wk", target: "4×4-min intervals at 90–95% HRmax, or sprint intervals", evidence: "Strong", cites: "17, 18, 19, 20", impact: "High (VO2max, insulin sensitivity)" },
  { n: 5, name: "Sleep ≥7 h, regular", target: "Same wake time ±30–60 min, 7.5–8.5 h in bed", evidence: "Strong/Moderate", cites: "33, 34, 35, 36", impact: "High (lean mass retention, appetite)" },
  { n: 6, name: "Daily steps / NEAT", target: "8,000–10,000 steps/day", evidence: "Moderate", cites: "24, 7", impact: "Medium-High" },
  { n: 7, name: "Whole-food, Mediterranean-style diet", target: "≥30 g fiber; mostly minimally processed foods; plenty of veg, legumes, olive oil, nuts, fish", evidence: "Strong", cites: "25, 26, 27", impact: "Medium-High" },
  { n: 8, name: "Blood pressure levers", target: "Less sodium, more potassium, nitrate-rich greens daily, isometric wall sits 3×/wk", evidence: "Strong/Moderate", cites: "21, 22, 28, 29, 38", impact: "Medium (vascular)" },
  { n: 9, name: "Creatine monohydrate", target: "3–5 g/day, every day", evidence: "Strong", cites: "39", impact: "Medium (strength, lean mass)" },
  { n: 10, name: "Alcohol low/none", target: "≤3–4 drinks/wk, none within ~3 h of bed", evidence: "Moderate", cites: "31, 37", impact: "Medium" },
];

export const compliance = [
  { tier: "95% (non-negotiable)", behaviors: "Daily protein target. Weekly average calories in range. Lifting sessions. Consistent wake time.", why: "These drive fat loss, muscle retention, and strength. Missing them costs the most." },
  { tier: "85–90%", behaviors: "Steps target. ≥30 g fiber / veg at most meals. Weekly interval session. Alcohol limits. Bedtime window.", why: "Large but forgiving. A missed day here and there is fine." },
  { tier: "80%", behaviors: "Nitrate greens daily, cocoa, specific meal timing, “perfect” food choices, extra supplements.", why: "Small effects. Do them when it’s easy." },
];

export const complianceNote =
  "Non-negotiables (aim for 95%): hit your protein target, get your lifting sessions done, keep a steady wake time, and keep the weekly calorie average in range. Flexible (80–90%): step count, the exact interval session, veg/fiber, alcohol limits. Optional (≥80% is plenty): beets/greens and cocoa, meal timing, supplements beyond creatine.";

export const complianceRule =
  "A 90% week is ~2–3 “off-plan” meals out of ~21. Keep protein high even in those meals, and don’t try to compensate the next day. Just resume.";

export const doctorIntro =
  "This plan is safe for most healthy adults. Check in with a clinician before starting, or get advice along the way, if any of these apply:";

export const doctorItems = [
  "You get chest pain or pressure, unusual shortness of breath, fainting, or palpitations on exertion. Also check in if you have known heart, kidney, or liver disease, or a family history of sudden cardiac death at a young age. Get cleared before doing max-effort intervals.",
  "Home BP is consistently ≥130/80 (stage 1 per ACC/AHA [38]), and especially if it is ≥160/100. Also if fasting glucose is ≥100 mg/dL or HbA1c ≥5.7% (prediabetes range per ADA 2026 [43]).",
  "You take BP medication, nitrates, PDE5 inhibitors, blood thinners, or ACE inhibitors/ARBs/potassium-sparing diuretics. Nitrate, citrulline, high-dose omega-3, and potassium-rich diets or supplements can add to these drugs’ effects.",
  "You have kidney disease or reduced kidney function. That affects protein, creatine, and potassium choices. Note that creatine raises serum creatinine a bit, so tell your lab you take it.",
  "You loudly snore or gasp in your sleep, or feel very sleepy in the daytime despite 7+ h in bed. That could be sleep apnea, which can undermine all of this.",
  "You have a history of disordered eating, or tracking makes you anxious. Use the plate method instead of logging numbers.",
];

export const personalize = [
  ["Starting weight & waist", "Every target scales with it: protein g/kg, the weekly loss rate, and the calorie estimate.", "Take a 7-day average of morning weights. Measure the waist at the navel, relaxed, after a normal exhale."],
  ["Sex", "Calorie needs, comfortable loads, iron/ferritin, and cycle effects on weekly weight noise.", "Women: compare the same cycle phase month to month and expect more water swings. Plan targets don’t change."],
  ["Body fat / BMI category", "If you have a lot of fat to lose, use protein based on goal weight and a deficit at the top of the range. If you’re already lean, use the low end.", "A rough estimate is fine (photos + waist-to-height ratio)."],
  ["Training age", "Beginners recomp easily. Trained lifters progress more slowly.", "Use the beginner or experienced load guidance in the training section."],
  ["Baseline labs & BP", "Decides which lever matters most (glucose vs lipids vs BP).", "See the labs table. Take home BP readings for 7 days (AM + PM)."],
  ["Diet history & schedule", "Sets your calorie baseline and which template fits.", "Log normally for 7–14 days before cutting anything."],
  ["Injuries, equipment", "Exercise choice.", "Use the substitution column in the session tables."],
];

export const metabolismIntro =
  "Total daily energy expenditure (TDEE) = resting metabolic rate (RMR) + thermic effect of food (TEF) + exercise + non-exercise activity (NEAT). “Metabolic health” is a separate idea: how well you handle glucose and fat, keep BP and blood lipids in range, and deliver oxygen to tissues. That depends on insulin sensitivity, mitochondrial capacity, VO2max, and muscle mass. You can move the second set of variables far more than the first.";

export const metabolism = [
  ["RMR", "Energy to keep you alive at rest; the largest share of TDEE in most people.", "Mostly lean mass (organs + muscle). Fat-free-mass-adjusted energy expenditure is stable from age 20 to 60 [1].", "Small. Muscle burns ~13 kcal/kg/day at rest vs ~4.5 for fat [2], so +2 kg of muscle ≈ +25 kcal/day. Worth having, but not a “metabolism boost”.", "Strong"],
  ["Adaptive thermogenesis", "RMR falling more than predicted during weight loss.", "Size of the deficit, how much weight you lose, how lean you are.", "Modest. ~50–60 kcal/day after a 12-kg loss, and it faded at 1–2 years [3]. The Biggest Loser’s −499 kcal/day [4] came from extreme loss with extreme exercise and doesn’t apply to a 5–10% cut.", "Moderate"],
  ["TEF", "Energy used to digest food, ~10% of intake (range 5–15%), higher for protein [5].", "More protein, more whole foods.", "Tens of kcal/day. Protein’s real advantage is fullness and protecting muscle.", "Strong"],
  ["Exercise energy", "Calories burned in planned sessions.", "Volume × intensity.", "At 4–5 h/wk, often ~1,500–3,000 kcal/wk depending on body size and intensity (estimate). Exercise alone gives modest weight loss; its value is fitness, muscle, and keeping weight off [6].", "Strong"],
  ["NEAT", "Walking, fidgeting, chores, standing.", "Steps, active commuting, standing breaks; tends to drop unconsciously when dieting.", "Can vary by hundreds of kcal/day between people. In overfeeding studies it explained ~2/3 of the extra energy burned [7]. Track steps so NEAT doesn’t quietly fall.", "Moderate"],
  ["Insulin sensitivity", "How well muscle, liver, and fat respond to insulin.", "Weight loss (5% already helps [8]), exercise (HIIT and resistance [19, 52]), sleep [33].", "Large and fast. Often measurable within weeks.", "Strong"],
  ["Mitochondrial capacity", "Muscle’s ability to burn fuel aerobically.", "Training volume plus intensity; higher intensities work well when time is limited [20, 23].", "Meaningful within 6–12 weeks.", "Strong (mechanistic RCTs)"],
  ["VO2max", "Peak aerobic capacity; one of the strongest predictors of mortality [15].", "Intervals plus aerobic volume.", "~+5 mL/kg/min on average in 6–12-week programs [18]. Bigger if you start unfit.", "Strong"],
  ["Muscle mass", "Glucose “sink”, strength, healthy aging.", "Resistance training + protein + no huge deficit.", "Beginners can gain lean mass while losing fat (recomp) [9, 14]. Trained people mostly maintain it.", "Strong"],
];

export const myths = [
  ["“Metabolism-boosting” foods (green tea, chili, celery, apple cider vinegar)", "Effects are trivial. Green tea’s effect on weight loss is very small, not significant, and not clinically meaningful [44].", "Strong (against)"],
  ["“Metabolism crashes after 30”", "No. Size-adjusted energy expenditure is flat from 20 to 60 [1]. Weight gain in midlife is mostly about behavior and lost muscle.", "Strong"],
  ["“Starvation mode” stops fat loss", "Adaptive thermogenesis is real but small for moderate diets (~50 kcal/day) [3]. Stalls are usually intake creeping up or NEAT dropping.", "Moderate"],
  ["Breakfast “kick-starts” metabolism / eat 6 small meals", "No RMR effect. In an RCT, breakfast didn’t change RMR or body mass [45]. Meal frequency is a matter of preference.", "Moderate-Strong"],
  ["16:8 fasting windows are special", "In RCTs, time-restricted eating without counting calories gave no extra weight loss vs 3 meals/day (TREAT [46]), and TRE + calorie restriction ≈ calorie restriction alone over 12 months [47]. It’s fine as an adherence tool if it suits you.", "Strong"],
  ["Zone 2 is the key to mitochondria", "Overhyped for the general public. A 2025 review found no evidence that Zone 2 beats higher intensities for mitochondrial or fat-oxidation gains, especially with limited time [23]. Easy cardio is still useful for volume, recovery, and steps.", "Moderate"],
  ["NEAT doesn’t matter", "False in the other direction. NEAT differs a lot between people and drops during dieting [7]. Steps are your cheapest way to protect the deficit.", "Moderate"],
  ["Cold plunges burn fat / boost metabolism", "Short-term physiological changes are real, but health and fat-loss benefits are unproven. Studies are small and confounded [48]. Cold water right after lifting blunted muscle and strength gains [49].", "Weak (benefit); Moderate (harm to gains)"],
  ["Sauna is a metabolic or longevity hack", "Observational Finnish data link frequent sauna use with lower CV mortality [50], but causation is unproven. Fine if you enjoy it, and it may help relaxation and BP. Don’t count it as exercise.", "Weak/observational"],
];

export const principles = [
  ["Resistance train each major muscle ≥2×/week", "Full-body 2–3×/wk", "Strong", "High", "Schoenfeld 2016 frequency MA [10]; PAG 2018 [16]"],
  ["Weekly volume ≥10 hard sets per muscle", "8–12 sets fits 4–5 h/wk; start at ~6–8", "Strong (dose-response)", "High", "Schoenfeld 2017 volume MA [11]"],
  ["Train close to failure", "RPE 7–9 (1–3 reps in reserve) on most sets; the last set of isolation moves can reach RPE 9–10", "Moderate", "High", "Practitioner consensus, consistent with the volume/effort literature"],
  ["Progressive overload", "Double progression: add reps, then load (+2.5–5%)", "Strong (principle) / Anecdotal (exact scheme)", "High", "ACSM/NSCA principles; practitioner"],
  ["Rep ranges", "Mostly 5–12 on compound lifts, 8–15 on accessories. Strength gains favor heavier sets, but muscle grows across a wide rep range.", "Moderate", "Medium", "Practitioner + RCT literature"],
  ["Intervals for VO2max", "4×4 min at 90–95% HRmax, 3 min easy between [17]. Intervals beat continuous training by ~1.2 mL/kg/min on average [18].", "Strong", "High", "Helgerud 2007 [17]; Milanović 2015 [18]"],
  ["Sprint intervals when short on time", "3×20 s all-out within a 10-min session, 3×/wk ≈ 50 min moderate cardio for insulin sensitivity, VO2peak, and mitochondria [20]", "Moderate (small RCT, sedentary men)", "Medium-High", "Gillen 2016 [20]"],
  ["HIIT for insulin sensitivity", "Lowers insulin resistance vs control (SMD −0.49) and vs continuous training [19]", "Strong", "High", "Jelleyman 2015 [19]; ACSM T2D 2022 [52]"],
  ["Isometric wall sits for BP", "4×2 min, 1–4 min rest, 3×/wk. Isometric training cut BP by −8.2/−4.0 mmHg, the largest drop of any exercise type [21].", "Strong (MA of RCTs)", "Medium-High (vascular)", "Edwards 2023 [21]; Cornelissen 2013 [22]"],
  ["Combined aerobic + resistance for BP", "−6.0/−2.5 mmHg [21]", "Strong", "Medium", "Edwards 2023 [21]"],
  ["Exercise improves endothelial function", "Flow-mediated dilation +2–3 percentage points with aerobic, resistance, or combined training; higher aerobic intensity → bigger gain [42]", "Strong", "Medium-High", "Ashor 2015 [42]"],
  ["Daily steps", "Mortality risk keeps falling up to ~8,000–10,000/day in adults <60 [24]", "Moderate (cohort data)", "Medium-High", "Paluch 2022 [24]"],
];

export const vascularNote =
  "Why vascular health responds so well: each session raises blood flow and shear stress on the artery wall. Over time that increases nitric-oxide production and improves endothelial function [42]. Regular training lowers resting BP [21, 22], and weight loss plus a lower-sodium, higher-potassium diet adds to the effect [28, 29]. Rhythmic aerobic work, lifting, and isometrics each lower BP, so the plan uses all three.";

export const templates = [
  {
    id: "A",
    name: "3 Lift + 1 Interval",
    role: "Default",
    time: "~4.3–4.8 h",
    blurb: "Full-body lifting three days, one 4×4 interval day, walks around them.",
    days: [
      ["Mon", "Full-body A (squat focus) + wall-sit finisher", "55–65′", "Finisher: 4×2 min wall sit, 2 min rest. Pick a depth that feels like ~RPE 7–8 by the last 30 s."],
      ["Tue", "Walk / NEAT", "—", "Steps target. Optional 20′ easy cardio."],
      ["Wed", "Full-body B (hinge focus) + wall sits", "55–65′", ""],
      ["Thu", "Walk / NEAT", "—", ""],
      ["Fri", "Full-body C (volume/accessories) + wall sits", "55–65′", ""],
      ["Sat", "4×4 intervals (bike, rower, incline treadmill, or hill run)", "35–40′", "Warm up 10′, 4×4′ at 90–95% HRmax (RPE 8–9, can only say a few words), 3′ easy between, cool down 5′."],
      ["Sun", "Long walk/hike or rest", "45–90′ easy", "Counts toward steps, not the 4–5 h."],
    ],
  },
  {
    id: "B",
    name: "2 Full-body + 2 Conditioning",
    role: "More conditioning",
    time: "~4.3 h",
    blurb: "Two longer lifts, one interval day, one steady cardio day, walks on the other days.",
    days: [
      ["Mon", "Full-body A+ (squat + press + pull + hinge accessory)", "65–75′", "Use the Lift A table plus 1 set each from B’s hinge and pull."],
      ["Tue", "4×4 intervals", "35–40′", "As in Template A."],
      ["Wed", "Walk / steps", "—", ""],
      ["Thu", "Full-body B+ (hinge + vertical press/pull + single-leg)", "65–75′", "Use the Lift B table plus 1 extra set on the squat pattern."],
      ["Fri", "Walk / steps", "—", ""],
      ["Sat", "Steady cardio + wall sits", "50′", "40–45′ at moderate-to-vigorous effort (RPE 5–6; conversational but working) + 4×2′ wall sits. Zone 2-to-3 work is fine here. It adds volume and recovery, but don’t make it your only cardio [23]."],
      ["Sun", "Walk / steps", "—", ""],
    ],
  },
  {
    id: "C",
    name: "Minimal effective dose",
    role: "Busy or travel week",
    time: "~1.7–2 h",
    blurb: "Two short lifts and one sprint session. Strength and muscle hold up well on short maintenance doses (practitioner/anecdotal).",
    days: [
      ["Day 1", "Lift A-short: squat 3×, bench 3×, row 3×, RDL 2×", "45′", "Keep load and intensity, cut volume ~1/3."],
      ["Day 2", "Sprint intervals", "10–12′", "2′ easy, 3×20 s all-out bike (or hill sprints), 2′ easy between, 3′ cool down. Gillen protocol [20]. Hotel-gym friendly."],
      ["Day 3", "Lift B-short: deadlift 3×, OHP 3×, pulldown/pull-up 3×, split squat 2× + wall sits", "45′", ""],
      ["Daily", "Steps", "—", "≥7,000–8,000. The cheapest lever in busy weeks."],
    ],
  },
];

export const sessionIntro =
  "Warm up for 5 min, then do 2–3 ramp-up sets on the first lift. RPE = rating of perceived exertion on a 1–10 scale; RPE 8 ≈ 2 reps left in the tank. Main lifts rest 2–3 min, accessories 60–90 s. Supersets of non-competing exercises save time.";

export const sessions = {
  A: [
    ["Back squat", "3–4 × 5–8", "7–8", "Goblet squat, front squat, hack squat, leg press"],
    ["Bench press", "3–4 × 6–10", "7–8", "DB bench, push-up (add load/tempo), machine press"],
    ["One-arm DB row (superset with bench)", "3 × 8–12/side", "8", "Chest-supported row, cable row, inverted row"],
    ["Romanian deadlift", "3 × 8–10", "7–8", "DB RDL, hip hinge on cable, back extension"],
    ["Cable face pull or lateral raise", "2–3 × 12–15", "8–9", "Band pull-apart, rear-delt fly"],
    ["Dead bug / plank", "2 × 30–45 s", "—", "Pallof press, ab wheel"],
    ["Wall-sit finisher", "4 × 2 min, 2′ rest", "~7–8 by end", "Isometric leg extension or handgrip (4×2′ at 30% max)"],
  ],
  B: [
    ["Trap-bar deadlift", "3–4 × 4–6", "7–8", "Conventional/sumo DL, KB deadlift, rack pull"],
    ["Standing overhead press", "3 × 6–10", "7–8", "Seated DB press, landmine press, machine shoulder press"],
    ["Pull-up / lat pulldown", "3 × 6–10", "8", "Assisted pull-up, neutral-grip pulldown, band pull-down"],
    ["Bulgarian split squat", "3 × 8–10/side", "8", "Reverse lunge, step-up, single-leg press"],
    ["Incline DB press", "2 × 8–12", "8–9", "Incline machine, deficit push-up"],
    ["Lying/seated hamstring curl", "2 × 10–15", "8–9", "Nordic (eccentric), swiss-ball curl"],
    ["Farmer carry", "3 × 30–40 m", "—", "Suitcase carry, KB rack carry"],
  ],
  C: [
    ["Leg press or front squat", "3 × 8–12", "8", "Hack squat, goblet squat, belt squat"],
    ["Chin-up (weighted if able)", "3 × 6–10", "8", "Pulldown, assisted chin, ring row"],
    ["Incline barbell or DB bench", "3 × 8–10", "8", "Machine incline, landmine press"],
    ["Hip thrust", "3 × 8–12", "8", "Glute bridge, 45° back extension, cable pull-through"],
    ["Seated cable row", "3 × 10–12", "8–9", "Machine row, DB row"],
    ["Standing calf raise", "2–3 × 10–15", "9", "Seated calf, single-leg DB calf raise"],
    ["Biceps curl + triceps pushdown superset", "2–3 × 10–15", "9", "Any curl/extension variant"],
    ["Pallof press / side plank", "2 × 10/side or 30 s", "—", "Suitcase carry"],
  ],
};

export const sessionMeta = {
  A: { title: "Lift A", focus: "Squat / horizontal press / row" },
  B: { title: "Lift B", focus: "Hinge / vertical press / pull / single-leg" },
  C: { title: "Lift C", focus: "Volume / accessories" },
};

export const volumeNote =
  "Weekly hard sets in Template A (approx.): quads ~10–12, glutes/hamstrings ~10–12, chest ~9–10, back ~12–15, shoulders ~8–9 direct + pressing, arms ~5–6 direct + compounds. That sits at the evidence-backed ≥10-set mark for most muscles [11] without blowing the time budget. In Template B, add 1 set to each main lift.";

export const phases = [
  { weeks: "0 (baseline)", name: "Test & set up", lifting: "Find working weights: 2 sets that feel like RPE 7. Log everything.", intervals: "10′ easy + 2×4′ hard to learn the effort.", steps: "Measure current average." },
  { weeks: "1–2", name: "Learn & groove", lifting: "3 sets on main lifts @ RPE 6–7. Perfect technique.", intervals: "4×4: do 3×3′ @ RPE 8.", steps: "+1,000/day above baseline." },
  { weeks: "3–5", name: "Accumulate", lifting: "Add a 4th set to the main lifts (or Template B extras). RPE 7–8. Double progression each week.", intervals: "4×4′ @ RPE 8–9.", steps: "8,000+." },
  { weeks: "6", name: "Deload", lifting: "Cut sets by ~40–50%, keep the load, RPE ≤6.", intervals: "2×4′ or easy 30′.", steps: "Keep." },
  { weeks: "7–10", name: "Intensify", lifting: "Main lifts move to the lower rep range (4–6 / 6–8) @ RPE 8–9. Accessories stay at 8–15 reps.", intervals: "4×4′; optional 5th rep in wk 9–10. Template C weeks: SIT 3×20 s → 4×20 s.", steps: "8,000–10,000." },
  { weeks: "11", name: "Test week", lifting: "Work up to a 3–5RM (or rep-max at a fixed load) on 2–3 main lifts @ RPE 9. Retest the wall-sit hold.", intervals: "Repeat a benchmark (e.g., 4×4 distance/watts, or 2-km row time).", steps: "Keep." },
  { weeks: "12", name: "Deload + re-measure", lifting: "Light week. Repeat baseline measurements and labs.", intervals: "Easy.", steps: "Keep." },
];

export const progressionRule =
  "Each exercise has a rep range (e.g., 6–10). Once you hit the top of the range on all sets at ≤ the target RPE, add load: +2.5–5 kg on lower-body lifts, +1–2.5 kg on upper-body lifts, or one dumbbell step. If reps fall below the range two sessions in a row, cut the load 5–10%. Deloads every ~5–6 weeks are practitioner standard (anecdotal/moderate). During a calorie deficit they’re cheap insurance against fatigue and joint aches. After week 12, either start another 12-week block or run a 2–4-week maintenance-calorie phase (see diet breaks).";

export const heartRateNote =
  "HRmax estimates from age formulas are rough. Use RPE as the main guide: 4×4 work should feel like RPE 8–9 (you can say only a few words), recoveries like RPE 3–4. Your interval benchmark (watts, pace, distance) is the best VO2max proxy you have without a lab test.";

export const nutritionTargets = [
  ["Calorie deficit", "~300–500 kcal/day (≈15–20% below maintenance), aiming for 0.5–0.7% of body weight/week.", "Strong", "High", "Deficits >~500 kcal/day stop lean-mass gains [9]. Slow loss (0.7%/wk) beat fast loss (1.4%/wk) for lean mass and strength in athletes [30]. Larger bodies can sit at the high end."],
  ["Find maintenance first", "Log your usual intake for 7–14 days and compare with the weight trend. Or use a calculator estimate and adjust.", "Anecdotal (method)", "High", "Predictive equations can be off by hundreds of kcal. Your scale trend is the real calibration."],
  ["Protein", "1.6–2.2 g/kg/day. If you carry a lot of fat, base it on goal weight. Spread over 3–5 meals of ~0.4 g/kg.", "Strong", "High", "Morton 2018: benefit plateaus ~1.6 g/kg (CI up to 2.2) [12]. ISSN: 1.4–2.0 g/kg, and higher (2.3–3.1 g/kg) may help in a deficit [13]. 2.4 vs 1.2 g/kg in a deficit: +1.2 kg lean, −4.8 vs −3.5 kg fat [14]. Per-meal ~0.4 g/kg [32]."],
  ["Fiber", "≥30 g/day (benefit is greatest at 25–29 g, with more benefit above that).", "Strong (mostly cohort + RCT risk-factor data)", "Medium-High", "Reynolds 2019: 15–30% lower risk of CV death, T2D, and more [26]."],
  ["Minimally processed foods", "~80–90% of calories from whole or minimally processed foods.", "Moderate-Strong", "High (appetite)", "On the ultra-processed diet people ate ~500 kcal/day more and gained 0.9 kg in 2 weeks, vs losing 0.9 kg on the unprocessed diet [27]."],
  ["Dietary pattern", "Mediterranean-style (olive oil, nuts, legumes, fish, veg, fruit, whole grains). DASH is a fine alternative for BP.", "Strong", "High (CV)", "PREDIMED: ~30% fewer major CV events (HR 0.69–0.72) [25]."],
  ["Nitrate-rich vegetables", "1–2 servings/day of arugula, spinach, beets, celery, lettuce, bok choy. Skip mouthwash right after meals (it can kill the mouth bacteria that convert nitrate; mechanistic).", "Moderate", "Medium (vascular)", "Nitrate/beet juice: SBP −4.4 mmHg in short trials [40]."],
  ["Cocoa flavanols", "Optional: ~10–20 g unsweetened natural (non-Dutched) cocoa, or a standardized extract (~500 mg flavanols in COSMOS).", "Moderate (BP) / Weak (hard outcomes)", "Low-Medium", "Cochrane: BP −1.8 mmHg [41]. COSMOS: primary CV outcome not significant; CV death −27% (secondary) [51]. Chocolate bars bring sugar and calories."],
  ["Sodium", "~1,500–2,300 mg/day. Mostly cut restaurant and packaged foods.", "Strong", "Medium-High (BP)", "−4.4 g/day salt → −4.2/−2.1 mmHg (more if hypertensive) [28]. ACC/AHA advise sodium reduction [38]."],
  ["Potassium", "From food: 3,500–5,000 mg/day (beans, potatoes, yogurt, bananas, leafy greens, squash). Not pills unless your doctor approves.", "Strong", "Medium (BP)", "−3.5/−2.0 mmHg; larger effects in hypertension [29]. See kidney/medication caution."],
  ["Alcohol", "Ideally ≤3–4 drinks/week, ≤2 per occasion, none within ~3 h of bed.", "Moderate", "Medium", "No mortality benefit at low intake vs never-drinkers [31]. It fragments second-half sleep [37], adds calories, and tends to bring loose eating with it."],
  ["Meal timing / frequency", "Whatever helps you stick to the plan. Get protein at each meal and have a protein-containing meal within a few hours around training.", "Strong (that timing matters little)", "Low", "TREAT [46], Liu 2022 [47], Bath Breakfast [45]."],
  ["Diet breaks / refeeds", "Optional: 1–2 weeks at maintenance every 6–12 weeks, or between 12-wk blocks.", "Weak-Moderate", "Low-Medium (adherence)", "MATADOR (men with obesity): 2-wk on/2-wk off → more fat loss and less RMR drop [53]. Single trial. Treat as a psychological and adherence tool."],
];

export const plate = [
  ["Protein (anchor)", "1–2 palms (≈25–50 g protein)", "Chicken, turkey, lean beef, fish/salmon, eggs + egg whites, Greek yogurt/skyr, cottage cheese, tofu/tempeh, lentils + whey"],
  ["Vegetables (½ plate)", "2 fists, at least 1 leafy/nitrate-rich per day", "Arugula, spinach, mixed greens, beets, broccoli, peppers, zucchini, frozen veg mixes"],
  ["Quality carbs (¼ plate)", "1–2 cupped hands. More on training days, fewer on rest days if that suits you.", "Potatoes, oats, rice, quinoa, beans/lentils, whole-grain bread, fruit"],
  ["Fats", "1–2 thumbs", "Extra-virgin olive oil, nuts, seeds, avocado, olives"],
];

export const plateNote =
  "Men or bigger/more active people usually need the upper end of each portion. Women or smaller people need the lower end. Adjust by the weight trend, not by feel.";

export const meals = [
  ["Breakfast", "Greek yogurt + berries + oats + walnuts, or a 3-egg + egg-white veggie omelet + toast, or overnight oats with whey", "~30–40 g"],
  ["Lunch", "Big “nitrate salad”: arugula/spinach, beets, chickpeas, chicken or tuna, olive oil + lemon, or a grain bowl, or leftovers", "~35–45 g"],
  ["Snack / post-workout", "Whey or soy shake + fruit, or cottage cheese + fruit, or skyr", "~25–30 g"],
  ["Dinner", "Salmon/lean meat/tofu + potato or rice + 2 fists veg + olive oil", "~35–50 g"],
  ["Optional evening", "Casein/Greek yogurt, or hot cocoa made with unsweetened cocoa + milk", "~15–25 g"],
];

export const weeklyFood =
  "2–3 fish meals (≥1 oily fish), 3+ legume servings, daily leafy greens, 2–3 fruits/day, nuts most days. 1–2 “free” meals/week built into the weekly calorie average.";

export const sampleDay = {
  intro: "Illustration for an ~80 kg person. Scale portions to your weight. Estimates — check your own labels.",
  rows: [
    ["Breakfast", "250 g plain Greek yogurt, 40 g oats, 1 cup berries, 15 g walnuts, coffee", "~28 g"],
    ["Lunch", "Large arugula + spinach salad, 1 roasted beet, ½ cup chickpeas, 150 g grilled chicken, 1 tbsp olive oil", "~55 g"],
    ["Post-training", "1 scoop whey in milk + banana", "~32 g"],
    ["Dinner", "170 g salmon, 250 g potatoes, broccoli + peppers, side salad", "~42 g"],
    ["Evening", "Hot cocoa (10 g natural cocoa, milk)", "~8 g"],
  ],
  total: "≈ 2,100–2,300 kcal; ≈ 165 g protein (≈2.0 g/kg); fiber ≈ 35–40 g.",
};

export const grocery = [
  ["Proteins", "Chicken breast/thighs, lean ground beef/turkey, salmon/sardines/trout, canned tuna/salmon, eggs + liquid egg whites, Greek yogurt/skyr, cottage cheese, tofu/tempeh/edamame, lentils, whey or soy protein."],
  ["Vegetables", "Arugula, spinach, beets (fresh or pre-cooked vacuum-packed), celery, romaine, bok choy — those are the nitrate-rich ones — plus broccoli, peppers, carrots, frozen veg mixes, tomatoes, onions/garlic."],
  ["Carbs", "Oats, potatoes/sweet potatoes, rice/quinoa, whole-grain bread/wraps, canned beans/chickpeas, fruit (berries, bananas, citrus, apples, kiwi)."],
  ["Fats and extras", "Extra-virgin olive oil, walnuts/almonds, chia/flax, avocado, olives, unsweetened natural cocoa, herbs/spices, low-sodium broth, vinegar, mustard, salsa."],
];

export const sleepFindings = [
  ["Adults need ≥7 h regularly; ≤6 h is inadequate [33]", "Plan 7.5–8.5 h in bed to actually sleep ≥7 h.", "Strong (AASM/SRS consensus)"],
  ["In a 14-day calorie deficit, 5.5 h vs 8.5 h of sleep cut fat loss by 55% and raised lean-mass loss by 60% [34]", "Short sleep turns fat loss into muscle loss. Small, short study, but the direction matches other evidence.", "Moderate"],
  ["Extending sleep by ~1.2 h/night (habitual short sleepers) cut intake by ~270 kcal/day [35]", "More sleep = easier deficit.", "Moderate (RCT)"],
  ["Sleep regularity predicted mortality more strongly than sleep duration [36]", "A consistent wake time is a top priority, even on weekends.", "Weak-Moderate (large cohort)"],
  ["400 mg caffeine even 6 h before bed cut total sleep by >1 h [54]", "Have caffeine at least 8 h before bed (practical buffer). Keep it ≤400 mg/day.", "Moderate"],
  ["Alcohol speeds sleep onset but disrupts the second half of the night and suppresses REM [37]", "Last drink ≥3 h before bed. Keep it light.", "Moderate"],
];

export const sleepRoutine = [
  ["Wake (fixed, ±30–60 min, 7 days/wk)", "Get outdoor light for 5–15 min (walk the dog, coffee outside). It anchors your circadian rhythm (mechanistic; practical)."],
  ["Wake + 0–8 h", "Caffeine window. None after ~2 pm if bedtime is ~10–11 pm."],
  ["Afternoon/evening", "Train whenever you can. Morning vs evening matters far less than consistency. If hard evening sessions make it hard to fall asleep, finish them ≥2 h before bed."],
  ["−3 h", "Last big meal and last alcohol."],
  ["−60 min", "Wind down: dim lights, screens off or in night mode, next day planned, cool room (~18–20 °C, practitioner)."],
  ["Bed", "Same time ±30–60 min. If you’re awake >20 min, get up and read in dim light (CBT-I principle)."],
];

export const lifestyle = [
  ["Stress", "Chronic stress mostly hurts through worse sleep, more snacking, and skipped sessions. Use the plan’s structure (fixed training slots, default meals) to cut decision fatigue. Walks, 5-min slow breathing, and social training all help.", "Weak-Moderate (indirect); Anecdotal for specific tactics"],
  ["Sunlight / daylight", "Morning outdoor light helps anchor the sleep-wake rhythm. Outdoor walks also count toward steps. Don’t rely on sun for vitamin D in a Michigan winter. Use DRI-level intake from food or a supplement [55].", "Mechanistic / Weak"],
  ["Sitting time", "Break up long sitting with 2–5 min walking or stairs every 30–60 min. ACSM recommends breaking up sedentary time for glucose control [52].", "Moderate"],
  ["Sauna", "Optional, 2–4×/wk if you enjoy it. Benefits are observational [50]. Hydrate. Avoid alcohol with it.", "Weak"],
  ["Cold exposure", "Optional for mood or resilience. Not a fat-loss tool [48]. Keep cold plunges ≥6 h from lifting, or on non-lifting days [49].", "Weak / Moderate (harm to gains)"],
  ["Smoking / vaping nicotine", "Biggest single vascular negative if present. Stopping beats every other item here.", "Strong"],
];

export const supplements = [
  { tier: "Strong", name: "Creatine monohydrate", dose: "3–5 g/day, any time; loading not needed", effect: "More strength and lean mass from training. The most effective legal ergogenic aid [39].", safety: "Long safety record [39]. Can add 0.5–2 kg of water weight early, which isn’t fat. Raises serum creatinine a little (tell your doctor).", cost: "Excellent (very cheap)" },
  { tier: "Strong", name: "Protein powder (whey, or soy/pea blend)", dose: "As needed to reach your protein target, 25–40 g servings", effect: "Convenience. Protein supplementation adds lean mass and strength in resistance training [12].", safety: "Third-party tested (NSF Certified for Sport / Informed Choice).", cost: "Excellent per g of protein" },
  { tier: "Strong (if low intake)", name: "Vitamin D3", dose: "DRI level (600 IU/day for adults 19–70), or more only if you’re deficient", effect: "Corrects a deficiency. Doesn’t help fat loss if your level is already OK.", safety: "The 2024 Endocrine Society guideline recommends against routine 25(OH)D testing in healthy adults under 75 and advises sticking to the DRI [55]. Test only if your doctor sees a reason.", cost: "Good, cheap" },
  { tier: "Strong", name: "Caffeine", dose: "3–6 mg/kg ~60 min before hard sessions (start ~1.5–3 mg/kg) [56]", effect: "Better performance and session quality.", safety: "Mind the sleep cutoff. ≤400 mg/day total. Raises BP short-term.", cost: "Excellent (coffee)" },
  { tier: "Moderate", name: "Omega-3 (EPA+DHA)", dose: "1–2 g/day if you rarely eat oily fish. Lowering triglycerides takes ~4 g/day (prescription doses).", effect: "Lowers triglycerides about 20–30% at 4 g/day [57]. General CV-prevention benefit from supplements is uncertain.", safety: "Check with a doctor before high doses if you take anticoagulants. Fish 2×/wk is the first choice.", cost: "Fair" },
  { tier: "Moderate", name: "Dietary nitrate (beet juice/shots or nitrate greens)", dose: "~300–500 mg nitrate (e.g., 1 beet shot or 2 big handfuls of arugula) daily or 2–3 h before training", effect: "SBP ~−4 mmHg in short trials [40]. Small endurance benefit.", safety: "Pink urine (harmless). Caution with nitrates/PDE5 inhibitors/BP meds. Food first.", cost: "Good (food), fair (shots)" },
  { tier: "Moderate", name: "L-citrulline", dose: "3–6 g/day (≥6 g for diastolic BP effect)", effect: "SBP ~−4 mmHg in small meta-analyses [58].", safety: "Well tolerated. Same medication caution as nitrate. One 2018 meta-analysis on the topic was retracted, so evidence is weaker than it looks.", cost: "Fair" },
  { tier: "Moderate", name: "Psyllium husk", dose: "5–10 g/day with water, before meals; build up slowly", effect: "Lowers glucose/HbA1c in proportion to how dysglycemic you are, with ~no effect if normoglycemic [59]. Also helps you reach the fiber target.", safety: "Take 2 h away from medications. Drink plenty of water.", cost: "Excellent" },
  { tier: "Moderate-Weak", name: "Magnesium (glycinate/citrate)", dose: "200–350 mg elemental/day in the evening if your diet is low in it", effect: "Low-quality evidence: falls asleep ~17 min faster in older adults with insomnia [60].", safety: "Avoid with kidney disease. Oxide/citrate can loosen stools.", cost: "Fair" },
  { tier: "Weak / skip", name: "Green tea extract, “fat burners”, CLA, raspberry ketone, garcinia, apple cider vinegar pills", dose: "—", effect: "Little to no meaningful fat loss (e.g., green tea Cochrane [44]).", safety: "Concentrated green tea extract has been linked to rare liver injury. Stimulant stacks raise BP.", cost: "Poor" },
  { tier: "Weak / skip", name: "“Test boosters”, NAD+/NMN, BCAAs (with adequate protein), multivitamin “insurance”, collagen for muscle", dose: "—", effect: "No meaningful benefit for these goals in healthy people eating enough protein (BCAAs/collagen are inferior protein).", safety: "Supplements are loosely regulated. Choose third-party tested products.", cost: "Poor" },
  { tier: "Use caution", name: "Berberine, high-dose red yeast rice", dose: "—", effect: "These act drug-like (glucose/lipid lowering). Red yeast rice contains a statin-identical compound, which goes against the no-prescription-drug intent.", safety: "Interactions and liver/muscle side effects. Skip unless a doctor is involved.", cost: "n/a" },
];

export const supplementNote =
  "Berberine and magnesium aren’t graded beyond what’s cited. The berberine/red yeast rice row is a safety flag, not an evidence review.";

export const trackingMetrics = [
  ["Body weight", "Morning, after the bathroom, before food. Use the 7-day average.", "Daily (look only at the weekly average)", "−0.5 to −0.7%/week on average"],
  ["Waist", "Tape at the navel, relaxed.", "Weekly", "Falling ~0.5–1 cm every 1–2 weeks early on (practitioner). Waist-to-height <0.5 is a common target."],
  ["Strength log", "Load × reps × RPE for the main lifts.", "Every session", "Rising reps or load most weeks for the first 8–12 weeks"],
  ["Interval benchmark", "Watts/pace/distance in 4×4 or a 2-km row.", "Every 4 weeks", "Same HR/RPE at higher output"],
  ["Resting HR", "Wearable or manual, on waking.", "Daily (weekly avg)", "Drifting down a few bpm over 8–12 weeks"],
  ["Blood pressure", "Validated upper-arm cuff: 2 readings AM + PM, seated after 5 min rest, for 7 days (AHA protocol).", "Baseline week, then 1 week/month", "<120/80 is normal. Look for a downward trend [38]."],
  ["Steps", "Phone/wearable.", "Daily (weekly avg)", "8,000–10,000"],
  ["Sleep", "Wearable or log: bedtime, wake time, how rested you feel 1–5.", "Daily", "≥7 h on ≥6 nights; wake time ±60 min"],
  ["Photos", "Front/side/back, same light.", "Every 4 weeks", "Visual recomp even when the scale is slow"],
];

export const labs = [
  ["Fasting glucose", "Glycemic control.", "Normal <100 mg/dL. Prediabetes 100–125 [43]."],
  ["HbA1c", "~3-month glucose average.", "Normal <5.7%. Prediabetes 5.7–6.4% [43]. It moves slowly, so 12-week changes are small."],
  ["Fasting insulin + HOMA-IR", "Insulin resistance (HOMA-IR = glucose mg/dL × insulin µU/mL ÷ 405).", "No universal cutoff. Track your own trend. Labs vary."],
  ["Lipid panel + ApoB", "Atherogenic particle burden (ApoB is the best single marker).", "Discuss targets with your clinician. Triglycerides respond fastest to weight loss, alcohol cuts, and fewer refined carbs."],
  ["hs-CRP", "Low-grade inflammation.", "Retest when you’re not sick or sore. Hard training raises it temporarily."],
  ["TSH (± free T4)", "Rules out thyroid issues as a cause of stalls or fatigue.", "Baseline only, unless it’s abnormal."],
  ["25(OH) vitamin D", "Only if clinically indicated.", "Endocrine Society 2024 advises against routine screening in healthy adults under 75 [55]. Include it if your doctor agrees."],
  ["Optional: CMP (kidney/liver), CBC, ferritin (esp. women), Lp(a) once in life", "Safety for protein/creatine use and fatigue workup; Lp(a) is genetic CV risk.", "Lp(a) doesn’t respond to lifestyle. Test it once."],
];

export const labsNote =
  "Do labs fasting (10–12 h), at the same time of day, and ≥48 h after hard training. Tell the lab and clinician that you take creatine.";

export const outcomes = [
  ["Body weight", "−5 to −8% (0.5–0.7%/wk × 12)", "−8 to −12% (including a 2–4-wk maintenance break)", "Math from the target rate [9, 30]. Real-world loss is often slower."],
  ["Fat vs lean", "Most of the loss is fat. Beginners may gain lean mass.", "Lean mass maintained or up.", "[9, 14, 30]"],
  ["Strength", "Beginners: large gains on main lifts. Trained: modest gains or maintenance during the cut.", "Continued gains, especially after returning to maintenance.", "Practitioner expectation (anecdotal for magnitude); strength holds up in a deficit [9]."],
  ["VO2max", "~+5 mL/kg/min average (more if unfit)", "Further gains, slowing.", "[18]"],
  ["Resting BP", "Plausibly −4 to −8 mmHg systolic with training + isometrics + diet (larger if elevated). Effects partly overlap, so don’t sum them.", "Maintained if habits persist.", "[21, 22, 28, 29, 40]"],
  ["Insulin sensitivity", "Improves measurably with 5% weight loss + exercise.", "More with continued loss (muscle keeps improving at 11–16% loss).", "[8, 19]"],
  ["Triglycerides / waist", "Usually improve early.", "Further improvement.", "Weight-loss literature; individual."],
  ["Diabetes risk (if prediabetic)", "Starts to drop.", "Lifestyle with ~7% loss + 150 min/wk activity cut diabetes incidence 58% in DPP [61].", "[61]"],
];

export const adjustments = [
  ["Weekly average weight flat for 2–3 weeks, waist flat", "Was adherence really ≥85%? Hidden calories (oils, drinks, weekends)? Did steps drop?", "Cut ~150–250 kcal/day (mainly carbs/fats; keep protein) OR add ~2,000 steps/day. Change one thing at a time."],
  ["Weight flat but waist down and strength up", "You’re probably recomping (water + muscle).", "Change nothing for 2 more weeks."],
  ["Losing >1%/week, or strength falling 2+ weeks", "Deficit too large. Sleep or protein low?", "Add 150–250 kcal/day (carbs around training). Take a deload."],
  ["Strength stall on one lift, others fine", "Technique, fatigue, the rep range.", "Swap the variant or rep range for 4 weeks. Drop load 10% and build back."],
  ["Everything stalls + poor sleep / high fatigue / irritability", "Stress and recovery debt.", "Deload week + 1–2 weeks at maintenance calories (diet break). Fix sleep first."],
  ["Diet fatigue after 8–12 weeks", "Normal.", "Planned 1–2-week maintenance break [53], then resume."],
  ["BP not improving", "Measurement technique, sodium, alcohol, sleep apnea, caffeine before readings.", "Tighten sodium. Do isometrics 3×/wk consistently. See the safety list if it stays ≥130/80."],
];

export const adjustmentNote =
  "All the adjustment rules above are practitioner heuristics (anecdotal/moderate). The research-backed constraints are the loss-rate and deficit limits [9, 30].";

export const trendCopy = {
  "need-data": "Log at least two weekly check-ins. The plan says to judge a stall only after 2–3 weeks of data.",
  "need-span": "Those check-ins fall on the same date, so there is no weekly rate yet.",
  "too-fast": "Losing faster than 1% of body weight per week. The plan’s first check is whether the deficit is too large, or sleep or protein is low. Then add 150–250 kcal/day (carbs around training) and take a deload.",
  "on-target": "About 0.5–0.7% of body weight per week, which is the plan’s target rate.",
  "recomp": "Weight is flat and waist is down. The plan says you are probably recomping (water + muscle). Change nothing for 2 more weeks.",
  "flat-waist-up": "Weight is flat and waist is up across these check-ins. Look at the stall row: adherence, hidden calories, and steps, before changing food.",
  "flat": "Weight reads as flat. First check: was adherence really ≥85%? Hidden calories (oils, drinks, weekends)? Did steps drop? Then cut ~150–250 kcal/day (mainly carbs and fats; keep protein) OR add ~2,000 steps/day. Change one thing at a time.",
  "a-bit-fast": "Faster than 0.7%/week and not past 1%/week. The plan doesn’t prescribe a separate change for this band. Watch strength, sleep, and how the deficit feels.",
  "a-bit-slow": "Slower than 0.5%/week, and not flat. The plan’s cut-or-steps adjustment is for a flat weight and a flat waist after 2–3 weeks. Keep logging before you change the plan.",
  "gaining": "Weight is up across these check-ins. The plan’s stall checks still start with adherence, hidden calories (oils, drinks, weekends), and whether steps dropped.",
  "mixed": "The recent check-ins don’t sit cleanly in one of the plan’s rows. Read the rate below against the adjustment table.",
};

export const flatDisclosure =
  "On this screen, weight counts as flat when the change is under 0.1% of body weight per week, and waist counts as changed when it moves by more than 0.1 cm over the same check-ins. The plan itself just says “flat.” Those cutoffs only stop a noisy scale from firing the stall advice. The adjustment rules are practitioner heuristics.";

export const references = [
  { n: 1, citation: "Pontzer H, et al. (2021). Daily energy expenditure through the human life course. Science.", url: "https://doi.org/10.1126/science.abe5017" },
  { n: 2, citation: "Wang Z, et al. (2010). Specific metabolic rates of major organs and tissues across adulthood (uses Elia 1992 values: muscle 13, adipose 4.5 kcal/kg/day). Am J Clin Nutr.", url: "https://pmc.ncbi.nlm.nih.gov/articles/PMC2980962/" },
  { n: 3, citation: "Martins C, Gower BA, Hill JO, Hunter GR (2020). Metabolic adaptation is not a major barrier to weight-loss maintenance. Am J Clin Nutr.", url: "https://doi.org/10.1093/ajcn/nqaa086" },
  { n: 4, citation: "Fothergill E, et al. (2016). Persistent metabolic adaptation 6 years after “The Biggest Loser” competition. Obesity.", url: "https://doi.org/10.1002/oby.21538" },
  { n: 5, citation: "Westerterp KR (2004). Diet induced thermogenesis. Nutr Metab.", url: "https://doi.org/10.1186/1743-7075-1-5" },
  { n: 6, citation: "Donnelly JE, et al. (2009). ACSM Position Stand: Appropriate physical activity intervention strategies for weight loss and prevention of weight regain. Med Sci Sports Exerc.", url: "https://doi.org/10.1249/MSS.0b013e3181949333" },
  { n: 7, citation: "Levine JA, Eberhardt NL, Jensen MD (1999). Role of nonexercise activity thermogenesis in resistance to fat gain in humans. Science.", url: "https://doi.org/10.1126/science.283.5399.212" },
  { n: 8, citation: "Magkos F, et al. (2016). Effects of moderate and subsequent progressive weight loss on metabolic function and adipose tissue biology in humans with obesity. Cell Metab.", url: "https://doi.org/10.1016/j.cmet.2016.02.005" },
  { n: 9, citation: "Murphy C, Koehler K (2022). Energy deficiency impairs resistance training gains in lean mass but not strength: a meta-analysis and meta-regression. Scand J Med Sci Sports.", url: "https://doi.org/10.1111/sms.14075" },
  { n: 10, citation: "Schoenfeld BJ, Ogborn D, Krieger JW (2016). Effects of resistance training frequency on measures of muscle hypertrophy: a systematic review and meta-analysis. Sports Med.", url: "https://doi.org/10.1007/s40279-016-0543-8" },
  { n: 11, citation: "Schoenfeld BJ, Ogborn D, Krieger JW (2017). Dose-response relationship between weekly resistance training volume and increases in muscle mass. J Sports Sci.", url: "https://doi.org/10.1080/02640414.2016.1210197" },
  { n: 12, citation: "Morton RW, et al. (2018). A systematic review, meta-analysis and meta-regression of the effect of protein supplementation on resistance training-induced gains in muscle mass and strength. Br J Sports Med.", url: "https://doi.org/10.1136/bjsports-2017-097608" },
  { n: 13, citation: "Jäger R, et al. (2017). ISSN Position Stand: protein and exercise. J Int Soc Sports Nutr.", url: "https://doi.org/10.1186/s12970-017-0177-8" },
  { n: 14, citation: "Longland TM, et al. (2016). Higher compared with lower dietary protein during an energy deficit combined with intense exercise promotes greater lean mass gain and fat mass loss. Am J Clin Nutr.", url: "https://doi.org/10.3945/ajcn.115.119339" },
  { n: 15, citation: "Mandsager K, et al. (2018). Association of cardiorespiratory fitness with long-term mortality among adults undergoing exercise treadmill testing. JAMA Netw Open.", url: "https://jamanetwork.com/journals/jamanetworkopen/fullarticle/2707428" },
  { n: 16, citation: "Piercy KL, et al. (2018). The Physical Activity Guidelines for Americans. JAMA.", url: "https://doi.org/10.1001/jama.2018.14854" },
  { n: 17, citation: "Helgerud J, et al. (2007). Aerobic high-intensity intervals improve VO2max more than moderate training. Med Sci Sports Exerc.", url: "https://doi.org/10.1249/mss.0b013e3180304570" },
  { n: 18, citation: "Milanović Z, Sporiš G, Weston M (2015). Effectiveness of HIT and continuous endurance training for VO2max improvements: systematic review and meta-analysis. Sports Med.", url: "https://doi.org/10.1007/s40279-015-0365-0" },
  { n: 19, citation: "Jelleyman C, et al. (2015). The effects of high-intensity interval training on glucose regulation and insulin resistance: a meta-analysis. Obes Rev.", url: "https://doi.org/10.1111/obr.12317" },
  { n: 20, citation: "Gillen JB, et al. (2016). Twelve weeks of sprint interval training improves indices of cardiometabolic health similar to traditional endurance training despite a five-fold lower exercise volume and time commitment. PLoS One.", url: "https://doi.org/10.1371/journal.pone.0154075" },
  { n: 21, citation: "Edwards JJ, et al. (2023). Exercise training and resting blood pressure: a large-scale pairwise and network meta-analysis of RCTs. Br J Sports Med.", url: "https://doi.org/10.1136/bjsports-2022-106503" },
  { n: 22, citation: "Cornelissen VA, Smart NA (2013). Exercise training for blood pressure: a systematic review and meta-analysis. J Am Heart Assoc.", url: "https://doi.org/10.1161/JAHA.112.004473" },
  { n: 23, citation: "Storoschuk KL, Moran-MacDonald A, Gibala MJ, Gurd BJ (2025). Much ado about Zone 2: a narrative review. Sports Med.", url: "https://doi.org/10.1007/s40279-025-02261-y" },
  { n: 24, citation: "Paluch AE, et al. (2022). Daily steps and all-cause mortality: a meta-analysis of 15 international cohorts. Lancet Public Health.", url: "https://doi.org/10.1016/S2468-2667(21)00302-9" },
  { n: 25, citation: "Estruch R, et al. (2018). Primary prevention of cardiovascular disease with a Mediterranean diet supplemented with extra-virgin olive oil or nuts (PREDIMED, republished). N Engl J Med.", url: "https://doi.org/10.1056/NEJMoa1800389" },
  { n: 26, citation: "Reynolds A, et al. (2019). Carbohydrate quality and human health: a series of systematic reviews and meta-analyses. Lancet.", url: "https://doi.org/10.1016/S0140-6736(18)31809-9" },
  { n: 27, citation: "Hall KD, et al. (2019). Ultra-processed diets cause excess calorie intake and weight gain: an inpatient RCT. Cell Metab.", url: "https://doi.org/10.1016/j.cmet.2019.05.008" },
  { n: 28, citation: "He FJ, Li J, MacGregor GA (2013). Effect of longer term modest salt reduction on blood pressure: Cochrane systematic review and meta-analysis. BMJ.", url: "https://doi.org/10.1136/bmj.f1325" },
  { n: 29, citation: "Aburto NJ, et al. (2013). Effect of increased potassium intake on cardiovascular risk factors and disease: systematic review and meta-analyses. BMJ.", url: "https://doi.org/10.1136/bmj.f1378" },
  { n: 30, citation: "Garthe I, et al. (2011). Effect of two different weight-loss rates on body composition and strength and power-related performance in elite athletes. Int J Sport Nutr Exerc Metab.", url: "https://doi.org/10.1123/ijsnem.21.2.97" },
  { n: 31, citation: "Zhao J, et al. (2023). Association between daily alcohol intake and risk of all-cause mortality: systematic review and meta-analyses. JAMA Netw Open.", url: "https://doi.org/10.1001/jamanetworkopen.2023.6185" },
  { n: 32, citation: "Schoenfeld BJ, Aragon AA (2018). How much protein can the body use in a single meal for muscle-building? J Int Soc Sports Nutr.", url: "https://doi.org/10.1186/s12970-018-0215-1" },
  { n: 33, citation: "Watson NF, et al. (2015). Recommended amount of sleep for a healthy adult: joint consensus statement of the AASM and SRS. J Clin Sleep Med / Sleep.", url: "https://jcsm.aasm.org/doi/full/10.5664/jcsm.4758" },
  { n: 34, citation: "Nedeltcheva AV, et al. (2010). Insufficient sleep undermines dietary efforts to reduce adiposity. Ann Intern Med.", url: "https://doi.org/10.7326/0003-4819-153-7-201010050-00006" },
  { n: 35, citation: "Tasali E, et al. (2022). Effect of sleep extension on objectively assessed energy intake among adults with overweight: an RCT. JAMA Intern Med.", url: "https://doi.org/10.1001/jamainternmed.2021.8098" },
  { n: 36, citation: "Windred DP, et al. (2024). Sleep regularity is a stronger predictor of mortality risk than sleep duration. Sleep.", url: "https://doi.org/10.1093/sleep/zsad253" },
  { n: 37, citation: "Ebrahim IO, et al. (2013). Alcohol and sleep I: effects on normal sleep. Alcohol Clin Exp Res.", url: "https://doi.org/10.1111/acer.12006" },
  { n: 38, citation: "Whelton PK, et al. (2017/2018). ACC/AHA Guideline for the prevention, detection, evaluation, and management of high blood pressure in adults. Hypertension / JACC.", url: "https://www.jacc.org/doi/10.1016/j.jacc.2017.11.006" },
  { n: 39, citation: "Kreider RB, et al. (2017). ISSN position stand: safety and efficacy of creatine supplementation in exercise, sport, and medicine. J Int Soc Sports Nutr.", url: "https://doi.org/10.1186/s12970-017-0173-z" },
  { n: 40, citation: "Siervo M, et al. (2013). Inorganic nitrate and beetroot juice supplementation reduces blood pressure in adults: systematic review and meta-analysis. J Nutr.", url: "https://doi.org/10.3945/jn.112.170233" },
  { n: 41, citation: "Ried K, Fakler P, Stocks NP (2017). Effect of cocoa on blood pressure. Cochrane Database Syst Rev.", url: "https://doi.org/10.1002/14651858.CD008893.pub3" },
  { n: 42, citation: "Ashor AW, et al. (2015). Exercise modalities and endothelial function: systematic review and dose-response meta-analysis of RCTs. Sports Med.", url: "https://doi.org/10.1007/s40279-014-0272-9" },
  { n: 43, citation: "American Diabetes Association (2026). 2. Diagnosis and Classification of Diabetes: Standards of Care in Diabetes—2026. Diabetes Care.", url: "https://doi.org/10.2337/dc26-S002" },
  { n: 44, citation: "Jurgens TM, et al. (2012). Green tea for weight loss and weight maintenance in overweight or obese adults. Cochrane Database Syst Rev.", url: "https://doi.org/10.1002/14651858.CD008650.pub2" },
  { n: 45, citation: "Betts JA, et al. (2014). The causal role of breakfast in energy balance and health: an RCT in lean adults (Bath Breakfast Project). Am J Clin Nutr.", url: "https://doi.org/10.3945/ajcn.114.083402" },
  { n: 46, citation: "Lowe DA, et al. (2020). Effects of time-restricted eating on weight loss and other metabolic parameters (TREAT RCT). JAMA Intern Med.", url: "https://doi.org/10.1001/jamainternmed.2020.4153" },
  { n: 47, citation: "Liu D, et al. (2022). Calorie restriction with or without time-restricted eating in weight loss. N Engl J Med.", url: "https://doi.org/10.1056/NEJMoa2114833" },
  { n: 48, citation: "Espeland D, de Weerd L, Mercer JB (2022). Health effects of voluntary exposure to cold water – a continuing subject of debate. Int J Circumpolar Health.", url: "https://doi.org/10.1080/22423982.2022.2111789" },
  { n: 49, citation: "Roberts LA, et al. (2015). Post-exercise cold water immersion attenuates acute anabolic signalling and long-term adaptations in muscle to strength training. J Physiol.", url: "https://doi.org/10.1113/JP270570" },
  { n: 50, citation: "Laukkanen T, et al. (2015). Association between sauna bathing and fatal cardiovascular and all-cause mortality events. JAMA Intern Med.", url: "https://doi.org/10.1001/jamainternmed.2014.8187" },
  { n: 51, citation: "Sesso HD, et al. (2022). Effect of cocoa flavanol supplementation for the prevention of cardiovascular disease events: COSMOS RCT. Am J Clin Nutr.", url: "https://doi.org/10.1093/ajcn/nqac055" },
  { n: 52, citation: "Kanaley JA, et al. (2022). Exercise/physical activity in individuals with type 2 diabetes: ACSM consensus statement. Med Sci Sports Exerc.", url: "https://doi.org/10.1249/MSS.0000000000002800" },
  { n: 53, citation: "Byrne NM, et al. (2018). Intermittent energy restriction improves weight loss efficiency in obese men: the MATADOR study. Int J Obes.", url: "https://doi.org/10.1038/ijo.2017.206" },
  { n: 54, citation: "Drake C, et al. (2013). Caffeine effects on sleep taken 0, 3, or 6 hours before going to bed. J Clin Sleep Med.", url: "https://doi.org/10.5664/jcsm.3170" },
  { n: 55, citation: "Demay MB, et al. (2024). Vitamin D for the prevention of disease: an Endocrine Society clinical practice guideline. J Clin Endocrinol Metab.", url: "https://academic.oup.com/jcem/article/109/8/1907/7685305" },
  { n: 56, citation: "Guest NS, et al. (2021). ISSN position stand: caffeine and exercise performance. J Int Soc Sports Nutr.", url: "https://doi.org/10.1186/s12970-020-00383-4" },
  { n: 57, citation: "Skulas-Ray AC, et al. (2019). Omega-3 fatty acids for the management of hypertriglyceridemia: AHA science advisory. Circulation.", url: "https://doi.org/10.1161/CIR.0000000000000709" },
  { n: 58, citation: "Barkhidarian B, et al. (2019). Effects of L-citrulline supplementation on blood pressure: a systematic review and meta-analysis. Avicenna J Phytomed.", url: "https://pmc.ncbi.nlm.nih.gov/articles/PMC6369322/", also: { label: "See also Mirenayat et al. 2019, Nutr Metab", url: "https://doi.org/10.1186/s12986-019-0415-y" } },
  { n: 59, citation: "Gibb RD, et al. (2015). Psyllium fiber improves glycemic control proportional to loss of glycemic control: a meta-analysis. Am J Clin Nutr.", url: "https://doi.org/10.3945/ajcn.115.106989" },
  { n: 60, citation: "Mah J, Pitre T (2021). Oral magnesium supplementation for insomnia in older adults: a systematic review and meta-analysis. BMC Complement Med Ther.", url: "https://doi.org/10.1186/s12906-021-03297-z" },
  { n: 61, citation: "Knowler WC, et al. (2002). Reduction in the incidence of type 2 diabetes with lifestyle intervention or metformin (DPP). N Engl J Med.", url: "https://doi.org/10.1056/NEJMoa012512" },
];

export const disclaimer =
  "This is educational coaching guidance, not medical advice. Personalize it with your clinician if any item in “Check with a doctor first” applies.";

export const nav = [
  { id: "plan", label: "Plan" },
  { id: "train", label: "Training" },
  { id: "eat", label: "Nutrition" },
  { id: "sleep", label: "Sleep" },
  { id: "supplements", label: "Supplements" },
  { id: "track", label: "Tracking" },
  { id: "references", label: "References" },
];
