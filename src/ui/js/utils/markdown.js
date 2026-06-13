import { renderManaCost } from './manaRenderer.js';

/**
 * Parses inline formatting like bold, inline code, custom card paths,
 * rule citations, and mana costs.
 * 
 * @param {string} text The raw text line to parse
 * @returns {string} The parsed HTML line
 */
export function parseInlineStyling(text) {
  let parsed = text;
  
  // Bold **text** -> <strong>text</strong>
  parsed = parsed.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
  
  // Code `code` -> <code class="inline-code">code</code>
  parsed = parsed.replace(/`(.*?)`/g, '<code class="inline-code">$1</code>');
  
  // Custom card image preview path highlight
  parsed = parsed.replace(/(custom_cards\/[a-zA-Z0-9_-]+\.png)/gi, '<span class="inline-card-preview-link">🖼️ $1</span>');
  
  // Mana cost rendering (e.g. {2}{W}{W} or {X}{R})
  const manaRegex = /({[^{}]+})+/g;
  parsed = parsed.replace(manaRegex, (match) => {
    return renderManaCost(match);
  });
  
  // Rule citations inline linking (e.g. Rule 100.1a (Page 2) or Regla 510.4 (Página 87))
  const ruleRegex = /(Rule|Regla)\s+([0-9a-zA-Z.]+)\s+\((Page|P&aacute;gina|Página)\s+(\d+)\)/gi;
  parsed = parsed.replace(ruleRegex, (match, word, ruleId, pageWord, pageNum) => {
    return `<a href="/rules.pdf#page=${pageNum}" target="_blank" class="rule-link-inline" title="Ver reglamento: ${word} ${ruleId} (Pág. ${pageNum})">${match}</a>`;
  });
  
  return parsed;
}

/**
 * Formats a block of text into structured HTML paragraphs, lists, and code block formatting.
 * 
 * @param {string} text The raw message text
 * @returns {string} The formatted HTML string
 */
export function formatMarkdown(text) {
  if (!text) return "";
  
  // Sanitize simple tags
  let html = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  
  const lines = html.split("\n");
  let listActive = false;
  let resultLines = [];
  
  for (let line of lines) {
    // Unordered lists
    if (line.trim().startsWith("- ") || line.trim().startsWith("* ")) {
      if (!listActive) {
        listActive = true;
        resultLines.push("<ul>");
      }
      const itemText = line.trim().substring(2);
      resultLines.push(`<li class="chat-list-item">${parseInlineStyling(itemText)}</li>`);
      continue;
    }
    
    // Close list if line is not an item
    if (listActive && !line.trim().startsWith("- ") && !line.trim().startsWith("* ")) {
      listActive = false;
      resultLines.push("</ul>");
    }
    
    // Code blocks (simple line skip for block indicators)
    if (line.trim().startsWith("```")) {
      continue;
    }
    
    // Regular paragraphs
    if (line.trim() !== "") {
      resultLines.push(`<p class="chat-paragraph">${parseInlineStyling(line)}</p>`);
    }
  }
  
  if (listActive) {
    resultLines.push("</ul>");
  }
  
  return resultLines.join("");
}
