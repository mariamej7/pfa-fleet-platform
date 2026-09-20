import {
  getDashboardSummary,
  type DashboardSummary,
} from "@/lib/api";


export default async function DashboardPage() {
  let summary: DashboardSummary;

  try {
    summary = await getDashboardSummary();
  } catch {
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
            Données temporairement indisponibles
          </h2>

          <p className="mt-2 text-amber-900">
            Le service d&apos;analyse peut mettre quelques secondes à redémarrer.
            Actualisez la page pour réessayer.
          </p>

          <a
            className="mt-5 inline-flex rounded-lg bg-amber-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-amber-800"
            href="/dashboard"
          >
            Réessayer
          </a>
        </div>
      </div>
    );
  }

  const nombreVehicules = summary.nombre_vehicules ?? 0;
  const distanceTotale = summary.distance_totale_km ?? 0;
  const alertesFinales = summary.nb_alertes_finales_uniques ?? 0;
  const alertesCritiques = summary.nb_alertes_p1_critiques ?? 0;

  return (
    <div>

      {/* Titre */}
      <div className="mb-8">

        <p className="mb-2 text-sm font-semibold text-blue-600">
          Vue d&apos;ensemble
        </p>

        <h1 className="text-3xl font-bold text-slate-900">
          Tableau de bord flotte
        </h1>

        <p className="mt-2 text-slate-500">
          Synthèse des performances de la flotte et des événements
          liés au carburant.
        </p>

      </div>


      {/* KPI */}
      <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">

        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">

          <p className="text-sm font-medium text-slate-500">
            Véhicules
          </p>

          <p className="mt-2 text-3xl font-bold">
            {Math.round(nombreVehicules)}
          </p>

          <p className="mt-2 text-xs text-slate-400">
            Véhicules analysés
          </p>

        </div>


        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">

          <p className="text-sm font-medium text-slate-500">
            Distance totale
          </p>

          <p className="mt-2 text-3xl font-bold">
            {distanceTotale.toLocaleString("fr-FR", {
              maximumFractionDigits: 1,
            })}{" "}
            km
          </p>

          <p className="mt-2 text-xs text-slate-400">
            Sur la période analysée
          </p>

        </div>


        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">

          <p className="text-sm font-medium text-slate-500">
            Alertes finales
          </p>

          <p className="mt-2 text-3xl font-bold">
            {alertesFinales}
          </p>

          <p className="mt-2 text-xs text-slate-400">
            Événements à investiguer
          </p>

        </div>


        <div className="rounded-xl border border-red-100 bg-white p-6 shadow-sm">

          <p className="text-sm font-medium text-slate-500">
            Alertes critiques
          </p>

          <p className="mt-2 text-3xl font-bold text-red-600">
            {alertesCritiques}
          </p>

          <p className="mt-2 text-xs text-slate-400">
            Priorité P1
          </p>

        </div>

      </div>


      {/* Informations secondaires */}
      <div className="mt-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">

        <h2 className="text-lg font-semibold">
          Synthèse des données
        </h2>

        <div className="mt-6 grid gap-6 md:grid-cols-3">

          <div>
            <p className="text-sm text-slate-500">
              Mesures analysées
            </p>

            <p className="mt-1 text-xl font-semibold">
              {(summary.nombre_total_mesures ?? 0).toLocaleString(
                "fr-FR"
              )}
            </p>
          </div>


          <div>
            <p className="text-sm text-slate-500">
              Ravitaillements potentiels
            </p>

            <p className="mt-1 text-xl font-semibold">
              {summary.nb_ravitaillements_potentiels ?? 0}
            </p>
          </div>


          <div>
            <p className="text-sm text-slate-500">
              Candidats détectés par IA
            </p>

            <p className="mt-1 text-xl font-semibold">
              {summary.nb_candidats_ia ?? 0}
            </p>
          </div>

        </div>

      </div>

    </div>
  );
}
