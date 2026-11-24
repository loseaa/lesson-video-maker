(() => {
  "use strict";

  const W = 1600;
  const H = 850;
  const ink = "#243939";
  const red = "#aa5544";
  const gold = "#dfad62";
  const jade = "#487969";
  const paper = "#f0ddad";
  const { phase, easeOut, easeInOut, pose } = window.explainerMotion;

  function path(ctx, points, fill, outline, width = 3) {
    ctx.beginPath();
    points.forEach(([x, y], index) => index ? ctx.lineTo(x, y) : ctx.moveTo(x, y));
    ctx.closePath();
    ctx.fillStyle = fill;
    ctx.fill();
    if (outline) {
      ctx.strokeStyle = outline;
      ctx.lineWidth = width;
      ctx.stroke();
    }
  }

  function box(ctx, x, y, w, h, radius, fill, stroke) {
    ctx.beginPath();
    ctx.roundRect(x, y, w, h, radius);
    ctx.fillStyle = fill;
    ctx.fill();
    if (stroke) {
      ctx.strokeStyle = stroke;
      ctx.lineWidth = 3;
      ctx.stroke();
    }
  }

  function oval(ctx, x, y, rx, ry, color, angle = 0) {
    ctx.beginPath();
    ctx.ellipse(x, y, rx, ry, angle, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.fill();
  }

  function line(ctx, points, color, width) {
    ctx.beginPath();
    ctx.lineJoin = "round";
    ctx.lineCap = "round";
    points.forEach(([x, y], index) => index ? ctx.lineTo(x, y) : ctx.moveTo(x, y));
    ctx.strokeStyle = color;
    ctx.lineWidth = width;
    ctx.stroke();
  }

  function windowAt(ctx, x, y, w, h) {
    box(ctx, x, y, w, h, 3, "#213e3b", "#849278");
    line(ctx, [[x + w / 2, y + 2], [x + w / 2, y + h - 2]], "#879477", 3);
  }

  function roof(ctx, x, y, w, h, color = "#314f49") {
    ctx.beginPath();
    ctx.moveTo(x - 41, y + h);
    ctx.quadraticCurveTo(x + 19, y + h * .76, x + w * .21, y);
    ctx.lineTo(x + w * .79, y);
    ctx.quadraticCurveTo(x + w - 19, y + h * .76, x + w + 41, y + h);
    ctx.quadraticCurveTo(x + w * .53, y + h * 1.2, x - 41, y + h);
    ctx.fillStyle = color;
    ctx.fill();
    for (let n = 1; n < 12; n++) {
      const offset = n / 12;
      line(ctx, [[x + w * (.235 + .53 * offset), y + 6], [x + w * offset, y + h - 5]], "#a3a68556", 2);
    }
    line(ctx, [[x + w * .21, y], [x + w * .79, y]], "#415f55", 7);
    line(ctx, [[x - 24, y + h + 2], [x + w * .5, y + h + 12], [x + w + 24, y + h + 2]], "#213d37", 8);
  }

  function terrain(ctx, light = true) {
    const g = ctx.createLinearGradient(0, 0, 0, H);
    g.addColorStop(0, light ? "#f8e5bd" : "#294749");
    g.addColorStop(1, light ? "#e0c894" : "#152e32");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, W, H);
    oval(ctx, 1286, 228, 145, 145, light ? "#e4ab68a8" : "#d6a15b66");
    path(ctx, [[0,574],[170,460],[315,527],[540,390],[707,505],[895,350],[1050,448],[1235,314],[1434,432],[1600,319],[1600,850],[0,850]], light ? "#9da68a80" : "#8caa8b42");
    path(ctx, [[0,637],[215,528],[415,600],[620,500],[810,600],[1050,526],[1220,545],[1350,460],[1600,554],[1600,850],[0,850]], light ? "#7685786e" : "#82957c47");
    path(ctx, [[0,742],[213,667],[430,715],[640,654],[937,688],[1150,625],[1411,681],[1600,624],[1600,850],[0,850]], light ? "#af9e70" : "#3e6458");
    for (let i = 0; i < 15; i++) {
      const x = 19 + i * 117;
      const y = 65 + (i * 71) % 750;
      line(ctx, [[x, y], [x + 39 + (i % 3) * 15, y]], light ? "#a6905e43" : "#ffd59130", 2);
    }
  }

  function floor(ctx, color = "#ab8c60") {
    path(ctx, [[0,647],[1600,647],[1600,850],[0,850]], color);
    for (let i = 1; i < 5; i++) {
      const y = 645 + i * i * 12;
      line(ctx, [[0,y],[1600,y]], "#5e55464f", 2);
    }
    for (let i = -3; i < 5; i++) {
      line(ctx, [[800 + i * 135,647],[800 + i * 350,850]], "#5e55464f", 2);
    }
  }

  function fortress(ctx, x, y, size, opening, holeLight = 0) {
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(size, size);
    box(ctx, -170, 206, 940, 225, 0, "#ad9367", "#7e7658");
    for (let row = 0; row < 5; row++) {
      for (let i = 0; i < 18; i++) {
        const xx = -169 + i * 56 + (row % 2) * 12;
        line(ctx, [[xx, 215 + row * 43], [xx + 52, 215 + row * 43]], "#e4cb9466", 2);
        line(ctx, [[xx, 220 + row * 43], [xx, 251 + row * 43]], "#796f5249", 2);
      }
    }
    box(ctx, 22, 69, 526, 147, 2, "#b67250", "#775744");
    box(ctx, 38, 112, 492, 12, 2, "#e3b77882");
    for (let i = 0; i < 7; i++) windowAt(ctx, 55 + i * 69, 132, 45, 52);
    roof(ctx, 20, 24, 529, 78);
    box(ctx, 147, 221, 273, 211, [91, 91, 1, 1], "#d4b37e", "#7b6041");
    box(ctx, 170, 240, 227, 192, [71, 71, 1, 1], "#283d37");
    path(ctx, [[174,431],[389,431],[326,344],[235,344]], "#cbb083");
    box(ctx, 225, 205, 117, 30, 4, "#795846", "#d9ac6e");
    ctx.textAlign = "center";
    ctx.fillStyle = "#f5d897";
    ctx.font = '700 21px "Songti SC", serif';
    ctx.fillText("楚", 284, 228);
    ctx.save();
    ctx.beginPath();
    ctx.roundRect(170, 240, 227, 192, [71, 71, 1, 1]);
    ctx.clip();
    for (let i = 0; i < 2; i++) {
      const width = 115 * (1 - .91 * opening);
      const xx = i ? 397 - width : 170;
      box(ctx, xx, 237, width, 201, 0, i ? "#a35d42" : "#b16b4f", "#724735");
      for (let rivet = 0; rivet < 4; rivet++) {
        const rx = xx + ((rivet + 1) / 5) * width;
        oval(ctx, rx, 329, 3.4, 3.5, "#deaf6a");
        oval(ctx, rx, 351, 3.4, 3.5, "#deaf6a");
      }
      oval(ctx, xx + width * (i ? .18 : .82), 372, 7, 6, "#513d31");
    }
    ctx.restore();
    if (holeLight > 0) {
      oval(ctx, 546, 396, 67 + 7 * holeLight, 62 + 8 * holeLight, "#f8d18c8c");
    }
    box(ctx, 503, 350, 86, 82, [37, 37, 0, 0], "#8a7355");
    box(ctx, 516, 364, 61, 68, [27, 27, 0, 0], "#273834");
    line(ctx, [[509,434],[585,434]], "#d7b979", 6);
    ctx.restore();
  }

  function character(ctx, {x, y, size = 1, facing = 1, robe = jade, king = false, lift = 0, tilt = 0, gesture = 0}) {
    ctx.save();
    ctx.translate(x, y - lift);
    ctx.scale(size * facing, size);
    ctx.rotate(tilt);
    oval(ctx, 0, 1, 92, 15, "#1b2f2c31");
    box(ctx, -47, -17, 39, 20, 10, "#273a37");
    box(ctx, 15, -17, 41, 20, 10, "#273a37");
    const cuff = 37 * gesture;
    path(ctx, [[-58,-160],[-27,-173],[42,-166],[69,-127],[83+cuff,-88-cuff],[99+cuff,-107-cuff],[89+cuff,-63-cuff],[53,-57],[67,-13],[-68,-13],[-51,-67],[-77,-59],[-94,-85]], robe, ink, 4);
    path(ctx, [[-25,-168],[10,-125],[35,-163],[27,-175],[-15,-181]], "#f1dda2", ink);
    path(ctx, [[10,-125],[-9,-87],[-19,-17],[18,-17],[28,-125],[40,-159]], "#efcf8950");
    line(ctx, [[-51,-68],[-5,-60],[51,-74]], "#253d35", 10);
    box(ctx, -10, -68, 25, 16, 5, "#e5b966", "#6b5a36");
    line(ctx, [[-62,-101],[-77,-72]], "#e9bf79", 6);
    line(ctx, [[78 + cuff,-91-cuff],[84+cuff,-72-cuff]], "#e9bf79", 7);
    oval(ctx, 96+cuff, -83-cuff, 15, 10, "#df9f72", -.5);
    oval(ctx, -31, -196, 19, 22, "#cf8b62");
    oval(ctx, 8, -205, 48, 53, "#e5a877");
    oval(ctx, 47, -197, 13, 9, "#e5a877");
    path(ctx, [[-40,-224],[-29,-246],[14,-258],[52,-232],[43,-211],[24,-218],[19,-226],[-8,-218],[-18,-194],[-31,-191]], "#293936");
    if (king) {
      box(ctx, -49, -272, 104, 30, 5, "#2a3837", "#d9a963");
      line(ctx, [[-65,-274],[72,-274]], "#edbc69", 9);
      for (let i = 0; i < 5; i++) {
        line(ctx, [[32 + i * 9,-273],[32 + i * 9,-233]], "#d0aa67", 2);
        oval(ctx, 32 + i * 9, -231, 3, 4, "#d9b477");
      }
      path(ctx, [[6,-180],[34,-181],[35,-165],[22,-144],[8,-160]], "#353a32");
    } else {
      box(ctx, -24, -267, 53, 27, 7, "#344d46", "#253938");
      box(ctx, -12, -281, 30, 22, 4, "#667f60", "#273a34");
      line(ctx, [[-32,-246],[45,-246]], "#e0af67", 5);
    }
    line(ctx, [[-9,-213],[3,-216],[11,-213]], "#583f33", 3);
    line(ctx, [[23,-214],[37,-212]], "#583f33", 3);
    oval(ctx, 2, -204, 3.6, 5, "#2c392f");
    oval(ctx, 29, -203, 3.2, 5, "#2c392f");
    line(ctx, [[28,-185],[36,-187]], "#774d36", 2.5);
    oval(ctx, 12, -191, 7, 3, "#da7e6488");
    ctx.restore();
  }

  function pillar(ctx, x, dim = 1) {
    box(ctx, x, 0, 64, 643, 4, dim === 1 ? "#885544" : "#64483f");
    box(ctx, x + 9, 0, 13, 643, 3, "#c2855b6e");
    box(ctx, x - 16, 620, 96, 31, 5, "#533d35", "#a0794f");
  }

  function palace(ctx) {
    ctx.fillStyle = "#223c3e";
    ctx.fillRect(0, 0, W, H);
    box(ctx, 520, 103, 887, 539, 28, "#2e4b46", "#90764d");
    for (let i = 0; i < 5; i++) {
      box(ctx, 604 + i * 144, 176, 126, 385, 8, i % 2 ? "#35534d" : "#426159", "#ac8c5d");
    }
    floor(ctx, "#6d5845");
    pillar(ctx, 575, .4);
    pillar(ctx, 1416, 1);
    path(ctx, [[917,552],[1186,552],[1331,849],[766,849]], "#a45643");
    path(ctx, [[947,556],[1155,556],[1228,803],[863,803]], "#b97250");
    line(ctx, [[948,559],[866,805],[1227,805],[1156,559]], "#c99461", 4);
    box(ctx, 872, 541, 344, 47, 5, "#74563d", "#d2a16b");
    box(ctx, 905, 424, 276, 141, [20,20,0,0], "#855d42", "#d2a16b");
    box(ctx, 924, 448, 238, 82, 9, "#a6804c", "#bc9560");
  }

  function groupStreet(ctx, sleeves, rain, fade) {
    ctx.save();
    ctx.globalAlpha = fade;
    box(ctx, 581, 100, 938, 579, 50, "#d8aa73", "#e0bd81");
    ctx.beginPath();
    ctx.roundRect(584, 103, 932, 573, 48);
    ctx.clip();
    oval(ctx, 1260, 257, 110, 110, "#f8d58c");
    path(ctx, [[580,431],[942,330],[1519,414],[1519,702],[580,702]], "#a88661");
    path(ctx, [[904,344],[1152,344],[1539,724],[667,724]], "#bc9863");
    for (let i = 0; i < 4; i++) {
      const start = 625 + i * 236;
      box(ctx, start, 266 + (i % 2) * 26, 144, 220, 3, "#a66f54", "#795c43");
      roof(ctx, start, 209 + (i % 2) * 26, 144, 81);
      windowAt(ctx, start + 33, 334, 74, 68);
    }
    const robes = ["#7f604e", "#477b69", "#9c5b4c", "#826c4b", "#6f7764"];
    for (let row = 0; row < 4; row++) {
      for (let i = 0; i < 8; i++) {
        const y = 439 + row * 72 + ((i * 19) % 35);
        const x = 626 + i * 125 + (row % 2) * 42;
        const gesture = sleeves * ((i + row) % 3 === 0 ? 1 : .48);
        character(ctx, {x, y, size: .27 + row * .15, facing: i % 2 ? 1 : -1, robe: robes[(i + row) % 5], gesture});
      }
    }
    if (sleeves > 0) {
      ctx.globalAlpha = fade * sleeves;
      oval(ctx, 1230, 270, 199, 26, "#334d47b0", -.17);
      for (let i = 0; i < 11; i++) {
        const x = 1056 + i * 31;
        path(ctx, [[x,296],[x + 28,284],[x + 19,218],[x - 9,230]], robes[i % 5], "#4c513e");
      }
    }
    if (rain > 0) {
      ctx.globalAlpha = fade * rain;
      for (let i = 0; i < 19; i++) {
        const x = 719 + (i * 89) % 741;
        const y = 306 + (i * 53) % 251;
        line(ctx, [[x + 12,y],[x,y + 28]], "#fae8ac", 4);
      }
    }
    ctx.restore();
  }

  function table(ctx, x, y, w) {
    box(ctx, x + 37, y + 26, 27, 83, 4, "#543e32");
    box(ctx, x + w - 66, y + 26, 27, 83, 4, "#543e32");
    box(ctx, x, y, w, 39, 5, "#8c5540", "#cd995d");
    path(ctx, [[x + 17,y],[x + w - 17,y],[x + w - 64,y + 24],[x + 64,y + 24]], "#a76c4d");
    for (let i = 0; i < 3; i++) {
      const cx = x + w * (.25 + i * .24);
      oval(ctx, cx, y + 15, 29, 9, "#463e33");
      oval(ctx, cx, y + 13, 24, 6, "#d1ac68");
    }
  }

  function fruit(ctx, x, y, size, orange) {
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(size, size);
    oval(ctx, 0, 72, 102, 20, "#102c3066");
    oval(ctx, 0, 0, 91, 71, orange ? "#ce7f38" : "#a59a47", -.07);
    oval(ctx, -8, -5, 80, 63, orange ? "#e5a04e" : "#b5aa50", -.1);
    oval(ctx, -37, -27, 22, 12, orange ? "#ffc278" : "#d5c676", -.37);
    for (let i = 0; i < 13; i++) {
      oval(ctx, -62 + (i * 31) % 126, -39 + (i * 17) % 86, 1.8 + i % 2, 1.8, orange ? "#7d482467" : "#5c5e2f8c");
    }
    line(ctx, [[0,-56],[2,-88],[13,-109]], "#644d2e", 8);
    oval(ctx, 40, -81, 43, 15, "#63875c", -.4);
    oval(ctx, -26, -92, 34, 14, "#426f56", .4);
    line(ctx, [[8,-70],[66,-94]], "#a6a66d", 2);
    if (!orange) {
      oval(ctx, -44, -104, 22, 9, "#76986a", .42);
      oval(ctx, 33, -95, 24, 9, "#76986a", -.2);
    }
    ctx.restore();
  }

  function orchard(ctx, appear, focus) {
    ctx.save();
    ctx.globalAlpha = appear;
    terrain(ctx, false);
    path(ctx, [[718,145],[790,179],[848,245],[812,348],[909,463],[856,544],[1040,850],[630,850],[752,556],[676,466],[747,354],[727,233],[677,208]], "#518587");
    path(ctx, [[739,158],[781,188],[813,244],[772,347],[873,472],[814,552],[967,850],[689,850],[784,550],[710,467],[765,349],[744,234],[699,201]], "#729b92");
    for (let i = 0; i < 9; i++) {
      const y = 243 + i * 57;
      const x = [777,776,764,789,828,819,798,825,855][i];
      line(ctx, [[x - 23,y],[x,y],[x + 8,y - 6],[x + 43,y - 6]], "#b4c8a4a6", 3);
    }
    fruit(ctx, 435, 308 - 31 * appear, 1.39 + .12 * focus, true);
    fruit(ctx, 1164, 308 - 31 * appear, 1.38 + .12 * focus, false);
    ctx.restore();
  }

  function show(node, amount, {x = 0, y = 24, scale = 1} = {}) {
    pose(node, {opacity: amount, x: x * (1 - amount), y: y * (1 - amount), scale});
  }

  function frame(context) {
    const {root, scene, motion} = context;
    const canvas = root.querySelector("canvas");
    const ctx = canvas.getContext("2d", {alpha: false});
    const node = selector => root.querySelector(selector);
    const cue = name => motion("cue-" + name).progress;
    const enter = (name, to = .30, from = 0) => easeOut(phase(cue(name), from, to));
    const smooth = (name, to = .78, from = .05) => easeInOut(phase(cue(name), from, to));

    if (scene === "prologue") {
      terrain(ctx);
      path(ctx, [[716,843],[1009,646],[1053,623],[1124,644],[1015,845]], "#dcc18d");
      const angle = .1 * smooth("visit");
      fortress(ctx, 964 - angle * 81, 293 + angle * 52, .94 + angle, 0);
      character(ctx, {x:1180,y:741,size:1.62,facing:-1,gesture:.13 + .62 * smooth("name")});
      const cover = document.body.classList.contains("explainer-cover");
      show(node(".name-strip"), cover ? 1 : enter("name", .35, .14), {x:32, y:0});
      root.querySelectorAll(".bookmarks span").forEach((item, i) => {
        const p = cover ? 1 : easeOut(phase(cue("stakes"), i * .16, .3 + i * .16));
        show(item, p, {y:15});
      });
      return;
    }

    if (scene === "gate") {
      terrain(ctx);
      floor(ctx);
      const opening = smooth("open", .48, .1);
      const walking = smooth("open", .95, .36);
      const attention = enter("hole", .55, .23) * (1 - opening);
      fortress(ctx, 514, 182, 1.12, opening, attention);
      character(ctx, {x:465 + walking * 340,y:718 - walking * 46,size:1.19 - walking * .15,
        gesture:.21 + .55 * enter("refuse") * (1 - walking),tilt:walking * .06});
      character(ctx, {x:1251,y:697,size:1.07,facing:-1,robe:"#9f614c",gesture:.8 * attention});
      show(node(".hole-label"), attention, {y:10});
      show(node(".gate-bubble"), enter("refuse", .38, .1) * (1 - enter("open", .38)), {x:-36,y:0});
      show(node(".open-label"), enter("open", .68, .36), {y:15});
      show(node(".gate-note"), enter("gate-why"), {y:16});
      return;
    }

    if (scene === "court") {
      palace(ctx);
      const reveal = smooth("crowd", .45, .06);
      const exit = smooth("mirror", .42, 0);
      const question = enter("king", .43, .10);
      const mirror = enter("mirror", .44, .07);
      character(ctx, {x:1038,y:590,size:1.46,robe:red,king:true,facing:-1,gesture:.72 * question * (1 - mirror),tilt:.05 * mirror});
      character(ctx, {x:696,y:723,size:1.12,gesture:.18 + .74 * mirror});
      groupStreet(ctx, smooth("crowd", .82, .56), smooth("crowd", 1, .81), reveal * (1 - exit));
      show(node(".king-line"), question * (1 - reveal), {x:-26,y:0});
      show(node(".city-copy"), reveal * (1 - exit), {x:-26,y:0});
      const facts = root.querySelectorAll(".city-copy li");
      [.43,.60,.81].forEach((start, i) => show(facts[i], enter("crowd", start + .11, start), {x:-15,y:0}));
      show(node(".mirror-copy"), mirror, {x:-22,y:0});
      show(node(".court-note"), enter("court-why"), {y:16});
      return;
    }

    if (scene === "feast") {
      palace(ctx);
      table(ctx, 670, 600, 634);
      const passing = smooth("prisoner", .70, .04);
      const orchardIn = smooth("fruit", .4, 0);
      const orchardOut = smooth("result", .4, .02);
      const fruitPose = orchardIn * (1 - orchardOut);
      character(ctx, {x:1136,y:618,size:1.25,robe:red,king:true,facing:-1,tilt:.14 * orchardOut,gesture:passing * (1 - orchardOut)});
      character(ctx, {x:557,y:714,size:1.1,gesture:.75 * orchardOut});
      ctx.save();
      ctx.globalAlpha = 1 - enter("one-all");
      for (let i = 0; i < 3; i++) {
        character(ctx, {x:160 + i * 141 + passing * 573,y:713,size:i === 1 ? .88 : .96,robe:i === 1 ? "#7c7968" : "#865a4a",tilt:.07});
      }
      ctx.restore();
      orchard(ctx, fruitPose, .85 * enter("turn") * (1 - orchardOut));
      show(node(".feast-line"), enter("prisoner", .79, .52) * (1 - orchardIn), {x:-20,y:0});
      show(node(".south"), fruitPose * enter("fruit", .48, .3), {y:17});
      show(node(".north"), fruitPose * enter("fruit", .70, .46), {y:17});
      show(node(".fruit-river"), orchardIn * (1 - orchardOut), {y:12});
      show(node(".fruit-note"), enter("turn", .85, .51) * (1 - orchardOut), {y:15});
      show(node(".feast-note"), enter("result", .79, .38), {y:15});
      return;
    }

    terrain(ctx);
    box(ctx, 70, 45, 1461, 735, 33, "#f5e4bd", "#ac8e62");
    box(ctx, 84, 59, 1433, 706, 24, "#f6e7c6", "#ceb589");
    if (scene === "quiz") {
      const reveal = enter("quiz-answer", .15);
      const timer = smooth("quiz-pause", 1, 0);
      character(ctx, {x:1320,y:688,size:1.47,facing:-1,gesture:.23 + .53 * reveal});
      oval(ctx, 1321, 207, 81, 81, "#ded0a9");
      oval(ctx, 1321, 207, 67, 67, "#f8eccd");
      ctx.beginPath();
      ctx.arc(1321, 207, 74, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * (1 - timer));
      ctx.strokeStyle = reveal > 0 ? jade : red;
      ctx.lineWidth = 9;
      ctx.stroke();
      line(ctx, [[1321,170],[1321,207],[1342,221]], jade, 7);
      show(node(".answer-a"), enter("quiz-question", .50, .30) * (1 - .46 * reveal), {x:-27,y:0});
      const answer = node(".answer-b");
      answer.style.setProperty("--answer-bg", reveal > .5 ? "#d8e5c9" : "#fff4d6");
      answer.style.setProperty("--answer-border", reveal > .5 ? "#527967" : "#ad8c59");
      show(answer, enter("quiz-question", .67, .49), {x:-27,y:0,scale:1 + .035 * reveal});
      show(node(".correct"), reveal, {x:-10,y:0});
      show(node(".quiz-result"), enter("quiz-answer", .67, .40), {y:20});
      return;
    }

    const chapters = [
      {name:"cause", x:338, drawing:() => character(ctx, {x:338,y:485,size:.52,gesture:.55})},
      {name:"events", x:800, drawing:() => fortress(ctx, 734, 366, .23, .88)},
      {name:"end", x:1262, drawing:() => {
        oval(ctx, 1262, 424, 68, 61, "#cbdcc0");
        line(ctx, [[1230,425],[1252,447],[1296,398]], jade, 12);
      }},
    ];
    for (const {name, drawing} of chapters) {
      const entry = enter(name, .28);
      ctx.save();
      ctx.globalAlpha = entry;
      ctx.translate(0, (1 - entry) * 22);
      drawing();
      ctx.restore();
      show(node("." + name), entry, {y:22});
    }
    show(node(".retell"), enter("prompt", .35), {y:18});
  }

  window.drawExplainerScene = frame;
})();
