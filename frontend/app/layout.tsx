import type { Metadata } from "next";

import "./globals.css";

import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";


export const metadata: Metadata = {
  title: "Fleet Analytics Platform",
  description:
    "Plateforme d'analyse des performances de la flotte et de détection d'anomalies liées au carburant",
};


export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fr">

      <body className="bg-slate-50 text-slate-900">

        <Sidebar />

        <div className="ml-64 min-h-screen">

          <Header />

          <div className="p-8">
            {children}
          </div>

        </div>

      </body>

    </html>
  );
}