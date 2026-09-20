export default function DashboardLoading() {
  return (
    <div>
      <div className="mb-8">
        <p className="mb-2 text-sm font-semibold text-blue-600">
          Vue d&apos;ensemble
        </p>

        <h1 className="text-3xl font-bold text-slate-900">
          Tableau de bord flotte
        </h1>

        <p className="mt-2 text-slate-500">
          Connexion au service d&apos;analyse en cours…
        </p>
      </div>

      <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4" aria-hidden="true">
        {[0, 1, 2, 3].map((item) => (
          <div
            className="h-36 animate-pulse rounded-xl border border-slate-200 bg-white shadow-sm"
            key={item}
          />
        ))}
      </div>
    </div>
  );
}
