"use client";

import {
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  Activity,
  AlertTriangle,
  Gauge,
  Loader2,
  Route,
  Search,
  Truck,
} from "lucide-react";


const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";


type Vehicle = {
  deviceId: number;

  nombre_mesures?: number | null;

  debut_periode?: string | null;
  fin_periode?: string | null;

  jours_calendaires_periode?: number | null;
  jours_avec_donnees?: number | null;
  jours_actifs?: number | null;

  taux_couverture_jours_pct?: number | null;

  distance_km?: number | null;
  distance_moyenne_par_jour_actif_km?: number | null;

  vitesse_moyenne_mesures_kmh?: number | null;
  vitesse_moyenne_en_mouvement_kmh?: number | null;
  vitesse_max_kmh?: number | null;

  fuel_moyen_pct?: number | null;
  fuel_min_pct?: number | null;
  fuel_max_pct?: number | null;

  nb_ravitaillements_potentiels?: number | null;
  nb_baisses_suspectes?: number | null;

  nb_incoherences_fuel?: number | null;
  pct_incoherences_fuel?: number | null;

  nb_baisses_analysees?: number | null;
  nb_candidats_ia?: number | null;
  nb_alertes_regles?: number | null;
  nb_overlap_regles_ia?: number | null;
  nb_alertes_ia_uniquement?: number | null;
  nb_alertes_regle_uniquement?: number | null;
};


