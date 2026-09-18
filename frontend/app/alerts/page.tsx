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
  ExternalLink,
  Gauge,
  Loader2,
  MapPin,
  Search,
  ShieldAlert,
  Truck,
  X,
} from "lucide-react";


const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";


// ============================================================
// TYPE ALERTE
// ============================================================

type FuelAlert = {
  alert_id: string;

  deviceId: number | null;
  fixTime: string | null;

  alert_type: string | null;
  source_detection: string | null;
  suspicious_event_id: string | null;

  fuelLevel: number | null;
  drop_abs_pct: number | null;

  delta_time_sec: number | null;
  speed_kmh: number | null;
  distance_abs_m: number | null;

  ignition: boolean | null;

  ai_anomaly_score: number | null;
  ai_score_percentile: number | null;

  contexte_temporel: string | null;

  latitude: number | null;
  longitude: number | null;

  detection_combinee: string | null;
  ai_anomaly_flag: boolean | null;

  persistence: string | null;
  context_support: string | null;
  confidence_level: string | null;
  analysis_reason: string | null;

  fuel_event_pct: number | null;
  recovery_ratio: number | null;

  lien_carte: string | null;

  rang_priorite: number | null;
  priorite_alerte: string | null;
  raison_priorite: string | null;

  statut_validation: string | null;
};


// ============================================================
// PAGE PRINCIPALE
// ============================================================

