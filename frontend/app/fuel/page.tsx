"use client";

import {
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  AlertTriangle,
  Droplets,
  Fuel,
  Loader2,
  Search,
  TrendingDown,
  Truck,
} from "lucide-react";


const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";


type Vehicle = {
  deviceId: number;

  nombre_mesures?: number | null;

  fuel_moyen_pct?: number | null;
  fuel_min_pct?: number | null;
  fuel_max_pct?: number | null;

  nb_ravitaillements_potentiels?: number | null;

  hausse_moyenne_refuel_pct?: number | null;
  hausse_max_refuel_pct?: number | null;

  nb_baisses_suspectes?: number | null;

  baisse_moyenne_suspecte_pct?: number | null;
  baisse_max_suspecte_pct?: number | null;

  nb_incoherences_fuel?: number | null;
  pct_incoherences_fuel?: number | null;
};


type RefuelingEvent = {
  refuel_episode_id?: string | null;

  deviceId?: number | null;

  start_time?: string | null;
  end_time?: string | null;

  duration_sec?: number | null;
  n_steps?: number | null;

  start_fuel_pct?: number | null;
  end_fuel_pct?: number | null;

  total_delta_fuel_pct?: number | null;

  max_speed_kmh?: number | null;
  mean_speed_kmh?: number | null;

  event_id?: string | null;
  event_time?: string | null;

  event_category?: string | null;
  source_detection?: string | null;

  variation_fuel_pct?: number | null;
  fuel_level_pct?: number | null;
};


