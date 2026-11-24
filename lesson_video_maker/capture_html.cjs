"use strict";

const fs = require("node:fs/promises");
const path = require("node:path");
const { once } = require("node:events");
const { spawn } = require("node:child_process");
const { pathToFileURL } = require("node:url");

const [entry, rawFrames, cover, silent] = process.argv.slice(2);
const frames = Number(rawFrames);
const width = 1920;
const height = 1080;
const fps = 30;
const chromePath = process.env.LESSON_VIDEO_MAKER_CHROME || process.env.TECH_EXPLAINER_CHROME ||
  (process.platform === "darwin" ? "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" : "/usr/bin/chromium");

async function main() {
  if (!entry || !Number.isInteger(frames) || frames < 1 || !cover || !silent)
    throw Error("Expected an HTML entry, frame count, cover and silent video paths");
  if (typeof WebSocket !== "function") throw Error("HTML rendering requires Node.js 22+");
  await fs.access(chromePath).catch(() => {
    throw Error("Chrome executable not found. Set LESSON_VIDEO_MAKER_CHROME to its path.");
  });
  const profile = await fs.mkdtemp(path.join(path.dirname(silent), ".chrome-"));
  const chrome = spawn(chromePath, [
    "--headless", "--remote-debugging-port=0", "--user-data-dir=" + profile,
    "--disable-background-networking", "--disable-sync", "--no-first-run",
    "--no-default-browser-check", "--disable-component-update",
    "--disable-background-timer-throttling", "--disable-renderer-backgrounding",
    "about:blank",
  ], { stdio: ["ignore", "ignore", "pipe"] });
  let errorOutput = "";
  chrome.on("error", error => { errorOutput = error.message; });
  chrome.stderr.on("data", data => { errorOutput = (errorOutput + data).slice(-2800); });
  let endpoint;
  const sockets = [];
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

  async function connect(url) {
    const socket = new WebSocket(url);
    sockets.push(socket);
    await new Promise((resolve, reject) => {
      socket.addEventListener("open", resolve, { once: true });
      socket.addEventListener("error", () => reject(Error("Chrome WebSocket connection failed")), { once: true });
    });
    let id = 0;
    const waiting = new Map();
    socket.addEventListener("message", event => {
      const message = JSON.parse(event.data);
      const task = waiting.get(message.id);
      if (!task) return;
      waiting.delete(message.id);
      clearTimeout(task.timeout);
      if (message.error) task.reject(Error(task.method + ": " + message.error.message));
      else task.resolve(message.result);
    });
    return (method, params = {}) => {
      const token = ++id;
      return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          waiting.delete(token);
          reject(Error(method + " timed out: " + errorOutput));
        }, 14000);
        waiting.set(token, { resolve, reject, timeout, method });
        socket.send(JSON.stringify({ id: token, method, params }));
      });
    };
  }

  async function evaluate(session, expression, awaitPromise = false) {
    const result = await session("Runtime.evaluate", { expression, awaitPromise, returnByValue: true });
    if (result.exceptionDetails) throw Error(result.exceptionDetails.exception?.description ?? result.exceptionDetails.text);
    return result.result.value;
  }

  async function page() {
    const response = await fetch(endpoint + "/json/new?about:blank", { method: "PUT", signal: AbortSignal.timeout(4000) });
    if (!response.ok) throw Error("Could not create a Chrome page: HTTP " + response.status);
    const target = await response.json();
    const session = await connect(target.webSocketDebuggerUrl);
    await session("Emulation.setDeviceMetricsOverride",
      { width, height, deviceScaleFactor: 1, mobile: false });
    await session("Page.navigate", { url: pathToFileURL(entry).href + "?capture=1" });
    for (let attempt = 0; attempt < 300; attempt++) {
      const state = await evaluate(session,
        "({ ready: typeof window.renderExplainerFrame === 'function' && document.readyState === 'complete', error: window.explainerError })")
        .catch(() => ({}));
      if (state.error) throw Error(state.error);
      if (state.ready) {
        await evaluate(session, "document.fonts.ready.then(() => true)", true);
        return session;
      }
      await sleep(30);
    }
    throw Error("Custom HTML did not expose a ready explainer player");
  }

  async function snapshot(session, frame, format) {
    await evaluate(session, "window.renderExplainerFrame(" + frame + ")");
    const options = { format, captureBeyondViewport: false, fromSurface: true, optimizeForSpeed: true };
    if (format === "jpeg") options.quality = 92;
    const result = await session("Page.captureScreenshot", options);
    return Buffer.from(result.data, "base64");
  }

  try {
    for (let attempt = 0; attempt < 220; attempt++) {
      const portFile = await fs.readFile(path.join(profile, "DevToolsActivePort"), "utf8").catch(() => "");
      if (portFile) {
        endpoint = "http://127.0.0.1:" + portFile.split("\n")[0];
        break;
      }
      await sleep(50);
    }
    if (!endpoint) throw Error("Chrome did not start: " + errorOutput);
    const pages = await Promise.all(Array.from({ length: Math.min(4, frames) }, () => page()));
    const coverPage = pages[0];
    const coverFrame = await evaluate(coverPage,
      "document.body.classList.add('explainer-cover'); window.explainerCoverFrame");
    await fs.writeFile(cover, await snapshot(coverPage, coverFrame, "png"));
    await evaluate(coverPage, "document.body.classList.remove('explainer-cover')");

    const encoder = spawn("ffmpeg", ["-v", "error", "-y", "-f", "image2pipe", "-framerate", String(fps),
      "-c:v", "mjpeg", "-i", "pipe:0", "-c:v", "libx264", "-preset", "fast",
      "-crf", "18", "-pix_fmt", "yuv420p", "-an", silent],
    { stdio: ["pipe", "ignore", "inherit"] });
    const ended = once(encoder, "exit");
    ended.catch(() => {});
    // Avoid a broken-pipe crash masking an encoder error while a screenshot is in flight.
    encoder.stdin.on("error", () => {});
    try {
      for (let first = 0; first < frames; first += pages.length) {
        const group = pages.slice(0, frames - first);
        for (const buffer of await Promise.all(group.map((session, index) => snapshot(session, first + index, "jpeg")))) {
          if (encoder.exitCode !== null) throw Error("FFmpeg exited while reading HTML frames");
          if (!encoder.stdin.write(buffer)) {
            const state = await Promise.race([once(encoder.stdin, "drain").then(() => "drain"), ended]);
            if (state !== "drain") throw Error("FFmpeg exited while reading HTML frames");
          }
        }
      }
      encoder.stdin.end();
      const [code] = await ended;
      if (code !== 0) throw Error("FFmpeg exited with status " + code);
    } finally {
      if (encoder.exitCode === null && encoder.signalCode === null) encoder.kill();
    }
  } finally {
    for (const socket of sockets) socket.close();
    if (chrome.exitCode === null && chrome.signalCode === null) {
      const exited = once(chrome, "exit").catch(() => {});
      chrome.kill();
      await Promise.race([exited, sleep(1200)]);
    }
    await fs.rm(profile, { recursive: true, force: true, maxRetries: 3, retryDelay: 185 })
      .catch(error => console.error("Temporary browser profile cleanup:", error.code));
  }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
