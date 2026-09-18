"use client";

import {
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  AlertTriangle,
  BrainCircuit,
  CheckCircle2,
  Loader2,
  Search,
  Sparkles,
  TrendingDown,
  Truck,
} from "lucide-react";


const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";


type Vehicle = {
  deviceId: number;

  nb_baisses_analysees?: number | null;
  nb_candidats_ia?: number | null;

  nb_alertes_regles?: number | null;
  nb_overlap_regles_ia?: number | null;

  nb_alertes_ia_uniquement?: number | null;
  nb_alertes_regle_uniquement?: number | null;
};


type FuelAlert = {
  alert_id: string;

  deviceId: number | null;
  fixTime: string | null;

  source_detection: string | null;

  fuelLevel: number | null;
  drop_abs_pct: number | null;

  ai_anomaly_score: number | null;
  ai_score_percentile: number | null;

  contexte_temporel: string | null;

  confidence_level: string | null;

  rang_priorite: number | null;
  priorite_alerte: string | null;

  statut_validation: string | null;
};


export default function AnalyticsPage() {

  const [vehicles, setVehicles] =
    useState<Vehicle[]>([]);

  const [alerts, setAlerts] =
    useState<FuelAlert[]>([]);

  const [isLoading, setIsLoading] =
    useState(true);

  const [errorMessage, setErrorMessage] =
    useState<string | null>(null);

  const [vehicleFilter, setVehicleFilter] =
    useState("Tous");

  const [sourceFilter, setSourceFilter] =
    useState("Toutes");

  const [search, setSearch] =
    useState("");


  // ============================================================
  // CHARGEMENT
  // ============================================================

  useEffect(() => {

    async function loadData() {

      setIsLoading(true);
      setErrorMessage(null);

      try {

        const [
          vehiclesResponse,
          alertsResponse,
        ] = await Promise.all([

          fetch(
            `${API_URL}/api/vehicles`,
            {
              cache: "no-store",
            }
          ),

          fetch(
            `${API_URL}/api/alerts`,
            {
              cache: "no-store",
            }
          ),

        ]);


        if (!vehiclesResponse.ok) {

          throw new Error(
            "Impossible de récupérer les indicateurs IA des véhicules."
          );
        }


        if (!alertsResponse.ok) {

          throw new Error(
            "Impossible de récupérer les événements détectés."
          );
        }


        const vehicleData: Vehicle[] =
          await vehiclesResponse.json();

        const alertData: FuelAlert[] =
          await alertsResponse.json();


        setVehicles(
          vehicleData
        );

        setAlerts(
          alertData
        );

      } catch (error) {

        if (error instanceof Error) {

          setErrorMessage(
            error.message
          );

        } else {

          setErrorMessage(
            "Une erreur est survenue."
          );
        }

      } finally {

        setIsLoading(false);
      }
    }


    loadData();

  }, []);


  // ============================================================
  // KPI
  // ============================================================

  const totalAnalyzedDrops =
    vehicles.reduce(
      (total, vehicle) =>
        total +
        (
          vehicle.nb_baisses_analysees ??
          0
        ),
      0
    );


  const totalAiCandidates =
    vehicles.reduce(
      (total, vehicle) =>
        total +
        (
          vehicle.nb_candidats_ia ??
          0
        ),
      0
    );


  const totalRuleAlerts =
    vehicles.reduce(
      (total, vehicle) =>
        total +
        (
          vehicle.nb_alertes_regles ??
          0
        ),
      0
    );


  const totalOverlap =
    vehicles.reduce(
      (total, vehicle) =>
        total +
        (
          vehicle.nb_overlap_regles_ia ??
          0
        ),
      0
    );


  const totalAiOnly =
    vehicles.reduce(
      (total, vehicle) =>
        total +
        (
          vehicle.nb_alertes_ia_uniquement ??
          0
        ),
      0
    );


  // ============================================================
  // EVENEMENTS IA
  // ============================================================

  const aiAlerts =
    useMemo(() => {

      return alerts.filter(
        (alert) =>
          alert.source_detection ===
            "IA uniquement" ||
          alert.source_detection ===
            "Règle + IA"
      );

    }, [alerts]);


  // ============================================================
  // VEHICULES
  // ============================================================

  const vehicleIds =
    useMemo(() => {

      return vehicles
        .map(
          (vehicle) =>
            vehicle.deviceId
        )
        .sort(
          (a, b) => a - b
        );

    }, [vehicles]);


  // ============================================================
  // FILTRES
  // ============================================================

  const filteredAlerts =
    useMemo(() => {

      return aiAlerts.filter(
        (alert) => {

          const matchesVehicle =
            vehicleFilter === "Tous" ||
            String(
              alert.deviceId
            ) === vehicleFilter;


          const matchesSource =
            sourceFilter === "Toutes" ||
            alert.source_detection ===
              sourceFilter;


          const searchValue =
            search
              .trim()
              .toLowerCase();


          const matchesSearch =
            searchValue === "" ||
            String(
              alert.deviceId ?? ""
            ).includes(
              searchValue
            ) ||
            (
              alert.alert_id ?? ""
            )
              .toLowerCase()
              .includes(
                searchValue
              );


          return (
            matchesVehicle &&
            matchesSource &&
            matchesSearch
          );
        }
      );

    }, [
      aiAlerts,
      vehicleFilter,
      sourceFilter,
      search,
    ]);


  return (
    <div>

      {/* ===================================================== */}
      {/* EN-TETE */}
      {/* ===================================================== */}

      <div className="mb-8">

        <p className="mb-2 text-sm font-semibold text-blue-600">
          Intelligence artificielle
        </p>

        <h1 className="text-3xl font-bold text-slate-900">
          Résultats IA
        </h1>

        <p className="mt-2 max-w-3xl text-slate-500">
          Analyse des variations de carburant
          atypiques identifiées par le modèle
          Isolation Forest.
        </p>

      </div>


      {/* ===================================================== */}
      {/* CHARGEMENT */}
      {/* ===================================================== */}

      {isLoading && (

        <div className="flex min-h-[350px] items-center justify-center">

          <div className="text-center">

            <Loader2
              size={34}
              className="mx-auto animate-spin text-blue-600"
            />

            <p className="mt-3 text-sm text-slate-500">
              Chargement des résultats IA...
            </p>

          </div>

        </div>
      )}


      {/* ===================================================== */}
      {/* ERREUR */}
      {/* ===================================================== */}

      {errorMessage && (

        <div className="rounded-xl border border-red-200 bg-red-50 p-5">

          <div className="flex items-center gap-3">

            <AlertTriangle
              size={22}
              className="text-red-600"
            />

            <p className="font-medium text-red-700">
              {errorMessage}
            </p>

          </div>

        </div>
      )}


      {!isLoading &&
        !errorMessage && (
          <>

            {/* ================================================= */}
            {/* KPI */}
            {/* ================================================= */}

            <div className="grid gap-4 md:grid-cols-4">

              <KpiCard
                label="Baisses analysées"
                value={
                  totalAnalyzedDrops.toLocaleString(
                    "fr-FR"
                  )
                }
                description="Variations négatives exploitables analysées par l'IA"
                icon={
                  <TrendingDown size={22} />
                }
              />


              <KpiCard
                label="Candidats IA"
                value={
                  totalAiCandidates.toLocaleString(
                    "fr-FR"
                  )
                }
                description="Événements les plus atypiques proposés par Isolation Forest"
                icon={
                  <BrainCircuit size={22} />
                }
              />


              <KpiCard
                label="Règle + IA"
                value={
                  totalOverlap.toLocaleString(
                    "fr-FR"
                  )
                }
                description="Événements retrouvés par les deux approches"
                icon={
                  <CheckCircle2 size={22} />
                }
              />


              <KpiCard
                label="IA uniquement"
                value={
                  totalAiOnly.toLocaleString(
                    "fr-FR"
                  )
                }
                description="Événements proposés uniquement par le modèle"
                icon={
                  <Sparkles size={22} />
                }
              />

            </div>


            {/* ================================================= */}
            {/* EXPLICATION IA */}
            {/* ================================================= */}

            <div className="mt-6 rounded-xl border border-blue-100 bg-blue-50/50 p-6">

              <div className="flex items-start gap-4">

                <div className="rounded-lg bg-white p-3 text-blue-600">
                  <BrainCircuit
                    size={24}
                  />
                </div>


                <div>

                  <h2 className="font-semibold text-slate-900">
                    Quel est le rôle d&apos;Isolation Forest ?
                  </h2>


                  <p className="mt-2 text-sm leading-6 text-slate-600">

                    Le modèle analyse les baisses de
                    carburant et attribue un score
                    d&apos;anomalie à chaque événement.
                    Les observations les plus inhabituelles
                    sont proposées comme
                    <strong>
                      {" "}candidats à investiguer
                    </strong>
                    .

                  </p>


                  <p className="mt-2 text-xs leading-5 text-slate-500">

                    Le modèle ne confirme pas un vol,
                    une fuite ou une fraude.
                    Il sert à réduire le volume de données
                    que l&apos;utilisateur doit examiner manuellement.

                  </p>

                </div>

              </div>

            </div>


            {/* ================================================= */}
            {/* CONCORDANCE */}
            {/* ================================================= */}

            <div className="mt-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">

              <h2 className="font-semibold text-slate-900">
                Concordance entre les règles et l&apos;IA
              </h2>


              {totalRuleAlerts > 0 ? (

                <>

                  <p className="mt-4 text-3xl font-bold text-slate-900">

                    {totalOverlap}
                    {" sur "}
                    {totalRuleAlerts}

                  </p>


                  <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">

                    événements détectés par les règles
                    métier sont également retrouvés
                    parmi les candidats identifiés
                    par Isolation Forest.

                  </p>


                  <p className="mt-3 text-xs leading-5 text-slate-500">

                    Cette concordance montre que les
                    deux méthodes identifient plusieurs
                    événements communs.
                    Elle ne constitue pas une accuracy,
                    une précision ou un taux de réussite
                    du modèle.

                  </p>

                </>

              ) : (

                <p className="mt-3 text-sm text-slate-500">
                  Aucun événement n&apos;a été détecté
                  par les règles métier pour ce dataset.
                </p>
              )}

            </div>


            {/* ================================================= */}
            {/* RESULTATS PAR VEHICULE */}
            {/* ================================================= */}

            <div className="mt-8">

              <h2 className="text-xl font-bold text-slate-900">
                Résultats IA par véhicule
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                Répartition des observations analysées
                et des candidats proposés par le modèle.
              </p>


              <div className="mt-4 grid gap-4 lg:grid-cols-3">

                {vehicles.map(
                  (vehicle) => (

                    <VehicleAiCard
                      key={
                        vehicle.deviceId
                      }
                      vehicle={
                        vehicle
                      }
                    />

                  )
                )}

              </div>

            </div>


            {/* ================================================= */}
            {/* EVENEMENTS IA */}
            {/* ================================================= */}

            <div className="mt-8">

              <h2 className="text-xl font-bold text-slate-900">
                Événements identifiés par l&apos;IA
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                Liste des candidats IA actuellement
                disponibles pour investigation.
              </p>


              {/* FILTRES */}

              <div className="mt-5 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">

                <div className="grid gap-4 md:grid-cols-3">


                  {/* RECHERCHE */}

                  <div>

                    <label className="mb-2 block text-xs font-semibold text-slate-600">
                      Rechercher
                    </label>

                    <div className="relative">

                      <Search
                        size={17}
                        className="absolute left-3 top-3 text-slate-400"
                      />

                      <input
                        value={search}
                        onChange={
                          (event) =>
                            setSearch(
                              event.target.value
                            )
                        }
                        placeholder="Véhicule ou ID..."
                        className="w-full rounded-lg border border-slate-200 py-2.5 pl-10 pr-3 text-sm outline-none transition focus:border-blue-500"
                      />

                    </div>

                  </div>


                  {/* VEHICULE */}

                  <div>

                    <label className="mb-2 block text-xs font-semibold text-slate-600">
                      Véhicule
                    </label>

                    <select
                      value={
                        vehicleFilter
                      }
                      onChange={
                        (event) =>
                          setVehicleFilter(
                            event.target.value
                          )
                      }
                      className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-blue-500"
                    >

                      <option value="Tous">
                        Tous
                      </option>

                      {vehicleIds.map(
                        (deviceId) => (

                          <option
                            key={
                              deviceId
                            }
                            value={
                              String(
                                deviceId
                              )
                            }
                          >
                            {deviceId}
                          </option>

                        )
                      )}

                    </select>

                  </div>


                  {/* SOURCE */}

                  <div>

                    <label className="mb-2 block text-xs font-semibold text-slate-600">
                      Source
                    </label>

                    <select
                      value={
                        sourceFilter
                      }
                      onChange={
                        (event) =>
                          setSourceFilter(
                            event.target.value
                          )
                      }
                      className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-blue-500"
                    >

                      <option value="Toutes">
                        Toutes
                      </option>

                      <option value="IA uniquement">
                        IA uniquement
                      </option>

                      <option value="Règle + IA">
                        Règle + IA
                      </option>

                    </select>

                  </div>

                </div>


                <p className="mt-4 text-sm text-slate-500">

                  <strong className="text-slate-900">
                    {
                      filteredAlerts.length
                    }
                  </strong>{" "}

                  candidat(s) affiché(s)

                </p>

              </div>


              {/* TABLEAU */}

              <div className="mt-5 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">

                <div className="overflow-x-auto">

                  <table className="min-w-full">

                    <thead className="bg-slate-50">

                      <tr>

                        <TableHeader>
                          Véhicule
                        </TableHeader>

                        <TableHeader>
                          Date
                        </TableHeader>

                        <TableHeader>
                          Baisse
                        </TableHeader>

                        <TableHeader>
                          Score d&apos;anomalie
                        </TableHeader>

                        <TableHeader>
                          Source
                        </TableHeader>

                        <TableHeader>
                          Contexte temporel
                        </TableHeader>

                        <TableHeader>
                          Priorité
                        </TableHeader>

                      </tr>

                    </thead>


                    <tbody className="divide-y divide-slate-100">

                      {filteredAlerts.map(
                        (alert) => (

                          <tr
                            key={
                              alert.alert_id
                            }
                            className="transition hover:bg-slate-50"
                          >

                            {/* VEHICULE */}

                            <td className="whitespace-nowrap px-4 py-4">

                              <div className="flex items-center gap-2">

                                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-50 text-blue-600">

                                  <Truck
                                    size={16}
                                  />

                                </div>

                                <span className="font-semibold text-slate-900">
                                  {
                                    alert.deviceId ??
                                    "—"
                                  }
                                </span>

                              </div>

                            </td>


                            {/* DATE */}

                            <td className="whitespace-nowrap px-4 py-4 text-sm text-slate-600">

                              {formatDateTime(
                                alert.fixTime
                              )}

                            </td>


                            {/* BAISSE */}

                            <td className="whitespace-nowrap px-4 py-4">

                              <span className="font-semibold text-slate-900">

                                {formatNumber(
                                  alert.drop_abs_pct,
                                  2
                                )}
                                {" %"}

                              </span>

                            </td>


                            {/* SCORE */}

                            <td className="whitespace-nowrap px-4 py-4">

                              {alert.ai_score_percentile !=
                              null ? (

                                <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">

                                  {formatNumber(
                                    alert.ai_score_percentile,
                                    2
                                  )}
                                  {" %"}

                                </span>

                              ) : (

                                <span className="text-sm text-slate-400">
                                  —
                                </span>
                              )}

                            </td>


                            {/* SOURCE */}

                            <td className="whitespace-nowrap px-4 py-4">

                              <SourceBadge
                                source={
                                  alert.source_detection
                                }
                              />

                            </td>


                            {/* CONTEXTE */}

                            <td className="px-4 py-4 text-sm text-slate-600">

                              {
                                alert.contexte_temporel ??
                                "—"
                              }

                            </td>


                            {/* PRIORITE */}

                            <td className="whitespace-nowrap px-4 py-4">

                              <PriorityBadge
                                rank={
                                  alert.rang_priorite
                                }
                              />

                            </td>

                          </tr>
                        )
                      )}

                    </tbody>

                  </table>

                </div>


                {filteredAlerts.length ===
                  0 && (

                  <div className="px-6 py-14 text-center">

                    <BrainCircuit
                      size={32}
                      className="mx-auto text-slate-300"
                    />

                    <p className="mt-3 font-medium text-slate-700">
                      Aucun candidat IA trouvé
                    </p>

                    <p className="mt-1 text-sm text-slate-500">
                      Modifiez les filtres sélectionnés.
                    </p>

                  </div>
                )}

              </div>

            </div>

          </>
        )}

    </div>
  );
}


