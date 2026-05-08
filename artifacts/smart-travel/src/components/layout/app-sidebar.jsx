import React from 'react'
import { Link, useLocation } from 'wouter'
import {
    LayoutDashboard,
    Map,
    Database,
    Calendar,
    Activity,
    ShieldCheck,
    Globe,
    Cpu,
    TrendingUp
} from 'lucide-react'
import { cn } from '@/lib/utils'

const NavItem = ({ href, icon: Icon, label, active }) => (
    <Link
        href={href}
        className={cn(
            "flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-200 group relative",
            active
                ? "bg-emerald-500/10 text-emerald-500 font-medium"
                : "text-slate-400 hover:text-slate-100 hover:bg-slate-800"
        )}
    >
        <Icon className={cn("w-5 h-5", active ? "text-emerald-500" : "group-hover:text-emerald-400")} />
        <span>{label}</span>
        {active && (
            <div className="absolute left-0 w-1 h-6 bg-emerald-500 rounded-r-full" />
        )}
    </Link>
)

const NavGroup = ({ title, children }) => (
    <div className="space-y-1 my-4">
        <h3 className="px-3 text-[10px] uppercase tracking-wider text-slate-500 font-bold mb-2">
            {title}
        </h3>
        {children}
    </div>
)

export function AppSidebar() {
    const [pathname] = useLocation()

    return (
        <aside className="w-64 flex-shrink-0 border-r border-slate-800 bg-slate-900 flex flex-col h-screen fixed left-0 top-0 z-50">
            <div className="p-6">
                <div className="flex items-center gap-3 mb-8">
                    <div className="bg-emerald-500 p-2 rounded-xl shadow-lg shadow-emerald-500/20">
                        <TrendingUp className="w-6 h-6 text-white" />
                    </div>
                    <div>
                        <span className="text-white font-bold text-lg tracking-tight block">SmartTravel</span>
                        <span className="text-slate-500 text-[10px] uppercase font-bold">Data Platform v2</span>
                    </div>
                </div>

                <nav className="space-y-6">
                    <NavGroup title="Executive Summary">
                        <NavItem
                            href="/"
                            icon={LayoutDashboard}
                            label="Overview"
                            active={pathname === '/'}
                        />
                        <NavItem
                            href="/dashboards/smart-travel"
                            icon={Map}
                            label="Travel Analytics"
                            active={pathname.startsWith('/dashboards')}
                        />
                    </NavGroup>

                    <NavGroup title="Data Operations">
                        <NavItem
                            href="/connections"
                            icon={Database}
                            label="API Connectors"
                            active={pathname.startsWith('/connections')}
                        />
                        <NavItem
                            href="/airflow"
                            icon={Cpu}
                            label="Pipeline Lab"
                            active={pathname.startsWith('/airflow')}
                        />
                        <NavItem
                            href="/data"
                            icon={Globe}
                            label="Data Explorer"
                            active={pathname.startsWith('/data')}
                        />
                    </NavGroup>

                    <NavGroup title="Administration">
                        <NavItem
                            href="/admin"
                            icon={ShieldCheck}
                            label="Admin Portal"
                            active={pathname.startsWith('/admin')}
                        />
                        <NavItem
                            href="/schedules"
                            icon={Calendar}
                            label="Automation"
                            active={pathname.startsWith('/schedules')}
                        />
                        <NavItem
                            href="/monitoring"
                            icon={Activity}
                            label="Status"
                            active={pathname.startsWith('/monitoring')}
                        />
                    </NavGroup>
                </nav>
            </div>

            <div className="mt-auto p-4 border-t border-slate-800">
                <div className="bg-slate-800/50 rounded-lg p-3 flex items-center gap-3">
                    <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                    <span className="text-xs text-slate-300">System Healthy</span>
                </div>
            </div>
        </aside>
    )
}
