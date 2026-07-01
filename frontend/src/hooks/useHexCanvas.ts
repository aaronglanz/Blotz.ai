import { useEffect, useRef } from "react";

const G = "rgba(212,168,67,";
const B = "rgba(100,200,255,";
const T = "rgba(180,255,220,";

const NODES = [
  { xp: 0.48, yp: 0.25, col: B, r: 3.5, speed: 1100 },
  { xp: 0.5, yp: 0.42, col: G, r: 4, speed: 900 },
  { xp: 0.22, yp: 0.5, col: G, r: 3, speed: 1300 },
  { xp: 0.62, yp: 0.38, col: B, r: 2.5, speed: 1500 },
  { xp: 0.3, yp: 0.6, col: T, r: 2.5, speed: 1200 },
  { xp: 0.7, yp: 0.55, col: G, r: 2, speed: 1700 },
  { xp: 0.4, yp: 0.68, col: B, r: 2, speed: 1000 },
];
const STREAMS = [
  [0, 1], [1, 2], [1, 3], [2, 4], [3, 5], [4, 6], [1, 6],
];

interface Hex {
  x: number; y: number; size: number; base: number;
  phase: number; speed: number; timer: number; tier: number;
  glowing: boolean; glowAlpha: number;
}
interface Particle {
  x: number; y: number; vx: number; vy: number;
  r: number; a: number; life: number; col: string;
}

