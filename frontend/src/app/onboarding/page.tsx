"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Sparkles, CheckCircle2, ArrowRight } from "lucide-react";
import { recommendationsApi, ratingsApi } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import StarRating from "@/components/StarRating";
import toast from "react-hot-toast";

export default function OnboardingPage() {
  const { isAuthenticated } = useAuthStore();
  const router = useRouter();
  const [ratings, setRatings] = useState<Record<number, number>>({});

  const { data: popular = [], isLoading } = useQuery({
    queryKey: ["popular-onboarding"],
    queryFn: () => recommendationsApi.popular(15),
    enabled: isAuthenticated,
  });

  const rateMutation = useMutation({
    mutationFn: ({ movie_id, rating }: { movie_id: number; rating: number }) =>
      ratingsApi.rate(movie_id, rating),
  });

  const handleRate = (movieId: number, rating: number) => {
    setRatings((r) => ({ ...r, [movieId]: rating }));
    rateMutation.mutate({ movie_id: movieId, rating });
  };

  const handleFinish = () => {
    if (Object.keys(ratings).length < 3) {
      toast.error("Please rate at least 3 movies to get personalized recommendations");
      return;
    }
    toast.success("Preferences saved! Your recommendations are ready.");
    router.push("/");
  };

  const ratedCount = Object.keys(ratings).length;

  if (!isAuthenticated) {
    router.push("/login");
    return null;
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-10 space-y-8">
      {/* Header */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center gap-2 bg-accent-soft border border-accent/30 text-accent text-sm px-4 py-2 rounded-full">
          <Sparkles className="w-4 h-4" />
          Cold Start Setup
        </div>
        <h1 className="text-3xl font-bold">Rate some movies to get started</h1>
        <p className="text-text-secondary">
          Rate at least 3 films you&apos;ve seen. The more you rate, the better your recommendations.
        </p>
        <div className="flex items-center justify-center gap-2 text-sm">
          <span className={`font-medium ${ratedCount >= 3 ? "text-green-400" : "text-accent"}`}>
            {ratedCount} rated
          </span>
          <span className="text-muted">/ 3 minimum</span>
        </div>
      </div>

      {/* Movie list */}
      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-20 bg-card rounded-xl animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          {popular.map((movie) => (
            <div
              key={movie.id}
              className="bg-card border border-border rounded-xl p-4 flex items-center gap-4"
            >
              {/* Poster placeholder */}
              <div className="w-12 h-16 rounded-lg bg-gradient-to-br from-violet-800 to-gray-900 flex-shrink-0 flex items-center justify-center text-white/40 text-xs font-bold">
                {movie.title.slice(0, 2).toUpperCase()}
              </div>

              {/* Info */}
              <div className="flex-1 min-w-0">
                <h3 className="font-medium text-text-primary truncate">{movie.title}</h3>
                <p className="text-xs text-text-secondary">
                  {movie.year} · {movie.genres?.split(",")[0]?.trim()}
                </p>
              </div>

              {/* Rating */}
              <div className="flex items-center gap-3 flex-shrink-0">
                {ratings[movie.id] ? (
                  <CheckCircle2 className="w-4 h-4 text-green-400" />
                ) : (
                  <span className="text-xs text-muted">Haven&apos;t seen it</span>
                )}
                <StarRating
                  value={ratings[movie.id] ?? 0}
                  onChange={(r) => handleRate(movie.id, r)}
                  size="sm"
                />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* CTA */}
      <div className="flex justify-center">
        <button
          onClick={handleFinish}
          className="flex items-center gap-2 bg-accent hover:bg-accent-hover text-white font-medium px-8 py-3 rounded-xl transition-colors disabled:opacity-50"
          disabled={ratedCount === 0}
        >
          {ratedCount >= 3 ? "Get my recommendations" : "Skip for now"}
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
