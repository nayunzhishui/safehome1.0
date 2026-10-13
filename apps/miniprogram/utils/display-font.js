// Registers the Noto Serif SC subsets once per launch (UIproduct3 display face).
// Medium is "SafeSerif" (titles, greeting, numbers); Regular is "SafeSerifText" (content quotes).
// If loading fails, CSS falls back to the system serif listed in app.wxss.
const fontData = require("./display-font-data");

const FACES = [
  { family: "SafeSerif", weight: "500", data: fontData.medium },
  { family: "SafeSerifText", weight: "400", data: fontData.regular },
];

function loadDisplayFonts() {
  if (typeof wx === "undefined" || typeof wx.loadFontFace !== "function") return;
  FACES.forEach((face) => {
    wx.loadFontFace({
      global: true,
      family: face.family,
      source: `url("data:font/woff2;base64,${face.data}")`,
      desc: { style: "normal", weight: face.weight },
      scopes: ["webview", "native"],
      fail() {},
    });
  });
}

module.exports = { loadDisplayFonts };
