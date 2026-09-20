"use client";

import { useEffect } from "react";


export default function DashboardError({
  error,
  retry,
}: {
  error: Error & { digest?: string };
  retry: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div>
      <div className="mb-8">
        <p className="mb-2 text-sm font-semibold text-blue-600">
          Vue d&apos;ensemble
        </p>

        <h1 className="text-3xl font-bold text-slate-900">
          Tableau de bord flotte
        </h1>
      </div>

      <div
        className="max-w-2xl rounded-xl border border-amber-200 bg-amber-50 p-6"
        role="alert"
      >
        <h2 className="text-lg font-semibold text-amber-950">
          Impossible de charger le tableau de bord
        </h2>

        <p className="mt-2 text-amber-900">
          Le backend est peut-être en cours de redémarrage. Réessayez dans
          quelques secondes.
        </p>

        <button
          className="mt-5 rounded-lg bg-amber-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-amber-800"
          onClick={() => retry()}
          type="button"
        >
          Réessayer
        </button>
      </div>
    </div>
  );
}
