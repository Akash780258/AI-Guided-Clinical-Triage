"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { motion, AnimatePresence, useMotionValue, useSpring, useTransform } from "framer-motion";
import { useQuery } from "@tanstack/react-query";
import {
  LayoutDashboard,
  Users,
  Stethoscope,
  CalendarClock,
  FileText,
  FlaskConical,
  Receipt,
  Pill,
  BrainCircuit,
  BarChart3,
  Settings,
  LogOut,
  ChevronLeft,
  ChevronRight,
  Search,
  Bell,
  MessageSquare,
  Sun,
  Moon,
  ChevronDown,
  AlertTriangle,
  Activity,
  TrendingUp,
  HeartPulse,
  DollarSign,
  ClipboardList,
  ScanLine,
  UserPlus,
  FilePlus2,
  Sparkles,
  Eye,
  Pencil,
  Trash2,
  ChevronsLeft,
  ChevronsRight,
  Zap,
  ShieldAlert,
} from "lucide-react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  RadialBarChart,
  RadialBar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";

import apiClient from "@/lib/axios";
import { useAuthStore } from "@/store/auth.store";

/* ============================================================
   SECTION: TYPES & INTERFACES
   (Everything stays in this single file by design — v1 constraint)
============================================================ */
type NavItem = {
  key: string;
  label: string;
  href: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
};

type PatientStatus = "Stable" | "Critical" | "Under Observation" | "Discharged";

type Patient = {
  id: string;
  name: string;
  avatar: string;
  department: string;
  doctor: string;
  status: PatientStatus;
};

type Appointment = {
  id: string;
  time: string;
  patient: string;
  doctor: string;
  department: string;
  status: "Confirmed" | "Pending" | "Completed" | "Cancelled";
};

type AIAlert = {
  id: string;
  title: string;
  detail: string;
  severity: "critical" | "high" | "moderate";
  icon: React.ComponentType<{ size?: number; className?: string }>;
};

type QuickAction = {
  label: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  gradient: string;
  href: string;
};

/* ============================================================
   SECTION: DESIGN TOKENS — "Quantum Clinical Interface"
   Matte command-center surfaces, illuminated cyan edges, restrained
   status accents. Referenced by hex throughout instead of Tailwind
   gradient utilities so every panel reads as a flat, engineered
   surface rather than a soft translucent card.
============================================================ */
const INK = {
  base: "#050608",
  panel: "#0E1117",
  panelRaised: "#141922",
  cyan: "#3CF4FF",
  blue: "#4D8EFF",
  green: "#52FFB8",
  orange: "#FF9A3D",
  red: "#FF4A63",
  slate: "#7C8798",
};

const FONT_UI = "font-['IBM_Plex_Sans',_'Geist',_sans-serif]";
const FONT_MONO = "font-['JetBrains_Mono',_ui-monospace,_monospace]";

