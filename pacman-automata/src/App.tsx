import { useEffect, useRef, useState } from "react";

type DFAData = {
	estado_inicial: string;
	estados_finales: string[];
	alfabeto: string[];
	transiciones: Record<string, Record<string, string>>;
	ctx: {
		w: number;
		h: number;
		paredes: number[][];
		fantasmas: number[][];
		inicio: number[];
		meta: number[] | null;
		pastillas: number[][]; // el índice i define el bit i del mask
	};
};

function cargarImagen(url: string) {
	return new Promise<HTMLImageElement>((resolve, reject) => {
		const img = new Image();
		img.onload = () => resolve(img);
		img.onerror = reject;
		img.src = url; // viene de /public => mismo origen (sin CORS)
	});
}

function parseState(s: string) {
	if (s === "MUERTE") return { muerte: true } as const;
	const [pos, maskStr] = s.split("|");
	const [xStr, yStr] = pos.split(",");
	return { muerte: false, x: +xStr, y: +yStr, mask: Number(maskStr) } as const;
}

function tienePastilla(mask: number, i: number) {
	return ((mask >> i) & 1) === 1;
}

export default function App() {
	const [data, setData] = useState<DFAData | null>(null);
	const [state, setState] = useState<string | null>(null);
	const [fantasmaImg, setfantasmaImg] = useState<HTMLImageElement | null>(null);
	const [pacmanImg, setPacmanImg] = useState<HTMLImageElement | null>(null);
	const canvasRef = useRef<HTMLCanvasElement>(null);
	const CELL = 55; // px por celda

	// cargar JSON
	useEffect(() => {
		fetch("dist/dfa.json")
			.then((r) => r.json())
			.then((d: DFAData) => {
				setData(d);
				setState(d.estado_inicial);
			});
	}, []);


	useEffect(() => {
		cargarImagen("dist/fantasmas/fantasma2.svg").then(setfantasmaImg).catch(console.error);
	}, []);

	useEffect(() => {
		cargarImagen("dist/pacman.svg").then(setPacmanImg).catch(console.error);
	}, []);


	// teclado
	useEffect(
		() => {
			if (!data || !state) return;
			const onKey = (e: KeyboardEvent) => {
				const key = e.key.toUpperCase();
				// Reset suave desde MUERTE
				if (key === "R" && state === "MUERTE") {
					setState(data.estado_inicial);
					return;
				}
				if (key === "R" && state === data.estados_finales[0]) {
					setState(data.estado_inicial);
					return;
				}
				if (!["W", "A", "S", "D", "R"].includes(key)) return;
				const next = data.transiciones[state]?.[key];
				if (next) setState(next);
			};
			window.addEventListener("keydown", onKey);
			return () => window.removeEventListener("keydown", onKey);
		},
		[data, state] as unknown as any
	);

	// draw
	useEffect(() => {
		if (!data || !state) return;
		const { ctx } = data;
		const cvs = canvasRef.current!;
		cvs.width = ctx.w * CELL;
		cvs.height = ctx.h * CELL;
		const g = cvs.getContext("2d")!;
		g.clearRect(0, 0, cvs.width, cvs.height);

		// fondo
		g.fillStyle = "#111";
		g.fillRect(0, 0, cvs.width, cvs.height);

		// grilla (suave)
		g.strokeStyle = "#222";
		g.lineWidth = 1;
		for (let x = 0; x <= ctx.w; x++) {
			g.beginPath();
			g.moveTo(x * CELL, 0);
			g.lineTo(x * CELL, cvs.height);
			g.stroke();
		}
		for (let y = 0; y <= ctx.h; y++) {
			g.beginPath();
			g.moveTo(0, y * CELL);
			g.lineTo(cvs.width, y * CELL);
			g.stroke();
		}

		// paredes - más gruesas visualmente
		g.fillStyle = "#5036d9";
		ctx.paredes.forEach(([x, y]) => {
			// Paredes con borde más grueso
			g.fillRect(x * CELL - 2, y * CELL - 2, CELL + 4, CELL + 4);
			// Interior más oscuro para dar efecto de profundidad
			g.fillStyle = "#3a2580";
			g.fillRect(x * CELL + 2, y * CELL + 2, CELL - 4, CELL - 4);
			g.fillStyle = "#5036d9"; // Restaurar color para las siguientes paredes
		});

		// meta
		if (ctx.meta) {
			const [gx, gy] = ctx.meta;
			g.fillStyle = "#2ecc71";
			g.fillRect(gx * CELL, gy * CELL, CELL, CELL);
		}
		const pad = 6;
		if (fantasmaImg) {
			data.ctx.fantasmas.forEach(([x, y]) => {
				g.drawImage(fantasmaImg, x * CELL + pad, y * CELL + pad, CELL - 2 * pad, CELL - 2 * pad);
			});
		} else {
			// fallback si no cargó el SVG
			g.fillStyle = "#bbff00ff";
			data.ctx.fantasmas.forEach(([x, y]) => g.fillRect(x * CELL + pad, y * CELL + pad, CELL - 2 * pad, CELL - 2 * pad));
		}

		// estado
		const st = parseState(state);

		// pastillas restantes (según mask)
		if (!st.muerte) {
			g.fillStyle = "#f1c40f";
			ctx.pastillas.forEach(([px, py], i) => {
				if (tienePastilla(st.mask, i)) {
					g.beginPath();
					g.arc(
						px * CELL + CELL / 2,
						py * CELL + CELL / 2,
						CELL * 0.12,
						0,
						Math.PI * 2
					);
					g.fill();
				}
			});
		}

		// inicio (S)
		const [sx, sy] = ctx.inicio;
		g.fillStyle = "#ffac2fff";
		g.fillRect(sx * CELL, sy * CELL, CELL, CELL);
		g.fillStyle = "white";
		g.font = "bold 14px sans-serif";
		g.fillText("", sx * CELL + 6, sy * CELL + 16);

		// Pac-Man / estado MUERTE
		if (st.muerte) {
			g.fillStyle = "rgba(231, 76, 60, 0.85)";
			g.fillRect(0, 0, cvs.width, cvs.height);
			g.fillStyle = "#fff";
			g.font = "bold 22px sans-serif";
			g.fillText("MUERTE — presioná R para reiniciar", 10, 28);
		} else {
			if (pacmanImg) {
				g.drawImage(pacmanImg, st.x * CELL + pad, st.y * CELL + pad, CELL - 2 * pad, CELL - 2 * pad);
			} else {
			}
		}

		// HUD
		const ganador = data.estados_finales.includes(state);
		if (ganador) {
			g.fillStyle = "rgba(116, 255, 95, 0.85)";
			g.fillRect(0, 0, cvs.width, cvs.height);
			g.fillStyle = "#fff";
			g.font = "bold 22px sans-serif";
			g.fillText("GANASTE! — presioná R para reiniciar", 10, 28);
			return;
		}
		g.fillStyle = "#fff";
		g.font = "14px monospace";
		g.fillText(`Estado: ${state}`, 10, cvs.height - 28);
		g.fillText(
			ganador ? "¡GANASTE!" : "W/A/S/D para mover",
			10,
			cvs.height - 10
		);
	}, [data, state]);

	if (!data || !state)
		return <div style={{ padding: 16, color: "#eee" }}>Cargando…</div>;
	return (
		<div className="Pacman"
			style={{

			}}
		>
			<h1 style={{ margin: "8px 0" }}>Pac-Man por Autómata (DFA)</h1>
			<canvas ref={canvasRef} className='PacmanCanvas' />
			<p style={{ opacity: 0.8, marginTop: 0 }}>
				Teclas: <b>W</b>/<b>A</b>/<b>S</b>/<b>D</b> —{" "}
				{state === "MUERTE" ? (
					<b>R = reiniciar</b>
				) : (
					"llegá a E comiendo todas las pastillas"
				)}
			</p>
		</div>
	);
}