export default function AlertsPage() {

  // ============================================================
  // ETAT
  // ============================================================

  const [alerts, setAlerts] =
    useState<FuelAlert[]>([]);

  const [isLoading, setIsLoading] =
    useState(true);

  const [errorMessage, setErrorMessage] =
    useState<string | null>(null);


  // Filtres

  const [search, setSearch] =
    useState("");

  const [priorityFilter, setPriorityFilter] =
    useState("Toutes");

  const [sourceFilter, setSourceFilter] =
    useState("Toutes");

  const [vehicleFilter, setVehicleFilter] =
    useState("Tous");


  // Alerte sélectionnée

  const [selectedAlert, setSelectedAlert] =
    useState<FuelAlert | null>(null);


  // ============================================================
  // CHARGEMENT DES ALERTES
  // ============================================================

  useEffect(() => {

    async function loadAlerts() {

      setIsLoading(true);
      setErrorMessage(null);

      try {

        const response = await fetch(
          `${API_URL}/api/alerts`,
          {
            cache: "no-store",
          }
        );


        if (!response.ok) {

          throw new Error(
            "Impossible de récupérer les alertes."
          );
        }


        const data: FuelAlert[] =
          await response.json();


        setAlerts(data);

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


    loadAlerts();

  }, []);


  // ============================================================
  // LISTE DES VEHICULES
  // ============================================================

  const vehicles =
    useMemo(() => {

      return Array.from(
        new Set(
          alerts
            .map(
              (alert) =>
                alert.deviceId
            )
            .filter(
              (
                value
              ): value is number =>
                value !== null
            )
        )
      ).sort(
        (a, b) =>
          a - b
      );

    }, [alerts]);


  // ============================================================
  // FILTRAGE DES ALERTES
  // ============================================================

  const filteredAlerts =
    useMemo(() => {

      return alerts.filter(
        (alert) => {

          const searchValue =
            search
              .trim()
              .toLowerCase();


          const matchesSearch =
            searchValue === "" ||

            String(
              alert.deviceId ?? ""
            )
              .toLowerCase()
              .includes(
                searchValue
              ) ||

            (
              alert.alert_id ?? ""
            )
              .toLowerCase()
              .includes(
                searchValue
              );


          const matchesPriority =
            priorityFilter ===
              "Toutes" ||

            alert.rang_priorite ===
              Number(
                priorityFilter.replace(
                  "P",
                  ""
                )
              );


          const matchesSource =
            sourceFilter ===
              "Toutes" ||

            alert.source_detection ===
              sourceFilter;


          const matchesVehicle =
            vehicleFilter ===
              "Tous" ||

            String(
              alert.deviceId
            ) ===
              vehicleFilter;


          return (
            matchesSearch &&
            matchesPriority &&
            matchesSource &&
            matchesVehicle
          );
        }
      );

    }, [
      alerts,
      search,
      priorityFilter,
      sourceFilter,
      vehicleFilter,
    ]);


  // ============================================================
  // KPI
  // ============================================================

  const p1Count =
    alerts.filter(
      (alert) =>
        alert.rang_priorite === 1
    ).length;


  const ruleAndAiCount =
    alerts.filter(
      (alert) =>
        alert.source_detection ===
        "Règle + IA"
    ).length;


  const aiOnlyCount =
    alerts.filter(
      (alert) =>
        alert.source_detection ===
        "IA uniquement"
    ).length;


  const ruleOnlyCount =
    alerts.filter(
      (alert) =>
        alert.source_detection ===
        "Règle uniquement"
    ).length;


  // ============================================================
  // MISE A JOUR LOCALE APRES MODIFICATION DU STATUT
  // ============================================================

  function handleStatusUpdated(
    updatedAlert: FuelAlert
  ) {

    // Mettre à jour l'alerte dans le tableau
    setAlerts(
      (currentAlerts) =>
        currentAlerts.map(
          (alert) =>
            alert.alert_id ===
            updatedAlert.alert_id
              ? updatedAlert
              : alert
        )
    );


    // Mettre à jour également la fiche ouverte
    setSelectedAlert(
      updatedAlert
    );
  }


  return (

    <div>

      {/* ===================================================== */}
      {/* EN-TETE */}
      {/* ===================================================== */}

      <div className="mb-8">

        <p className="mb-2 text-sm font-semibold text-blue-600">
          Investigation
        </p>


        <h1 className="text-3xl font-bold text-slate-900">
          Alertes carburant
        </h1>


        <p className="mt-2 max-w-3xl text-slate-500">
          Consultez les événements atypiques détectés
          automatiquement et priorisez les investigations.
          Ces événements ne constituent pas une confirmation
          de vol, de fuite ou de fraude.
        </p>

      </div>


      {/* ===================================================== */}
      {/* CHARGEMENT */}
      {/* ===================================================== */}

      {isLoading && (

        <div className="flex min-h-[300px] items-center justify-center">

          <div className="text-center">

            <Loader2
              size={32}
              className="mx-auto animate-spin text-blue-600"
            />


            <p className="mt-3 text-sm text-slate-500">
              Chargement des alertes...
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

            {/* ================================================= */}
            {/* KPI */}
            {/* ================================================= */}

            <div className="grid gap-4 md:grid-cols-4">

              <KpiCard
                label="Événements à investiguer"
                value={alerts.length}
                description="Événements uniques"
                icon={
                  <ShieldAlert size={22} />
                }
              />


              <KpiCard
                label="Priorité P1"
                value={p1Count}
                description="À examiner en premier"
                icon={
                  <AlertTriangle size={22} />
                }
              />


              <KpiCard
                label="Règle + IA"
                value={ruleAndAiCount}
                description="Détectés par les deux méthodes"
                icon={
                  <CheckCircle2 size={22} />
                }
              />


              <KpiCard
                label="IA uniquement"
                value={aiOnlyCount}
                description="Proposés par Isolation Forest"
                icon={
                  <BrainCircuit size={22} />
                }
              />

            </div>


            {/* ================================================= */}
            {/* EXPLICATION ORIGINE */}
            {/* ================================================= */}

            <div className="mt-6 rounded-xl border border-blue-100 bg-blue-50/50 p-5">

              <p className="font-semibold text-slate-900">
                D&apos;où viennent les alertes ?
              </p>


              <p className="mt-2 text-sm leading-6 text-slate-600">

                Sur les{" "}

                <strong>
                  {alerts.length}
                </strong>{" "}

                événements à investiguer,{" "}

                <strong>
                  {aiOnlyCount}
                </strong>{" "}

                viennent uniquement de l&apos;IA,{" "}

                <strong>
                  {ruleAndAiCount}
                </strong>{" "}

                sont détectés à la fois par les règles
                et l&apos;IA, et{" "}

                <strong>
                  {ruleOnlyCount}
                </strong>{" "}

                proviennent uniquement des règles métier.

              </p>

            </div>


            {/* ================================================= */}
            {/* FILTRES */}
            {/* ================================================= */}

            <div className="mt-6 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">

              <div className="grid gap-4 md:grid-cols-4">


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


                {/* PRIORITE */}

                <FilterSelect
                  label="Priorité"
                  value={priorityFilter}
                  onChange={
                    setPriorityFilter
                  }
                  options={[
                    "Toutes",
                    "P1",
                    "P2",
                    "P3",
                    "P4",
                    "P5",
                  ]}
                />


                {/* SOURCE */}

                <FilterSelect
                  label="Source de détection"
                  value={sourceFilter}
                  onChange={
                    setSourceFilter
                  }
                  options={[
                    "Toutes",
                    "Règle + IA",
                    "IA uniquement",
                    "Règle uniquement",
                  ]}
                />


                {/* VEHICULE */}

                <FilterSelect
                  label="Véhicule"
                  value={vehicleFilter}
                  onChange={
                    setVehicleFilter
                  }
                  options={[
                    "Tous",
                    ...vehicles.map(
                      String
                    ),
                  ]}
                />

              </div>


              <p className="mt-4 text-sm text-slate-500">

                <strong className="text-slate-900">
                  {filteredAlerts.length}
                </strong>{" "}

                événement(s) affiché(s)

              </p>

            </div>


            {/* ================================================= */}
            {/* TABLEAU */}
            {/* ================================================= */}

            <div className="mt-6 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">

              <div className="overflow-x-auto">

                <table className="min-w-full">

                  <thead className="bg-slate-50">

                    <tr>

                      <TableHeader>
                        Priorité
                      </TableHeader>

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
                        Source
                      </TableHeader>

                      <TableHeader>
                        Confiance
                      </TableHeader>

                      <TableHeader>
                        Score d'anomalie
                      </TableHeader>

                      <TableHeader>
                        Statut
                      </TableHeader>

                      <TableHeader>
                        Position
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
                          onClick={
                            () =>
                              setSelectedAlert(
                                alert
                              )
                          }
                          className="cursor-pointer transition hover:bg-blue-50/50"
                          title="Cliquer pour consulter le détail"
                        >

                          {/* PRIORITE */}

                          <td className="whitespace-nowrap px-4 py-4">

                            <PriorityBadge
                              rank={
                                alert.rang_priorite
                              }
                              label={
                                alert.priorite_alerte
                              }
                            />

                          </td>


                          {/* VEHICULE */}

                          <td className="whitespace-nowrap px-4 py-4 text-sm font-semibold text-slate-900">

                            {alert.deviceId ??
                              "—"}

                          </td>


                          {/* DATE */}

                          <td className="whitespace-nowrap px-4 py-4 text-sm text-slate-600">

                            {formatDate(
                              alert.fixTime
                            )}

                          </td>


                          {/* BAISSE */}

                          <td className="whitespace-nowrap px-4 py-4">

                            <p className="font-semibold text-slate-900">

                              {formatNumber(
                                alert.drop_abs_pct,
                                2
                              )}

                              {" %"}

                            </p>


                            <p className="mt-1 text-xs text-slate-400">

                              Niveau :{" "}

                              {formatNumber(
                                alert.fuelLevel,
                                1
                              )}

                              {" %"}

                            </p>

                          </td>


                          {/* SOURCE */}

                          <td className="whitespace-nowrap px-4 py-4">

                            <SourceBadge
                              source={
                                alert.source_detection
                              }
                            />

                          </td>


                          {/* CONFIANCE */}

                          <td className="whitespace-nowrap px-4 py-4">

                            <ConfidenceBadge
                              value={
                                alert.confidence_level
                              }
                            />

                          </td>


                          {/* SCORE IA */}

                          <td className="whitespace-nowrap px-4 py-4 text-sm text-slate-600">

                            {alert.ai_score_percentile !==
                            null
                              ? `${formatNumber(
                                  alert.ai_score_percentile,
                                  2
                                )} %`
                              : "—"}

                          </td>


                          {/* STATUT */}

                          <td className="whitespace-nowrap px-4 py-4">

                            <StatusBadge
                              value={
                                alert.statut_validation ??
                                "À vérifier"
                              }
                            />

                          </td>


                          {/* POSITION */}

                          <td className="whitespace-nowrap px-4 py-4">

                            {alert.lien_carte ? (

                              <a
                                href={
                                  alert.lien_carte
                                }
                                target="_blank"
                                rel="noreferrer"
                                onClick={
                                  (event) =>
                                    event.stopPropagation()
                                }
                                className="inline-flex items-center gap-1 text-sm font-semibold text-blue-600 hover:text-blue-800"
                              >

                                Carte

                                <ExternalLink
                                  size={14}
                                />

                              </a>

                            ) : (

                              <span className="text-sm text-slate-400">
                                —
                              </span>

                            )}

                          </td>

                        </tr>

                      )
                    )}

                  </tbody>

                </table>

              </div>


              {/* AUCUN RESULTAT */}

              {filteredAlerts.length ===
                0 && (

                <div className="px-6 py-14 text-center">

                  <AlertTriangle
                    size={30}
                    className="mx-auto text-slate-300"
                  />


                  <p className="mt-3 font-medium text-slate-700">
                    Aucun événement trouvé
                  </p>


                  <p className="mt-1 text-sm text-slate-500">
                    Modifiez les filtres pour afficher
                    d&apos;autres événements.
                  </p>

                </div>

              )}

            </div>


            {/* ================================================= */}
            {/* NOTE METIER */}
            {/* ================================================= */}

            <div className="mt-6 rounded-xl border border-slate-200 bg-white p-5">

              <p className="text-sm font-semibold text-slate-900">
                Comment utiliser cette page ?
              </p>


              <p className="mt-2 text-sm leading-6 text-slate-500">

                Commencez par les événements P1 et P2,
                puis vérifiez leur source de détection,
                leur contexte, leur position GPS et les
                données du véhicule.

                Cliquez sur une ligne pour consulter
                le détail de l&apos;événement.

                La priorité sert à organiser
                l&apos;investigation ; elle ne confirme
                pas automatiquement une anomalie réelle.

              </p>

            </div>

          </>
        )}


      {/* ===================================================== */}
      {/* FICHE DETAIL */}
      {/* ===================================================== */}

      {selectedAlert && (

        <AlertDetailModal
          alert={
            selectedAlert
          }
          onClose={
            () =>
              setSelectedAlert(
                null
              )
          }
          onStatusUpdated={
            handleStatusUpdated
          }
        />

      )}

    </div>

  );
}


