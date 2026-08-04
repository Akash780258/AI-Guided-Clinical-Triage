"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  motion,
  AnimatePresence,
  useMotionValue,
  useSpring,
  useTransform,
} from "framer-motion";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation } from "@tanstack/react-query";
import { AxiosError } from "axios";

import { login } from "@/services/auth.service";
import { useAuthStore } from "@/store/auth.store";

/* ============================================================
   VALIDATION SCHEMA
============================================================ */
const loginSchema = z.object({
  email: z.string().min(1, "Email is required").email("Enter a valid email address"),
  password: z.string().min(6, "Password must be at least 6 characters"),
  rememberMe: z.boolean().optional(),
});
type LoginFormValues = z.infer<typeof loginSchema>;

type ViewState = "landing" | "login";

const REMEMBER_KEY = "agct_remembered_email";

/* ============================================================
   INTERACTIVE PARTICLE / 3D BACKGROUND
============================================================ */
function ParticleBackground({
  mouseX,
  mouseY,
}: {
  mouseX: React.MutableRefObject<number>;
  mouseY: React.MutableRefObject<number>;
}) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationFrame = 0;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const PARTICLE_COUNT = Math.min(140, Math.max(40, Math.floor((width * height) / 13000)));

    type Particle = {
      x: number;
      y: number;
      z: number;
      vx: number;
      vy: number;
      radius: number;
    };

    const particles: Particle[] = Array.from({ length: PARTICLE_COUNT }).map(() => ({
      x: Math.random() * width,
      y: Math.random() * height,
      z: Math.random() * 0.8 + 0.3,
      vx: (Math.random() - 0.5) * 0.25,
      vy: (Math.random() - 0.5) * 0.25,
      radius: Math.random() * 1.6 + 0.5,
    }));

    const resize = () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };
    window.addEventListener("resize", resize);

    const render = () => {
      ctx.clearRect(0, 0, width, height);
      const mx = mouseX.current || width / 2;
      const my = mouseY.current || height / 2;

      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        p.x += p.vx;
        p.y += p.vy;

        if (p.x < 0) p.x = width;
        if (p.x > width) p.x = 0;
        if (p.y < 0) p.y = height;
        if (p.y > height) p.y = 0;

        const parallaxX = (mx - width / 2) * 0.02 * p.z;
        const parallaxY = (my - height / 2) * 0.02 * p.z;

        const drawX = p.x + parallaxX;
        const drawY = p.y + parallaxY;

        ctx.beginPath();
        ctx.arc(drawX, drawY, p.radius * (0.6 + p.z), 0, Math.PI * 2);
        ctx.fillStyle = `rgba(140, 200, 255, ${0.2 + p.z * 0.4})`;
        ctx.fill();

        for (let j = i + 1; j < particles.length; j++) {
          const q = particles[j];
          const dx = p.x - q.x;
          const dy = p.y - q.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 110) {
            ctx.beginPath();
            ctx.moveTo(drawX, drawY);
            ctx.lineTo(q.x + parallaxX, q.y + parallaxY);
            ctx.strokeStyle = `rgba(140, 200, 255, ${0.09 * (1 - dist / 110)})`;
            ctx.lineWidth = 0.6;
            ctx.stroke();
          }
        }
      }

      animationFrame = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrame);
      window.removeEventListener("resize", resize);
    };
  }, [mouseX, mouseY]);

  return (
    <canvas
      ref={canvasRef}
      className="pointer-events-none absolute inset-0 h-full w-full opacity-70"
    />
  );
}

/* ============================================================
   ICONS (inline, no external icon package)
============================================================ */
function EyeIcon({ open }: { open: boolean }) {
  return open ? (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7Z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  ) : (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M17.94 17.94A10.94 10.94 0 0 1 12 20c-7 0-11-8-11-8a19.66 19.66 0 0 1 5.06-6.06M9.9 4.24A10.94 10.94 0 0 1 12 4c7 0 11 8 11 8a19.7 19.7 0 0 1-2.17 3.19M14.12 14.12a3 3 0 1 1-4.24-4.24" />
      <line x1="1" y1="1" x2="23" y2="23" />
    </svg>
  );
}

