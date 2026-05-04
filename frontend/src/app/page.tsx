"use client";

import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { Sparkles, TrendingUp, ArrowRight } from "lucide-react";
import { recommendationsApi } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import MovieGrid from "@/components/MovieGrid";
import SearchBar from "@/components/SearchBar";
import Link from "next/link";

export default function HomePage() {
  const { isAuthenticated } = useAuthStore();
  const router = useRouter();

  const { data: popular = [], isLoading: loadingPopular } = useQuery({
    queryKey: ["popular"],
    queryFn: () => recommendationsApi.popular(18),
  });

  const { data: personal = [], isLoading: loadingPersonal } = useQuery({
    queryKey: ["personal"],
    queryFn: () => recommendationsApi.personal(12),
    enabled: isAuthenticated,
  });

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-12">
      {/* Hero */}
      <section className="text-center space-y-6 py-8">
        <div className="inline-flex items-center gap-2 bg-accent-soft border border-accent/30 text-accent text-xs px-3 py-1.5 rounded-full">
          <Sparkles className="w-3 h-3" />
          AI-powered recommendations
        </div>
        <h1 className="text-5xl font-bold text-gradient leading-tight">
          Find Your Next
          <br />
          Favorite Film
        </h1>
        <p className="text-text-secondary max-w-md mx-auto">
          Hybrid recommendation engine combining collaborative filtering, content similarity, and popularity scoring.
        </p>
        <div className="flex justify-center">
          <SearchBar />
        </div>
        {!isAuthenticated && (
          <div className="flex items-center justify-center gap-4 text-sm">
            <Link
              href="/register"
              className="bg-accent hover:bg-accent-hover text-white px-6 py-2.5 rounded-xl transition-colors font-medium"
            >
              Get started free
            </Link>
            <Link href="/search" className="text-text-secondary hover:text-text-primary transition-colors flex items-center gap-1">
              Browse movies <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        )}
      </section>

      {/* Personal recommendations */}
      {isAuthenticated && (
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-accent" />
              Recommended for You
            </h2>
            <Link href="/dashboard" className="text-sm text-accent hover:underline flex items-center gap-1">
              View all <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          <MovieGrid movies={personal} loading={loadingPersonal} emptyMessage="Rate some movies to get personalized recommendations!" />
        </section>
      )}

      {/* Popular */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-cyan" />
            Popular Now
          </h2>
          <Link href="/search?sort_by=popularity" className="text-sm text-accent hover:underline flex items-center gap-1">
            See all <ArrowRight className="w-3 h-3" />
          </Link>
        </div>
        <MovieGrid movies={popular} loading={loadingPopular} />
      </section>
    </div>
  );
}