// ============================================================
// FICHE DETAIL D'UNE ALERTE
// ============================================================

function AlertDetailModal({
  alert,
  onClose,
  onStatusUpdated,
}: {
  alert: FuelAlert;
  onClose: () => void;
  onStatusUpdated: (
    updatedAlert: FuelAlert
  ) => void;
}) {

  // ============================================================
  // ETAT DU STATUT
  // ============================================================

  const [selectedStatus, setSelectedStatus] =
    useState(
      alert.statut_validation ??
      "À vérifier"
    );


  const [isSavingStatus, setIsSavingStatus] =
    useState(false);


  const [statusError, setStatusError] =
    useState<string | null>(null);


  const [statusSuccess, setStatusSuccess] =
    useState(false);


  // ============================================================
  // SYNCHRONISER SI L'ALERTE CHANGE
  // ============================================================

  useEffect(() => {

    setSelectedStatus(
      alert.statut_validation ??
      "À vérifier"
    );

    setStatusError(null);

  }, [
    alert.alert_id,
    alert.statut_validation,
  ]);


  // ============================================================
  // ENREGISTRER LE STATUT
  // ============================================================

  async function saveStatus() {

    setIsSavingStatus(true);
    setStatusError(null);
    setStatusSuccess(false);


    try {

      const response = await fetch(
        `${API_URL}/api/alerts/${encodeURIComponent(
          alert.alert_id
        )}/status`,
        {
          method: "PATCH",

          headers: {
            "Content-Type":
              "application/json",
          },

          body: JSON.stringify({
            statut_validation:
              selectedStatus,
          }),
        }
      );


      if (!response.ok) {

        let message =
          "Impossible de modifier le statut.";


        try {

          const errorData =
            await response.json();


          if (
            typeof errorData.detail ===
            "string"
          ) {

            message =
              errorData.detail;
          }

        } catch {

          // Aucun contenu JSON exploitable

        }


        throw new Error(
          message
        );
      }


      const updatedAlert:
        FuelAlert =
        await response.json();


      onStatusUpdated(
        updatedAlert
      );


      setSelectedStatus(
        updatedAlert.statut_validation ??
        selectedStatus
      );


      setStatusSuccess(
        true
      );

    } catch (error) {

      if (
        error instanceof Error
      ) {

        setStatusError(
          error.message
        );

      } else {

        setStatusError(
          "Une erreur est survenue."
        );
      }

    } finally {

      setIsSavingStatus(
        false
      );
    }
  }


  return (

    <div
      className="fixed inset-0 z-50 flex justify-end bg-slate-950/40"
      onClick={
        onClose
      }
    >

      <div
        className="h-full w-full max-w-2xl overflow-y-auto bg-white shadow-2xl"
        onClick={
          (event) =>
            event.stopPropagation()
        }
      >

        {/* ================================================= */}
        {/* HEADER */}
        {/* ================================================= */}

        <div className="sticky top-0 z-10 border-b border-slate-200 bg-white px-6 py-5">

          <div className="flex items-start justify-between gap-4">

            <div>

              <p className="text-sm font-semibold text-blue-600">
                Investigation
              </p>


              <h2 className="mt-1 text-2xl font-bold text-slate-900">
                Détail de l&apos;alerte
              </h2>


              <p className="mt-1 break-all text-xs text-slate-400">
                {alert.alert_id}
              </p>

            </div>


            <button
              type="button"
              onClick={
                onClose
              }
              className="rounded-lg border border-slate-200 p-2 text-slate-500 transition hover:bg-slate-100"
              aria-label="Fermer"
            >

              <X size={20} />

            </button>

          </div>

        </div>


        <div className="space-y-6 p-6">


          {/* ================================================= */}
          {/* RESUME */}
          {/* ================================================= */}

          <div className="grid gap-4 sm:grid-cols-3">

            <DetailHighlight
              label="Priorité"
              value={
                alert.rang_priorite !==
                null
                  ? `P${alert.rang_priorite}`
                  : "—"
              }
            />


            <DetailHighlight
              label="Véhicule"
              value={
                alert.deviceId !==
                null
                  ? String(
                      alert.deviceId
                    )
                  : "—"
              }
            />


            <DetailHighlight
              label="Baisse"
              value={`${formatNumber(
                alert.drop_abs_pct,
                2
              )} %`}
            />

          </div>


          {/* ================================================= */}
          {/* STATUT INVESTIGATION */}
          {/* ================================================= */}

          <section className="rounded-xl border border-blue-200 bg-blue-50/40 p-5">

            <div className="flex items-center gap-2">

              <CheckCircle2
                size={19}
                className="text-blue-600"
              />


              <h3 className="font-semibold text-slate-900">
                Statut de l&apos;investigation
              </h3>

            </div>


            <p className="mt-2 text-sm leading-6 text-slate-600">

              Après examen de l&apos;événement,
              l&apos;utilisateur peut mettre à jour
              son statut.

              La modification est enregistrée
              dans PostgreSQL.

            </p>


            <div className="mt-5">

              <label className="mb-2 block text-xs font-semibold text-slate-600">
                Statut
              </label>


              <select
                value={
                  selectedStatus
                }
                onChange={
                  (event) => {

                    setSelectedStatus(
                      event.target.value
                    );

                    setStatusSuccess(
                      false
                    );

                    setStatusError(
                      null
                    );
                  }
                }
                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-3 text-sm font-medium outline-none transition focus:border-blue-500"
              >

                <option value="À vérifier">
                  À vérifier
                </option>


                <option value="Confirmée">
                  Confirmée après investigation
                </option>


                <option value="Faux positif">
                  Faux positif
                </option>


                <option value="Ignorée">
                  Ignorée
                </option>

              </select>

            </div>


            <button
              type="button"
              onClick={
                saveStatus
              }
              disabled={
                isSavingStatus
              }
              className="mt-4 inline-flex items-center justify-center rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
            >

              {isSavingStatus ? (
                <>

                  <Loader2
                    size={16}
                    className="mr-2 animate-spin"
                  />

                  Enregistrement...

                </>
              ) : (

                "Enregistrer le statut"

              )}

            </button>


            {/* SUCCES */}

            {statusSuccess && (

              <div className="mt-4 rounded-lg border border-emerald-200 bg-emerald-50 p-3">

                <div className="flex items-center gap-2">

                  <CheckCircle2
                    size={17}
                    className="text-emerald-600"
                  />


                  <p className="text-sm font-medium text-emerald-700">
                    Statut enregistré avec succès.
                  </p>

                </div>

              </div>

            )}


            {/* ERREUR */}

            {statusError && (

              <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-3">

                <div className="flex items-center gap-2">

                  <AlertTriangle
                    size={17}
                    className="text-red-600"
                  />


                  <p className="text-sm font-medium text-red-700">
                    {statusError}
                  </p>

                </div>

              </div>

            )}


            <p className="mt-4 text-xs leading-5 text-slate-500">

              « Confirmée après investigation »
              signifie que l&apos;événement a été retenu
              après vérification humaine.

              Cela ne signifie pas automatiquement
              qu&apos;un vol, une fuite ou une fraude
              a été confirmé.

            </p>

          </section>


          {/* ================================================= */}
          {/* EVENEMENT */}
          {/* ================================================= */}

          <DetailSection
            title="Événement"
            icon={
              <ShieldAlert size={18} />
            }
          >

            <DetailGrid>

              <DetailItem
                label="Date et heure"
                value={
                  formatDate(
                    alert.fixTime
                  )
                }
              />


              <DetailItem
                label="Type"
                value={
                  alert.alert_type ??
                  "—"
                }
              />


              <DetailItem
                label="Source de détection"
                value={
                  alert.source_detection ??
                  "—"
                }
              />


              <DetailItem
                label="Statut actuel"
                value={
                  alert.statut_validation ??
                  "À vérifier"
                }
              />

            </DetailGrid>

          </DetailSection>


          {/* ================================================= */}
          {/* VARIATION CARBURANT */}
          {/* ================================================= */}

          <DetailSection
            title="Variation de carburant"
            icon={
              <Gauge size={18} />
            }
          >

            <DetailGrid>

              <DetailItem
                label="Niveau après événement"
                value={`${formatNumber(
                  alert.fuelLevel,
                  2
                )} %`}
              />


              <DetailItem
                label="Baisse observée"
                value={`${formatNumber(
                  alert.drop_abs_pct,
                  2
                )} %`}
              />


              <DetailItem
                label="Variation événement"
                value={`${formatNumber(
                  alert.fuel_event_pct,
                  2
                )} %`}
              />


              <DetailItem
                label="Ratio de récupération"
                value={
                  formatNumber(
                    alert.recovery_ratio,
                    2
                  )
                }
              />

            </DetailGrid>

          </DetailSection>


          {/* ================================================= */}
          {/* CONTEXTE VEHICULE */}
          {/* ================================================= */}

          <DetailSection
            title="Contexte véhicule"
            icon={
              <Truck size={18} />
            }
          >

            <DetailGrid>

              <DetailItem
                label="Vitesse"
                value={`${formatNumber(
                  alert.speed_kmh,
                  1
                )} km/h`}
              />


              <DetailItem
                label="Distance"
                value={`${formatNumber(
                  alert.distance_abs_m,
                  1
                )} m`}
              />


              <DetailItem
                label="Intervalle temporel"
                value={
                  formatDuration(
                    alert.delta_time_sec
                  )
                }
              />


              <DetailItem
                label="Contact moteur"
                value={
                  alert.ignition ===
                  null
                    ? "—"
                    : alert.ignition
                      ? "ON"
                      : "OFF"
                }
              />

            </DetailGrid>

          </DetailSection>


          {/* ================================================= */}
          {/* ANALYSE IA */}
          {/* ================================================= */}

          <DetailSection
            title="Analyse IA"
            icon={
              <BrainCircuit size={18} />
            }
          >

            <DetailGrid>

              <DetailItem
                label="Candidat IA"
                value={
                  alert.ai_anomaly_flag ===
                  null
                    ? "—"
                    : alert.ai_anomaly_flag
                      ? "Oui"
                      : "Non"
                }
              />


              <DetailItem
                label="Score d'anomalie"
                value={
                  alert.ai_score_percentile !==
                  null
                    ? `${formatNumber(
                        alert.ai_score_percentile,
                        2
                      )} %`
                    : "—"
                }
              />


              <DetailItem
                label="Score brut IA"
                value={
                  formatNumber(
                    alert.ai_anomaly_score,
                    4
                  )
                }
              />


              <DetailItem
                label="Détection combinée"
                value={
                  alert.detection_combinee ??
                  "—"
                }
              />

            </DetailGrid>

          </DetailSection>


          {/* ================================================= */}
          {/* ANALYSE CONTEXTUELLE */}
          {/* ================================================= */}

          <DetailSection
            title="Analyse contextuelle"
            icon={
              <CheckCircle2 size={18} />
            }
          >

            <DetailGrid>

              <DetailItem
                label="Niveau de confiance"
                value={
                  alert.confidence_level ??
                  "—"
                }
              />


              <DetailItem
                label="Persistance"
                value={
                  alert.persistence ??
                  "—"
                }
              />


              <DetailItem
                label="Contexte temporel"
                value={
                  alert.contexte_temporel ??
                  "—"
                }
              />


              <DetailItem
                label="Support contextuel"
                value={
                  alert.context_support ??
                  "—"
                }
              />

            </DetailGrid>


            {alert.analysis_reason && (

              <div className="mt-4 rounded-lg bg-slate-50 p-4">

                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Interprétation
                </p>


                <p className="mt-2 text-sm leading-6 text-slate-700">
                  {alert.analysis_reason}
                </p>

              </div>

            )}

          </DetailSection>


          {/* ================================================= */}
          {/* PRIORISATION */}
          {/* ================================================= */}

          <DetailSection
            title="Priorisation"
            icon={
              <AlertTriangle size={18} />
            }
          >

            <DetailGrid>

              <DetailItem
                label="Priorité"
                value={
                  alert.rang_priorite !==
                  null
                    ? `P${alert.rang_priorite}`
                    : "—"
                }
              />


              <DetailItem
                label="Libellé"
                value={
                  alert.priorite_alerte ??
                  "—"
                }
              />

            </DetailGrid>


            {alert.raison_priorite && (

              <div className="mt-4 rounded-lg bg-amber-50 p-4">

                <p className="text-xs font-semibold uppercase tracking-wide text-amber-700">
                  Pourquoi cette priorité ?
                </p>


                <p className="mt-2 text-sm leading-6 text-amber-800">
                  {alert.raison_priorite}
                </p>

              </div>

            )}

          </DetailSection>


          {/* ================================================= */}
          {/* POSITION GPS */}
          {/* ================================================= */}

          <DetailSection
            title="Position"
            icon={
              <MapPin size={18} />
            }
          >

            <DetailGrid>

              <DetailItem
                label="Latitude"
                value={
                  formatNumber(
                    alert.latitude,
                    6
                  )
                }
              />


              <DetailItem
                label="Longitude"
                value={
                  formatNumber(
                    alert.longitude,
                    6
                  )
                }
              />

            </DetailGrid>


            {alert.lien_carte && (

              <a
                href={
                  alert.lien_carte
                }
                target="_blank"
                rel="noreferrer"
                className="mt-4 inline-flex items-center gap-2 rounded-lg border border-blue-200 bg-blue-50 px-4 py-2.5 text-sm font-semibold text-blue-700 transition hover:bg-blue-100"
              >

                <MapPin
                  size={16}
                />

                Ouvrir la position sur la carte

                <ExternalLink
                  size={14}
                />

              </a>

            )}

          </DetailSection>


          {/* ================================================= */}
          {/* AVERTISSEMENT */}
          {/* ================================================= */}

          <div className="rounded-xl border border-slate-200 bg-slate-50 p-5">

            <p className="text-sm font-semibold text-slate-900">
              Interprétation de l&apos;alerte
            </p>


            <p className="mt-2 text-sm leading-6 text-slate-600">

              Cette fiche regroupe les éléments utiles
              à l&apos;investigation.

              Une alerte indique un événement atypique
              ou suspect à examiner.

              Elle ne permet pas, à elle seule,
              de conclure à un vol, une fuite
              ou une fraude.

            </p>

          </div>

        </div>

      </div>

    </div>

  );
}


