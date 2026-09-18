"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import {
  LayoutDashboard,
  Upload,
  Truck,
  Fuel,
  TriangleAlert,
  Brain,
  Database,
} from "lucide-react";

const navigation = [
  {
    name: "Vue d'ensemble",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    name: "Importer des données",
    href: "/imports",
    icon: Upload,
  },
  {
    name: "Performance flotte",
    href: "/fleet",
    icon: Truck,
  },
  {
    name: "Carburant",
    href: "/fuel",
    icon: Fuel,
  },
  {
    name: "Alertes",
    href: "/alerts",
    icon: TriangleAlert,
  },
  {
    name: "Résultats IA",
    href: "/analytics",
    icon: Brain,
  },
  {
    name: "Qualité des données",
    href: "/data-quality",
    icon: Database,
  },
];


export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 border-r border-slate-800 bg-slate-950 text-white">

      {/* Logo / titre */}
      <div className="flex h-20 items-center border-b border-slate-800 px-6">
        <div>
          <p className="text-lg font-bold">
            Fleet Analytics
          </p>

          <p className="text-xs text-slate-400">
            Oritech • PFA
          </p>
        </div>
      </div>


      {/* Navigation */}
      <nav className="space-y-2 p-4">

        {navigation.map((item) => {
          const Icon = item.icon;

          const isActive =
            pathname === item.href ||
            pathname.startsWith(`${item.href}/`);

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`
                flex items-center gap-3 rounded-lg px-4 py-3
                text-sm font-medium transition
                ${
                  isActive
                    ? "bg-blue-600 text-white"
                    : "text-slate-300 hover:bg-slate-800 hover:text-white"
                }
              `}
            >
              <Icon size={19} />

              <span>
                {item.name}
              </span>
            </Link>
          );
        })}

      </nav>


      {/* Bas de sidebar */}
      <div className="absolute bottom-0 w-full border-t border-slate-800 p-5">

        <p className="text-xs text-slate-500">
          Plateforme d&apos;analyse de flotte
        </p>


      </div>

    </aside>
  );
}