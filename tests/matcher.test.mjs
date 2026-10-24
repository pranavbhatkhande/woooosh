import assert from "node:assert/strict";
import test from "node:test";
import { matchAnswer, normalize, withinOneEdit } from "../js/matcher.js";

const countries = [
  { name: "France", aliases: ["French Republic"], tier: "pad", gem: false },
  { name: "United States", aliases: ["USA", "U.S.A.", "US"], tier: "pad", gem: false },
  { name: "Austria", aliases: [], tier: "ascent", gem: false },
  { name: "Côte d'Ivoire", aliases: ["Ivory Coast"], tier: "orbit", gem: false },
  { name: "Zambia", aliases: [], tier: "orbit", gem: false },
  { name: "Gambia", aliases: ["The Gambia"], tier: "apex", gem: true },
  { name: "Iran", aliases: [], tier: "ceiling", gem: false },
  { name: "Iraq", aliases: [], tier: "ceiling", gem: false },
];

test("normalize folds case, accents, punctuation, articles, and &", () => {
  assert.equal(normalize("  The MATRIX! "), "matrix");
  assert.equal(normalize("Áustria"), "austria");
  assert.equal(normalize("rock & roll"), "rock and roll");
  assert.equal(normalize("rock + roll"), "rock and roll");
  assert.equal(normalize("an atlas"), "atlas");
  assert.equal(normalize("Côte d'Ivoire"), "cote divoire");
  assert.equal(normalize("well-known"), "well known");
});

test("exact, alias, plural, and typo matches", () => {
  assert.equal(matchAnswer("france", countries).name, "France");
  assert.equal(matchAnswer("THE French Republic", countries).name, "France");
  assert.equal(matchAnswer("u.s.a.", countries).name, "United States");
  assert.equal(matchAnswer("ivory coast", countries).name, "Côte d'Ivoire");
  assert.equal(matchAnswer("austrai", countries).via, "typo");
  assert.equal(matchAnswer("austrai", countries).name, "Austria");
  assert.equal(matchAnswer("austrix", countries).name, "Austria");
  assert.equal(matchAnswer("cats", [{ name: "Cat", aliases: [], tier: "pad", gem: false }]).via, "plural");
  assert.equal(matchAnswer("countries", [{ name: "Country", aliases: [], tier: "pad", gem: false }]).name, "Country");
  assert.equal(matchAnswer("berries", [{ name: "Berry", aliases: [], tier: "pad", gem: false }]).name, "Berry");
  assert.equal(matchAnswer("buses", [{ name: "Bus", aliases: [], tier: "pad", gem: false }]).name, "Bus");
  assert.equal(matchAnswer("boxes", [{ name: "Box", aliases: [], tier: "pad", gem: false }]).name, "Box");
  assert.equal(matchAnswer("movies", [{ name: "Movie", aliases: [], tier: "pad", gem: false }]).name, "Movie");
  assert.equal(matchAnswer("horses", [{ name: "Horse", aliases: [], tier: "pad", gem: false }]).name, "Horse");
  assert.equal(matchAnswer("glasses", [{ name: "Glass", aliases: [], tier: "pad", gem: false }]).name, "Glass");
});

test("short words, misses, and near-name collisions do not typo-match", () => {
  assert.equal(matchAnswer("irn", countries), null);
  assert.equal(matchAnswer("iraq", countries).name, "Iraq");
  assert.equal(matchAnswer("iran", countries).name, "Iran");
  assert.equal(matchAnswer("pari", [{ name: "Paris", aliases: [], tier: "pad", gem: false }]), null);
  assert.equal(matchAnswer("paris", [{ name: "Paris", aliases: [], tier: "pad", gem: false }]).name, "Paris");
  assert.equal(matchAnswer("gambii", countries), null);
  assert.equal(matchAnswer("zambia", countries).name, "Zambia");
  assert.equal(matchAnswer("gambia", countries).name, "Gambia");
  assert.equal(matchAnswer("zzzzzz", countries), null);
  assert.equal(matchAnswer("   ", countries), null);
  assert.equal(withinOneEdit("gambia", "zambia"), true);
  assert.equal(withinOneEdit("austria", "australia"), false);
});

test("an ambiguous plural matches nothing", () => {
  const answers = [
    { name: "Pie", aliases: [], tier: "pad", gem: false },
    { name: "Py", aliases: [], tier: "apex", gem: true },
  ];
  assert.equal(matchAnswer("pies", answers), null);
  assert.equal(matchAnswer("pie", answers).name, "Pie");
});

test("exact match wins when a neighbor is one edit away", () => {
  assert.equal(matchAnswer("Austria", countries).via, "exact");
});