// ============================================================
// SECTION DETAIL
// ============================================================

function DetailSection({
  title,
  icon,
  children,
}: {
  title: string;
  icon: ReactNode;
  children: ReactNode;
}) {

  return (

    <section className="rounded-xl border border-slate-200 p-5">

      <div className="flex items-center gap-2">

        <span className="text-blue-600">
          {icon}
        </span>


        <h3 className="font-semibold text-slate-900">
          {title}
        </h3>

      </div>


      <div className="mt-4">
        {children}
      </div>

    </section>

  );
}


// ============================================================
// GRILLE DETAIL
// ============================================================

function DetailGrid({
  children,
}: {
  children: ReactNode;
}) {

  return (

    <div className="grid gap-4 sm:grid-cols-2">
      {children}
    </div>

  );
}


// ============================================================
// ITEM DETAIL
// ============================================================

function DetailItem({
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


      <p className="mt-1 break-words text-sm font-semibold text-slate-900">
        {value}
      </p>

    </div>

  );
}


// ============================================================
// INDICATEUR PRINCIPAL DETAIL
// ============================================================

function DetailHighlight({
  label,
  value,
}: {
  label: string;
  value: string;
}) {

  return (

    <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">

      <p className="text-xs text-slate-500">
        {label}
      </p>


      <p className="mt-1 text-xl font-bold text-slate-900">
        {value}
      </p>

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
  value: number;
  description: string;
  icon: ReactNode;
}) {

  return (

    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">

      <div className="flex items-start justify-between">

        <div>

          <p className="text-sm text-slate-500">
            {label}
          </p>


          <p className="mt-2 text-3xl font-bold text-slate-900">
            {value}
          </p>

        </div>


        <div className="rounded-lg bg-slate-50 p-2.5 text-blue-600">
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
// FILTRE SELECT
// ============================================================

function FilterSelect({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (
    value: string
  ) => void;
  options: string[];
}) {

  return (

    <div>

      <label className="mb-2 block text-xs font-semibold text-slate-600">
        {label}
      </label>


      <select
        value={
          value
        }
        onChange={
          (event) =>
            onChange(
              event.target.value
            )
        }
        className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-blue-500"
      >

        {options.map(
          (option) => (

            <option
              key={
                option
              }
              value={
                option
              }
            >

              {option}

            </option>

          )
        )}

      </select>

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
// BADGE PRIORITE
// ============================================================

function PriorityBadge({
  rank,
  label,
}: {
  rank: number | null;
  label: string | null;
}) {

  const classes:
    Record<number, string> = {

    1:
      "bg-red-50 text-red-700 border-red-200",

    2:
      "bg-orange-50 text-orange-700 border-orange-200",

    3:
      "bg-blue-50 text-blue-700 border-blue-200",

    4:
      "bg-slate-50 text-slate-600 border-slate-200",

    5:
      "bg-amber-50 text-amber-700 border-amber-200",
  };


  const className =
    rank !== null
      ? classes[rank] ??
        "bg-slate-50 text-slate-600 border-slate-200"
      : "bg-slate-50 text-slate-600 border-slate-200";


  return (

    <span
      title={
        label ?? undefined
      }
      className={`inline-flex rounded-full border px-3 py-1 text-xs font-bold ${className}`}
    >

      {rank !== null
        ? `P${rank}`
        : "—"}

    </span>

  );
}


// ============================================================
// BADGE SOURCE
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


  let className =
    "bg-slate-100 text-slate-700";


  if (
    source ===
    "Règle + IA"
  ) {

    className =
      "bg-emerald-50 text-emerald-700";

  } else if (
    source ===
    "IA uniquement"
  ) {

    className =
      "bg-blue-50 text-blue-700";

  } else if (
    source ===
    "Règle uniquement"
  ) {

    className =
      "bg-violet-50 text-violet-700";
  }


  return (

    <span
      className={`rounded-full px-3 py-1 text-xs font-semibold ${className}`}
    >

      {source}

    </span>

  );
}


// ============================================================
// BADGE CONFIANCE
// ============================================================

function ConfidenceBadge({
  value,
}: {
  value: string | null;
}) {

  if (!value) {

    return (

      <span className="text-sm text-slate-400">
        —
      </span>

    );
  }


  let className =
    "bg-slate-100 text-slate-600";


  if (
    value ===
    "Forte"
  ) {

    className =
      "bg-emerald-50 text-emerald-700";

  } else if (
    value ===
    "Moyenne"
  ) {

    className =
      "bg-amber-50 text-amber-700";

  } else if (
    value ===
    "Faible"
  ) {

    className =
      "bg-red-50 text-red-700";
  }


  return (

    <span
      className={`rounded-full px-3 py-1 text-xs font-semibold ${className}`}
    >

      {value}

    </span>

  );
}


// ============================================================
// BADGE STATUT
// ============================================================

function StatusBadge({
  value,
}: {
  value: string;
}) {

  let className =
    "bg-amber-50 text-amber-700";


  if (
    value ===
    "Confirmée"
  ) {

    className =
      "bg-emerald-50 text-emerald-700";

  } else if (
    value ===
    "Faux positif"
  ) {

    className =
      "bg-red-50 text-red-700";

  } else if (
    value ===
    "Ignorée"
  ) {

    className =
      "bg-slate-100 text-slate-600";
  }


  return (

    <span
      className={`rounded-full px-3 py-1 text-xs font-semibold ${className}`}
    >

      {value}

    </span>

  );
}


// ============================================================
// FORMATAGE NOMBRE
// ============================================================

function formatNumber(
  value:
    | number
    | null,
  decimals: number
) {

  if (
    value === null ||
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


// ============================================================
// FORMATAGE DATE
// ============================================================

function formatDate(
  value: string | null
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
      day:
        "2-digit",

      month:
        "2-digit",

      year:
        "numeric",

      hour:
        "2-digit",

      minute:
        "2-digit",
    }
  );
}


// ============================================================
// FORMATAGE DUREE
// ============================================================

function formatDuration(
  seconds:
    | number
    | null
) {

  if (
    seconds === null ||
    Number.isNaN(
      seconds
    )
  ) {

    return "—";
  }


  if (
    seconds < 60
  ) {

    return `${formatNumber(
      seconds,
      0
    )} s`;
  }


  const minutes =
    seconds / 60;


  if (
    minutes < 60
  ) {

    return `${formatNumber(
      minutes,
      1
    )} min`;
  }


  return `${formatNumber(
    minutes / 60,
    1
  )} h`;
}