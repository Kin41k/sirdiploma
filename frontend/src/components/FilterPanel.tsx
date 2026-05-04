"use client";

import { useState } from "react";
import { SlidersHorizontal, ChevronDown } from "lucide-react";
import type { MovieFilters } from "@/types/movie";

const GENRES = [
  "Action", "Adventure", "Animation", "Comedy", "Crime", "Documentary",
  "Drama", "Fantasy", "Horror", "History", "Music", "Mystery",
  "Romance", "Science Fiction", "Thriller", "War", "Western",
];

const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "fr", label: "French" },
  { code: "de", label: "German" },
  { code: "es", label: "Spanish" },
  { code: "ja", label: "Japanese" },
  { code: "ko", label: "Korean" },
  { code: "zh", label: "Chinese" },
  { code: "it", label: "Italian" },
  { code: "ru", label: "Russian" },
];

interface Props {
  filters: MovieFilters;
  onChange: (filters: MovieFilters) => void;
}

export default function FilterPanel({ filters, onChange }: Props) {
  const [open, setOpen] = useState(false);

  const update = (key: keyof MovieFilters, value: unknown) =>
    onChange({ ...filters, [key]: value || undefined, page: 1 });

  return (
    <div className="w-full">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 text-sm text-text-secondary hover:text-text-primary border border-border rounded-lg px-3 py-2 transition-colors"
      >
        <SlidersHorizontal className="w-4 h-4" />
        Filters
        <ChevronDown className={`w-4 h-4 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>

      {open && (
        <div className="mt-3 p-4 bg-card border border-border rounded-xl grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 text-sm">
          {/* Genre */}
          <div className="space-y-1">
            <label className="text-xs text-muted font-medium uppercase tracking-wide">Genre</label>
            <select
              value={filters.genre || ""}
              onChange={(e) => update("genre", e.target.value)}
              className="w-full bg-surface border border-border rounded-lg px-2 py-2 text-text-primary focus:outline-none focus:border-accent"
            >
              <option value="">All</option>
              {GENRES.map((g) => <option key={g} value={g}>{g}</option>)}
            </select>
          </div>

          {/* Year from */}
          <div className="space-y-1">
            <label className="text-xs text-muted font-medium uppercase tracking-wide">Year from</label>
            <input
              type="number"
              min={1900}
              max={2025}
              value={filters.year_from || ""}
              onChange={(e) => update("year_from", +e.target.value)}
              placeholder="1900"
              className="w-full bg-surface border border-border rounded-lg px-2 py-2 text-text-primary focus:outline-none focus:border-accent"
            />
          </div>

          {/* Year to */}
          <div className="space-y-1">
            <label className="text-xs text-muted font-medium uppercase tracking-wide">Year to</label>
            <input
              type="number"
              min={1900}
              max={2025}
              value={filters.year_to || ""}
              onChange={(e) => update("year_to", +e.target.value)}
              placeholder="2024"
              className="w-full bg-surface border border-border rounded-lg px-2 py-2 text-text-primary focus:outline-none focus:border-accent"
            />
          </div>

          {/* Language */}
          <div className="space-y-1">
            <label className="text-xs text-muted font-medium uppercase tracking-wide">Language</label>
            <select
              value={filters.language || ""}
              onChange={(e) => update("language", e.target.value)}
              className="w-full bg-surface border border-border rounded-lg px-2 py-2 text-text-primary focus:outline-none focus:border-accent"
            >
              <option value="">All</option>
              {LANGUAGES.map((l) => <option key={l.code} value={l.code}>{l.label}</option>)}
            </select>
          </div>

          {/* Sort by */}
          <div className="space-y-1">
            <label className="text-xs text-muted font-medium uppercase tracking-wide">Sort by</label>
            <select
              value={filters.sort_by || "popularity"}
              onChange={(e) => update("sort_by", e.target.value)}
              className="w-full bg-surface border border-border rounded-lg px-2 py-2 text-text-primary focus:outline-none focus:border-accent"
            >
              <option value="popularity">Popularity</option>
              <option value="rating">Rating</option>
              <option value="year">Year</option>
              <option value="votes">Vote count</option>
            </select>
          </div>
        </div>
      )}
    </div>
  );
}
