#!/usr/bin/env node
// Render a .drawio file to SVG with draw.io's own renderer (viewer-static.min.js) in headless Chromium.
//
//   node tools/render-svg.cjs examples/sample.drawio examples/sample.svg
//
// draw.io's viewer script and the icons the diagram references are fetched from the
// jgraph/drawio GitHub repo (pinned tag) and cached in .cache/drawio/. Icons are inlined
// into the SVG as data URIs so the file is self-contained.
// Requires the `playwright` npm package and a Chromium it can launch.

const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const DRAWIO_TAG = process.env.DRAWIO_TAG || "v32.4.1";
const RAW = `https://raw.githubusercontent.com/jgraph/drawio/${DRAWIO_TAG}/src/main/webapp/`;
const CACHE = path.resolve(__dirname, "..", ".cache", "drawio", DRAWIO_TAG);
const ORIGIN = "http://drawio.local/";

async function cached(relPath) {
  const file = path.join(CACHE, relPath);
  if (!file.startsWith(CACHE + path.sep)) throw new Error(`bad path ${relPath}`);
  if (!fs.existsSync(file)) {
    const res = await fetch(RAW + relPath);
    if (!res.ok) throw new Error(`${res.status} fetching ${RAW + relPath}`);
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.writeFileSync(file, Buffer.from(await res.arrayBuffer()));
  }
  return fs.readFileSync(file);
}

const MIME = { ".js": "text/javascript", ".svg": "image/svg+xml", ".png": "image/png", ".css": "text/css" };

async function main() {
  const [input, output] = process.argv.slice(2);
  if (!input || !output) {
    console.error("usage: render-svg.cjs INPUT.drawio OUTPUT.svg");
    process.exit(2);
  }
  const xml = fs.readFileSync(input, "utf8");

  const browser = await chromium.launch();
  try {
    const page = await browser.newPage();
    page.on("pageerror", (e) => console.error("page error:", e.message));
    await page.route(ORIGIN + "**", async (route) => {
      const rel = decodeURIComponent(new URL(route.request().url()).pathname.slice(1));
      if (rel === "index.html") {
        return route.fulfill({
          contentType: "text/html",
          body: `<!doctype html><html><head><meta charset="utf-8"></head><body>
                 <div id="graph"></div><script src="js/viewer-static.min.js"></script></body></html>`,
        });
      }
      try {
        const body = await cached(rel);
        await route.fulfill({ body, contentType: MIME[path.extname(rel)] || "application/octet-stream" });
      } catch (e) {
        console.error(String(e));
        await route.fulfill({ status: 404, body: "" });
      }
    });

    await page.goto(ORIGIN + "index.html");
    await page.waitForFunction(() => typeof Graph !== "undefined" && typeof mxCodec !== "undefined");

    const svg = await page.evaluate((xml) => {
      const doc = mxUtils.parseXml(xml);
      const diagram = doc.documentElement.getElementsByTagName("diagram")[0];
      const modelNode = Editor.parseDiagramNode(diagram);
      const graph = new Graph(document.getElementById("graph"));
      graph.setEnabled(false);
      new mxCodec(modelNode.ownerDocument).decode(modelNode, graph.getModel());
      // background, scale, border, nocrop, crisp, ignoreSelection, showText
      const root = graph.getSvg("#ffffff", 1, 20, false, null, true, true);
      return mxUtils.getXml(root);
    }, xml);

    // Inline every image the renderer referenced by draw.io-relative path.
    const hrefs = new Set([...svg.matchAll(/(?:xlink:)?href="((?:http:\/\/drawio\.local\/)?img\/[^"]+)"/g)].map((m) => m[1]));
    let out = svg;
    for (const href of hrefs) {
      const rel = href.replace(ORIGIN, "");
      const data = (await cached(rel)).toString("base64");
      const uri = `data:${MIME[path.extname(rel)] || "application/octet-stream"};base64,${data}`;
      out = out.split(`"${href}"`).join(`"${uri}"`);
    }

    fs.writeFileSync(output, `<?xml version="1.0" encoding="UTF-8"?>\n${out}\n`);
    console.log(`wrote ${output} (${hrefs.size} icons inlined)`);
  } finally {
    await browser.close();
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
