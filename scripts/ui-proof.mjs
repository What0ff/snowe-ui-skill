// Browser-executed checks for declared roles/actions. No inference of business meaning or taste.
// This function is self-contained so the CDP runner can serialize it into the inspected page.
export function inspectUiContract(contract) {
  const findings = [];
  const normalize = value => String(value ?? "").replace(/\s+/g, " ").trim();
  const modal = document.querySelector("dialog:modal");
  function hiddenReason(node) {
    if (modal && !modal.contains(node)) return "outside active modal";
    let opacity = 1;
    for (let current = node; current instanceof Element; current = current.parentElement) {
      const style = getComputedStyle(current);
      opacity *= Number.parseFloat(style.opacity || "1");
      if (style.display === "none" || style.visibility !== "visible" || style.contentVisibility === "hidden") return "hidden by style";
      if (current.hasAttribute("hidden") || current.hasAttribute("inert") || current.getAttribute("aria-hidden") === "true") return "hidden from interaction/accessibility";
    }
    if (opacity <= 0.01) return "hidden by opacity";
    const bounds = node.getBoundingClientRect();
    return bounds.width > 0 && bounds.height > 0 ? null : "empty rendered bounds";
  }
  function accessibleName(node) {
    const labelled = node.getAttribute("aria-labelledby");
    if (labelled) return normalize(labelled.split(/\s+/).map(id => document.getElementById(id)?.textContent || "").join(" "));
    return normalize(node.getAttribute("aria-label") || Array.from(node.labels || []).map(label => label.textContent).join(" ") || node.innerText || node.getAttribute("title"));
  }
  function clipBounds(node, viewport, includeSelf) {
    let clip = viewport ? {left:0, top:0, right:innerWidth, bottom:innerHeight} : {left:-Infinity, top:-Infinity, right:Infinity, bottom:Infinity};
    for (let current = includeSelf ? node : node.parentElement; current; current = current.parentElement) {
      const style = getComputedStyle(current), rect = current.getBoundingClientRect();
      const sx = current.offsetWidth ? rect.width / current.offsetWidth : 1;
      const sy = current.offsetHeight ? rect.height / current.offsetHeight : 1;
      if (/^(auto|scroll|hidden|clip)$/.test(style.overflowX)) {
        clip.left = Math.max(clip.left, rect.left + current.clientLeft*sx);
        clip.right = Math.min(clip.right, rect.left + (current.clientLeft+current.clientWidth)*sx);
      }
      if (/^(auto|scroll|hidden|clip)$/.test(style.overflowY)) {
        clip.top = Math.max(clip.top, rect.top + current.clientTop*sy);
        clip.bottom = Math.min(clip.bottom, rect.top + (current.clientTop+current.clientHeight)*sy);
      }
    }
    return clip;
  }
  function textRects(node) {
    const walker = document.createTreeWalker(node, NodeFilter.SHOW_TEXT), rectangles = [];
    while (walker.nextNode()) {
      if (!normalize(walker.currentNode.textContent)) continue;
      const parent = walker.currentNode.parentElement;
      if (hiddenReason(parent)) continue;
      const range = document.createRange(); range.selectNodeContents(walker.currentNode);
      rectangles.push(...Array.from(range.getClientRects()).filter(rect => rect.width && rect.height));
    }
    return rectangles;
  }
  const inspected = [];
  for (const role of contract.required || []) {
    const matches = document.querySelectorAll(role.selector);
    if (matches.length !== 1) { findings.push({id:role.id, reason:"expected one owner", count:matches.length}); continue; }
    const node = matches[0], reason = hiddenReason(node), bounds = node.getBoundingClientRect();
    inspected.push({id:role.id, selector:role.selector, name:accessibleName(node), text:normalize(node.value ?? node.innerText), bounds:{left:bounds.left,top:bounds.top,width:bounds.width,height:bounds.height}});
    if (reason) { findings.push({id:role.id, reason}); continue; }
    if (role.kind === "control" && !accessibleName(node)) findings.push({id:role.id, reason:"missing accessible name"});
    if (role.name !== undefined && accessibleName(node) !== normalize(role.name)) findings.push({id:role.id, reason:"accessible name mismatch"});
    if (role.text !== undefined && normalize(node.value ?? node.innerText) !== normalize(role.text)) findings.push({id:role.id, reason:"content mismatch"});
    const rects = role.kind === "text" ? textRects(node) : [bounds];
    if (!rects.length) { findings.push({id:role.id, reason:"no rendered text"}); continue; }
    const clip = clipBounds(node, role.viewport !== false, role.kind === "text");
    for (const rect of rects) {
      if (rect.left < clip.left-1 || rect.top < clip.top-1 || rect.right > clip.right+1 || rect.bottom > clip.bottom+1) {
        findings.push({id:role.id, reason:"clipped or outside required viewport"}); break;
      }
      if (role.viewport !== false) {
        const points = [0.1,0.5,0.9].map(factor => [rect.left+rect.width*factor,rect.top+rect.height*.5]);
        if (points.some(([x,y]) => {
          const top = document.elementFromPoint(x,y);
          return top && top !== node && !node.contains(top) && !top.contains(node);
        })) { findings.push({id:role.id, reason:"occluded at sampled content points"}); break; }
      }
    }
  }
  const groups = new Map();
  for (const declaration of contract.actions || []) {
    for (const node of document.querySelectorAll(declaration.selector)) {
      if (hiddenReason(node)) continue;
      const value = key => declaration[key] ?? node.getAttribute(`data-${key}`);
      const operation = value("operation"), target = value("target"), outcome = value("outcome"), context = value("context") || "page";
      if (![operation,target,outcome].every(item => typeof item === "string" && item.trim())) {
        findings.push({id:declaration.selector, reason:"incomplete declared action identity"}); continue;
      }
      const key = JSON.stringify([operation,target,outcome,context]);
      const entries = groups.get(key) || [];
      if (!entries.some(entry => entry.node === node)) entries.push({node,name:accessibleName(node),exception:declaration.allowDuplicateReason || null});
      groups.set(key,entries);
    }
  }
  const duplicateActions = [];
  for (const [key, entries] of groups) {
    if (entries.length > 1 && !entries.every(entry => entry.exception)) duplicateActions.push({identity:JSON.parse(key),labels:entries.map(entry=>entry.name)});
  }
  return {findings, duplicateActions, inspected,
    boundary:"Declared required-role visibility and action identity; sampled occlusion, not full pixel or aesthetic certification"};
}