// ============================================================
// KPI CARD
// ============================================================

function KpiCard({
  label,
  value,
  description,
  icon,
}: {
  label: string;
  value: string;
  description: string;
  icon: ReactNode;
}) {

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">

      <div className="flex items-start justify-between gap-3">

        <div>

          <p className="text-sm text-slate-500">
            {label}
          </p>

          <p className="mt-2 text-2xl font-bold text-slate-900">
            {value}
          </p>

        </div>


        <div className="rounded-lg bg-blue-50 p-2.5 text-blue-600">
          {icon}
        </div>

      </div>


      <p className="mt-3 text-xs leading-5 text-slate-400">
        {description}
      </p>

    </div>
  );
}


// ============================================================
// CARTE VEHICULE
// ============================================================

function VehicleAiCard({
  vehicle,
}: {
  vehicle: Vehicle;
}) {

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">

      <div className="flex items-center gap-3">

        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-50 text-blue-600">

          <Truck
            size={20}
          />

        </div>


        <div>

          <p className="text-xs text-slate-400">
            Véhicule
          </p>

          <p className="text-lg font-bold text-slate-900">
            {vehicle.deviceId}
          </p>

        </div>

      </div>


      <div className="mt-5 grid grid-cols-2 gap-3">

        <SmallMetric
          label="Baisses analysées"
          value={
            String(
              vehicle.nb_baisses_analysees ??
              0
            )
          }
        />

        <SmallMetric
          label="Candidats IA"
          value={
            String(
              vehicle.nb_candidats_ia ??
              0
            )
          }
        />

        <SmallMetric
          label="Règle + IA"
          value={
            String(
              vehicle.nb_overlap_regles_ia ??
              0
            )
          }
        />

        <SmallMetric
          label="IA uniquement"
          value={
            String(
              vehicle.nb_alertes_ia_uniquement ??
              0
            )
          }
        />

      </div>

    </div>
  );
}


