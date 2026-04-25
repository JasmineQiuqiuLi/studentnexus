export function highlightText(text, phrases = []) {
  if (!phrases.length) return text;

  let result = text;

  phrases.forEach((phrase) => {
    if (!phrase) return;

    const escaped = phrase.replace(
      /[.*+?^${}()|[\]\\]/g,
      "\\$&"
    );

    const regex = new RegExp(escaped, "gi");

    result = result.replace(
      regex,
      '<mark class="source-highlight">$&</mark>'
    );
  });

  return result;
}