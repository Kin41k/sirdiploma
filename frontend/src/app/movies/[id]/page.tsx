"use client";

import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Star, Clock, Calendar, Globe, ThumbsUp } from "lucide-react";
import { moviesApi, ratingsApi } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import StarRating from "@/components/StarRating";
import SimilarMovies from "@/components/SimilarMovies";
import toast from "react-hot-toast";

export default function MovieDetailPage() {
  const { id } = useParams();
  const movieId = Number(id);
  const { isAuthenticated } = useAuthStore();
  const queryClient = useQueryClient();

  const { data: movie, isLoading } = useQuery({
    queryKey: ["movie", movieId],
    queryFn: () => moviesApi.detail(movieId),
  });

  const rateMutation = useMutation({
    mutationFn: (rating: number) => ratingsApi.rate(movieId, rating),
    onSuccess: () => {
      toast.success("Rating saved!");
      queryClient.invalidateQueries({ queryKey: ["movie", movieId] });
    },
    onError: () => toast.error("Failed to save rating"),
  });

  if (isLoading) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-10 animate-pulse space-y-4">
        <div className="h-8 bg-card rounded w-1/2" />
        <div className="h-64 bg-card rounded" />
      </div>
    );
  }

  if (!movie) return <div className="text-center py-20 text-text-secondary">Movie not found</div>;

  const genres = movie.genres?.split(",").map((g) => g.trim()) ?? [];
  const keywords = movie.keywords?.split(",").slice(0, 10).map((k) => k.trim()) ?? [];

  return (
    <div className="max-w-5xl mx-auto px-4 py-10 space-y-10">
      {/* Header */}
      <div className="flex flex-col md:flex-row gap-8">
        {/* Poster */}
        <div className="flex-shrink-0 w-48 md:w-56">
          {movie.poster_url ? (
            <img
              src={movie.poster_url}
              alt={movie.title}
              className="w-full rounded-xl border border-border"
            />
          ) : (
            <div className="w-full aspect-[2/3] rounded-xl bg-gradient-to-br from-violet-800 to-gray-900 flex items-center justify-center">
              <span className="text-4xl font-bold text-white/30">{movie.title.slice(0, 2).toUpperCase()}</span>
            </div>
          )}
        </div>

        {/* Info */}
        <div className="flex-1 space-y-4">
          <h1 className="text-3xl font-bold text-text-primary leading-tight">{movie.title}</h1>

          {/* Meta */}
          <div className="flex flex-wrap items-center gap-4 text-sm text-text-secondary">
            <span className="flex items-center gap-1">
              <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
              <span className="font-medium text-text-primary">{movie.vote_average.toFixed(1)}</span>
              <span>({movie.vote_count.toLocaleString()} votes)</span>
            </span>
            {movie.year && (
              <span className="flex items-center gap-1">
                <Calendar className="w-4 h-4" /> {movie.year}
              </span>
            )}
            {movie.runtime && (
              <span className="flex items-center gap-1">
                <Clock className="w-4 h-4" /> {movie.runtime} min
              </span>
            )}
            {movie.original_language && (
              <span className="flex items-center gap-1">
                <Globe className="w-4 h-4" /> {movie.original_language.toUpperCase()}
              </span>
            )}
          </div>

          {/* Genres */}
          {genres.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {genres.map((g) => (
                <span key={g} className="bg-accent-soft text-accent text-xs px-3 py-1 rounded-full border border-accent/20">
                  {g}
                </span>
              ))}
            </div>
          )}

          {/* Overview */}
          {movie.overview && (
            <p className="text-text-secondary leading-relaxed">{movie.overview}</p>
          )}

          {/* User rating */}
          {isAuthenticated && (
            <div className="pt-2">
              <p className="text-xs text-muted mb-2 uppercase tracking-wide">Your rating</p>
              <StarRating
                value={movie.user_rating ?? 0}
                onChange={(r) => rateMutation.mutate(r)}
                size="lg"
              />
            </div>
          )}

          {/* Keywords */}
          {keywords.length > 0 && (
            <div className="flex flex-wrap gap-1.5 pt-2">
              {keywords.map((k) => (
                <span key={k} className="text-xs bg-surface border border-border px-2 py-0.5 rounded-md text-text-secondary">
                  #{k}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Similar movies */}
      <SimilarMovies movies={movie.similar_movies} />
    </div>
  );
}