export default function FuelPage() {

  const [vehicles, setVehicles] =
    useState<Vehicle[]>([]);

  const [refuelings, setRefuelings] =
    useState<RefuelingEvent[]>([]);

  const [isLoading, setIsLoading] =
    useState(true);

  const [errorMessage, setErrorMessage] =
    useState<string | null>(null);

  const [vehicleFilter, setVehicleFilter] =
    useState("Tous");

  const [search, setSearch] =
    useState("");


  // ============================================================
  // CHARGEMENT
  // ============================================================

  useEffect(() => {

    async function loadFuelData() {

      setIsLoading(true);
      setErrorMessage(null);

      try {

        const [
          vehiclesResponse,
          refuelingsResponse,
        ] = await Promise.all([
          fetch(
            `${API_URL}/api/vehicles`,
            {
              cache: "no-store",
            }
          ),

          fetch(
            `${API_URL}/api/fuel/refuelings`,
            {
              cache: "no-store",
            }
          ),
        ]);


        if (!vehiclesResponse.ok) {

          throw new Error(
            "Impossible de récupérer les indicateurs carburant des véhicules."
          );
        }


        if (!refuelingsResponse.ok) {

          throw new Error(
            "Impossible de récupérer les ravitaillements potentiels."
          );
        }


        const vehicleData: Vehicle[] =
          await vehiclesResponse.json();

        const refuelingData: RefuelingEvent[] =
          await refuelingsResponse.json();


        setVehicles(vehicleData);

        setRefuelings(refuelingData);

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


    loadFuelData();

  }, []);


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
  // KPI GLOBAUX
  // ============================================================

  const totalRefuelings =
    refuelings.length;


  const totalSuspiciousDrops =
    vehicles.reduce(
      (total, vehicle) =>
        total +
        (
          vehicle.nb_baisses_suspectes ??
          0
        ),
      0
    );


  const totalFuelInconsistencies =
    vehicles.reduce(
      (total, vehicle) =>
        total +
        (
          vehicle.nb_incoherences_fuel ??
          0
        ),
      0
    );


  const vehiclesWithRefuelings =
    new Set(
      refuelings
        .map(
          (event) =>
            event.deviceId
        )
        .filter(
          (
            value
          ): value is number =>
            typeof value === "number"
        )
    ).size;


  // ============================================================
  // FILTRAGE
  // ============================================================

  const filteredRefuelings =
    useMemo(() => {

      return refuelings.filter(
        (event) => {

          const matchesVehicle =
            vehicleFilter === "Tous" ||
            String(
              event.deviceId
            ) === vehicleFilter;


          const searchValue =
            search
              .trim()
              .toLowerCase();


          const matchesSearch =
            searchValue === "" ||
            String(
              event.deviceId ?? ""
            ).includes(
              searchValue
            ) ||
            (
              event.event_id ?? ""
            )
              .toLowerCase()
              .includes(
                searchValue
              ) ||
            (
              event.refuel_episode_id ??
              ""
            )
              .toLowerCase()
              .includes(
                searchValue
              );


          return (
            matchesVehicle &&
            matchesSearch
          );
        }
      );

    }, [
      refuelings,
      vehicleFilter,
      search,
    ]);


  return (
    <div>

      {/* ===================================================== */}
      {/* EN-TETE */}
      {/* ===================================================== */}

      <div className="mb-8">

        <p className="mb-2 text-sm font-semibold text-blue-600">
          Carburant
        </p>

        <h1 className="text-3xl font-bold text-slate-900">
          Analyse carburant
        </h1>

        <p className="mt-2 max-w-3xl text-slate-500">
          Analysez les niveaux de carburant,
          les ravitaillements potentiels,
          les baisses atypiques et la qualité
          du signal carburant.
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
              Chargement des données carburant...
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
                label="Ravitaillements potentiels"
                value={
                  totalRefuelings.toLocaleString(
                    "fr-FR"
                  )
                }
                description="Épisodes détectés automatiquement"
                icon={
                  <Fuel size={22} />
                }
              />


              <KpiCard
                label="Baisses détectées par règles"
                value={
                  totalSuspiciousDrops.toLocaleString(
                    "fr-FR"
                  )
                }
                description="Événements nécessitant une analyse"
                icon={
                  <TrendingDown
                    size={22}
                  />
                }
              />


              <KpiCard
                label="Véhicules concernés"
                value={
                  vehiclesWithRefuelings.toLocaleString(
                    "fr-FR"
                  )
                }
                description="Avec au moins un ravitaillement potentiel"
                icon={
                  <Truck size={22} />
                }
              />


              <KpiCard
                label="Mesures fuel incohérentes"
                value={
                  totalFuelInconsistencies.toLocaleString(
                    "fr-FR"
                  )
                }
                description="Valeurs nécessitant une prudence d'interprétation"
                icon={
                  <AlertTriangle
                    size={22}
                  />
                }
              />

            </div>


            {/* ================================================= */}
            {/* AVERTISSEMENT METIER */}
            {/* ================================================= */}

            <div className="mt-6 rounded-xl border border-blue-100 bg-blue-50/50 p-5">

              <p className="font-semibold text-slate-900">
                Interprétation des résultats
              </p>

              <p className="mt-2 text-sm leading-6 text-slate-600">
                Les hausses importantes du niveau
                sont présentées comme des
                <strong>
                  {" "}ravitaillements potentiels
                </strong>
                . Les baisses atypiques sont des
                événements à investiguer et ne
                constituent pas automatiquement
                une preuve de vol, de fuite ou
                de fraude.
              </p>

              <p className="mt-2 text-xs leading-5 text-slate-500">
                Le niveau de carburant est exprimé
                en pourcentage. Sans capacité de
                réservoir ni quantité réellement
                ajoutée lors des pleins, la plateforme
                ne convertit pas ces variations en litres.
              </p>

            </div>


            {/* ================================================= */}
            {/* PROFIL CARBURANT VEHICULES */}
            {/* ================================================= */}

            <div className="mt-8">

              <h2 className="text-xl font-bold text-slate-900">
                Profil carburant par véhicule
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                Niveau moyen, plage observée
                et événements détectés pour chaque véhicule.
              </p>


              <div className="mt-4 grid gap-4 lg:grid-cols-3">

                {vehicles.map(
                  (vehicle) => (

                    <FuelVehicleCard
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
            {/* RAVITAILLEMENTS */}
            {/* ================================================= */}

            <div className="mt-8">

              <div>

                <h2 className="text-xl font-bold text-slate-900">
                  Ravitaillements potentiels
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  Épisodes de hausse du niveau
                  de carburant identifiés par le pipeline.
                </p>

              </div>


              {/* FILTRES */}

              <div className="mt-5 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">

                <div className="grid gap-4 md:grid-cols-2">


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
                        placeholder="Véhicule ou identifiant..."
                        className="w-full rounded-lg border border-slate-200 py-2.5 pl-10 pr-3 text-sm outline-none transition focus:border-blue-500"
                      />

                    </div>

                  </div>


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

                </div>


                <p className="mt-4 text-sm text-slate-500">

                  <strong className="text-slate-900">
                    {
                      filteredRefuelings.length
                    }
                  </strong>{" "}

                  épisode(s) affiché(s)

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
                          Niveau avant
                        </TableHeader>

                        <TableHeader>
                          Niveau après
                        </TableHeader>

                        <TableHeader>
                          Hausse
                        </TableHeader>

                        <TableHeader>
                          Durée
                        </TableHeader>

                        <TableHeader>
                          Vitesse moy.
                        </TableHeader>

                      </tr>

                    </thead>


                    <tbody className="divide-y divide-slate-100">

                      {filteredRefuelings.map(
                        (
                          event,
                          index
                        ) => (

                          <tr
                            key={
                              event.event_id ??
                              `${event.deviceId}-${event.event_time}-${index}`
                            }
                            className="transition hover:bg-slate-50"
                          >

                            <td className="whitespace-nowrap px-4 py-4">

                              <div className="flex items-center gap-2">

                                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-50 text-blue-600">

                                  <Truck
                                    size={16}
                                  />

                                </div>

                                <span className="font-semibold text-slate-900">
                                  {
                                    event.deviceId ??
                                    "—"
                                  }
                                </span>

                              </div>

                            </td>


                            <td className="whitespace-nowrap px-4 py-4 text-sm text-slate-600">

                              {formatDateTime(
                                event.event_time ??
                                event.start_time
                              )}

                            </td>


                            <td className="whitespace-nowrap px-4 py-4 text-sm text-slate-600">

                              {formatPercent(
                                event.start_fuel_pct
                              )}

                            </td>


                            <td className="whitespace-nowrap px-4 py-4 text-sm font-semibold text-slate-900">

                              {formatPercent(
                                event.end_fuel_pct ??
                                event.fuel_level_pct
                              )}

                            </td>


                            <td className="whitespace-nowrap px-4 py-4">

                              <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">

                                +
                                {formatNumber(
                                  event.total_delta_fuel_pct ??
                                  event.variation_fuel_pct,
                                  2
                                )}
                                {" pts"}

                              </span>

                            </td>


                            <td className="whitespace-nowrap px-4 py-4 text-sm text-slate-600">

                              {formatDuration(
                                event.duration_sec
                              )}

                            </td>


                            <td className="whitespace-nowrap px-4 py-4 text-sm text-slate-600">

                              {event.mean_speed_kmh !=
                              null
                                ? `${formatNumber(
                                    event.mean_speed_kmh,
                                    1
                                  )} km/h`
                                : "—"}

                            </td>

                          </tr>

                        )
                      )}

                    </tbody>

                  </table>

                </div>


                {filteredRefuelings.length ===
                  0 && (

                  <div className="px-6 py-14 text-center">

                    <Fuel
                      size={32}
                      className="mx-auto text-slate-300"
                    />

                    <p className="mt-3 font-medium text-slate-700">
                      Aucun ravitaillement potentiel
                    </p>

                    <p className="mt-1 text-sm text-slate-500">
                      Aucun événement ne correspond
                      aux filtres sélectionnés.
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


      <p className="mt-3 text-xs leading-5 text-slate-400">
        {description}
      </p>

    </div>
  );
}


// ============================================================
// CARTE VEHICULE
// ============================================================

function FuelVehicleCard({
  vehicle,
}: {
  vehicle: Vehicle;
}) {

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">

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

            <p className="text-lg font-bold text-slate-900">
              {vehicle.deviceId}
            </p>

          </div>

        </div>


        <Droplets
          size={21}
          className="text-blue-500"
        />

      </div>


      <div className="mt-5">

        <p className="text-xs text-slate-500">
          Niveau moyen
        </p>

        <p className="mt-1 text-3xl font-bold text-slate-900">

          {formatPercent(
            vehicle.fuel_moyen_pct
          )}

        </p>

      </div>


      <div className="mt-5 grid grid-cols-2 gap-3">

        <SmallMetric
          label="Minimum"
          value={
            formatPercent(
              vehicle.fuel_min_pct
            )
          }
        />

        <SmallMetric
          label="Maximum"
          value={
            formatPercent(
              vehicle.fuel_max_pct
            )
          }
        />

        <SmallMetric
          label="Ravitaillements"
          value={
            String(
              vehicle.nb_ravitaillements_potentiels ??
              0
            )
          }
        />

        <SmallMetric
          label="Baisses règles"
          value={
            String(
              vehicle.nb_baisses_suspectes ??
              0
            )
          }
        />

      </div>


      <div className="mt-4 border-t border-slate-100 pt-4">

        <div className="flex items-center justify-between text-sm">

          <span className="text-slate-500">
            Incohérences fuel
          </span>

          <span
            className={
              (
                vehicle.nb_incoherences_fuel ??
                0
              ) > 0
                ? "font-semibold text-amber-700"
                : "font-semibold text-emerald-700"
            }
          >
            {
              vehicle.nb_incoherences_fuel ??
              0
            }
          </span>

        </div>

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


function formatPercent(
  value:
    | number
    | null
    | undefined
) {

  if (value == null) {
    return "—";
  }

  return `${formatNumber(
    value,
    1
  )} %`;
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


function formatDuration(
  seconds:
    | number
    | null
    | undefined
) {

  if (seconds == null) {
    return "—";
  }

  if (seconds < 60) {

    return `${Math.round(
      seconds
    )} s`;
  }


  if (seconds < 3600) {

    return `${Math.round(
      seconds / 60
    )} min`;
  }


  return `${formatNumber(
    seconds / 3600,
    1
  )} h`;
}