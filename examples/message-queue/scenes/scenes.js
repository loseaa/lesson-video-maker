"use strict";

window.drawExplainerScene = ({ scene, root, sceneTime, motion }) => {
  const { phase, easeOut, easeInOut, focus, pose } = window.explainerMotion;
  const node = id => root.querySelector("#" + id);
  const progress = id => motion("m-" + id).progress;
  const entry = (id, end = .24, start = 0) => easeOut(phase(progress(id), start, end));
  const exit = (id, start = 0, end = .23) => easeInOut(phase(progress(id), start, end));

  function accent(element, amount) {
    element.classList.add("card-focus");
    element.style.setProperty("--focus", amount);
  }

  function stage(id, cue, { x = 0, y = 34, strength = .043, leave = 0, exitX = -35, delay = 0 } = {}) {
    const element = node(id);
    const entered = entry(cue, delay + .24, delay);
    const peak = focus(progress(cue));
    pose(element, {
      x: x * (1 - entered) + exitX * leave, y: y * (1 - entered),
      opacity: entered * (1 - leave), scale: 1 + strength * peak,
    });
    accent(element, peak * entered * (1 - leave));
    return entered;
  }

  const headline = root.querySelector(".headline, .lead");
  const arrived = easeOut(phase(sceneTime, 0, .48));
  pose(headline, { y: 24 * (1 - arrived), opacity: arrived });

  if (scene === "intro") {
    const show = easeOut(phase(sceneTime, .15, .65));
    const identified = focus(progress("same-id"));
    pose(node("i-card"), { x: 84 * (1 - show), y: -36 * (1 - show), opacity: show, scale: 1 + .025 * identified });
    stage("i-expected", "expected", { y: 15, strength: .034 });
    stage("i-real", "actual", { y: 23 });
    stage("i-rows", "same-id", { x: 28, y: 11, strength: .037 });
    stage("i-question", "follow", { x: -44, y: 0 });
    const n = Math.round(10 + 10 * easeInOut(phase(progress("actual"), .05, .38)));
    node("intro-count").textContent = "+" + n;
  } else if (scene === "delivery") {
    const publish = easeInOut(phase(progress("publish"), .03, .52));
    const dispatch = easeInOut(phase(progress("dispatch"), .06, .6));
    const gotAck = easeInOut(phase(progress("receipt"), .35, .64));
    pose(node("a-file"), { x: 494 * publish + 535 * dispatch + 66 * gotAck,
      y: -46 * Math.sin(Math.PI * dispatch) - 34 * gotAck,
      opacity: entry("publish", .13) * (1 - gotAck), scale: 1 + .05 * focus(progress("dispatch")) });
    const processing = focus(progress("write"));
    pose(node("a-consumer"), { y: -8 * processing, scale: 1 + .046 * processing });
    accent(node("a-consumer"), processing);
    const returning = easeInOut(phase(progress("receipt"), .05, .55));
    pose(node("a-ack"), { x: 522 * (1 - returning), opacity: entry("receipt", .23), scale: 1 + .045 * focus(progress("receipt")) });
    accent(node("a-ack"), focus(progress("receipt")));
    node("a-state").textContent = gotAck > .3 ? "已收到 ACK" : dispatch > .45 ? "等待消费端确认" : publish > .3 ? "已有 E-42" : "待入队";
  } else if (scene === "crash") {
    stage("f-write", "commit", { x: -45 });
    const faulty = easeInOut(phase(progress("missing"), .18, .38));
    const right = node("f-ack");
    right.classList.toggle("broken", faulty > .35);
    node("fault-title").textContent = faulty > .35 ? "未送达" : "等待送达";
    node("fault-detail").textContent = faulty > .35 ? "进程崩溃 · ACK 未收到" : "消费者准备确认";
    const issue = focus(progress("missing"));
    const arrivedRight = easeOut(phase(sceneTime, .3, 1.1));
    pose(right, { x: 53 * (1 - arrivedRight), y: -12 * issue, scale: 1 + .046 * issue, opacity: arrivedRight });
    accent(right, issue);
    stage("f-status", "queue-view", { x: -57, y: 0, strength: .04 });
    stage("f-file", "requeue", { x: 136, y: -38, strength: .075 });
  } else if (scene === "repeat") {
    const first = easeOut(phase(sceneTime, .1, .72));
    pose(node("r-copy1"), { x: -51 * (1 - first), y: 44 * (1 - first), opacity: first });
    stage("r-copy2", "duplicate", { x: 95, y: -22, strength: .075 });
    stage("r-guideline", "at-least", { x: -37, y: 0, leave: exit("idempotent") });
    const warning = stage("r-risk", "unsafe", { x: 52, y: 0, strength: .053, leave: exit("idempotent") });
    const count = Math.round(10 + 10 * easeInOut(phase(progress("unsafe"), .13, .54)));
    node("risk-total").textContent = "+" + (warning > 0 ? count : 10);
    stage("r-lesson", "idempotent", { x: 54, y: -16, strength: .065, delay: .14 });
  } else if (scene === "unique") {
    const unique = focus(progress("unique-key"));
    const retry = focus(progress("conflict"));
    const schema = node("g-key");
    const conflict = node("sql-conflict");
    accent(schema, unique);
    pose(schema, { x: 8 * unique, scale: 1 + .021 * unique });
    schema.classList.toggle("selected", unique > .24);
    conflict.classList.toggle("selected", retry > .24);
    stage("g-insert", "insert-first", { y: -52, strength: .06 });
    stage("g-retry", "conflict", { x: 67, y: -13, strength: .035,
      leave: exit("conflict", .48, .78), exitX: 83 });
    stage("g-count", "one-row", { y: 24, strength: .065 });
  } else if (scene === "transaction") {
    stage("t-writes", "both", { x: -59 });
    const blocked = exit("rollback", .12, .52) * (1 - entry("race", .37));
    const rule = focus(progress("row-gate"));
    pose(node("t-ledger"), { x: -53 * blocked, opacity: 1 - .71 * blocked });
    pose(node("t-balance"), { x: -70 * blocked, opacity: 1 - .71 * blocked, scale: 1 + .048 * rule });
    accent(node("t-balance"), rule);
    stage("t-return", "returned-rows", { y: 12, strength: .037, leave: exit("rollback", .12, .5) });
    stage("t-rollback", "rollback", { x: 74, leave: exit("race"), exitX: 63 });
    stage("t-concurrent", "race", { x: 70, y: 0, delay: .13 });
  } else if (scene === "order") {
    const bad = node("o-bad");
    const wrong = entry("early");
    const dim = entry("late");
    const attention = focus(progress("early"));
    pose(bad, { x: -72 * (1 - wrong), opacity: wrong * (1 - .52 * dim), scale: 1 + .026 * attention });
    accent(bad, attention);
    stage("o-good", "late", { x: 68, y: 0, strength: .031 });
    stage("o-repeat", "ack-repeat", { x: -51, y: 0, strength: .04 });
  } else if (scene === "ending") {
    stage("e-id", "stable", { x: -51, y: 0 });
    stage("e-db", "database", { y: 39 });
    stage("e-ack", "finish-ack", { x: 51, y: 0 });
    stage("e-total", "final", { y: 59, delay: .11, strength: .05 });
  }
};