// ============================================================
// SMALL METRIC
// ============================================================

function SmallMetric({
  label,
  value,
}: {
  label: string;
  value: string;
}) {

  return (
    <div className="rounded-lg bg-slate-50 p-3">

      <p className="text-xs text-slate-500">
        {label}
      </p>

      <p className="mt-1 text-sm font-semibold text-slate-900">
        {value}
      </p>

    </div>
  );
}


// ============================================================
// SOURCE BADGE
// ============================================================

function SourceBadge({
  source,
}: {
  source: string | null;
}) {

  if (!source) {

    return (
      <span className="text-sm text-slate-400">
        —
      </span>
    );
  }


  const className =
    source === "Règle + IA"
      ? "bg-emerald-50 text-emerald-700"
      : "bg-blue-50 text-blue-700";


  return (
    <span
      className={`rounded-full px-3 py-1 text-xs font-semibold ${className}`}
    >
      {source}
    </span>
  );
}


// ============================================================
// PRIORITE
// ============================================================

function PriorityBadge({
  rank,
}: {
  rank: number | null;
}) {

  if (rank == null) {

    return (
      <span className="text-slate-400">
        —
      </span>
    );
  }


  const classes: Record<number, string> = {

    1:
      "bg-red-50 text-red-700",

    2:
      "bg-orange-50 text-orange-700",

    3:
      "bg-blue-50 text-blue-700",

    4:
      "bg-slate-100 text-slate-700",

    5:
      "bg-amber-50 text-amber-700",
  };


  return (
    <span
      className={`rounded-full px-3 py-1 text-xs font-bold ${
        classes[rank] ??
        "bg-slate-100 text-slate-700"
      }`}
    >
      P{rank}
    </span>
  );
}


// ============================================================
// HEADER TABLE
// ============================================================

function TableHeader({
  children,
}: {
  children: ReactNode;
}) {

  return (
    <th className="whitespace-nowrap px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
      {children}
    </th>
  );
}


// ============================================================
// FORMATAGE
// ============================================================

function formatNumber(
  value:
    | number
    | null
    | undefined,
  decimals = 1
) {

  if (
    value == null ||
    Number.isNaN(value)
  ) {
    return "—";
  }

  return value.toLocaleString(
    "fr-FR",
    {
      minimumFractionDigits:
        decimals,

      maximumFractionDigits:
        decimals,
    }
  );
}


function formatDateTime(
  value:
    | string
    | null
    | undefined
) {

  if (!value) {
    return "—";
  }

  const date =
    new Date(value);

  if (
    Number.isNaN(
      date.getTime()
    )
  ) {
    return value;
  }

  return date.toLocaleString(
    "fr-FR",
    {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }
  );
}