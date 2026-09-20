"use client";

import {
  useEffect,
  useRef,
  useState,
} from "react";

import {
  AlertCircle,
  BrainCircuit,
  CheckCircle2,
  FileText,
  Loader2,
  Play,
  UploadCloud,
  X,
  XCircle,
} from "lucide-react";

import {
  analyzeFleetDataset,
  uploadFleetFile,
  validateFleetDataset,
  type DatasetAnalysisResult,
  type DatasetValidationResult,
  type UploadResult,
} from "@/lib/api";


const MAX_DEMO_FILE_SIZE_BYTES =
  5 * 1024 * 1024;


export default function ImportsPage() {

  const fileInputRef =
    useRef<HTMLInputElement>(null);

  const [selectedFile, setSelectedFile] =
    useState<File | null>(null);

  const [importKey, setImportKey] =
    useState("");

  const [isUploading, setIsUploading] =
    useState(false);

  const [isValidating, setIsValidating] =
    useState(false);

  const [isAnalyzing, setIsAnalyzing] =
    useState(false);

  const [uploadResult, setUploadResult] =
    useState<UploadResult | null>(null);

  const [
    validationResult,
    setValidationResult,
  ] =
    useState<DatasetValidationResult | null>(
      null
    );

  const [
    analysisResult,
    setAnalysisResult,
  ] =
    useState<DatasetAnalysisResult | null>(
      null
    );

  const [errorMessage, setErrorMessage] =
    useState<string | null>(null);


  // ============================================================
  // CONSERVATION DE LA DERNIERE ANALYSE
  // ============================================================

  const LAST_ANALYSIS_STORAGE_KEY =
    "fleet_last_analysis_result";


  useEffect(() => {

    try {

      const savedAnalysis =
        localStorage.getItem(
          LAST_ANALYSIS_STORAGE_KEY
        );

      if (!savedAnalysis) {
        return;
      }

      const parsedAnalysis =
        JSON.parse(savedAnalysis) as DatasetAnalysisResult;

      setAnalysisResult(parsedAnalysis);

    } catch {

      localStorage.removeItem(
        LAST_ANALYSIS_STORAGE_KEY
      );
    }

  }, []);


  // ============================================================
  // SELECTION DU FICHIER
  // ============================================================

  function handleSelectFile() {
    fileInputRef.current?.click();
  }


  function handleFileChange(
    event: React.ChangeEvent<HTMLInputElement>
  ) {

    const file =
      event.target.files?.[0];

    if (!file) {
      return;
    }

    if (
      file.size >
      MAX_DEMO_FILE_SIZE_BYTES
    ) {
      setSelectedFile(null);
      setUploadResult(null);
      setValidationResult(null);
      setErrorMessage(
        "Le mode démonstration accepte des fichiers de 5 Mo maximum."
      );

      event.target.value = "";
      return;
    }

    setSelectedFile(file);

    setUploadResult(null);
    setValidationResult(null);
    setErrorMessage(null);
  }


  function handleRemoveFile() {

    setSelectedFile(null);

    setUploadResult(null);
    setValidationResult(null);

    setErrorMessage(null);

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }


  // ============================================================
  // FORMATAGE
  // ============================================================

  function formatFileSize(
    bytes: number
  ) {

    if (bytes < 1024) {
      return `${bytes} octets`;
    }

    if (bytes < 1024 * 1024) {

      return `${(
        bytes / 1024
      ).toFixed(1)} KB`;
    }

    if (
      bytes <
      1024 * 1024 * 1024
    ) {

      return `${(
        bytes /
        1024 /
        1024
      ).toFixed(2)} MB`;
    }

    return `${(
      bytes /
      1024 /
      1024 /
      1024
    ).toFixed(2)} GB`;
  }


  function formatDate(
    date: string | null
  ) {

    if (!date) {
      return "Non disponible";
    }

    const parsedDate =
      new Date(date);

    return parsedDate.toLocaleString(
      "fr-FR"
    );
  }


  // ============================================================
  // UPLOAD + VALIDATION
  // ============================================================

  async function handleUpload() {

    if (!selectedFile) {
      return;
    }

    const normalizedImportKey =
      importKey.trim();

    if (!normalizedImportKey) {
      setErrorMessage(
        "Saisissez la clé d'import."
      );
      return;
    }

    setIsUploading(true);

    setErrorMessage(null);
    setUploadResult(null);
    setValidationResult(null);
    setAnalysisResult(null);

    localStorage.removeItem(
      LAST_ANALYSIS_STORAGE_KEY
    );

    try {

      // 1. Upload
      const uploaded =
        await uploadFleetFile(
          selectedFile,
          normalizedImportKey
        );

      setUploadResult(
        uploaded
      );

      // 2. Validation
      setIsValidating(true);

      const validation =
        await validateFleetDataset(
          uploaded.upload_id,
          normalizedImportKey
        );

      setValidationResult(
        validation
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

      setIsUploading(false);
      setIsValidating(false);
    }
  }


  // ============================================================
  // ANALYSE COMPLETE
  // ============================================================

  async function handleAnalyze() {

    if (
      !uploadResult ||
      !validationResult ||
      !validationResult.compatible ||
      !importKey.trim()
    ) {
      return;
    }

    setIsAnalyzing(true);

    setErrorMessage(null);
    setAnalysisResult(null);

    try {

      const result =
        await analyzeFleetDataset(
          uploadResult.upload_id,
          importKey.trim()
        );

      setAnalysisResult(
        result
      );

      localStorage.setItem(
        LAST_ANALYSIS_STORAGE_KEY,
        JSON.stringify(result)
      );

    } catch (error) {

      if (error instanceof Error) {

        setErrorMessage(
          error.message
        );

      } else {

        setErrorMessage(
          "Une erreur est survenue pendant l'analyse."
        );
      }

    } finally {

      setIsAnalyzing(false);
    }
  }


  // ============================================================
  // CONTROLE QUALITE
  // ============================================================

  const qualityOk =
    analysisResult
      ? Object.values(
          analysisResult.quality_controls
        ).every(
          (value) => value === 0
        )
      : false;


  // ============================================================
  // ORIGINE DES EVENEMENTS
  // ============================================================

  const aiOnly =
    analysisResult
      ? (
          analysisResult.ai.nombre_candidats_ia -
          analysisResult.ai.nombre_regle_et_ia
        )
      : 0;

  const ruleAndAi =
    analysisResult
      ? analysisResult.ai.nombre_regle_et_ia
      : 0;

  const ruleOnly =
    analysisResult
      ? (
          analysisResult.platform.nombre_alertes_finales -
          analysisResult.ai.nombre_candidats_ia
        )
      : 0;


  // ============================================================
  // MOTEUR DE TRAITEMENT UTILISE
  // ============================================================

  type AnalysisResultWithEngine =
    DatasetAnalysisResult & {
      moteur_code?: "pandas" | "spark";
      moteur_utilise?: string;
    };

  const moteurUtilise =
    analysisResult
      ? (
          analysisResult as AnalysisResultWithEngine
        ).moteur_utilise
      : undefined;

  const moteurCode =
    analysisResult
      ? (
          analysisResult as AnalysisResultWithEngine
        ).moteur_code
      : undefined;


  return (
    <div>

      {/* ===================================================== */}
      {/* EN-TETE */}
      {/* ===================================================== */}

      <div className="mb-8">

        <p className="mb-2 text-sm font-semibold text-blue-600">
          Importation
        </p>

        <h1 className="text-3xl font-bold text-slate-900">
          Importer des données de flotte
        </h1>

        <p className="mt-2 max-w-3xl text-slate-500">
          Importez un fichier télématique,
          vérifiez sa compatibilité puis lancez
          l&apos;analyse complète de la flotte.
        </p>

      </div>


      {/* ===================================================== */}
      {/* BLOC PRINCIPAL */}
      {/* ===================================================== */}

      <div className="rounded-xl border border-slate-200 bg-white p-8 shadow-sm">


        {/* =================================================== */}
        {/* IMPORT */}
        {/* =================================================== */}

        <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-300 px-6 py-14">

          <div className="mb-4 rounded-full bg-blue-50 p-4">

            <UploadCloud
              size={32}
              className="text-blue-600"
            />

          </div>

          <h2 className="text-lg font-semibold text-slate-900">
            Déposez votre fichier de flotte
          </h2>

          <p className="mt-2 text-sm text-slate-500">
            Formats acceptés : CSV et Parquet
          </p>

          <p className="mt-2 max-w-xl text-center text-xs leading-5 text-slate-500">
            Démonstration gratuite : 5 Mo et 100&nbsp;000 lignes maximum,
            analyse Pandas et un seul traitement à la fois.
          </p>


          <div className="mt-6 w-full max-w-md text-left">

            <label
              htmlFor="import-key"
              className="text-sm font-medium text-slate-700"
            >
              Clé d&apos;import
            </label>

            <input
              id="import-key"
              type="password"
              value={importKey}
              onChange={(event) => {
                setImportKey(event.target.value);
                setErrorMessage(null);
              }}
              autoComplete="off"
              placeholder="Saisissez votre clé secrète"
              disabled={
                isUploading ||
                isValidating ||
                isAnalyzing
              }
              className="mt-2 w-full rounded-lg border border-slate-300 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100 disabled:bg-slate-100"
            />

            <p className="mt-2 text-xs text-slate-500">
              Cette clé reste uniquement dans cette page.
            </p>

          </div>


          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,.parquet"
            onChange={handleFileChange}
            className="hidden"
          />


          <button
            type="button"
            onClick={handleSelectFile}
            disabled={
              isUploading ||
              isValidating ||
              isAnalyzing
            }
            className="mt-6 rounded-lg bg-blue-600 px-5 py-3 text-sm font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Sélectionner un fichier
          </button>


          {selectedFile && (

            <div className="mt-6 min-w-[340px]">

              <div className="flex items-center justify-between gap-4 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3">

                <div className="flex items-center gap-3">

                  <FileText
                    size={21}
                    className="text-blue-600"
                  />

                  <div>

                    <p className="max-w-[230px] truncate text-sm font-medium text-slate-900">
                      {selectedFile.name}
                    </p>

                    <p className="mt-1 text-xs text-slate-500">
                      {formatFileSize(
                        selectedFile.size
                      )}
                    </p>

                  </div>

                </div>


                <button
                  type="button"
                  onClick={handleRemoveFile}
                  disabled={
                    isUploading ||
                    isValidating ||
                    isAnalyzing
                  }
                  className="rounded-md p-1 text-slate-400 transition hover:bg-slate-200 hover:text-slate-700 disabled:opacity-40"
                >
                  <X size={18} />
                </button>

              </div>


              <button
                type="button"
                onClick={handleUpload}
                disabled={
                  isUploading ||
                  isValidating ||
                  isAnalyzing ||
                  !importKey.trim()
                }
                className="mt-4 flex w-full items-center justify-center gap-2 rounded-lg bg-emerald-600 px-5 py-3 text-sm font-medium text-white transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60"
              >

                {isUploading ? (
                  <>
                    <Loader2
                      size={18}
                      className="animate-spin"
                    />

                    Importation...
                  </>
                ) : isValidating ? (
                  <>
                    <Loader2
                      size={18}
                      className="animate-spin"
                    />

                    Validation...
                  </>
                ) : (
                  <>
                    <UploadCloud size={18} />

                    Importer et valider
                  </>
                )}

              </button>

            </div>
          )}

        </div>


        {/* =================================================== */}
        {/* ERREUR */}
        {/* =================================================== */}

        {errorMessage && (

          <div className="mt-6 rounded-lg border border-red-200 bg-red-50 p-4">

            <div className="flex items-center gap-2">

              <XCircle
                size={20}
                className="text-red-600"
              />

              <p className="text-sm font-medium text-red-700">
                {errorMessage}
              </p>

            </div>

          </div>
        )}


        {/* =================================================== */}
        {/* UPLOAD OK */}
        {/* =================================================== */}

        {uploadResult && (

          <div className="mt-6 rounded-xl border border-emerald-200 bg-emerald-50 p-6">

            <div className="flex items-center gap-3">

              <CheckCircle2
                size={24}
                className="text-emerald-600"
              />

              <div>

                <h3 className="font-semibold text-emerald-900">
                  Fichier importé avec succès
                </h3>

                <p className="mt-1 text-sm text-emerald-700">
                  Le fichier a été reçu par la plateforme.
                </p>

              </div>

            </div>


            <div className="mt-5 grid gap-4 md:grid-cols-2">

              <div>

                <p className="text-xs text-emerald-700">
                  Nom du fichier
                </p>

                <p className="mt-1 text-sm font-medium text-slate-900">
                  {uploadResult.original_filename}
                </p>

              </div>


              <div>

                <p className="text-xs text-emerald-700">
                  Taille
                </p>

                <p className="mt-1 text-sm font-medium text-slate-900">
                  {formatFileSize(
                    uploadResult.size_bytes
                  )}
                </p>

              </div>

            </div>

          </div>
        )}


        {/* =================================================== */}
        {/* VALIDATION EN COURS */}
        {/* =================================================== */}

        {isValidating && (

          <div className="mt-6 rounded-xl border border-blue-200 bg-blue-50 p-6">

            <div className="flex items-center gap-3">

              <Loader2
                size={22}
                className="animate-spin text-blue-600"
              />

              <div>

                <p className="font-semibold text-blue-900">
                  Validation du dataset...
                </p>

                <p className="mt-1 text-sm text-blue-700">
                  Vérification de la structure
                  et des colonnes nécessaires.
                </p>

              </div>

            </div>

          </div>
        )}


        {/* =================================================== */}
        {/* RESULTAT VALIDATION */}
        {/* =================================================== */}

        {validationResult && (

          <div className="mt-6 rounded-xl border border-slate-200 bg-white p-6">

            <div className="flex items-start justify-between gap-4">

              <div className="flex items-center gap-3">

                {validationResult.compatible ? (

                  <CheckCircle2
                    size={26}
                    className="text-emerald-600"
                  />

                ) : (

                  <AlertCircle
                    size={26}
                    className="text-amber-600"
                  />
                )}


                <div>

                  <h2 className="text-lg font-semibold text-slate-900">
                    Validation du dataset
                  </h2>

                  <p className="mt-1 text-sm text-slate-500">
                    {validationResult.message}
                  </p>

                </div>

              </div>


              <span
                className={
                  validationResult.compatible
                    ? "rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700"
                    : "rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-700"
                }
              >
                {validationResult.niveau_analyse}
              </span>

            </div>


            <div className="mt-7 grid gap-4 md:grid-cols-4">

              <Metric
                label="Nombre de lignes"
                value={
                  validationResult.nombre_lignes.toLocaleString(
                    "fr-FR"
                  )
                }
              />

              <Metric
                label="Véhicules détectés"
                value={
                  validationResult.nombre_vehicules ??
                  "—"
                }
              />

              <Metric
                label="Colonnes"
                value={
                  validationResult.nombre_colonnes
                }
              />

              <Metric
                label="Format"
                value={
                  validationResult.extension
                    .replace(".", "")
                    .toUpperCase()
                }
              />

            </div>


            <div className="mt-6 grid gap-4 md:grid-cols-2">

              <InfoBox
                label="Début de période"
                value={
                  formatDate(
                    validationResult.debut_periode
                  )
                }
              />

              <InfoBox
                label="Fin de période"
                value={
                  formatDate(
                    validationResult.fin_periode
                  )
                }
              />

            </div>


            {validationResult.compatible &&
              uploadResult && (

                <div className="mt-7 border-t border-slate-200 pt-6">

                  <button
                    type="button"
                    onClick={handleAnalyze}
                    disabled={isAnalyzing}
                    className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-6 py-3 font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
                  >

                    {isAnalyzing ? (
                      <>
                        <Loader2
                          size={19}
                          className="animate-spin"
                        />

                        Analyse du dataset en cours...
                      </>
                    ) : (
                      <>
                        <Play size={19} />

                        Lancer l&apos;analyse
                      </>
                    )}

                  </button>

                </div>
              )}

          </div>
        )}


        {/* =================================================== */}
        {/* ANALYSE EN COURS */}
        {/* =================================================== */}

        {isAnalyzing && (

          <div className="mt-6 rounded-xl border border-blue-200 bg-blue-50 p-6">

            <div className="flex items-center gap-4">

              <Loader2
                size={28}
                className="animate-spin text-blue-600"
              />

              <div>

                <h3 className="font-semibold text-blue-900">
                  Analyse de la flotte en cours
                </h3>

                <p className="mt-1 text-sm text-blue-700">
                  Préparation des données,
                  règles métier,
                  analyse contextuelle,
                  Isolation Forest et calcul des KPI.
                </p>

              </div>

            </div>

          </div>
        )}


        {/* =================================================== */}
        {/* RESULTATS ANALYSE */}
        {/* =================================================== */}

        {analysisResult && (

          <div className="mt-6 rounded-xl border border-emerald-200 bg-white p-6 shadow-sm">


            {/* TITRE */}

            <div className="flex items-start gap-3">

              <div className="rounded-lg bg-emerald-50 p-3">

                <BrainCircuit
                  size={26}
                  className="text-emerald-600"
                />

              </div>


              <div>

                <h2 className="text-xl font-bold text-slate-900">
                  Analyse terminée avec succès
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  Le pipeline Data a analysé
                  automatiquement le dataset.
                </p>

                {moteurUtilise && (

                  <div className="mt-3 flex items-center gap-2">

                    <span className="text-sm font-medium text-slate-500">
                      Moteur utilisé :
                    </span>

                    <span
                      className={
                        moteurCode === "spark"
                          ? "rounded-full bg-orange-100 px-3 py-1 text-xs font-bold text-orange-700"
                          : "rounded-full bg-blue-100 px-3 py-1 text-xs font-bold text-blue-700"
                      }
                    >
                      {moteurUtilise}
                    </span>

                  </div>

                )}

              </div>

            </div>


            {/* ================================================= */}
            {/* SYNTHESE */}
            {/* ================================================= */}

            <div className="mt-8">

              <h3 className="font-semibold text-slate-900">
                Synthèse du dataset
              </h3>

              <p className="mt-1 text-sm text-slate-500">
                Vue générale des données analysées.
              </p>


              <div className="mt-4 grid gap-4 md:grid-cols-4">

                <Metric
                  label="Mesures préparées"
                  value={
                    analysisResult.preparation.nombre_lignes_preparees.toLocaleString(
                      "fr-FR"
                    )
                  }
                />

                <Metric
                  label="Véhicules"
                  value={
                    analysisResult.kpi.nombre_vehicules
                  }
                />

                <Metric
                  label="Distance totale"
                  value={`${analysisResult.kpi.distance_totale_km.toLocaleString(
                    "fr-FR",
                    {
                      maximumFractionDigits: 1,
                    }
                  )} km`}
                />

                <Metric
                  label="Événements à investiguer"
                  value={
                    analysisResult.platform.nombre_alertes_finales
                  }
                />

              </div>

            </div>


            {/* ================================================= */}
            {/* DETECTION */}
            {/* ================================================= */}

            <div className="mt-8">

              <h3 className="font-semibold text-slate-900">
                Résultats de la détection
              </h3>

              <p className="mt-1 text-sm text-slate-500">
                Les règles métier et Isolation Forest
                recherchent des variations de carburant atypiques.
              </p>


              <div className="mt-4 grid gap-4 md:grid-cols-4">

                <Metric
                  label="Ravitaillements potentiels"
                  value={
                    analysisResult.rules.nombre_ravitaillements
                  }
                />

                <Metric
                  label="Baisses détectées par les règles"
                  value={
                    analysisResult.rules.nombre_baisses_suspectes
                  }
                />

                <Metric
                  label="Candidats détectés par l'IA"
                  value={
                    analysisResult.ai.nombre_candidats_ia
                  }
                />

                <Metric
                  label="Détectés par règle + IA"
                  value={
                    analysisResult.ai.nombre_regle_et_ia
                  }
                />

              </div>

            </div>


            {/* ================================================= */}
            {/* ORIGINE DES EVENEMENTS */}
            {/* ================================================= */}

            <div className="mt-8 rounded-xl border border-blue-100 bg-blue-50/40 p-6">

              <h3 className="font-semibold text-slate-900">
                Origine des événements à investiguer
              </h3>

              <p className="mt-1 text-sm text-slate-500">
                Cette répartition indique quelle méthode
                a détecté chaque événement.
              </p>


              <div className="mt-5 grid gap-4 md:grid-cols-3">

                <SourceCard
                  label="IA uniquement"
                  value={aiOnly}
                  description="Événements proposés uniquement par Isolation Forest."
                />

                <SourceCard
                  label="Règle + IA"
                  value={ruleAndAi}
                  description="Événements détectés par les deux approches."
                />

                <SourceCard
                  label="Règle uniquement"
                  value={ruleOnly}
                  description="Événements détectés par les règles mais pas retenus parmi les candidats IA."
                />

              </div>


              <div className="mt-5 rounded-lg bg-white p-4 text-sm text-slate-600">

                <strong className="text-slate-900">
                  Total :
                </strong>{" "}

                {aiOnly} IA uniquement
                {" + "}
                {ruleAndAi} règle + IA
                {" + "}
                {ruleOnly} règle uniquement
                {" = "}

                <strong className="text-slate-900">
                  {
                    analysisResult.platform
                      .nombre_alertes_finales
                  } événements uniques
                </strong>

              </div>

            </div>


            {/* ================================================= */}
            {/* PRIORITES */}
            {/* ================================================= */}

            <div className="mt-8">

              <h3 className="font-semibold text-slate-900">
                Priorité d&apos;investigation
              </h3>

              <p className="mt-1 text-sm text-slate-500">
                La priorité aide l&apos;utilisateur à déterminer
                quels événements examiner en premier.
                Elle ne confirme pas un vol,
                une fuite ou une fraude.
              </p>


              <div className="mt-4 grid gap-3 md:grid-cols-5">

                <Priority
                  label="P1 Critique"
                  value={
                    analysisResult.platform.priorites.P1
                  }
                  description="Règle + IA avec confiance forte."
                />

                <Priority
                  label="P2 Élevée"
                  value={
                    analysisResult.platform.priorites.P2
                  }
                  description="Règle + IA avec confiance moyenne."
                />

                <Priority
                  label="P3 À investiguer"
                  value={
                    analysisResult.platform.priorites.P3
                  }
                  description="Événement atypique à vérifier."
                />

                <Priority
                  label="P4 Faible"
                  value={
                    analysisResult.platform.priorites.P4
                  }
                  description="Règle uniquement."
                />

                <Priority
                  label="P5 Prudence"
                  value={
                    analysisResult.platform.priorites.P5
                  }
                  description="IA avec une longue coupure de transmission."
                />

              </div>

            </div>


            {/* ================================================= */}
            {/* ANALYSE CONTEXTUELLE */}
            {/* ================================================= */}

            <div className="mt-8">

              <h3 className="font-semibold text-slate-900">
                Analyse contextuelle des{" "}
                {
                  analysisResult.rules
                    .nombre_baisses_suspectes
                } baisses détectées par les règles
              </h3>

              <p className="mt-1 text-sm text-slate-500">
                Le niveau de confiance concerne uniquement
                les événements détectés par les règles métier.
              </p>


              <div className="mt-4 grid gap-4 md:grid-cols-3">

                <Metric
                  label="Confiance forte"
                  value={
                    analysisResult.context.confiance_forte
                  }
                />

                <Metric
                  label="Confiance moyenne"
                  value={
                    analysisResult.context.confiance_moyenne
                  }
                />

                <Metric
                  label="Confiance faible"
                  value={
                    analysisResult.context.confiance_faible
                  }
                />

              </div>

            </div>


            {/* ================================================= */}
            {/* CONCORDANCE REGLES / IA */}
            {/* ================================================= */}

            <div className="mt-8 rounded-xl border border-slate-200 p-6">

              <h3 className="font-semibold text-slate-900">
                Concordance entre les règles et l&apos;IA
              </h3>


              {analysisResult.rules
                .nombre_baisses_suspectes > 0 ? (

                <div className="mt-4">

                  <p className="text-2xl font-bold text-slate-900">

                    {
                      analysisResult.ai
                        .nombre_regle_et_ia
                    }
                    {" sur "}
                    {
                      analysisResult.rules
                        .nombre_baisses_suspectes
                    }

                  </p>


                  <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">

                    alertes détectées par les règles métier
                    sont également retrouvées parmi les
                    événements jugés les plus atypiques
                    par Isolation Forest.

                  </p>


                  <p className="mt-3 text-xs leading-5 text-slate-500">

                    Cette information montre la concordance
                    entre les deux méthodes.
                    Elle ne constitue pas une mesure
                    d&apos;accuracy ou de précision du modèle.

                  </p>

                </div>

              ) : (

                <div className="mt-4">

                  <p className="text-sm font-medium text-slate-700">
                    Aucune baisse suspecte n&apos;a été détectée
                    par les règles métier.
                  </p>

                  <p className="mt-2 text-xs text-slate-500">
                    La concordance règles / IA n&apos;est donc
                    pas évaluée pour ce dataset.
                  </p>

                </div>
              )}

            </div>


            {/* ================================================= */}
            {/* QUALITE */}
            {/* ================================================= */}

            <div
              className={
                qualityOk
                  ? "mt-8 rounded-lg border border-emerald-200 bg-emerald-50 p-4"
                  : "mt-8 rounded-lg border border-amber-200 bg-amber-50 p-4"
              }
            >

              <div className="flex items-center gap-2">

                {qualityOk ? (

                  <CheckCircle2
                    size={20}
                    className="text-emerald-600"
                  />

                ) : (

                  <AlertCircle
                    size={20}
                    className="text-amber-600"
                  />
                )}


                <p className="font-semibold text-slate-900">

                  {qualityOk
                    ? "Contrôles des tables finales : OK"
                    : "Des contrôles nécessitent une vérification"}

                </p>

              </div>

            </div>

          </div>
        )}


        {/* =================================================== */}
        {/* PIPELINE */}
        {/* =================================================== */}

        <div className="mt-8 grid gap-5 md:grid-cols-3">

          <PipelineStep
            number="1"
            title="Import"
            description="Réception du fichier télématique."
          />

          <PipelineStep
            number="2"
            title="Validation"
            description="Vérification de la structure et de la qualité des données."
          />

          <PipelineStep
            number="3"
            title="Analyse"
            description="Règles métier, analyse contextuelle, Isolation Forest et KPI."
          />

        </div>

      </div>

    </div>
  );
}


// ============================================================
// METRIC
// ============================================================

function Metric({
  label,
  value,
}: {
  label: string;
  value: string | number;
}) {

  return (
    <div className="rounded-lg bg-slate-50 p-4">

      <p className="text-xs text-slate-500">
        {label}
      </p>

      <p className="mt-2 text-xl font-bold text-slate-900">
        {value}
      </p>

    </div>
  );
}


// ============================================================
// INFO
// ============================================================

function InfoBox({
  label,
  value,
}: {
  label: string;
  value: string;
}) {

  return (
    <div className="rounded-lg border border-slate-200 p-4">

      <p className="text-xs font-medium text-slate-500">
        {label}
      </p>

      <p className="mt-2 text-sm font-semibold text-slate-900">
        {value}
      </p>

    </div>
  );
}


// ============================================================
// SOURCE
// ============================================================

function SourceCard({
  label,
  value,
  description,
}: {
  label: string;
  value: number;
  description: string;
}) {

  return (
    <div className="rounded-lg border border-blue-100 bg-white p-5">

      <p className="text-sm font-semibold text-slate-800">
        {label}
      </p>

      <p className="mt-3 text-3xl font-bold text-slate-900">
        {value}
      </p>

      <p className="mt-2 text-xs leading-5 text-slate-500">
        {description}
      </p>

    </div>
  );
}


// ============================================================
// PRIORITE
// ============================================================

function Priority({
  label,
  value,
  description,
}: {
  label: string;
  value: number;
  description: string;
}) {

  return (
    <div className="rounded-lg border border-slate-200 p-4">

      <p className="text-xs font-semibold text-slate-600">
        {label}
      </p>

      <p className="mt-2 text-2xl font-bold text-slate-900">
        {value}
      </p>

      <p className="mt-2 text-xs leading-5 text-slate-500">
        {description}
      </p>

    </div>
  );
}


// ============================================================
// PIPELINE
// ============================================================

function PipelineStep({
  number,
  title,
  description,
}: {
  number: string;
  title: string;
  description: string;
}) {

  return (
    <div className="rounded-lg bg-slate-50 p-5">

      <div className="mb-3 flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 text-sm font-bold text-blue-600">
        {number}
      </div>

      <p className="text-sm font-semibold text-slate-900">
        {title}
      </p>

      <p className="mt-2 text-sm text-slate-500">
        {description}
      </p>

    </div>
  );
}