export default function FleetPage() {

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

    async function loadVehicles() {

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
            "Impossible de récupérer les performances de la flotte."
          );
        }

        const data: Vehicle[] =
          await response.json();

        setVehicles(data);

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

    loadVehicles();

  }, []);


  // ============================================================
  // RECHERCHE
  // ============================================================

  const filteredVehicles =
    useMemo(() => {

      const value =
        search.trim();

      if (!value) {
        return vehicles;
      }

      return vehicles.filter(
        (vehicle) =>
          String(
            vehicle.deviceId
          ).includes(value)
      );

    }, [
      vehicles,
      search,
    ]);


  // ============================================================
  // KPI GLOBAUX
  // ============================================================

  const totalDistance =
    vehicles.reduce(
      (sum, vehicle) =>
        sum +
        (
          vehicle.distance_km ??
          0
        ),
      0
    );


  const totalMeasures =
    vehicles.reduce(
      (sum, vehicle) =>
        sum +
        (
          vehicle.nombre_mesures ??
          0
        ),
      0
    );


  const coverageValues =
    vehicles
      .map(
        (vehicle) =>
          vehicle.taux_couverture_jours_pct
      )
      .filter(
        (
          value
        ): value is number =>
          typeof value === "number"
      );


  const averageCoverage =
    coverageValues.length > 0
      ? coverageValues.reduce(
          (sum, value) =>
            sum + value,
          0
        ) /
        coverageValues.length
      : 0;


  return (
    <div>

      {/* ===================================================== */}
      {/* EN-TETE */}
      {/* ===================================================== */}

      <div className="mb-8">

        <p className="mb-2 text-sm font-semibold text-blue-600">
          Performance
        </p>

        <h1 className="text-3xl font-bold text-slate-900">
          Performance flotte
        </h1>

        <p className="mt-2 max-w-3xl text-slate-500">
          Comparez l&apos;activité observée,
          les distances parcourues et les
          indicateurs de performance des véhicules
          du dataset actuellement analysé.
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
              Chargement des performances...
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

      {!isLoading &&
        !errorMessage && (
          <>

            {/* =============================================== */}
            {/* KPI GLOBAUX */}
            {/* =============================================== */}

            <div className="grid gap-4 md:grid-cols-4">

              <KpiCard
                label="Véhicules analysés"
                value={
                  vehicles.length.toLocaleString(
                    "fr-FR"
                  )
                }
                description="Véhicules présents dans le dataset"
                icon={
                  <Truck size={22} />
                }
              />


              <KpiCard
                label="Distance totale"
                value={`${formatNumber(
                  totalDistance,
                  1
                )} km`}
                description="Somme des distances observées"
                icon={
                  <Route size={22} />
                }
              />


              <KpiCard
                label="Mesures analysées"
                value={
                  totalMeasures.toLocaleString(
                    "fr-FR"
                  )
                }
                description="Mesures télématiques préparées"
                icon={
                  <Activity size={22} />
                }
              />


              <KpiCard
                label="Couverture moyenne"
                value={`${formatNumber(
                  averageCoverage,
                  1
                )} %`}
                description="Moyenne de la couverture des jours"
                icon={
                  <Gauge size={22} />
                }
              />

            </div>


            {/* =============================================== */}
            {/* EXPLICATION */}
            {/* =============================================== */}

            <div className="mt-6 rounded-xl border border-blue-100 bg-blue-50/50 p-5">

              <p className="font-semibold text-slate-900">
                Comment lire ces indicateurs ?
              </p>

              <p className="mt-2 text-sm leading-6 text-slate-600">
                La distance mesure l&apos;activité
                observée dans les données.
                Les jours actifs correspondent aux
                jours où le véhicule a parcouru au
                moins une distance significative.
                La couverture indique la proportion
                de jours de la période pour lesquels
                des données sont disponibles.
              </p>

              <p className="mt-2 text-xs leading-5 text-slate-500">
                Les jours actifs ne représentent pas
                un taux d&apos;utilisation horaire du véhicule.
              </p>

            </div>


            {/* =============================================== */}
            {/* RECHERCHE */}
            {/* =============================================== */}

            <div className="mt-6 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">

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
                      type="text"
                      value={search}
                      onChange={
                        (event) =>
                          setSearch(
                            event.target.value
                          )
                      }
                      placeholder="Ex. 701"
                      className="w-full rounded-lg border border-slate-200 py-2.5 pl-10 pr-3 text-sm outline-none transition focus:border-blue-500"
                    />

                  </div>

                </div>


                <p className="text-sm text-slate-500">

                  <strong className="text-slate-900">
                    {
                      filteredVehicles.length
                    }
                  </strong>{" "}
                  véhicule(s) affiché(s)

                </p>

              </div>

            </div>


            {/* =============================================== */}
            {/* TABLEAU */}
            {/* =============================================== */}

            <div className="mt-6 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">

              <div className="overflow-x-auto">

                <table className="min-w-full">

                  <thead className="bg-slate-50">

                    <tr>

                      <TableHeader>
                        Véhicule
                      </TableHeader>

                      <TableHeader>
                        Distance
                      </TableHeader>

                      <TableHeader>
                        Jours actifs
                      </TableHeader>

                      <TableHeader>
                        Couverture
                      </TableHeader>

                      <TableHeader>
                        Distance / jour actif
                      </TableHeader>

                      <TableHeader>
                        Vitesse en mouvement
                      </TableHeader>

                      <TableHeader>
                        Vitesse max.
                      </TableHeader>

                      <TableHeader>
                        Mesures
                      </TableHeader>

                    </tr>

                  </thead>


                  <tbody className="divide-y divide-slate-100">

                    {filteredVehicles.map(
                      (vehicle) => (

                        <tr
                          key={
                            vehicle.deviceId
                          }
                          className="transition hover:bg-slate-50"
                        >

                          {/* VEHICULE */}

                          <td className="whitespace-nowrap px-4 py-4">

                            <div className="flex items-center gap-3">

                              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-50 text-blue-600">

                                <Truck
                                  size={18}
                                />

                              </div>

                              <div>

                                <p className="font-semibold text-slate-900">
                                  {
                                    vehicle.deviceId
                                  }
                                </p>

                                <p className="text-xs text-slate-400">
                                  Device ID
                                </p>

                              </div>

                            </div>

                          </td>


                          {/* DISTANCE */}

                          <td className="whitespace-nowrap px-4 py-4">

                            <p className="font-semibold text-slate-900">
                              {formatNumber(
                                vehicle.distance_km,
                                1
                              )}{" "}
                              km
                            </p>

                          </td>


                          {/* JOURS ACTIFS */}

                          <td className="whitespace-nowrap px-4 py-4">

                            <p className="font-medium text-slate-900">

                              {
                                vehicle.jours_actifs ??
                                "—"
                              }

                              {vehicle.jours_calendaires_periode !=
                                null && (
                                <span className="font-normal text-slate-400">
                                  {" "}
                                  /{" "}
                                  {
                                    vehicle.jours_calendaires_periode
                                  }
                                </span>
                              )}

                            </p>

                          </td>


                          {/* COUVERTURE */}

                          <td className="whitespace-nowrap px-4 py-4">

                            <CoverageBadge
                              value={
                                vehicle.taux_couverture_jours_pct
                              }
                            />

                          </td>


                          {/* DISTANCE / JOUR */}

                          <td className="whitespace-nowrap px-4 py-4 text-sm text-slate-600">

                            {formatNumber(
                              vehicle.distance_moyenne_par_jour_actif_km,
                              1
                            )}{" "}
                            km

                          </td>


                          {/* VITESSE MOYENNE EN MOUVEMENT */}

                          <td className="whitespace-nowrap px-4 py-4 text-sm text-slate-600">

                            {formatNumber(
                              vehicle.vitesse_moyenne_en_mouvement_kmh,
                              1
                            )}{" "}
                            km/h

                          </td>


                          {/* VITESSE MAX */}

                          <td className="whitespace-nowrap px-4 py-4 text-sm text-slate-600">

                            {formatNumber(
                              vehicle.vitesse_max_kmh,
                              1
                            )}{" "}
                            km/h

                          </td>


                          {/* MESURES */}

                          <td className="whitespace-nowrap px-4 py-4 text-sm text-slate-600">

                            {
                              vehicle.nombre_mesures !=
                              null
                                ? vehicle.nombre_mesures.toLocaleString(
                                    "fr-FR"
                                  )
                                : "—"
                            }

                          </td>

                        </tr>
                      )
                    )}

                  </tbody>

                </table>

              </div>


              {filteredVehicles.length ===
                0 && (

                <div className="px-6 py-14 text-center">

                  <Truck
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


            {/* =============================================== */}
            {/* DETAILS PAR VEHICULE */}
            {/* =============================================== */}

            <div className="mt-8">

              <h2 className="text-xl font-bold text-slate-900">
                Détail par véhicule
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                Indicateurs complémentaires
                calculés automatiquement pour chaque véhicule.
              </p>


              <div className="mt-4 grid gap-4 lg:grid-cols-2">

                {filteredVehicles.map(
                  (vehicle) => (

                    <VehicleCard
                      key={
                        `detail-${vehicle.deviceId}`
                      }
                      vehicle={
                        vehicle
                      }
                    />

                  )
                )}

              </div>

            </div>

          </>
        )}

    </div>
  );
}


// ============================================================
// CARTE KPI
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

      <div className="flex items-start justify-between gap-4">

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


      <p className="mt-3 text-xs text-slate-400">
        {description}
      </p>

    </div>
  );
}


