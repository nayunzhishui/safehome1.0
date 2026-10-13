// P3 line icons (Figma 637:415). Each SVG is the icon's vector group exported for one size and
// tone; GEOMETRY places it inside the square exactly as the Figma instance does:
// group insets [top, right, bottom, left] and stroke overflow [y, x], all in percent.
const GEOMETRY = {
  alert: [[16.67, 14.58, 20.83, 14.58], [6, 5.29]],
  bell: [[22.92, 20.83, 6.25, 20.83], [5.29, 6.43]],
  book: [[21.56, 14.58, 18.75, 14.58], [6.28, 5.29]],
  calendar: [[14.58, 16.67, 16.67, 16.67], [5.45, 5.62]],
  chart: [[33.33, 18.75, 18.75, 18.75], [7.83, 6]],
  clock: [[14.58, 14.58, 14.58, 14.58], [5.29, 5.29]],
  check: [[16.67, 18.75, 14.58, 18.75], [5.45, 6]],
  "chevron-down": [[39.58, 25, 35.42, 25], [15, 7.5]],
  "chevron-right": [[25, 35.42, 25, 39.58], [7.5, 15]],
  compass: [[16.67, 16.67, 16.67, 16.67], [5.62, 5.62]],
  diary: [[14.58, 22.92, 14.58, 22.92], [5.29, 6.92]],
  info: [[14.58, 14.58, 14.58, 14.58], [5.29, 5.29]],
  leaf: [[14.58, 18.75, 14.58, 33.33], [5.29, 7.83]],
  lock: [[18.75, 20.83, 14.58, 20.83], [5.62, 6.43]],
  message: [[27.08, 14.58, 14.58, 14.58], [6.43, 5.29]],
  pen: [[22.92, 22.92, 25, 25], [7.2, 7.2]],
  person: [[19.58, 20.83, 16.67, 20.83], [5.88, 6.43]],
  phone: [[16.67, 16.67, 18.71, 18.71], [5.8, 5.8]],
  search: [[18.75, 16.67, 16.67, 18.75], [5.81, 5.81]],
  shield: [[14.58, 20.83, 14.58, 20.83], [5.29, 6.43]],
  slash: [[14.58, 14.58, 14.58, 14.58], [5.29, 5.29]],
};

function round(value) {
  return Math.round(value * 1000) / 1000;
}

function boxFor(name) {
  const geometry = GEOMETRY[name];
  if (!geometry) return "";
  const [[top, right, bottom, left], [padY, padX]] = geometry;
  const width = 100 - left - right;
  const height = 100 - top - bottom;
  return [
    `left:${round(left - (padX * width) / 100)}%`,
    `top:${round(top - (padY * height) / 100)}%`,
    `width:${round(width * (1 + (2 * padX) / 100))}%`,
    `height:${round(height * (1 + (2 * padY) / 100))}%`,
  ].join(";");
}

Component({
  properties: {
    name: { type: String, value: "" },
    size: { type: Number, value: 24 },
    tone: { type: String, value: "ink" },
  },
  data: { src: "", box: "" },
  lifetimes: {
    attached() { this.refresh(); },
  },
  observers: {
    "name, size, tone"() { this.refresh(); },
  },
  methods: {
    refresh() {
      const { name, size, tone } = this.data;
      this.setData({ src: name ? `/assets/icons/p3/${name}-${size}-${tone}.svg` : "", box: boxFor(name) });
    },
  },
});

module.exports = { GEOMETRY, boxFor };
