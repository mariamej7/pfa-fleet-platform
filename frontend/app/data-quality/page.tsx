
"use client";

import {
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  AlertTriangle,
  CheckCircle2,
  Database,
  Gauge,
  Loader2,
  Search,
  ShieldCheck,
  Truck,
} from "lucide-react";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";

// ============================================================
// TYPES
// ============================================================

type Vehicle = {
  deviceId: number;

  nombre_mesures?: number | null;

  debut_periode?: string | null;
  fin_periode?: string | null;

  jours_calendaires_periode?: number | null;
  jours_avec_donnees?: number | null;
  jours_actifs?: number | null;

  taux_couverture_jours_pct?: number | null;

  nb_incoherences_fuel?: number | null;
  pct_incoherences_fuel?: number | null;
};

// ============================================================
// PAGE PRINCIPALE
// ============================================================

export default function DataQualityPage() {
  const [vehicles, setVehicles] =
    useState<Vehicle[]>([]);

  const [isLoading, setIsLoading] =
    useState(true);

  const [errorMessage, setErrorMessage] =
    useState<string | null>(null);

  const [search, setSearch] =
    useState("");

  // ============================================================
  // CHARGEMENT DES DONNEES
  // ============================================================

  useEffect(() => {
    async function loadQualityData() {
      setIsLoading(true);
      setErrorMessage(null);

      try {
        const response = await fetch(
          `${API_URL}/api/vehicles`,
          {
            cache: "no-store",
          }
        );

        if (!response.ok) {
          throw new Error(
            "Impossible de récupérer les indicateurs de qualité des données."
          );
        }

        const data: Vehicle[] =
          await response.json();

        setVehicles(data);
      } catch (error) {
        if (error instanceof Error) {
          setErrorMessage(error.message);
        } else {
          setErrorMessage(
            "Une erreur est survenue."
          );
        }
      } finally {
        setIsLoading(false);
      }
    }

    loadQualityData();
  }, []);

  // ============================================================
  // FILTRAGE
  // ============================================================

  const filteredVehicles = useMemo(() => {
    const value = search.trim();

    if (!value) {
      return vehicles;
    }

    return vehicles.filter(
      (vehicle) =>
        String(vehicle.deviceId).includes(value)
    );
  }, [vehicles, search]);

  // ============================================================
  // KPI
  // ============================================================

  const totalMeasurements = vehicles.reduce(
    (total, vehicle) =>
      total + (vehicle.nombre_mesures ?? 0),
    0
  );

  const totalFuelInconsistencies = vehicles.reduce(
    (total, vehicle) =>
      total + (vehicle.nb_incoherences_fuel ?? 0),
    0
  );

  const fuelInconsistencyRate =
    totalMeasurements > 0
      ? (totalFuelInconsistencies / totalMeasurements) * 100
      : 0;

  const coverageValues = vehicles
    .map(
      (vehicle) =>
        vehicle.taux_couverture_jours_pct
    )
    .filter(
      (value): value is number =>
        typeof value === "number"
    );

  const averageCoverage =
    coverageValues.length > 0
      ? coverageValues.reduce(
          (sum, value) => sum + value,
          0
        ) / coverageValues.length
      : 0;

  const vehiclesWithFuelIssues = vehicles.filter(
    (vehicle) =>
      (vehicle.nb_incoherences_fuel ?? 0) > 0
  ).length;

  const vehiclesWithIncompleteCoverage = vehicles.filter(
    (vehicle) =>
      vehicle.taux_couverture_jours_pct != null &&
      vehicle.taux_couverture_jours_pct < 100
  ).length;

  // ============================================================
  // AFFICHAGE
  // ============================================================

  return (
    <div>

      {/* ===================================================== */}
      {/* EN-TETE */}
      {/* ===================================================== */}

      <div className="mb-8">

        <p className="mb-2 text-sm font-semibold text-blue-600">
          Qualité des données
        </p>

        <h1 className="text-3xl font-bold text-slate-900">
          Qualité des données télématiques
        </h1>

        <p className="mt-2 max-w-3xl text-slate-500">
          Vérifiez la couverture temporelle
          et les incohérences du signal carburant
          avant d&apos;interpréter les résultats
          de la plateforme.
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
              Chargement des indicateurs de qualité...
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

      {/* ===================================================== */}
      {/* CONTENU */}
      {/* ===================================================== */}

      {!isLoading && !errorMessage && (
        <>

          {/* ================================================= */}
          {/* KPI */}
          {/* ================================================= */}

          <div className="grid gap-4 md:grid-cols-4">

            <KpiCard
              label="Mesures analysées"
              value={totalMeasurements.toLocaleString("fr-FR")}
              description="Mesures préparées du dataset actif"
              icon={<Database size={22} />}
            />

            <KpiCard
              label="Couverture moyenne"
              value={`${formatNumber(
                averageCoverage,
                1
              )} %`}
              description="Couverture moyenne des jours observés"
              icon={<Gauge size={22} />}
            />

            <KpiCard
              label="Incohérences carburant"
              value={totalFuelInconsistencies.toLocaleString(
                "fr-FR"
              )}
              description="Valeurs du signal carburant hors plage cohérente"
              icon={<AlertTriangle size={22} />}
            />

            <KpiCard
              label="Taux d'incohérences carburant"
              value={`${formatNumber(
                fuelInconsistencyRate,
                2
              )} %`}
              description="Part des mesures concernées dans le dataset"
              icon={
                totalFuelInconsistencies > 0 ? (
                  <AlertTriangle size={22} />
                ) : (
                  <ShieldCheck size={22} />
                )
              }
            />

          </div>

          {/* ================================================= */}
          {/* INTERPRETATION */}
          {/* ================================================= */}

          <div className="mt-6 rounded-xl border border-blue-100 bg-blue-50/50 p-6">

            <h2 className="font-semibold text-slate-900">
              Pourquoi contrôler la qualité avant l&apos;analyse ?
            </h2>

            <p className="mt-2 text-sm leading-6 text-slate-600">
              Une valeur carburant incohérente
              ou une période sans transmission
              peut produire une variation qui semble
              inhabituelle alors qu&apos;elle provient
              simplement de la qualité du signal.
            </p>

            <p className="mt-2 text-sm leading-6 text-slate-600">
              La plateforme conserve donc ces indicateurs
              afin que l&apos;utilisateur interprète
              les alertes avec le contexte nécessaire.
            </p>

            <p className="mt-3 text-xs leading-5 text-slate-500">
              Une incohérence de mesure est un problème
              de qualité des données. Elle ne doit pas être
              confondue avec une anomalie carburant réelle.
            </p>

          </div>

          {/* ================================================= */}
          {/* RESUME QUALITE */}
          {/* ================================================= */}

          <div className="mt-6 grid gap-4 md:grid-cols-2">

            <QualitySummaryCard
              title="Qualité du signal carburant"
              value={vehiclesWithFuelIssues}
              total={vehicles.length}
              description={
                vehiclesWithFuelIssues === 0
                  ? "Aucun véhicule ne présente de valeur de carburant incohérente."
                  : "Véhicule(s) présentant au moins une incohérence du signal carburant."
              }
              good={vehiclesWithFuelIssues === 0}
            />

            <QualitySummaryCard
              title="Couverture temporelle"
              value={vehiclesWithIncompleteCoverage}
              total={vehicles.length}
              description={
                vehiclesWithIncompleteCoverage === 0
                  ? "Tous les véhicules disposent de données sur l'ensemble des jours de leur période."
                  : "Véhicule(s) présentent une couverture inférieure à 100 %."
              }
              good={vehiclesWithIncompleteCoverage === 0}
            />

          </div>

          {/* ================================================= */}
          {/* RECHERCHE */}
          {/* ================================================= */}

          <div className="mt-8">

            <h2 className="text-xl font-bold text-slate-900">
              Qualité par véhicule
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Identifiez rapidement les véhicules
              nécessitant une interprétation prudente.
            </p>

            <div className="mt-5 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">

              <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">

                <div className="w-full md:max-w-sm">

                  <label className="mb-2 block text-xs font-semibold text-slate-600">
                    Rechercher un véhicule
                  </label>

                  <div className="relative">

                    <Search
                      size={17}
                      className="absolute left-3 top-3 text-slate-400"
                    />

                    <input
                      value={search}
                      onChange={(event) =>
                        setSearch(event.target.value)
                      }
                      placeholder="Ex. 701"
                      className="w-full rounded-lg border border-slate-200 py-2.5 pl-10 pr-3 text-sm outline-none transition focus:border-blue-500"
                    />

                  </div>

                </div>

                <p className="text-sm text-slate-500">

                  <strong className="text-slate-900">
                    {filteredVehicles.length}
                  </strong>{" "}

                  véhicule(s) affiché(s)

                </p>

              </div>

            </div>

          </div>

          {/* ================================================= */}
          {/* TABLEAU */}
          {/* ================================================= */}

          <div className="mt-5 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">

            <div className="overflow-x-auto">

              <table className="min-w-full">

                <thead className="bg-slate-50">

                  <tr>

                    <TableHeader>
                      Véhicule
                    </TableHeader>

                    <TableHeader>
                      Mesures
                    </TableHeader>

                    <TableHeader>
                      Jours avec données
                    </TableHeader>

                    <TableHeader>
                      Jours période
                    </TableHeader>

                    <TableHeader>
                      Couverture
                    </TableHeader>

                    <TableHeader>
                      Incohérences carburant
                    </TableHeader>

                    <TableHeader>
                      % incohérences
                    </TableHeader>

                    <TableHeader>
                      Statut
                    </TableHeader>

                  </tr>

                </thead>

                <tbody className="divide-y divide-slate-100">

                  {filteredVehicles.map((vehicle) => {

                    const hasFuelIssue =
                      (vehicle.nb_incoherences_fuel ?? 0) > 0;

                    const incompleteCoverage =
                      vehicle.taux_couverture_jours_pct != null &&
                      vehicle.taux_couverture_jours_pct < 100;

                    return (
                      <tr
                        key={vehicle.deviceId}
                        className="transition hover:bg-slate-50"
                      >

                        {/* VEHICULE */}

                        <td className="whitespace-nowrap px-4 py-4">

                          <div className="flex items-center gap-3">

                            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
                              <Truck size={18} />
                            </div>

                            <span className="font-semibold text-slate-900">
                              {vehicle.deviceId}
                            </span>

                          </div>

                        </td>

                        {/* MESURES */}

                        <td className="whitespace-nowrap px-4 py-4 text-sm text-slate-600">

                          {vehicle.nombre_mesures != null
                            ? vehicle.nombre_mesures.toLocaleString(
                                "fr-FR"
                              )
                            : "—"}

                        </td>

                        {/* JOURS DONNEES */}

                        <td className="whitespace-nowrap px-4 py-4 text-sm text-slate-600">

                          {vehicle.jours_avec_donnees ?? "—"}

                        </td>

                        {/* JOURS PERIODE */}

                        <td className="whitespace-nowrap px-4 py-4 text-sm text-slate-600">

                          {vehicle.jours_calendaires_periode ?? "—"}

                        </td>

                        {/* COUVERTURE */}

                        <td className="whitespace-nowrap px-4 py-4">

                          <CoverageBadge
                            value={
                              vehicle.taux_couverture_jours_pct
                            }
                          />

                        </td>

                        {/* INCOHERENCES */}

                        <td className="whitespace-nowrap px-4 py-4">

                          <span
                            className={
                              hasFuelIssue
                                ? "font-semibold text-amber-700"
                                : "font-semibold text-emerald-700"
                            }
                          >

                            {vehicle.nb_incoherences_fuel ?? 0}

                          </span>

                        </td>

                        {/* POURCENTAGE */}

                        <td className="whitespace-nowrap px-4 py-4 text-sm text-slate-600">

                          {formatNumber(
                            vehicle.pct_incoherences_fuel,
                            2
                          )}
                          {" %"}

                        </td>

                        {/* STATUT */}

                        <td className="whitespace-nowrap px-4 py-4">

                          <QualityBadge
                            hasFuelIssue={hasFuelIssue}
                            incompleteCoverage={
                              incompleteCoverage
                            }
                          />

                        </td>

                      </tr>
                    );

                  })}

                </tbody>

              </table>

            </div>

            {filteredVehicles.length === 0 && (

              <div className="px-6 py-14 text-center">

                <Database
                  size={32}
                  className="mx-auto text-slate-300"
                />

                <p className="mt-3 font-medium text-slate-700">
                  Aucun véhicule trouvé
                </p>

                <p className="mt-1 text-sm text-slate-500">
                  Modifiez votre recherche.
                </p>

              </div>

            )}

          </div>

          {/* ================================================= */}
          {/* DETAIL CARTES */}
          {/* ================================================= */}

          <div className="mt-8">

            <h2 className="text-xl font-bold text-slate-900">
              Diagnostic par véhicule
            </h2>

            <div className="mt-4 grid gap-4 lg:grid-cols-2">

              {filteredVehicles.map((vehicle) => (

                <VehicleQualityCard
                  key={`quality-${vehicle.deviceId}`}
                  vehicle={vehicle}
                />

              ))}

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
// RESUME QUALITE
// ============================================================

function QualitySummaryCard({
  title,
  value,
  total,
  description,
  good,
}: {
  title: string;
  value: number;
  total: number;
  description: string;
  good: boolean;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">

      <div className="flex items-start justify-between gap-4">

        <div>

          <p className="font-semibold text-slate-900">
            {title}
          </p>

          <p className="mt-3 text-3xl font-bold text-slate-900">

            {value}

            <span className="ml-1 text-base font-normal text-slate-400">
              / {total}
            </span>

          </p>

        </div>

        <div
          className={
            good
              ? "rounded-lg bg-emerald-50 p-3 text-emerald-600"
              : "rounded-lg bg-amber-50 p-3 text-amber-600"
          }
        >

          {good ? (
            <CheckCircle2 size={22} />
          ) : (
            <AlertTriangle size={22} />
          )}

        </div>

      </div>

      <p className="mt-3 text-sm leading-6 text-slate-500">
        {description}
      </p>

    </div>
  );
}

// ============================================================
// CARTE QUALITE VEHICULE
// ============================================================

function VehicleQualityCard({
  vehicle,
}: {
  vehicle: Vehicle;
}) {
  const hasFuelIssue =
    (vehicle.nb_incoherences_fuel ?? 0) > 0;

  const incompleteCoverage =
    vehicle.taux_couverture_jours_pct != null &&
    vehicle.taux_couverture_jours_pct < 100;

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">

      <div className="flex items-center justify-between">

        <div className="flex items-center gap-3">

          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
            <Truck size={20} />
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

        <QualityBadge
          hasFuelIssue={hasFuelIssue}
          incompleteCoverage={incompleteCoverage}
        />

      </div>

      <div className="mt-6 grid grid-cols-2 gap-4">

        <SmallMetric
          label="Mesures"
          value={
            vehicle.nombre_mesures != null
              ? vehicle.nombre_mesures.toLocaleString(
                  "fr-FR"
                )
              : "—"
          }
        />

        <SmallMetric
          label="Couverture"
          value={`${formatNumber(
            vehicle.taux_couverture_jours_pct,
            1
          )} %`}
        />

        <SmallMetric
          label="Jours avec données"
          value={
            vehicle.jours_avec_donnees != null
              ? String(vehicle.jours_avec_donnees)
              : "—"
          }
        />

        <SmallMetric
          label="Jours de la période"
          value={
            vehicle.jours_calendaires_periode != null
              ? String(
                  vehicle.jours_calendaires_periode
                )
              : "—"
          }
        />

        <SmallMetric
          label="Incohérences carburant"
          value={String(
            vehicle.nb_incoherences_fuel ?? 0
          )}
        />

        <SmallMetric
          label="% incohérences"
          value={`${formatNumber(
            vehicle.pct_incoherences_fuel,
            2
          )} %`}
        />

      </div>

      {(hasFuelIssue || incompleteCoverage) && (

        <div className="mt-5 rounded-lg bg-amber-50 p-4">

          <p className="text-xs font-semibold text-amber-800">
            Point d&apos;attention
          </p>

          <p className="mt-1 text-xs leading-5 text-amber-700">

            {hasFuelIssue && incompleteCoverage
              ? "Le véhicule présente à la fois des incohérences du signal carburant et une couverture temporelle incomplète."
              : hasFuelIssue
                ? "Le signal carburant contient des mesures incohérentes. Les événements de ce véhicule doivent être interprétés avec prudence."
                : "La couverture temporelle est incomplète. Certaines périodes ne disposent pas de données."}

          </p>

        </div>

      )}

    </div>
  );
}

// ============================================================
// PETIT KPI
// ============================================================

function SmallMetric({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-lg bg-slate-50 p-4">

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
// COUVERTURE
// ============================================================

function CoverageBadge({
  value,
}: {
  value?: number | null;
}) {
  if (value == null) {
    return (
      <span className="text-slate-400">
        —
      </span>
    );
  }

  let className =
    "bg-red-50 text-red-700";

  if (value >= 95) {
    className =
      "bg-emerald-50 text-emerald-700";
  } else if (value >= 80) {
    className =
      "bg-amber-50 text-amber-700";
  }

  return (
    <span
      className={`rounded-full px-3 py-1 text-xs font-semibold ${className}`}
    >

      {formatNumber(value, 1)}
      {" %"}

    </span>
  );
}

// ============================================================
// STATUT QUALITE
// ============================================================

function QualityBadge({
  hasFuelIssue,
  incompleteCoverage,
}: {
  hasFuelIssue: boolean;
  incompleteCoverage: boolean;
}) {
  if (!hasFuelIssue && !incompleteCoverage) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">

        <CheckCircle2 size={13} />

        OK

      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700">

      <AlertTriangle size={13} />

      À surveiller

    </span>
  );
}

// ============================================================
// TABLE HEADER
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
  value: number | null | undefined,
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
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }
  );
}