// ============================================================
// DETAILS VEHICULE
// ============================================================

function VehicleCard({
  vehicle,
}: {
  vehicle: Vehicle;
}) {

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">

      <div className="flex items-center justify-between">

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

            <h3 className="text-lg font-bold text-slate-900">
              {vehicle.deviceId}
            </h3>

          </div>

        </div>


        <CoverageBadge
          value={
            vehicle.taux_couverture_jours_pct
          }
        />

      </div>


      <div className="mt-6 grid grid-cols-2 gap-4">

        <SmallMetric
          label="Distance"
          value={`${formatNumber(
            vehicle.distance_km,
            1
          )} km`}
        />

        <SmallMetric
          label="Jours actifs"
          value={
            vehicle.jours_actifs != null
              ? String(
                  vehicle.jours_actifs
                )
              : "—"
          }
        />

        <SmallMetric
          label="Vitesse en mouvement"
          value={`${formatNumber(
            vehicle.vitesse_moyenne_en_mouvement_kmh,
            1
          )} km/h`}
        />

        <SmallMetric
          label="Vitesse maximale"
          value={`${formatNumber(
            vehicle.vitesse_max_kmh,
            1
          )} km/h`}
        />

        <SmallMetric
          label="Distance / jour actif"
          value={`${formatNumber(
            vehicle.distance_moyenne_par_jour_actif_km,
            1
          )} km`}
        />

        <SmallMetric
          label="Jours avec données"
          value={
            vehicle.jours_avec_donnees !=
            null
              ? String(
                  vehicle.jours_avec_donnees
                )
              : "—"
          }
        />

      </div>


      {(vehicle.debut_periode ||
        vehicle.fin_periode) && (

        <div className="mt-5 border-t border-slate-100 pt-4">

          <p className="text-xs text-slate-400">
            Période observée
          </p>

          <p className="mt-1 text-sm font-medium text-slate-700">

            {formatDate(
              vehicle.debut_periode
            )}

            {" → "}

            {formatDate(
              vehicle.fin_periode
            )}

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
// BADGE COUVERTURE
// ============================================================

function CoverageBadge({
  value,
}: {
  value?: number | null;
}) {

  if (value == null) {

    return (
      <span className="text-sm text-slate-400">
        —
      </span>
    );
  }


  let className =
    "bg-red-50 text-red-700";

  if (value >= 90) {

    className =
      "bg-emerald-50 text-emerald-700";

  } else if (
    value >= 70
  ) {

    className =
      "bg-amber-50 text-amber-700";
  }


  return (
    <span
      className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${className}`}
    >
      {formatNumber(
        value,
        1
      )}{" "}
      %
    </span>
  );
}


// ============================================================
// ENTETE TABLE
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


function formatDate(
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

  return date.toLocaleDateString(
    "fr-FR"
  );
}