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
  
  // Italic *text* -> <em>text</em>
  parsed = parsed.replace(/\*(.*?)\*/g, "<em>$1</em>");
  
  // Italic _text_ -> <em>text</em>
  parsed = parsed.replace(/_(.*?)_/g, "<em>$1</em>");
  
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
 * Supports nested list elements based on indentation level.
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
  let resultLines = [];
  
  // listStack keeps track of nested lists: array of { indent: number, type: 'ul' | 'ol' }
  let listStack = [];
  
  for (let line of lines) {
    const trimmed = line.trim();
    
    // Code block indicator - close all lists before starting/ending code blocks
    if (trimmed.startsWith("```")) {
      while (listStack.length > 0) {
        resultLines.push(`</${listStack.pop().type}>`);
      }
      continue;
    }
    
    // Check if the line is a list item
    const ulMatch = line.match(/^(\s*)([-*])\s+(.*)$/);
    const olMatch = line.match(/^(\s*)(\d+)\.\s+(.*)$/);
    
    if (ulMatch || olMatch) {
      const match = ulMatch || olMatch;
      const indent = match[1].length;
      const listType = ulMatch ? 'ul' : 'ol';
      const itemText = match[3];
      
      if (listStack.length === 0) {
        listStack.push({ indent: indent, type: listType });
        resultLines.push(`<${listType}>`);
      } else {
        let lastList = listStack[listStack.length - 1];
        if (indent > lastList.indent) {
          listStack.push({ indent: indent, type: listType });
          resultLines.push(`<${listType}>`);
        } else if (indent < lastList.indent) {
          while (listStack.length > 0 && indent < listStack[listStack.length - 1].indent) {
            resultLines.push(`</${listStack.pop().type}>`);
          }
          if (listStack.length === 0) {
            listStack.push({ indent: indent, type: listType });
            resultLines.push(`<${listType}>`);
          } else {
            let currentList = listStack[listStack.length - 1];
            if (currentList.type !== listType) {
              resultLines.push(`</${currentList.type}>`);
              listStack[listStack.length - 1].type = listType;
              resultLines.push(`<${listType}>`);
            }
          }
        } else {
          if (lastList.type !== listType) {
            resultLines.push(`</${lastList.type}>`);
            listStack[listStack.length - 1].type = listType;
            resultLines.push(`<${listType}>`);
          }
        }
      }
      
      resultLines.push(`<li class="chat-list-item">${parseInlineStyling(itemText)}</li>`);
      continue;
    }
    
    // Non-list line: close all open lists
    if (listStack.length > 0) {
      while (listStack.length > 0) {
        resultLines.push(`</${listStack.pop().type}>`);
      }
    }
    
    // Regular paragraphs
    if (trimmed !== "") {
      resultLines.push(`<p class="chat-paragraph">${parseInlineStyling(line)}</p>`);
    }
  }
  
  // Close any lists left open
  while (listStack.length > 0) {
    resultLines.push(`</${listStack.pop().type}>`);
  }
  
  return resultLines.join("");
}