/* ============================================================
   SECTION: STATIC DATA
   Navigation now maps to real routes. Sidebar links to pages that
   are not yet built (v1 = dashboard only) will simply 404 until
   those routes exist — this is intentional, not a bug.
============================================================ */
const NAV_ITEMS: NavItem[] = [
  { key: "dashboard", label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { key: "patients", label: "Patients", href: "/patients", icon: Users },
  { key: "doctors", label: "Doctors", href: "/doctors", icon: Stethoscope },
  { key: "appointments", label: "Appointments", href: "/appointments", icon: CalendarClock },
  { key: "records", label: "Medical Records", href: "/medical-records", icon: FileText },
  { key: "laboratory", label: "Laboratory", href: "/laboratory", icon: FlaskConical },
  { key: "billing", label: "Billing", href: "/billing", icon: Receipt },
  { key: "pharmacy", label: "Pharmacy", href: "/pharmacy", icon: Pill },
  { key: "ai", label: "AI Analysis", href: "/ai-analysis", icon: BrainCircuit },
  { key: "reports", label: "Reports", href: "/reports", icon: BarChart3 },
  { key: "settings", label: "Settings", href: "/settings", icon: Settings },
];

const PATIENT_GROWTH = [
  { month: "Jan", patients: 420 },
  { month: "Feb", patients: 460 },
  { month: "Mar", patients: 510 },
  { month: "Apr", patients: 545 },
  { month: "May", patients: 590 },
  { month: "Jun", patients: 640 },
  { month: "Jul", patients: 705 },
  { month: "Aug", patients: 760 },
];

const APPOINTMENTS_DATA = [
  { day: "Mon", appointments: 38 },
  { day: "Tue", appointments: 52 },
  { day: "Wed", appointments: 45 },
  { day: "Thu", appointments: 61 },
  { day: "Fri", appointments: 55 },
  { day: "Sat", appointments: 30 },
  { day: "Sun", appointments: 18 },
];

const REVENUE_DATA = [
  { month: "Jan", revenue: 82000 },
  { month: "Feb", revenue: 91000 },
  { month: "Mar", revenue: 87500 },
  { month: "Apr", revenue: 104000 },
  { month: "May", revenue: 112500 },
  { month: "Jun", revenue: 121000 },
  { month: "Jul", revenue: 134500 },
  { month: "Aug", revenue: 142800 },
];

// Colors recalibrated to the telemetry palette — values/order untouched.
const DISEASE_DISTRIBUTION = [
  { name: "Cardiology", value: 28, color: INK.cyan },
  { name: "Respiratory", value: 21, color: INK.blue },
  { name: "Neurology", value: 16, color: INK.green },
  { name: "Orthopedics", value: 14, color: INK.orange },
  { name: "Oncology", value: 12, color: INK.red },
  { name: "Other", value: 9, color: INK.slate },
];

const DEPARTMENT_PERFORMANCE = [
  { name: "ICU", value: 92, fill: INK.cyan },
  { name: "ER", value: 84, fill: INK.orange },
  { name: "Surgery", value: 78, fill: INK.green },
  { name: "Pediatrics", value: 88, fill: INK.blue },
];

// TODO: Replace mock patients with GET /patients
const RECENT_PATIENTS: Patient[] = [
  { id: "AGCT-10231", name: "Rebecca Turner", avatar: "RT", department: "Cardiology", doctor: "Dr. A. Mehta", status: "Critical" },
  { id: "AGCT-10232", name: "Daniel Osei", avatar: "DO", department: "Neurology", doctor: "Dr. S. Kapoor", status: "Stable" },
  { id: "AGCT-10233", name: "Priya Nair", avatar: "PN", department: "Orthopedics", doctor: "Dr. R. Fernandes", status: "Under Observation" },
  { id: "AGCT-10234", name: "Marcus Lee", avatar: "ML", department: "Oncology", doctor: "Dr. T. Nakamura", status: "Stable" },
  { id: "AGCT-10235", name: "Aisha Khan", avatar: "AK", department: "Respiratory", doctor: "Dr. J. Alvarez", status: "Discharged" },
  { id: "AGCT-10236", name: "Oliver Grant", avatar: "OG", department: "ICU", doctor: "Dr. A. Mehta", status: "Critical" },
  { id: "AGCT-10237", name: "Sana Iqbal", avatar: "SI", department: "Pediatrics", doctor: "Dr. L. Brooks", status: "Stable" },
  { id: "AGCT-10238", name: "Ethan Brooks", avatar: "EB", department: "Cardiology", doctor: "Dr. A. Mehta", status: "Under Observation" },
];

// TODO: Replace mock appointments with GET /appointments?upcoming=true
const UPCOMING_APPOINTMENTS: Appointment[] = [
  { id: "AP-001", time: "09:00 AM", patient: "Rebecca Turner", doctor: "Dr. A. Mehta", department: "Cardiology", status: "Confirmed" },
  { id: "AP-002", time: "09:45 AM", patient: "Daniel Osei", doctor: "Dr. S. Kapoor", department: "Neurology", status: "Pending" },
  { id: "AP-003", time: "10:30 AM", patient: "Priya Nair", doctor: "Dr. R. Fernandes", department: "Orthopedics", status: "Confirmed" },
  { id: "AP-004", time: "11:15 AM", patient: "Marcus Lee", doctor: "Dr. T. Nakamura", department: "Oncology", status: "Completed" },
  { id: "AP-005", time: "12:00 PM", patient: "Aisha Khan", doctor: "Dr. J. Alvarez", department: "Respiratory", status: "Cancelled" },
];

// TODO: Replace AI alerts with GET /ai/alerts
const AI_ALERTS: AIAlert[] = [
  {
    id: "al-1",
    title: "Urgent attention required",
    detail: "Oliver Grant (ICU) shows rising troponin levels — predicted risk of cardiac event within 6 hours.",
    severity: "critical",
    icon: ShieldAlert,
  },
  {
    id: "al-2",
    title: "Abnormal lab report",
    detail: "Rebecca Turner's latest lipid panel flagged 3 out-of-range markers by AI screening.",
    severity: "high",
    icon: FlaskConical,
  },
  {
    id: "al-3",
    title: "Predicted admission surge",
    detail: "AI model forecasts a 22% rise in ER admissions this weekend based on regional flu trends.",
    severity: "moderate",
    icon: TrendingUp,
  },
  {
    id: "al-4",
    title: "Clinical recommendation",
    detail: "Consider early discharge review for 4 stable patients in Orthopedics to free up capacity.",
    severity: "moderate",
    icon: Sparkles,
  },
];

// "gradient" now carries a single accent hex instead of a Tailwind
// gradient utility — consumed as a flat, edge-lit control surface.
const QUICK_ACTIONS: QuickAction[] = [
  { label: "Analyze Report", icon: ScanLine, gradient: INK.cyan, href: "/ai-analysis" },
  { label: "Upload Scan", icon: FilePlus2, gradient: INK.blue, href: "/medical-records/upload" },
  { label: "Create Patient", icon: UserPlus, gradient: INK.green, href: "/patients/new" },
  { label: "Book Appointment", icon: CalendarClock, gradient: INK.orange, href: "/appointments/new" },
  { label: "Generate Report", icon: ClipboardList, gradient: INK.blue, href: "/reports/new" },
];

const STATUS_STYLES: Record<PatientStatus, string> = {
  Stable: "border-l-2 border-[#52FFB8]/70 bg-[#52FFB8]/[0.06] text-[#52FFB8]",
  Critical: "border-l-2 border-[#FF4A63]/70 bg-[#FF4A63]/[0.06] text-[#FF4A63]",
  "Under Observation": "border-l-2 border-[#FF9A3D]/70 bg-[#FF9A3D]/[0.06] text-[#FF9A3D]",
  Discharged: "border-l-2 border-[#7C8798]/60 bg-[#7C8798]/[0.06] text-[#9BA5B4]",
};

const APPT_STATUS_STYLES: Record<Appointment["status"], string> = {
  Confirmed: "border-l-2 border-[#3CF4FF]/70 bg-[#3CF4FF]/[0.06] text-[#3CF4FF]",
  Pending: "border-l-2 border-[#FF9A3D]/70 bg-[#FF9A3D]/[0.06] text-[#FF9A3D]",
  Completed: "border-l-2 border-[#52FFB8]/70 bg-[#52FFB8]/[0.06] text-[#52FFB8]",
  Cancelled: "border-l-2 border-[#FF4A63]/70 bg-[#FF4A63]/[0.06] text-[#FF4A63]",
};

const SEVERITY_STYLES: Record<AIAlert["severity"], string> = {
  critical: "border-l-2 border-[#FF4A63]/70 bg-[#FF4A63]/[0.04] text-[#FF4A63]",
  high: "border-l-2 border-[#FF9A3D]/70 bg-[#FF9A3D]/[0.04] text-[#FF9A3D]",
  moderate: "border-l-2 border-[#3CF4FF]/70 bg-[#3CF4FF]/[0.04] text-[#3CF4FF]",
};

const CHART_TOOLTIP_STYLE = {
  background: "#141922",
  border: "1px solid rgba(60,244,255,0.22)",
  borderRadius: 4,
  fontSize: 12,
  fontFamily: "'JetBrains Mono', ui-monospace, monospace",
  boxShadow: "0 16px 40px -16px rgba(0,0,0,0.75)",
  color: "#E2E8F0",
};

const CHART_TICK_STYLE = { fontSize: 11, fontFamily: "'JetBrains Mono', ui-monospace, monospace", fill: "#5B6472" };
const CHART_GRID_STROKE = "rgba(60,244,255,0.06)";

/* ============================================================
   SECTION: HELPER FUNCTIONS (pure, no hooks)
============================================================ */
function getInitials(name: string): string {
  return name
    .split(" ")
    .map((p) => p[0])
    .filter(Boolean)
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

function getGreeting(hour: number): string {
  if (hour < 12) return "Good Morning";
  if (hour < 17) return "Good Afternoon";
  return "Good Evening";
}

function isNavItemActive(pathname: string, href: string): boolean {
  if (href === "/dashboard") return pathname === "/dashboard";
  return pathname === href || pathname.startsWith(`${href}/`);
}

/* ============================================================
   SECTION: LOCAL HOOK — count-up animation
   (kept as an in-file function per the single-file constraint,
   not extracted to /hooks)
============================================================ */
function useCountUp(target: number, durationMs = 1400) {
  const [value, setValue] = useState(0);
  useEffect(() => {
    let raf = 0;
    const start = performance.now();
    const tick = (now: number) => {
      const progress = Math.min(1, (now - start) / durationMs);
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(Math.floor(eased * target));
      if (progress < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, durationMs]);
  return value;
}

/* ============================================================
   SECTION: PARTICLE BACKGROUND (ambient canvas effect)
   Same particle simulation — recolored to instrument-panel dust.
============================================================ */
function ParticleField() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let raf = 0;
    let width = (canvas.width = canvas.offsetWidth);
    let height = (canvas.height = canvas.offsetHeight);

    const COUNT = Math.min(70, Math.max(24, Math.floor((width * height) / 22000)));
    type P = { x: number; y: number; vx: number; vy: number; r: number };
    const particles: P[] = Array.from({ length: COUNT }).map(() => ({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.2,
      vy: (Math.random() - 0.5) * 0.2,
      r: Math.random() * 1.4 + 0.4,
    }));

    const onResize = () => {
      width = canvas.width = canvas.offsetWidth;
      height = canvas.height = canvas.offsetHeight;
    };
    window.addEventListener("resize", onResize);

    const render = () => {
      ctx.clearRect(0, 0, width, height);
      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0) p.x = width;
        if (p.x > width) p.x = 0;
        if (p.y < 0) p.y = height;
        if (p.y > height) p.y = 0;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(60, 244, 255, 0.4)";
        ctx.fill();

        for (let j = i + 1; j < particles.length; j++) {
          const q = particles[j];
          const dx = p.x - q.x;
          const dy = p.y - q.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 100) {
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(q.x, q.y);
            ctx.strokeStyle = `rgba(77, 142, 255, ${0.07 * (1 - dist / 100)})`;
            ctx.lineWidth = 0.5;
            ctx.stroke();
          }
        }
      }
      raf = requestAnimationFrame(render);
    };
    render();

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", onResize);
    };
  }, []);

  return <canvas ref={canvasRef} className="pointer-events-none absolute inset-0 h-full w-full opacity-60" />;
}