function SpinnerIcon() {
  return (
    <svg className="animate-spin" width="18" height="18" viewBox="0 0 24 24" fill="none">
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" opacity="0.25" />
      <path d="M22 12a10 10 0 0 1-10 10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
    </svg>
  );
}

/* ============================================================
   MAIN PAGE COMPONENT
============================================================ */
export default function LoginPage() {
  const router = useRouter();
  const setTokens = useAuthStore((s) => s.setTokens);

  const [view, setView] = useState<ViewState>("landing");
  const [showPassword, setShowPassword] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const mouseX = useRef(0);
  const mouseY = useRef(0);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      mouseX.current = e.clientX;
      mouseY.current = e.clientY;
      tiltX.set(e.clientX);
      tiltY.set(e.clientY);
    };
    window.addEventListener("mousemove", handler);
    return () => window.removeEventListener("mousemove", handler);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ---- 3D tilt on the glass card ----
  const tiltX = useMotionValue(0);
  const tiltY = useMotionValue(0);
  const rotateX = useSpring(
    useTransform(tiltY, [0, typeof window !== "undefined" ? window.innerHeight : 800], [8, -8]),
    { stiffness: 120, damping: 20 }
  );
  const rotateY = useSpring(
    useTransform(tiltX, [0, typeof window !== "undefined" ? window.innerWidth : 1200], [-8, 8]),
    { stiffness: 120, damping: 20 }
  );

  const rememberedEmail = useMemo(() => {
    if (typeof window === "undefined") return "";
    return localStorage.getItem(REMEMBER_KEY) ?? "";
  }, []);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: rememberedEmail,
      password: "",
      rememberMe: !!rememberedEmail,
    },
  });

  const mutation = useMutation({
    mutationFn: (values: { email: string; password: string }) => login(values),
    onSuccess: (response: any) => {
      setTokens(response.access_token, response.refresh_token);
      router.push("/dashboard");
    },
    onError: (err: unknown) => {
      const axiosErr = err as AxiosError<{ detail?: string; message?: string }>;
      const message =
        axiosErr?.response?.data?.detail ??
        axiosErr?.response?.data?.message ??
        "Invalid credentials. Please try again.";
      setServerError(message);
    },
  });

  const onSubmit = (values: LoginFormValues) => {
    setServerError(null);
    if (values.rememberMe) {
      localStorage.setItem(REMEMBER_KEY, values.email);
    } else {
      localStorage.removeItem(REMEMBER_KEY);
    }
    mutation.mutate({ email: values.email, password: values.password });
  };

  return (
    <main className="relative flex min-h-screen w-full items-center justify-center overflow-hidden bg-[#040914] px-4">
      {/* Animated gradient blobs */}
      <div className="pointer-events-none absolute inset-0">
        <motion.div
          className="absolute -left-40 -top-40 h-[32rem] w-[32rem] rounded-full bg-cyan-500/20 blur-3xl"
          animate={{ x: [0, 40, 0], y: [0, 30, 0] }}
          transition={{ duration: 14, repeat: Infinity, ease: "easeInOut" }}
        />
        <motion.div
          className="absolute -bottom-40 -right-40 h-[32rem] w-[32rem] rounded-full bg-indigo-500/20 blur-3xl"
          animate={{ x: [0, -30, 0], y: [0, -40, 0] }}
          transition={{ duration: 16, repeat: Infinity, ease: "easeInOut" }}
        />
      </div>

      <ParticleBackground mouseX={mouseX} mouseY={mouseY} />

      <div className="relative z-10 flex w-full max-w-md flex-col items-center">
        <AnimatePresence mode="wait">
          {view === "landing" && (
            <motion.div
              key="landing"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.92, filter: "blur(6px)" }}
              transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
              className="flex w-full flex-col items-center text-center"
            >
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1, duration: 0.6 }}
                className="mb-2 text-5xl font-bold tracking-tight text-white"
              >
                AGCT
              </motion.div>
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.25, duration: 0.6 }}
                className="mb-1 text-lg font-medium text-cyan-300"
              >
                AI-Guided Clinical Triage
              </motion.p>
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.35, duration: 0.6 }}
                className="mb-10 text-sm text-slate-400"
              >
                Enterprise AI Clinical Platform
              </motion.p>

              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.45, duration: 0.6 }}
                className="flex flex-col gap-3 sm:flex-row"
              >
                <motion.button
                  whileHover={{ scale: 1.04 }}
                  whileTap={{ scale: 0.97 }}
                  onClick={() => setView("login")}
                  className="rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-500 px-8 py-3 font-semibold text-white shadow-lg shadow-cyan-500/20"
                >
                  Login
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.04 }}
                  whileTap={{ scale: 0.97 }}
                  className="rounded-xl border border-white/15 bg-white/5 px-8 py-3 font-semibold text-slate-200 backdrop-blur-md"
                >
                  Learn More
                </motion.button>
              </motion.div>
            </motion.div>
          )}

          {view === "login" && (
            <motion.div
              key="login"
              initial={{ opacity: 0, scale: 0.9, y: 30 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.92, y: 20 }}
              transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
              style={{ perspective: 1000 }}
              className="w-full"
            >
              <motion.div
                style={{ rotateX, rotateY, transformStyle: "preserve-3d" }}
                className="w-full rounded-3xl border border-white/10 bg-white/[0.06] p-8 shadow-2xl backdrop-blur-2xl"
              >
                <button
                  type="button"
                  onClick={() => setView("landing")}
                  className="mb-4 flex items-center gap-1 text-xs font-medium text-slate-400 hover:text-slate-200"
                >
                  ← Back
                </button>

                <h1 className="mb-1 text-2xl font-bold text-white">Welcome back</h1>
                <p className="mb-6 text-sm text-slate-400">Sign in to AGCT to continue</p>

                <form onSubmit={handleSubmit(onSubmit)} noValidate className="flex flex-col gap-4">
                  <div>
                    <label className="mb-1 block text-xs font-medium text-slate-300">Email</label>
                    <input
                      type="email"
                      autoComplete="email"
                      {...register("email")}
                      placeholder="you@hospital.com"
                      className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white placeholder:text-slate-500 outline-none transition focus:border-cyan-400/60 focus:ring-2 focus:ring-cyan-400/20"
                    />
                    {errors.email && (
                      <p className="mt-1 text-xs text-red-400">{errors.email.message}</p>
                    )}
                  </div>

                  <div>
                    <label className="mb-1 block text-xs font-medium text-slate-300">Password</label>
                    <div className="relative">
                      <input
                        type={showPassword ? "text" : "password"}
                        autoComplete="current-password"
                        {...register("password")}
                        placeholder="••••••••"
                        className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 pr-11 text-sm text-white placeholder:text-slate-500 outline-none transition focus:border-cyan-400/60 focus:ring-2 focus:ring-cyan-400/20"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword((v) => !v)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200"
                        aria-label="Toggle password visibility"
                      >
                        <EyeIcon open={showPassword} />
                      </button>
                    </div>
                    {errors.password && (
                      <p className="mt-1 text-xs text-red-400">{errors.password.message}</p>
                    )}
                  </div>

                  <div className="flex items-center justify-between">
                    <label className="flex items-center gap-2 text-xs text-slate-300">
                      <input
                        type="checkbox"
                        {...register("rememberMe")}
                        className="h-4 w-4 rounded border-white/20 bg-white/5 accent-cyan-500"
                      />
                      Remember me
                    </label>
                    <button
                      type="button"
                      className="text-xs font-medium text-cyan-300 hover:text-cyan-200"
                    >
                      Forgot password?
                    </button>
                  </div>

                  <AnimatePresence>
                    {serverError && (
                      <motion.p
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        className="rounded-lg border border-red-400/30 bg-red-500/10 px-3 py-2 text-xs text-red-300"
                      >
                        {serverError}
                      </motion.p>
                    )}
                  </AnimatePresence>

                  <motion.button
                    type="submit"
                    disabled={mutation.isPending}
                    whileHover={{ scale: mutation.isPending ? 1 : 1.02 }}
                    whileTap={{ scale: mutation.isPending ? 1 : 0.98 }}
                    className="mt-2 flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-500 px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-cyan-500/20 disabled:opacity-60"
                  >
                    {mutation.isPending && <SpinnerIcon />}
                    {mutation.isPending ? "Signing In..." : "Sign In"}
                  </motion.button>
                </form>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </main>
  );
}