import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { compileAnswers, matchAnswer, normalize, variants, withinOneEdit } from "../js/match.js";

const cases = JSON.parse(readFileSync(new URL("./fixtures/normalize-cases.json", import.meta.url)));

test("normalize covers case, accents, articles, ampersands, punctuation", () => {
  for (const [input, expected] of cases) {
    assert.equal(normalize(input), expected, JSON.stringify(input));
  }
});

test("simple plurals and aliases match, typos only when unambiguous", () => {
  const compiled = compileAnswers([
    { name: "Shark", aliases: [], tier: "taxi", gem: false },
    { name: "Country", aliases: [], tier: "climb", gem: false },
    { name: "United States", aliases: ["USA", "US", "America"], tier: "taxi", gem: false },
    { name: "France", aliases: ["French Republic"], tier: "climb", gem: false },
    { name: "São Paulo", aliases: [], tier: "burn", gem: false },
    { name: "The Beatles", aliases: [], tier: "taxi", gem: false },
    { name: "Rock & Roll", aliases: [], tier: "burn", gem: false },
    { name: "Spider-Man", aliases: [], tier: "climb", gem: false },
    { name: "C++", aliases: ["cpp"], tier: "taxi", gem: false },
    { name: "C#", aliases: ["csharp"], tier: "climb", gem: false },
    { name: "C", aliases: [], tier: "burn", gem: false },
    { name: "Receive", aliases: [], tier: "stall", gem: false },
    { name: "Saturn", aliases: [], tier: "apogee", gem: false },
    { name: "Satura", aliases: [], tier: "escape", gem: true },
    { name: "New York", aliases: ["NYC"], tier: "taxi", gem: false },
  ]);

  assert.equal(matchAnswer(compiled, "SHARKS").name, "Shark");
  assert.equal(matchAnswer(compiled, "countries").name, "Country");
  assert.equal(matchAnswer(compiled, "the united states").name, "United States");
  assert.equal(matchAnswer(compiled, "usa").name, "United States");
  assert.equal(matchAnswer(compiled, "french republic").name, "France");
  assert.equal(matchAnswer(compiled, "Sao Paulo").name, "São Paulo");
  assert.equal(matchAnswer(compiled, "beatles").name, "The Beatles");
  assert.equal(matchAnswer(compiled, "rock and roll").name, "Rock & Roll");
  assert.equal(matchAnswer(compiled, "spiderman").name, "Spider-Man");
  assert.equal(matchAnswer(compiled, "c++").name, "C++");
  assert.equal(matchAnswer(compiled, "c#").name, "C#");
  assert.equal(matchAnswer(compiled, "c").name, "C");
  assert.equal(matchAnswer(compiled, "recieve").name, "Receive");
  assert.equal(matchAnswer(compiled, "newyork").name, "New York");
  assert.equal(matchAnswer(compiled, "satur"), null);
  assert.equal(matchAnswer(compiled, "cat"), null);
  assert.equal(matchAnswer(compiled, ""), null);
});

test("edit distance helper and variant helper", () => {
  assert.equal(withinOneEdit("receive", "recieve"), true);
  assert.equal(withinOneEdit("kitten", "kiten"), true);
  assert.equal(withinOneEdit("abcdef", "abxxef"), false);
  assert.equal(withinOneEdit("abc", "xyz"), false);
  assert.ok(variants("sharks").has("shark"));
  assert.ok(variants("shark").has("sharks"));
  assert.ok(variants("berry").has("berries"));
  assert.ok(variants("movies").has("movie"));
});

test("alias collision on the exact key matches nothing", () => {
  const compiled = compileAnswers([
    { name: "Mercury", aliases: ["quicksilver"], tier: "taxi", gem: false },
    { name: "Mercury planet", aliases: ["quicksilver"], tier: "burn", gem: false },
  ]);
  assert.equal(matchAnswer(compiled, "quicksilver"), null);
  assert.equal(matchAnswer(compiled, "mercury").name, "Mercury");
});
