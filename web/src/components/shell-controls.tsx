"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { BarChart3, Building2, Compass, Globe2, Landmark, Menu, Search, Users, X } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import type { EntityKind, Navigation, SearchItem } from "@/lib/types";

const areaIcons = [BarChart3, Globe2, Building2, Users, Compass, Landmark];
const groups: { kind: EntityKind; label: string }[] = [
  { kind: "question", label: "Questions" }, { kind: "topic", label: "Topics" },
  { kind: "chart", label: "Charts" }, { kind: "indicator", label: "Indicators" },
  { kind: "region", label: "Areas" },
];

export function HeaderControls({ navigation, searchItems }: { navigation: Navigation; searchItems: SearchItem[] }) {
  const pathname = usePathname();
  const router = useRouter();
  const [searchOpen, setSearchOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const menuCloseRef = useRef<HTMLButtonElement>(null);
  const results = useMemo(() => {
    const terms = query.toLocaleLowerCase().trim().split(/\s+/).filter(Boolean);
    const matches = terms.length ? searchItems.filter((item) => terms.every((term) => item.text.toLocaleLowerCase().includes(term))) : searchItems;
    return groups.map((group) => ({ ...group, items: matches.filter((item) => item.kind === group.kind).slice(0, 6) })).filter((group) => group.items.length);
  }, [query, searchItems]);
  const flatResults = results.flatMap((group) => group.items);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") { event.preventDefault(); setSearchOpen(true); }
      if (event.key === "Escape") { setSearchOpen(false); setMenuOpen(false); }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);
  useEffect(() => { if (new URLSearchParams(window.location.search).get("search") === "open") setSearchOpen(true); }, []);
  useEffect(() => { if (searchOpen) { setActive(0); requestAnimationFrame(() => inputRef.current?.focus()); } }, [searchOpen]);
  useEffect(() => { if (menuOpen) requestAnimationFrame(() => menuCloseRef.current?.focus()); }, [menuOpen]);
  useEffect(() => { setMenuOpen(false); setSearchOpen(false); }, [pathname]);
  useEffect(() => {
    document.body.classList.toggle("overlay-open", searchOpen || menuOpen);
    return () => document.body.classList.remove("overlay-open");
  }, [searchOpen, menuOpen]);

  function choose(item: SearchItem) { setSearchOpen(false); setQuery(""); router.push(item.href); }
  function searchKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (event.key === "ArrowDown") { event.preventDefault(); setActive((value) => Math.min(value + 1, flatResults.length - 1)); }
    if (event.key === "ArrowUp") { event.preventDefault(); setActive((value) => Math.max(value - 1, 0)); }
    if (event.key === "Enter" && flatResults[active]) { event.preventDefault(); choose(flatResults[active]); }
    if (event.key === "Escape") setSearchOpen(false);
  }

  return <>
    <button className="mobile-menu" aria-label="Open Explore menu" aria-expanded={menuOpen} onClick={() => setMenuOpen(true)}><Menu /></button>
    <div className="header-actions"><button className="search-trigger" aria-haspopup="dialog" onClick={() => setSearchOpen(true)}><Search size={18} /><span>Search the atlas…</span><kbd>⌘ K</kbd></button><Link href="/atlas">About</Link></div>
    {menuOpen && <div className="overlay" role="presentation" onMouseDown={() => setMenuOpen(false)}><aside className="mobile-sheet" role="dialog" aria-modal="true" aria-label="Explore the atlas" onMouseDown={(event) => event.stopPropagation()}>
      <header><p className="rail-label">Explore</p><button ref={menuCloseRef} aria-label="Close Explore menu" onClick={() => setMenuOpen(false)}><X /></button></header>
      <button className="sheet-search" onClick={() => { setMenuOpen(false); setSearchOpen(true); }}><Search /> Search the atlas</button>
      <nav aria-label="Economic areas">{navigation.regions.map((area, index) => { const Icon = areaIcons[index]; return <Link key={area.href} href={area.href} aria-current={pathname.replace(/\/$/, "") === area.href ? "page" : undefined}><Icon /><span>{area.title}</span></Link>; })}</nav>
      <Link className="atlas-link" href="/atlas"><Compass /> Browse the full atlas</Link>
    </aside></div>}
    {searchOpen && <div className="overlay search-overlay" role="presentation" onMouseDown={() => setSearchOpen(false)}><section className="search-palette" role="dialog" aria-modal="true" aria-label="Search the economic atlas" onMouseDown={(event) => event.stopPropagation()}>
      <div className="search-input"><Search aria-hidden /><label className="sr-only" htmlFor="atlas-search">Search questions, topics, charts, indicators, and areas</label><input id="atlas-search" ref={inputRef} value={query} onChange={(event) => { setQuery(event.target.value); setActive(0); }} onKeyDown={searchKeyDown} placeholder="Search questions, topics, charts…" autoComplete="off" /><button aria-label="Close search" onClick={() => setSearchOpen(false)}><X /></button></div>
      <div className="search-results" role="listbox" aria-label="Search results">{results.map((group) => <section key={group.kind}><h2>{group.label}</h2>{group.items.map((item) => { const index = flatResults.indexOf(item); return <button key={item.id} role="option" aria-selected={index === active} onMouseEnter={() => setActive(index)} onClick={() => choose(item)}><span>{item.title}</span><small>{group.label.slice(0, -1)}</small></button>; })}</section>)}{!flatResults.length && <div className="search-empty"><strong>No atlas entries found</strong><p>Try a broader term or another spelling.</p></div>}</div>
      <footer><span><kbd>↑</kbd><kbd>↓</kbd> navigate</span><span><kbd>↵</kbd> open</span><span><kbd>esc</kbd> close</span></footer>
    </section></div>}
  </>;
}