/* ============================================================
   SECTION: RADAR PULSE — "AI is thinking" motif
   Replaces the neural-node cluster with a mission-control radar
   sweep: concentric rings, a rotating sweep line, and blips.
============================================================ */
function NeuralPulse() {
  const rings = [24, 42, 60, 78];
  const blips = useMemo(
    () => [
      { x: 100, y: 45, r: 3, delay: 0 },
      { x: 62, y: 118, r: 2.4, delay: 0.6 },
      { x: 142, y: 130, r: 2.4, delay: 1.2 },
      { x: 100, y: 100, r: 2, delay: 1.8 },
    ],
    []
  );

  return (
    <svg viewBox="0 0 200 200" className="h-28 w-28 sm:h-32 sm:w-32">
      <defs>
        <clipPath id="radarClip">
          <circle cx="100" cy="100" r="80" />
        </clipPath>
        <linearGradient id="sweepGrad" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor={INK.cyan} stopOpacity="0" />
          <stop offset="100%" stopColor={INK.cyan} stopOpacity="0.55" />
        </linearGradient>
      </defs>

      {rings.map((r, i) => (
        <circle key={i} cx="100" cy="100" r={r} fill="none" stroke={INK.cyan} strokeOpacity={0.16} strokeWidth={1} />
      ))}
      <line x1="100" y1="20" x2="100" y2="180" stroke={INK.cyan} strokeOpacity={0.08} strokeWidth={1} />
      <line x1="20" y1="100" x2="180" y2="100" stroke={INK.cyan} strokeOpacity={0.08} strokeWidth={1} />

      <g clipPath="url(#radarClip)">
        <motion.g
          style={{ transformOrigin: "100px 100px" }}
          animate={{ rotate: 360 }}
          transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
        >
          <path d="M100,100 L100,20 A80,80 0 0,1 165,60 Z" fill="url(#sweepGrad)" />
        </motion.g>
      </g>

      {blips.map((b, i) => (
        <motion.circle
          key={i}
          cx={b.x}
          cy={b.y}
          r={b.r}
          fill={INK.cyan}
          initial={{ opacity: 0.2 }}
          animate={{ opacity: [0.2, 1, 0.2] }}
          transition={{ duration: 2, repeat: Infinity, delay: b.delay }}
        />
      ))}

      <circle cx="100" cy="100" r="80" fill="none" stroke={INK.cyan} strokeOpacity={0.3} strokeWidth={1.5} />
    </svg>
  );
}

/* ============================================================
   SECTION: CORNER BRACKETS — signature HUD-panel motif
   Purely decorative marker used on every panel/card surface.
============================================================ */
function CornerBrackets({ color = INK.cyan }: { color?: string }) {
  const stroke = { borderColor: color };
  return (
    <>
      <div
        className="pointer-events-none absolute left-0 top-0 h-3 w-3 border-l border-t opacity-40"
        style={stroke}
      />
      <div
        className="pointer-events-none absolute right-0 top-0 h-3 w-3 border-r border-t opacity-40"
        style={stroke}
      />
      <div
        className="pointer-events-none absolute bottom-0 left-0 h-3 w-3 border-b border-l opacity-40"
        style={stroke}
      />
      <div
        className="pointer-events-none absolute bottom-0 right-0 h-3 w-3 border-b border-r opacity-40"
        style={stroke}
      />
    </>
  );
}