export function useHexCanvas(canvasRef: React.RefObject<HTMLCanvasElement | null>) {
  const rafRef = useRef<number>(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let W = 0, H = 0;
    let hexes: Hex[] = [];
    let particles: Particle[] = [];
    let scanY = 0;
    const streamPos = STREAMS.map(() => Math.random());
    const streamSpeed = STREAMS.map(() => 0.002 + Math.random() * 0.003);
    let glitchHexes: Hex[] = [];
    let glitchTimer = 0;

    function spawnParticle(ry: boolean): Particle {
      return {
        x: Math.random() * (W || 800), y: ry ? Math.random() * (H || 600) : (H || 600) + 5,
        vx: (Math.random() - 0.5) * 0.4, vy: -Math.random() * 0.6 - 0.15,
        r: Math.random() * 1.5 + 0.3, a: Math.random() * 0.7 + 0.2,
        life: ry ? Math.random() : 0, col: Math.random() < 0.7 ? G : B,
      };
    }

    function buildHexes() {
      hexes = [];
      const size = Math.min(W, H) * 0.052;
      const hw = size * 2;
      const hh = Math.sqrt(3) * size;
      const cols = Math.ceil(W / (hw * 0.75)) + 2;
      const rows = Math.ceil(H / hh) + 2;
      for (let row = -1; row < rows; row++) {
        for (let col = -1; col < cols; col++) {
          const x = col * hw * 0.75;
          const y = row * hh + (col % 2 === 0 ? 0 : hh / 2);
          const dx = x / W - 0.48;
          const dy = y / H - 0.4;
          const dist = Math.sqrt(dx * dx + dy * dy * 1.4);
          const base = Math.max(0, 0.22 - dist * 0.32);
          hexes.push({
            x, y, size, base,
            phase: Math.random() * Math.PI * 2,
            speed: 0.006 + Math.random() * 0.01,
            timer: Math.random() * 200,
            tier: dist < 0.12 ? 2 : dist < 0.25 ? 1 : 0,
            glowing: false, glowAlpha: 0,
          });
        }
      }
      particles = Array.from({ length: 80 }, () => spawnParticle(true));
    }

    function resize() {
      W = canvas!.offsetWidth;
      H = canvas!.offsetHeight;
      canvas!.width = W * devicePixelRatio;
      canvas!.height = H * devicePixelRatio;
      ctx!.scale(devicePixelRatio, devicePixelRatio);
      buildHexes();
    }

    function hexPath(x: number, y: number, r: number) {
      ctx!.beginPath();
      for (let i = 0; i < 6; i++) {
        const a = (Math.PI / 180) * (60 * i - 30);
        i === 0
          ? ctx!.moveTo(x + r * Math.cos(a), y + r * Math.sin(a))
          : ctx!.lineTo(x + r * Math.cos(a), y + r * Math.sin(a));
      }
      ctx!.closePath();
    }

    function drawHexGrid() {
      glitchTimer++;
      if (glitchTimer > 90 + Math.random() * 60) {
        glitchTimer = 0;
        const cnt = 3 + Math.floor(Math.random() * 6);
        glitchHexes = [];
        const cands = hexes.filter((h) => h.tier > 0);
        for (let i = 0; i < cnt; i++) {
          const h = cands[Math.floor(Math.random() * cands.length)];
          if (h) { h.glowing = true; h.glowAlpha = 1; glitchHexes.push(h); }
        }
      }
      glitchHexes.forEach((h) => {
        h.glowAlpha = Math.max(0, h.glowAlpha - 0.025);
        if (h.glowAlpha <= 0) h.glowing = false;
      });
      hexes.forEach((h) => {
        h.timer++;
        const pulse = Math.sin(h.phase + h.timer * h.speed) * 0.5 + 0.5;
        let alpha = h.base * (0.5 + pulse * 0.5);
        const sd = Math.abs(h.y - scanY);
        alpha += sd < h.size * 2 ? (1 - sd / (h.size * 2)) * 0.35 : 0;
        if (h.glowing) alpha = Math.max(alpha, h.glowAlpha * 0.8);
        if (alpha < 0.01) return;
        hexPath(h.x, h.y, h.size - 1.2);
        ctx!.strokeStyle = G + alpha + ")";
        ctx!.lineWidth = h.tier === 2 ? 1.0 : h.tier === 1 ? 0.7 : 0.45;
        ctx!.stroke();
        if (h.tier === 2 || h.glowing) {
          const fa = h.glowing ? h.glowAlpha * 0.18 : alpha * 0.07 * pulse;
          ctx!.fillStyle = (h.glowing ? B : G) + fa + ")";
          ctx!.fill();
        }
        if (h.tier === 2 && pulse > 0.8) {
          ctx!.beginPath();
          ctx!.arc(h.x, h.y, 1.2, 0, Math.PI * 2);
          ctx!.fillStyle = G + (alpha * 0.9) + ")";
          ctx!.fill();
        }
      });
    }

    function drawNodes() {
      NODES.forEach((n, i) => {
        const nx = n.xp * W, ny = n.yp * H;
        const p1 = (Math.sin(Date.now() / n.speed + i) + 1) / 2;
        const p2 = (Math.sin(Date.now() / (n.speed * 0.6) + i + 2) + 1) / 2;
        const g1 = ctx!.createRadialGradient(nx, ny, 0, nx, ny, 28);
        g1.addColorStop(0, n.col + "0.18)");
        g1.addColorStop(1, n.col + "0)");
        ctx!.fillStyle = g1;
        ctx!.beginPath(); ctx!.arc(nx, ny, 28, 0, Math.PI * 2); ctx!.fill();
        ctx!.beginPath(); ctx!.arc(nx, ny, 6 + p1 * 18, 0, Math.PI * 2);
        ctx!.strokeStyle = n.col + (0.5 * (1 - p1)) + ")"; ctx!.lineWidth = 1; ctx!.stroke();
        ctx!.beginPath(); ctx!.arc(nx, ny, 4 + p2 * 12, 0, Math.PI * 2);
        ctx!.strokeStyle = n.col + (0.35 * (1 - p2)) + ")"; ctx!.lineWidth = 0.7; ctx!.stroke();
        ctx!.beginPath(); ctx!.arc(nx, ny, n.r + 3, 0, Math.PI * 2);
        ctx!.strokeStyle = n.col + "0.6)"; ctx!.lineWidth = 0.8; ctx!.stroke();
        ctx!.beginPath(); ctx!.arc(nx, ny, n.r, 0, Math.PI * 2);
        ctx!.fillStyle = n.col + "1)"; ctx!.fill();
        const chLen = 12, chGap = n.r + 2;
        ctx!.strokeStyle = n.col + "0.45)"; ctx!.lineWidth = 0.7;
        [[1, 0], [-1, 0], [0, 1], [0, -1]].forEach(([dx, dy]) => {
          ctx!.beginPath();
          ctx!.moveTo(nx + dx * chGap, ny + dy * chGap);
          ctx!.lineTo(nx + dx * (chGap + chLen), ny + dy * (chGap + chLen));
          ctx!.stroke();
        });
        for (let k = 0; k < 6; k++) {
          const a = (k / 6) * Math.PI * 2;
          const ir = n.r + 3, or = n.r + 6;
          ctx!.beginPath();
          ctx!.moveTo(nx + Math.cos(a) * ir, ny + Math.sin(a) * ir);
          ctx!.lineTo(nx + Math.cos(a) * or, ny + Math.sin(a) * or);
          ctx!.strokeStyle = n.col + "0.55)"; ctx!.lineWidth = 0.8; ctx!.stroke();
        }
      });
    }

    function drawStreams() {
      STREAMS.forEach(([ai, bi], si) => {
        streamPos[si] = (streamPos[si] + streamSpeed[si]) % 1;
        const a = NODES[ai], b = NODES[bi];
        const ax = a.xp * W, ay = a.yp * H, bx = b.xp * W, by = b.yp * H;
        ctx!.beginPath(); ctx!.moveTo(ax, ay); ctx!.lineTo(bx, by);
        ctx!.strokeStyle = G + "0.07)"; ctx!.lineWidth = 0.5;
        ctx!.setLineDash([4, 8]); ctx!.stroke(); ctx!.setLineDash([]);
        const pos = streamPos[si];
        for (let k = 1; k <= 8; k++) {
          const tp = Math.max(0, pos - k * 0.012);
          const trx = ax + (bx - ax) * tp, try_ = ay + (by - ay) * tp;
          ctx!.beginPath(); ctx!.arc(trx, try_, 1.5 * (1 - k / 10), 0, Math.PI * 2);
          ctx!.fillStyle = a.col + (0.5 * (1 - k / 8)) + ")"; ctx!.fill();
        }
        const tx = ax + (bx - ax) * pos, ty = ay + (by - ay) * pos;
        const hg = ctx!.createRadialGradient(tx, ty, 0, tx, ty, 6);
        hg.addColorStop(0, a.col + "0.9)"); hg.addColorStop(1, a.col + "0)");
        ctx!.fillStyle = hg; ctx!.beginPath(); ctx!.arc(tx, ty, 6, 0, Math.PI * 2); ctx!.fill();
        ctx!.beginPath(); ctx!.arc(tx, ty, 2, 0, Math.PI * 2);
        ctx!.fillStyle = a.col + "1)"; ctx!.fill();
      });
    }

    function drawParticles() {
      particles.forEach((p, i) => {
        p.x += p.vx; p.y += p.vy; p.life += 0.004;
        if (p.life > 1) { particles[i] = spawnParticle(false); return; }
        ctx!.beginPath(); ctx!.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx!.fillStyle = p.col + (p.a * Math.sin(p.life * Math.PI) * 0.5) + ")"; ctx!.fill();
      });
    }

    function drawScan() {
      scanY += 0.6;
      if (scanY > H + 100) scanY = -100;
      const sg = ctx!.createLinearGradient(0, scanY - 40, 0, scanY + 40);
      sg.addColorStop(0, "transparent");
      sg.addColorStop(0.45, G + "0.04)");
      sg.addColorStop(0.5, G + "0.09)");
      sg.addColorStop(0.55, G + "0.04)");
      sg.addColorStop(1, "transparent");
      ctx!.fillStyle = sg; ctx!.fillRect(0, scanY - 40, W, 80);
      ctx!.beginPath(); ctx!.moveTo(0, scanY); ctx!.lineTo(W, scanY);
      ctx!.strokeStyle = G + "0.18)"; ctx!.lineWidth = 0.7; ctx!.stroke();
    }

    function drawCornerHUD() {
      const cx = W - 20, cy = 20;
      ctx!.strokeStyle = G + "0.2)"; ctx!.lineWidth = 0.7;
      ctx!.beginPath(); ctx!.moveTo(cx - 30, cy); ctx!.lineTo(cx, cy); ctx!.lineTo(cx, cy + 30); ctx!.stroke();
      const bw = 24 + Math.sin(Date.now() / 800) * 10;
      ctx!.fillStyle = G + "0.3)";
      ctx!.fillRect(cx - bw, cy + 5, bw - 2, 1.5);
      ctx!.fillRect(cx - bw * 0.6, cy + 9, bw * 0.6 - 2, 1.5);
      ctx!.fillRect(cx - bw * 0.85, cy + 13, bw * 0.85 - 2, 1.5);
      const bx = 20, by = H - 20;
      ctx!.beginPath(); ctx!.moveTo(bx + 30, by); ctx!.lineTo(bx, by); ctx!.lineTo(bx, by - 30); ctx!.stroke();
      const bw2 = 20 + Math.cos(Date.now() / 1100) * 8;
      ctx!.fillRect(bx + 2, by - 5, bw2, 1.5);
      ctx!.fillRect(bx + 2, by - 9, bw2 * 0.7, 1.5);
      ctx!.fillRect(bx + 2, by - 13, bw2 * 0.5, 1.5);
    }

    function frame() {
      ctx!.clearRect(0, 0, W, H);
      drawHexGrid();
      drawStreams();
      drawNodes();
      drawParticles();
      drawScan();
      drawCornerHUD();
      rafRef.current = requestAnimationFrame(frame);
    }

    resize();
    rafRef.current = requestAnimationFrame(frame);

    const handleResize = () => {
      cancelAnimationFrame(rafRef.current);
      resize();
      rafRef.current = requestAnimationFrame(frame);
    };
    window.addEventListener("resize", handleResize);

    return () => {
      cancelAnimationFrame(rafRef.current);
      window.removeEventListener("resize", handleResize);
    };
  }, [canvasRef]);
}
