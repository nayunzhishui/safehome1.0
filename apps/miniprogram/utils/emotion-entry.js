const { VOCABULARY } = require("./emotionVocabulary.generated");

// 情绪按选择顺序用“、”连接，第一个是主要情绪，强度只对应它；自己填的词写成“词（类名）”，
// 后端按类统计（backend/services/emotion_vocabulary_service.py）。
const SEPARATOR = "、";
const MAX_SELECTED = VOCABULARY.max_selected;
const CUSTOM_MAX_LENGTH = VOCABULARY.custom_word_max_length;
const BODY_NOTE_MAX_LENGTH = VOCABULARY.body_note_max_length;
const UNCLEAR_WORDS = [VOCABULARY.body_unclear, ...(VOCABULARY.unknown.child_words || [])];

function emotionGroups(role) {
  const key = role === "child" ? "child_words" : "parent_words";
  const groups = VOCABULARY.categories
    .filter((category) => (category[key] || []).length)
    .map((category) => ({ code: category.code, label: category.label, words: category[key] }));
  const unknownWords = role === "child" ? VOCABULARY.unknown.child_words || [] : [];
  if (unknownWords.length) groups.push({ code: VOCABULARY.unknown.code, label: VOCABULARY.unknown.label, words: unknownWords });
  return groups;
}

function customCategoryLabels() {
  return VOCABULARY.categories.map((category) => category.label);
}

function bodyRegions() {
  return [...VOCABULARY.body_regions, { label: "其他", words: [VOCABULARY.body_unclear] }];
}

// 选中顺序写进每个词，页面据此显示 1、2、3。
function decorateEmotionGroups(groups, selected) {
  return groups.map((group) => ({
    ...group,
    words: group.words.map((word) => ({ word, order: selected.findIndex((item) => !item.custom && item.word === word) + 1 })),
  }));
}

function customSelections(selected) {
  return selected
    .map((item, index) => ({ ...item, order: index + 1 }))
    .filter((item) => item.custom);
}

function decorateBodyRegions(regions, selected) {
  return regions.map((region) => ({
    ...region,
    words: region.words.map((word) => ({ word, selected: selected.includes(word) })),
  }));
}

// “说不清”“看不出来”与其他词互斥。
function toggleEmotion(selected, word) {
  if (selected.some((item) => !item.custom && item.word === word)) {
    return { selected: selected.filter((item) => item.custom || item.word !== word) };
  }
  if (UNCLEAR_WORDS.includes(word)) return { selected: [{ word, custom: false }] };
  const kept = selected.filter((item) => item.custom || !UNCLEAR_WORDS.includes(item.word));
  if (kept.length >= MAX_SELECTED) return { selected, error: `最多选 ${MAX_SELECTED} 个，先点掉一个再选。` };
  return { selected: [...kept, { word, custom: false }] };
}

function cleanCustomWord(value) {
  return Array.from(String(value || "").replace(/[、（）()：:\s]/g, "")).slice(0, CUSTOM_MAX_LENGTH).join("");
}

function addCustomEmotion(selected, rawWord, categoryIndex) {
  const word = cleanCustomWord(rawWord);
  const label = customCategoryLabels()[categoryIndex];
  if (!word) return { selected, error: "先写一个词。" };
  if (!label) return { selected, error: "请选一个最接近的类，统计时会按这个类算。" };
  if (selected.some((item) => item.word === word)) return { selected, error: "这个词已经选上了。" };
  const kept = selected.filter((item) => item.custom || !UNCLEAR_WORDS.includes(item.word));
  if (kept.length >= MAX_SELECTED) return { selected, error: `最多选 ${MAX_SELECTED} 个，先点掉一个再加。` };
  return { selected: [...kept, { word, custom: true, label }] };
}

function removeEmotion(selected, word) {
  return selected.filter((item) => item.word !== word);
}

function toggleBody(selected, word) {
  if (selected.includes(word)) return selected.filter((item) => item !== word);
  if (word === VOCABULARY.body_unclear) return [word];
  return [...selected.filter((item) => item !== VOCABULARY.body_unclear), word];
}

function composeEmotions(selected) {
  return selected.map((item) => (item.custom ? `${item.word}（${item.label}）` : item.word)).join(SEPARATOR);
}

function composeBody(words, note) {
  const text = words.join(SEPARATOR);
  const extra = String(note || "").trim();
  if (!extra) return text;
  return text ? `${text}：${extra}` : extra;
}

// 参与者看到的情绪：去掉自填词后面存的类名。
function displayEmotions(stored) {
  return String(stored || "")
    .split(SEPARATOR)
    .map((token) => token.trim().replace(/（[^（）]+）$/, ""))
    .filter(Boolean)
    .join(SEPARATOR);
}

module.exports = {
  MAX_SELECTED,
  CUSTOM_MAX_LENGTH,
  BODY_NOTE_MAX_LENGTH,
  emotionGroups,
  customCategoryLabels,
  bodyRegions,
  decorateEmotionGroups,
  customSelections,
  decorateBodyRegions,
  toggleEmotion,
  addCustomEmotion,
  removeEmotion,
  toggleBody,
  composeEmotions,
  composeBody,
  displayEmotions,
};