/* ============================================================
   SECTION: MODULE HEADER — console-style panel header
   Every panel reads as a manufactured hardware module: an ID,
   a title, a live status word, and optional metadata (sync time,
   warning count). Purely presentational — feeds the same panels
   that were already rendering their own ad hoc headers.
============================================================ */
function ModuleHeader({
  id,
  title,
  icon: Icon,
  status = "ONLINE",
  statusColor = INK.green,
  meta,
}: {
  id: string;
  title: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  status?: string;
  statusColor?: string;
  meta?: string;
}) {
  return (
    <div className="mb-3 flex items-center justify-between border-b border-white/[0.06] pb-2.5">
      <div className="flex items-center gap-2.5">
        <Icon size={14} className="text-slate-500" />
        <div>
          <div className="flex items-center gap-2">
            <span className={`text-[9px] tracking-[0.15em] text-slate-600 ${FONT_MONO}`}>{id}</span>
            <h3 className={`text-xs font-semibold uppercase tracking-wider text-white ${FONT_UI}`}>{title}</h3>
          </div>
        </div>
      </div>
      <div className="flex items-center gap-2">
        {meta && <span className={`hidden text-[10px] text-slate-600 sm:inline ${FONT_MONO}`}>{meta}</span>}
        <span className="flex items-center gap-1.5">
          <span className="relative flex h-1.5 w-1.5">
            <motion.span
              className="absolute inline-flex h-full w-full rounded-full"
              style={{ backgroundColor: statusColor }}
              animate={{ opacity: [0.7, 0, 0.7], scale: [1, 2, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
            />
            <span className="relative inline-flex h-1.5 w-1.5 rounded-full" style={{ backgroundColor: statusColor }} />
          </span>
          <span className={`text-[9px] tracking-[0.1em] ${FONT_MONO}`} style={{ color: statusColor }}>
            {status}
          </span>
        </span>
      </div>
    </div>
  );
}

/* ============================================================
   SECTION: SCAN SWEEP — shared hover diagnostic-scan primitive
   A thin illuminated bar travels across the element on hover
   instead of a glow/fill. Pair with `group relative overflow-hidden`
   on the parent element.
============================================================ */
function ScanSweep({ color = INK.cyan }: { color?: string }) {
  return (
    <span
      aria-hidden
      className="pointer-events-none absolute inset-y-0 -left-1/3 w-1/3 -translate-x-full opacity-0 transition-all duration-700 ease-out group-hover:translate-x-[400%] group-hover:opacity-100"
      style={{ background: `linear-gradient(90deg, transparent, ${color}22, transparent)` }}
    />
  );
}

/* ============================================================
   SECTION: GLASS CARD — reusable-in-file wrapper (not exported)
   Kept the same component/name for structural parity, rebuilt as
   a matte engineered panel: solid fill, hairline cyan-tinted edge,
   faint inner top highlight, corner brackets, no blur.
============================================================ */
function GlassCard({
  children,
  className = "",
  delay = 0,
}: {
  children: React.ReactNode;
  className?: string;
  delay?: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -3 }}
      transition={{ duration: 0.5, delay, ease: [0.22, 1, 0.36, 1] }}
      className={`relative overflow-hidden rounded-md border border-[#3CF4FF]/[0.1] bg-[#0E1117] shadow-[inset_0_1px_0_0_rgba(60,244,255,0.05)] transition-all duration-300 hover:border-[#3CF4FF]/[0.22] hover:bg-[#101520] ${className}`}
    >
      <CornerBrackets />
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-[#3CF4FF]/25 to-transparent" />
      <div className="relative z-10">{children}</div>
    </motion.div>
  );
}

/* ============================================================
   SECTION: SUMMARY CARD — telemetry readout tile
   Same 3D mouse-tracking interaction and count-up animation as
   before; visual shell rebuilt as a flat instrument tile with a
   color-coded top rail and glowing wireframe sparkline.
============================================================ */
function SummaryCard({
  label,
  value,
  prefix = "",
  suffix = "",
  icon: Icon,
  gradient,
  spark,
  delay,
  onClick,
}: {
  label: string;
  value: number;
  prefix?: string;
  suffix?: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  gradient: string;
  spark: number[];
  delay: number;
  onClick?: () => void;
}) {
  const count = useCountUp(value);
  const ref = useRef<HTMLDivElement | null>(null);
  const mx = useMotionValue(0.5);
  const my = useMotionValue(0.5);
  const rotateX = useTransform(my, [0, 1], [6, -6]);
  const rotateY = useTransform(mx, [0, 1], [-6, 6]);
  const springX = useSpring(rotateX, { stiffness: 200, damping: 18 });
  const springY = useSpring(rotateY, { stiffness: 200, damping: 18 });

  const handleMove = (e: React.MouseEvent) => {
    const rect = ref.current?.getBoundingClientRect();
    if (!rect) return;
    mx.set((e.clientX - rect.left) / rect.width);
    my.set((e.clientY - rect.top) / rect.height);
  };

  const max = Math.max(...spark);
  const points = spark
    .map((v, i) => `${(i / (spark.length - 1)) * 100},${28 - (v / max) * 24}`)
    .join(" ");

  return (
    <motion.div
      ref={ref}
      onMouseMove={handleMove}
      onMouseLeave={() => {
        mx.set(0.5);
        my.set(0.5);
      }}
      style={{ rotateX: springX, rotateY: springY, transformStyle: "preserve-3d" }}
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -3 }}
      transition={{ duration: 0.5, delay, ease: [0.22, 1, 0.36, 1] }}
      onClick={onClick}
      role={onClick ? "button" : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={
        onClick
          ? (e) => {
              if (e.key === "Enter" || e.key === " ") onClick();
            }
          : undefined
      }
      className={`group relative overflow-hidden rounded-md border border-[#3CF4FF]/[0.1] bg-[#0E1117] p-5 shadow-[inset_0_1px_0_0_rgba(60,244,255,0.05)] transition-all duration-300 hover:border-[#3CF4FF]/[0.22] hover:bg-[#101520] ${onClick ? "cursor-pointer" : ""}`}
    >
      <CornerBrackets color={gradient} />
      <div className="pointer-events-none absolute inset-x-0 top-0 h-[2px]" style={{ background: gradient }} />
      <div className="relative z-10 flex items-start justify-between">
        <div>
          <p className={`text-[10px] font-medium uppercase tracking-wider text-slate-500 ${FONT_UI}`}>{label}</p>
          <p className={`mt-2 text-2xl font-semibold tracking-tight text-white ${FONT_MONO}`}>
            {prefix}
            {count.toLocaleString()}
            {suffix}
          </p>
        </div>
        <div
          className="flex h-9 w-9 items-center justify-center rounded-sm border"
          style={{ borderColor: `${gradient}55`, background: `${gradient}14` }}
        >
          <Icon size={16} style={{ color: gradient }} />
        </div>
      </div>
      <svg viewBox="0 0 100 28" className="relative z-10 mt-4 h-7 w-full opacity-90">
        <polyline
          points={points}
          fill="none"
          strokeWidth="1.5"
          style={{ stroke: gradient, filter: `drop-shadow(0 0 3px ${gradient}99)` }}
        />
      </svg>
    </motion.div>
  );
}

/* ============================================================
   MAIN DASHBOARD PAGE
============================================================ */
export default function DashboardPage() {
  const router = useRouter();
  const pathname = usePathname();

  const accessToken = useAuthStore((s: any) => s.accessToken);
  const storeUser = useAuthStore((s: any) => s.user);
  const logout = useAuthStore((s: any) => s.logout);

  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [darkMode, setDarkMode] = useState(true);
  const [profileMenuOpen, setProfileMenuOpen] = useState(false);
  const [now, setNow] = useState<Date | null>(null);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 5;

  useEffect(() => {
    setNow(new Date());
    const t = setInterval(() => setNow(new Date()), 1000 * 30);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    if (!accessToken) {
      router.push("/login");
    }
  }, [accessToken, router]);

  const { data: meData } = useQuery({
    queryKey: ["auth", "me"],
    queryFn: async () => {
      const res = await apiClient.get("/auth/me");
      return res.data;
    },
    enabled: !!accessToken,
    retry: false,
    staleTime: 5 * 60 * 1000,
  });

  const currentUser = meData ?? storeUser ?? { name: "Doctor", role: "Clinician" };
  const displayName: string = currentUser?.name ?? currentUser?.full_name ?? "Doctor";
  const initials = getInitials(displayName) || "DR";

  const handleLogout = () => {
    if (typeof logout === "function") {
      logout();
    }
    router.push("/login");
  };

  const handleNavigate = (href: string) => {
    router.push(href);
  };

  const handleDeletePatient = (patientId: string) => {
    const confirmed = confirm("Delete this patient?");
    if (!confirmed) return;
    // TODO: Connect Delete button to DELETE /patients/{id}
    // Not removing from the UI yet — backend integration will handle
    // refetching/updating RECENT_PATIENTS once the endpoint exists.
  };

  const filteredPatients = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return RECENT_PATIENTS;
    return RECENT_PATIENTS.filter(
      (p) =>
        p.name.toLowerCase().includes(q) ||
        p.id.toLowerCase().includes(q) ||
        p.department.toLowerCase().includes(q) ||
        p.doctor.toLowerCase().includes(q)
    );
  }, [search]);

  const totalPages = Math.max(1, Math.ceil(filteredPatients.length / pageSize));
  const pagedPatients = filteredPatients.slice((page - 1) * pageSize, page * pageSize);

  const greeting = useMemo(() => getGreeting(now ? now.getHours() : 9), [now]);

  return (
    <div className={darkMode ? "dark" : ""}>
      <div className={`relative flex min-h-screen w-full bg-[#050608] text-slate-300 ${FONT_UI}`}>
        {/* SYSTEM BACKDROP — blueprint grid, faint depth glow, scan sweep.
            Replaces the aurora wallpaper; every panel sits as a solid
            surface above this instead of translucent glass. */}
        <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden bg-[#050608]">
          <div
            className="absolute inset-0 opacity-[0.05]"
            style={{
              backgroundImage:
                "linear-gradient(#3CF4FF 1px, transparent 1px), linear-gradient(90deg, #3CF4FF 1px, transparent 1px)",
              backgroundSize: "44px 44px",
            }}
          />
          <div className="absolute left-[10%] top-[-10%] h-[36rem] w-[36rem] rounded-full bg-[#4D8EFF]/[0.05] blur-[130px]" />
          <div className="absolute bottom-[-15%] right-[5%] h-[32rem] w-[32rem] rounded-full bg-[#3CF4FF]/[0.05] blur-[130px]" />

          {/* orbital rings — slow-drifting coordinate rings, upper-right */}
          <motion.svg
            viewBox="0 0 600 600"
            className="absolute -right-40 -top-40 h-[42rem] w-[42rem] opacity-[0.06]"
            animate={{ rotate: 360 }}
            transition={{ duration: 140, repeat: Infinity, ease: "linear" }}
          >
            <circle cx="300" cy="300" r="280" fill="none" stroke={INK.cyan} strokeWidth="1" strokeDasharray="2 10" />
            <circle cx="300" cy="300" r="220" fill="none" stroke={INK.cyan} strokeWidth="1" />
            <circle cx="300" cy="300" r="150" fill="none" stroke={INK.blue} strokeWidth="1" strokeDasharray="1 6" />
          </motion.svg>

          {/* ECG telemetry trace — drifts along the bottom edge */}
          <svg className="absolute bottom-6 left-0 h-16 w-[200%] opacity-[0.05]" viewBox="0 0 1400 60" preserveAspectRatio="none">
            <motion.path
              d="M0,30 L120,30 L140,10 L160,50 L180,30 L340,30 L360,8 L378,52 L396,30 L560,30 L580,12 L598,48 L616,30 L780,30 L800,10 L818,50 L836,30 L1000,30 L1020,8 L1038,52 L1056,30 L1220,30 L1240,12 L1258,48 L1276,30 L1400,30"
              fill="none"
              stroke={INK.green}
              strokeWidth="1.5"
              animate={{ x: [0, -700] }}
              transition={{ duration: 14, repeat: Infinity, ease: "linear" }}
            />
          </svg>

          <motion.div
            className="absolute inset-x-0 h-px bg-[#3CF4FF]/30"
            style={{ boxShadow: "0 0 14px 2px rgba(60,244,255,0.3)" }}
            animate={{ top: ["-2%", "102%"] }}
            transition={{ duration: 9, repeat: Infinity, ease: "linear" }}
          />
        </div>

        {/* SIDEBAR — matte console panel, hairline cyan edge */}
        <motion.aside
          animate={{ width: sidebarOpen ? 252 : 84 }}
          transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
          className="sticky top-4 z-20 m-4 flex h-[calc(100vh-2rem)] flex-col overflow-hidden rounded-md border border-[#3CF4FF]/[0.1] bg-[#0E1117] shadow-[inset_0_1px_0_0_rgba(60,244,255,0.05)]"
        >
          <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-[#3CF4FF]/25 to-transparent" />

          <div className="relative z-10 flex items-center justify-between px-4 py-5">
            <AnimatePresence initial={false}>
              {sidebarOpen && (
                <motion.div
                  key="logo"
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -8 }}
                  className="flex items-center gap-2"
                >
                  <div className={`flex h-8 w-8 items-center justify-center rounded-sm border border-[#3CF4FF]/40 bg-[#3CF4FF]/10 text-sm font-bold text-[#3CF4FF] ${FONT_MONO}`}>
                    A
                  </div>
                  <span className="text-sm font-semibold tracking-[0.15em] text-white">AGCT</span>
                </motion.div>
              )}
            </AnimatePresence>
            <button
              onClick={() => setSidebarOpen((v) => !v)}
              className="flex h-7 w-7 items-center justify-center rounded-sm border border-white/10 bg-[#141922] text-slate-400 transition-colors hover:border-[#3CF4FF]/30 hover:text-[#3CF4FF]"
            >
              {sidebarOpen ? <ChevronLeft size={14} /> : <ChevronRight size={14} />}
            </button>
          </div>

          <nav className="relative z-10 flex-1 space-y-1 overflow-y-auto px-3 py-2">
            {NAV_ITEMS.map((item, idx) => {
              const Icon = item.icon;
              const isActive = isNavItemActive(pathname ?? "/dashboard", item.href);
              const moduleNo = String(idx + 1).padStart(2, "0");
              return (
                <button
                  key={item.key}
                  onClick={() => handleNavigate(item.href)}
                  aria-current={isActive ? "page" : undefined}
                  className={`group relative flex w-full items-center gap-3 overflow-hidden rounded-sm px-3 py-2.5 text-sm transition-colors ${
                    isActive ? "bg-[#3CF4FF]/[0.06] text-[#3CF4FF]" : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {isActive && (
                    <motion.div
                      layoutId="activeNav"
                      className="absolute inset-y-1 left-0 w-[2px] bg-[#3CF4FF] shadow-[0_0_8px_1px_rgba(60,244,255,0.6)]"
                      transition={{ type: "spring", stiffness: 350, damping: 28 }}
                    />
                  )}
                  <ScanSweep color={isActive ? INK.cyan : "#7C8798"} />
                  <span
                    className={`relative z-10 h-1 w-1 shrink-0 rounded-full ${isActive ? "bg-[#3CF4FF] shadow-[0_0_5px_1px_rgba(60,244,255,0.7)]" : "bg-slate-700"}`}
                  />
                  <Icon size={18} className="relative z-10 shrink-0" />
                  <AnimatePresence initial={false}>
                    {sidebarOpen && (
                      <motion.span
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="relative z-10 flex flex-1 items-center justify-between truncate"
                      >
                        <span className="truncate">{item.label}</span>
                        <span className={`ml-2 shrink-0 text-[9px] tracking-widest text-slate-700 ${FONT_MONO}`}>{moduleNo}</span>
                      </motion.span>
                    )}
                  </AnimatePresence>
                </button>
              );
            })}
          </nav>

          <div className="relative z-10 border-t border-white/[0.06] p-3">
            <button
              onClick={handleLogout}
              className="flex w-full items-center gap-3 rounded-sm px-3 py-2.5 text-sm text-[#FF4A63] transition-colors hover:bg-[#FF4A63]/[0.08]"
            >
              <LogOut size={18} className="shrink-0" />
              {sidebarOpen && <span>Logout</span>}
            </button>
          </div>
        </motion.aside>

        {/* MAIN COLUMN */}
        <div className="relative z-10 flex min-h-screen flex-1 flex-col">
          {/* TOPBAR — flat console strip */}
          <header className="sticky top-4 z-30 mx-4 mt-4 flex items-center justify-between gap-4 rounded-md border border-[#3CF4FF]/[0.1] bg-[#0E1117] px-6 py-3 shadow-[inset_0_1px_0_0_rgba(60,244,255,0.05)]">
            <div className="flex flex-1 items-center gap-3">
              <div className="relative hidden max-w-md flex-1 sm:block">
                {/* TODO: Replace client-side RECENT_PATIENTS filtering with a
                    debounced GET /patients?search= query via React Query once
                    the search bar needs to cover more than the current page's
                    mock data. */}
                <Search size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                <input
                  value={search}
                  onChange={(e) => {
                    setSearch(e.target.value);
                    setPage(1);
                  }}
                  placeholder="Search patients, doctors, records..."
                  className="w-full rounded-sm border border-white/10 bg-[#141922] py-2 pl-9 pr-3 text-sm text-slate-100 placeholder:text-slate-500 outline-none transition-colors focus:border-[#3CF4FF]/40 focus:ring-1 focus:ring-[#3CF4FF]/20"
                />
              </div>

              {/* SYSTEM TELEMETRY STRIP — read-only instrumentation readouts.
                  TODO: wire to GET /system/status once the endpoint exists;
                  static values for now, consistent with other mock panels. */}
              <div className={`hidden items-center gap-4 border-l border-white/10 pl-4 text-[10px] text-slate-500 lg:flex ${FONT_MONO}`}>
                <span className="flex items-center gap-1.5">
                  <span className="relative flex h-1.5 w-1.5">
                    <motion.span className="absolute inline-flex h-full w-full rounded-full bg-[#52FFB8]" animate={{ opacity: [0.7, 0, 0.7], scale: [1, 2, 1] }} transition={{ duration: 2, repeat: Infinity }} />
                    <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-[#52FFB8]" />
                  </span>
                  AI <span className="text-[#52FFB8]">ONLINE</span>
                </span>
                <span>HOSPITAL <span className="text-[#3CF4FF]">NOMINAL</span></span>
                <span>DB <span className="text-[#3CF4FF]">SYNCED</span></span>
                <span>LATENCY <span className="text-[#4D8EFF]">38MS</span></span>
                <span>INFERENCE <span className="text-[#4D8EFF]">112MS</span></span>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <div className="hidden items-center gap-1.5 rounded-sm border border-[#FF4A63]/30 bg-[#FF4A63]/[0.06] px-2.5 py-1.5 sm:flex">
                <span className="relative flex h-1.5 w-1.5">
                  <motion.span className="absolute inline-flex h-full w-full rounded-full bg-[#FF4A63]" animate={{ opacity: [0.8, 0, 0.8], scale: [1, 2, 1] }} transition={{ duration: 1.4, repeat: Infinity }} />
                  <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-[#FF4A63]" />
                </span>
                <span className={`text-[10px] tracking-wider text-[#FF4A63] ${FONT_MONO}`}>2 CRITICAL</span>
              </div>

              <span className={`hidden text-xs text-[#3CF4FF]/70 md:block ${FONT_MONO}`}>
                {now
                  ? now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
                  : "--:--"}
              </span>

              <button
                onClick={() => setDarkMode((v) => !v)}
                className="group relative flex h-9 w-9 items-center justify-center overflow-hidden rounded-sm border border-white/10 bg-[#141922] text-slate-400 transition-colors hover:border-[#3CF4FF]/30 hover:text-[#3CF4FF]"
              >
                <ScanSweep />
                {darkMode ? <Sun size={16} className="relative z-10" /> : <Moon size={16} className="relative z-10" />}
              </button>

              <button
                onClick={() => handleNavigate("/notifications")}
                className="group relative flex h-9 w-9 items-center justify-center overflow-hidden rounded-sm border border-white/10 bg-[#141922] text-slate-400 transition-colors hover:border-[#3CF4FF]/30 hover:text-[#3CF4FF]"
              >
                <ScanSweep />
                <Bell size={16} className="relative z-10" />
                <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-[#FF4A63] shadow-[0_0_6px_1px_rgba(255,74,99,0.7)]" />
              </button>

              <button
                onClick={() => handleNavigate("/messages")}
                className="group relative flex h-9 w-9 items-center justify-center overflow-hidden rounded-sm border border-white/10 bg-[#141922] text-slate-400 transition-colors hover:border-[#3CF4FF]/30 hover:text-[#3CF4FF]"
              >
                <ScanSweep />
                <MessageSquare size={16} className="relative z-10" />
                <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-[#3CF4FF] shadow-[0_0_6px_1px_rgba(60,244,255,0.7)]" />
              </button>

              <div className="relative">
                <button
                  onClick={() => setProfileMenuOpen((v) => !v)}
                  className="flex items-center gap-2 rounded-sm border border-white/10 bg-[#141922] py-1.5 pl-1.5 pr-2.5 text-sm text-slate-200 transition-colors hover:border-[#3CF4FF]/30"
                >
                  <div className={`flex h-7 w-7 items-center justify-center rounded-sm border border-[#3CF4FF]/40 bg-[#3CF4FF]/10 text-xs font-bold text-[#3CF4FF] ${FONT_MONO}`}>
                    {initials}
                  </div>
                  <span className="hidden max-w-[100px] truncate sm:block">{displayName}</span>
                  <ChevronDown size={14} className="text-slate-500" />
                </button>

                <AnimatePresence>
                  {profileMenuOpen && (
                    <motion.div
                      initial={{ opacity: 0, y: -8, scale: 0.97 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, y: -8, scale: 0.97 }}
                      transition={{ duration: 0.15 }}
                      className="absolute right-0 mt-2 w-48 overflow-hidden rounded-md border border-[#3CF4FF]/[0.15] bg-[#141922] shadow-[0_20px_50px_-16px_rgba(0,0,0,0.8)]"
                    >
                      <button
                        onClick={() => {
                          setProfileMenuOpen(false);
                          handleNavigate("/settings");
                        }}
                        className="flex w-full items-center gap-2 px-4 py-2.5 text-left text-sm text-slate-300 transition-colors hover:bg-[#3CF4FF]/[0.06]"
                      >
                        <Settings size={14} /> Settings
                      </button>
                      <button
                        onClick={handleLogout}
                        className="flex w-full items-center gap-2 px-4 py-2.5 text-left text-sm text-[#FF4A63] transition-colors hover:bg-[#FF4A63]/[0.08]"
                      >
                        <LogOut size={14} /> Logout
                      </button>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>
          </header>

          {/* SCROLLABLE CONTENT */}
          <main className="flex-1 overflow-y-auto px-4 pb-6 pt-4 sm:px-6">
            {/* HERO */}
            <GlassCard className="relative mb-6 overflow-hidden p-6 sm:p-8">
              <div className="absolute inset-0 z-0">
                <ParticleField />
              </div>
              <div className={`relative z-10 mb-4 flex items-center gap-2 text-[9px] tracking-[0.15em] text-slate-600 ${FONT_MONO}`}>
                <span>MODULE-01</span>
                <span className="text-slate-800">/</span>
                <span>COMMAND OVERVIEW</span>
              </div>
              <div className="relative z-10 flex flex-col items-start justify-between gap-6 sm:flex-row sm:items-center">
                <div>
                  <motion.div
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex items-center gap-2"
                  >
                    <span className="relative flex h-1.5 w-1.5">
                      <motion.span
                        className="absolute inline-flex h-full w-full rounded-full bg-[#52FFB8]"
                        animate={{ opacity: [0.7, 0, 0.7], scale: [1, 2.2, 1] }}
                        transition={{ duration: 2, repeat: Infinity }}
                      />
                      <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-[#52FFB8]" />
                    </span>
                    <p className={`text-xs font-medium uppercase tracking-[0.2em] text-[#3CF4FF] ${FONT_MONO}`}>
                      {greeting}, {displayName.split(" ")[0]}
                    </p>
                  </motion.div>
                  <motion.h1
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.05 }}
                    className="mt-2 text-2xl font-semibold tracking-tight text-white sm:text-3xl"
                  >
                    AI Clinical Assistant Ready
                  </motion.h1>
                  <motion.p
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="mt-2 max-w-lg text-sm leading-relaxed text-slate-400"
                  >
                    Today's Summary — 4 critical alerts, 61 appointments scheduled, and predictive models are actively monitoring 760 active patients.
                  </motion.p>
                </div>
                <NeuralPulse />
              </div>
            </GlassCard>

            {/* SUMMARY CARDS */}
            {/* TODO: Replace stats with GET /dashboard/stats */}
            <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
              <SummaryCard
                label="Total Patients"
                value={7602}
                icon={Users}
                gradient={INK.cyan}
                spark={[4, 6, 5, 8, 7, 9, 11, 10, 13]}
                delay={0.05}
                onClick={() => handleNavigate("/patients")}
              />
              <SummaryCard
                label="Today's Appointments"
                value={61}
                icon={CalendarClock}
                gradient={INK.blue}
                spark={[3, 5, 4, 6, 8, 7, 6, 9, 8]}
                delay={0.1}
                onClick={() => handleNavigate("/appointments")}
              />
              <SummaryCard
                label="Doctors Available"
                value={38}
                icon={Stethoscope}
                gradient={INK.green}
                spark={[6, 7, 6, 8, 7, 9, 8, 10, 9]}
                delay={0.15}
                onClick={() => handleNavigate("/doctors")}
              />
              <SummaryCard
                label="Emergency Cases"
                value={9}
                icon={HeartPulse}
                gradient={INK.red}
                spark={[2, 4, 3, 5, 6, 4, 7, 5, 9]}
                delay={0.2}
                onClick={() => handleNavigate("/patients?filter=critical")}
              />
              <SummaryCard
                label="Revenue"
                prefix="$"
                value={142800}
                icon={DollarSign}
                gradient={INK.orange}
                spark={[82, 91, 87, 104, 112, 121, 134, 142]}
                delay={0.25}
                onClick={() => handleNavigate("/billing")}
              />
              <SummaryCard
                label="Pending Reports"
                value={17}
                icon={FileText}
                gradient={INK.blue}
                spark={[9, 12, 10, 14, 11, 15, 13, 17]}
                delay={0.3}
                onClick={() => handleNavigate("/reports")}
              />
            </div>

            <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
              {/* LEFT / MAIN COLUMN */}
              <div className="space-y-6 xl:col-span-2">
                {/* CHARTS ROW */}
                <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                  <GlassCard className="p-5" delay={0.1}>
                    <ModuleHeader id="MODULE-02" title="Patient Growth" icon={Activity} status="SYNCED" statusColor={INK.cyan} meta="8MO TREND" />
                    <ResponsiveContainer width="100%" height={180}>
                      <AreaChart data={PATIENT_GROWTH}>
                        <defs>
                          <linearGradient id="patientGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor={INK.cyan} stopOpacity={0.35} />
                            <stop offset="100%" stopColor={INK.cyan} stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID_STROKE} />
                        <XAxis dataKey="month" stroke="#5B6472" tick={CHART_TICK_STYLE} />
                        <YAxis stroke="#5B6472" tick={CHART_TICK_STYLE} />
                        <Tooltip contentStyle={CHART_TOOLTIP_STYLE} />
                        <Area type="monotone" dataKey="patients" stroke={INK.cyan} fill="url(#patientGrad)" strokeWidth={1.5} />
                      </AreaChart>
                    </ResponsiveContainer>
                  </GlassCard>

                  <GlassCard className="p-5" delay={0.15}>
                    <ModuleHeader id="MODULE-03" title="Weekly Appointments" icon={CalendarClock} status="SYNCED" statusColor={INK.blue} meta="7D WINDOW" />
                    <ResponsiveContainer width="100%" height={180}>
                      <BarChart data={APPOINTMENTS_DATA}>
                        <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID_STROKE} />
                        <XAxis dataKey="day" stroke="#5B6472" tick={CHART_TICK_STYLE} />
                        <YAxis stroke="#5B6472" tick={CHART_TICK_STYLE} />
                        <Tooltip contentStyle={CHART_TOOLTIP_STYLE} />
                        <Bar dataKey="appointments" fill={INK.blue} radius={[2, 2, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </GlassCard>

                  <GlassCard className="p-5" delay={0.2}>
                    <ModuleHeader id="MODULE-04" title="Revenue Trend" icon={DollarSign} status="SYNCED" statusColor={INK.green} meta="8MO TREND" />
                    <ResponsiveContainer width="100%" height={180}>
                      <LineChart data={REVENUE_DATA}>
                        <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID_STROKE} />
                        <XAxis dataKey="month" stroke="#5B6472" tick={CHART_TICK_STYLE} />
                        <YAxis stroke="#5B6472" tick={CHART_TICK_STYLE} />
                        <Tooltip contentStyle={CHART_TOOLTIP_STYLE} />
                        <Line type="monotone" dataKey="revenue" stroke={INK.green} strokeWidth={1.5} dot={false} />
                      </LineChart>
                    </ResponsiveContainer>
                  </GlassCard>

                  <GlassCard className="p-5" delay={0.25}>
                    <ModuleHeader id="MODULE-05" title="Disease Distribution" icon={BarChart3} status="SYNCED" statusColor={INK.orange} meta="6 CATEGORIES" />
                    <ResponsiveContainer width="100%" height={180}>
                      <PieChart>
                        <Pie
                          data={DISEASE_DISTRIBUTION}
                          dataKey="value"
                          nameKey="name"
                          innerRadius={40}
                          outerRadius={70}
                          paddingAngle={3}
                        >
                          {DISEASE_DISTRIBUTION.map((entry, i) => (
                            <Cell key={i} fill={entry.color} stroke="#0E1117" strokeWidth={1} />
                          ))}
                        </Pie>
                        <Tooltip contentStyle={CHART_TOOLTIP_STYLE} />
                      </PieChart>
                    </ResponsiveContainer>
                  </GlassCard>
                </div>

                {/* DEPARTMENT PERFORMANCE */}
                <GlassCard className="p-5" delay={0.3}>
                  <ModuleHeader id="MODULE-06" title="Department Performance" icon={Zap} status="ONLINE" statusColor={INK.green} meta="4 DEPTS" />
                  <ResponsiveContainer width="100%" height={200}>
                    <RadialBarChart
                      innerRadius="20%"
                      outerRadius="90%"
                      data={DEPARTMENT_PERFORMANCE}
                      startAngle={90}
                      endAngle={-270}
                    >
                      <RadialBar background={{ fill: "#1A202C" }} dataKey="value" cornerRadius={2} />
                      <Tooltip contentStyle={CHART_TOOLTIP_STYLE} />
                    </RadialBarChart>
                  </ResponsiveContainer>
                  <div className="mt-2 flex flex-wrap gap-3">
                    {DEPARTMENT_PERFORMANCE.map((d) => (
                      <div key={d.name} className={`flex items-center gap-1.5 text-xs text-slate-400 ${FONT_MONO}`}>
                        <span className="h-2 w-2 rounded-[1px]" style={{ backgroundColor: d.fill }} />
                        {d.name} — {d.value}%
                      </div>
                    ))}
                  </div>
                </GlassCard>

                {/* RECENT PATIENTS TABLE */}
                <GlassCard className="p-5" delay={0.35}>
                  <ModuleHeader
                    id="MODULE-07"
                    title="Patient Database"
                    icon={Users}
                    status="ONLINE"
                    statusColor={INK.green}
                    meta={`${filteredPatients.length} RECORDS · SYNC 38MS`}
                  />
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[640px] text-left text-sm">
                      <thead>
                        <tr className={`border-b border-[#3CF4FF]/[0.12] text-[10px] uppercase tracking-wider text-slate-500 ${FONT_UI}`}>
                          <th className="pb-3 pr-4 font-medium">Patient</th>
                          <th className="pb-3 pr-4 font-medium">ID</th>
                          <th className="pb-3 pr-4 font-medium">Department</th>
                          <th className="pb-3 pr-4 font-medium">Doctor</th>
                          <th className="pb-3 pr-4 font-medium">Status</th>
                          <th className="pb-3 font-medium text-right">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {pagedPatients.map((p, i) => (
                          <motion.tr
                            key={p.id}
                            initial={{ opacity: 0, y: 6 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.04 }}
                            className="group relative border-b border-white/[0.05] transition-colors last:border-0 hover:bg-[#3CF4FF]/[0.025]"
                          >
                            <td className="relative py-3 pr-4">
                              <span
                                aria-hidden
                                className="absolute -left-px top-1/2 h-0 w-[2px] -translate-y-1/2 bg-[#3CF4FF] shadow-[0_0_6px_1px_rgba(60,244,255,0.6)] transition-all duration-300 group-hover:h-full"
                              />
                              <div className="flex items-center gap-2.5">
                                <div className={`flex h-8 w-8 items-center justify-center rounded-sm border border-[#3CF4FF]/30 bg-[#3CF4FF]/[0.08] text-xs font-bold text-[#3CF4FF] ${FONT_MONO}`}>
                                  {p.avatar}
                                </div>
                                <span className="font-medium text-slate-200">{p.name}</span>
                              </div>
                            </td>
                            <td className={`py-3 pr-4 text-slate-500 ${FONT_MONO}`}>{p.id}</td>
                            <td className="py-3 pr-4 text-slate-500">{p.department}</td>
                            <td className="py-3 pr-4 text-slate-500">{p.doctor}</td>
                            <td className="py-3 pr-4">
                              <span className={`inline-block px-2.5 py-1 text-xs ${STATUS_STYLES[p.status]}`}>
                                {p.status}
                              </span>
                            </td>
                            <td className="py-3">
                              <div className="flex items-center justify-end gap-2 text-slate-500">
                                <button
                                  onClick={() => handleNavigate(`/patients/${p.id}`)}
                                  className="rounded-sm p-1.5 transition-colors hover:bg-[#3CF4FF]/[0.08] hover:text-[#3CF4FF]"
                                >
                                  <Eye size={14} />
                                </button>
                                <button
                                  onClick={() => handleNavigate(`/patients/${p.id}/edit`)}
                                  className="rounded-sm p-1.5 transition-colors hover:bg-[#FF9A3D]/[0.08] hover:text-[#FF9A3D]"
                                >
                                  <Pencil size={14} />
                                </button>
                                <button
                                  onClick={() => handleDeletePatient(p.id)}
                                  className="rounded-sm p-1.5 transition-colors hover:bg-[#FF4A63]/[0.08] hover:text-[#FF4A63]"
                                >
                                  <Trash2 size={14} />
                                </button>
                              </div>
                            </td>
                          </motion.tr>
                        ))}
                        {pagedPatients.length === 0 && (
                          <tr>
                            <td colSpan={6} className="py-10 text-center">
                              <p className={`text-xs tracking-[0.15em] text-slate-600 ${FONT_MONO}`}>NO MATCHING RECORDS</p>
                              <p className="mt-1 text-[11px] text-slate-700">Adjust query parameters and retry.</p>
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>

                  <div className={`mt-4 flex items-center justify-between text-xs text-slate-500 ${FONT_MONO}`}>
                    <span>
                      Page {page} of {totalPages}
                    </span>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => setPage(1)}
                        disabled={page === 1}
                        className="rounded-sm p-1.5 transition-colors hover:bg-[#3CF4FF]/[0.08] hover:text-[#3CF4FF] disabled:opacity-30"
                      >
                        <ChevronsLeft size={14} />
                      </button>
                      <button
                        onClick={() => setPage((p) => Math.max(1, p - 1))}
                        disabled={page === 1}
                        className="rounded-sm p-1.5 transition-colors hover:bg-[#3CF4FF]/[0.08] hover:text-[#3CF4FF] disabled:opacity-30"
                      >
                        <ChevronLeft size={14} />
                      </button>
                      <button
                        onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                        disabled={page === totalPages}
                        className="rounded-sm p-1.5 transition-colors hover:bg-[#3CF4FF]/[0.08] hover:text-[#3CF4FF] disabled:opacity-30"
                      >
                        <ChevronRight size={14} />
                      </button>
                      <button
                        onClick={() => setPage(totalPages)}
                        disabled={page === totalPages}
                        className="rounded-sm p-1.5 transition-colors hover:bg-[#3CF4FF]/[0.08] hover:text-[#3CF4FF] disabled:opacity-30"
                      >
                        <ChevronsRight size={14} />
                      </button>
                    </div>
                  </div>
                </GlassCard>
              </div>

              {/* RIGHT UTILITY PANEL */}
              <div className="space-y-6">
                {/* AI INSIGHTS PANEL */}
                <GlassCard className="p-5" delay={0.15}>
                  <ModuleHeader id="MODULE-08" title="AI Insights" icon={BrainCircuit} status="INFERRING" statusColor={INK.cyan} />
                  <div className={`mb-4 flex items-center gap-4 text-[10px] text-slate-500 ${FONT_MONO}`}>
                    <span>CONFIDENCE <span style={{ color: INK.cyan }}>94.2%</span></span>
                    <span>MODEL HEALTH <span style={{ color: INK.green }}>NOMINAL</span></span>
                    <span className="hidden sm:inline">INFERENCE <span style={{ color: INK.blue }}>112MS</span></span>
                  </div>
                  <div className="space-y-3">
                    {AI_ALERTS.map((alert, i) => {
                      const AlertIcon = alert.icon;
                      return (
                        <motion.div
                          key={alert.id}
                          initial={{ opacity: 0, x: 12 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: 0.1 + i * 0.08 }}
                          whileHover={{ x: 2 }}
                          onClick={() => handleNavigate("/ai-analysis")}
                          role="button"
                          tabIndex={0}
                          onKeyDown={(e) => {
                            if (e.key === "Enter" || e.key === " ") handleNavigate("/ai-analysis");
                          }}
                          className={`cursor-pointer p-3 ${SEVERITY_STYLES[alert.severity]}`}
                        >
                          <div className="flex items-start gap-2.5">
                            <AlertIcon size={16} className="mt-0.5 shrink-0" />
                            <div>
                              <p className="text-xs font-semibold">{alert.title}</p>
                              <p className="mt-1 text-[11px] leading-relaxed text-slate-400">{alert.detail}</p>
                            </div>
                          </div>
                        </motion.div>
                      );
                    })}
                  </div>
                </GlassCard>

                {/* UPCOMING APPOINTMENTS TIMELINE */}
                <GlassCard className="p-5" delay={0.2}>
                  <ModuleHeader id="MODULE-09" title="Appointment Queue" icon={CalendarClock} status="ONLINE" statusColor={INK.cyan} meta={`${UPCOMING_APPOINTMENTS.length} QUEUED`} />
                  <div className="relative space-y-4 pl-4">
                    <div className="absolute bottom-2 left-1.5 top-2 w-px bg-white/[0.08]" />
                    {UPCOMING_APPOINTMENTS.map((a, i) => (
                      <motion.div
                        key={a.id}
                        initial={{ opacity: 0, x: -8 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.1 + i * 0.06 }}
                        className="relative"
                      >
                        <span className="absolute -left-4 top-1 h-2.5 w-2.5 rounded-full border-2 border-[#0E1117] bg-[#3CF4FF] shadow-[0_0_6px_1px_rgba(60,244,255,0.6)]" />
                        <div className="flex items-center justify-between">
                          <p className="text-xs font-semibold text-slate-200">{a.patient}</p>
                          <span className={`text-[11px] text-slate-500 ${FONT_MONO}`}>{a.time}</span>
                        </div>
                        <p className="text-[11px] text-slate-500">
                          {a.doctor} · {a.department}
                        </p>
                        <span className={`mt-1 inline-block px-2 py-0.5 text-[10px] ${APPT_STATUS_STYLES[a.status]}`}>
                          {a.status}
                        </span>
                      </motion.div>
                    ))}
                  </div>
                </GlassCard>

                {/* AI QUICK ACTIONS */}
                <GlassCard className="p-5" delay={0.25}>
                  <ModuleHeader id="MODULE-10" title="Quick Actions" icon={Sparkles} status="READY" statusColor={INK.orange} />
                  <div className="grid grid-cols-1 gap-2.5">
                    {QUICK_ACTIONS.map((action) => {
                      const ActionIcon = action.icon;
                      return (
                        <motion.button
                          key={action.label}
                          whileTap={{ opacity: 0.85 }}
                          onClick={() => handleNavigate(action.href)}
                          className="group relative flex items-center gap-3 overflow-hidden rounded-sm border border-white/10 bg-[#141922] px-3.5 py-3 text-left text-sm text-slate-200 transition-colors"
                          onMouseEnter={(e) => (e.currentTarget.style.borderColor = `${action.gradient}55`)}
                          onMouseLeave={(e) => (e.currentTarget.style.borderColor = "")}
                        >
                          <ScanSweep color={action.gradient} />
                          <div
                            className="relative z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-sm border"
                            style={{ borderColor: `${action.gradient}55`, background: `${action.gradient}14` }}
                          >
                            <ActionIcon size={15} style={{ color: action.gradient }} />
                          </div>
                          <span className="relative z-10">{action.label}</span>
                        </motion.button>
                      );
                    })}
                  </div>
                </GlassCard>

                {/* CRITICAL WATCH */}
                <GlassCard className="p-5" delay={0.3}>
                  <ModuleHeader id="MODULE-11" title="Critical Watch" icon={AlertTriangle} status="MONITORING" statusColor={INK.red} />
                  <p className="text-xs leading-relaxed text-slate-400">
                    2 ICU patients are being continuously monitored by the AGCT prediction engine for early deterioration signals. Care teams have been notified.
                  </p>
                </GlassCard>
              </div>
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}