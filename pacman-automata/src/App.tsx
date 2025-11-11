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
		pastillas: number[][];
	};
};


function parseState(s: string) {
	if (s === "MUERTE") return { muerte: true } as const;
	// const [pos] = s.split("|");
	const [xStr, yStr] = s.split(",");
	return { muerte: false, x: +xStr, y: +yStr } as const;
}


export default function App() {
	const [state, setState] = useState<string | null>(null);
	const [fantasmaImg, setFantasmaImg] = useState<HTMLImageElement | null>(null);
	const [pacmanImg, setPacmanImg] = useState<HTMLImageElement | null>(null);
	const [data, setData] = useState<DFAData | null>(null);
	const [json, setJson] = useState<DFAData | null>(null);
	const [pastillas, setPastillas] = useState<number[][]>([]);
	const [numeroMapa, setNumeroMapa] = useState<number>(0);
	const canvasRef = useRef<HTMLCanvasElement>(null);
	const CELDA = 55; // px por celda


	useEffect(() => {
		const load = async () => {
			try {
				// cargar fantasma
				const fantasma = new Image();
				fantasma.src = `${import.meta.env.BASE_URL}fantasmas/fantasma2.svg`;
				fantasma.onload = () => setFantasmaImg(fantasma);

				// cargar pacman
				const pacman = new Image();
				pacman.src = `${import.meta.env.BASE_URL}pacman.svg`;
				pacman.onload = () => setPacmanImg(pacman);

				const res = await fetch(`${import.meta.env.BASE_URL}dfa.json`);
				if (!res.ok) {
					throw new Error('No se pudo cargar dfa.json');
				}
				const json = await res.json();
				setJson(json);

				// CARGAR LOS DATOS DEL MAPA
				if (json) {
					const data = (json as any)[`mapa_${numeroMapa}`];
					setNumeroMapa(numeroMapa + 1);
					setData(data);
					setState(data.estado_inicial);
					setPastillas(data.ctx.pastillas);
				};
			} catch (err) {
				console.error(err);
			}
		};

		load();
	}, []);



	// teclado
	useEffect(
		() => {
			if (!data || !state) return;
			const onKey = (e: KeyboardEvent) => {
				const key = e.key.toUpperCase();
				if (key === "R" && state === "MUERTE") {
					setState(data.estado_inicial);
					setPastillas(data.ctx.pastillas);
					return;
				}
				if (!["W", "A", "S", "D", "R"].includes(key)) return;
				const next = data.transiciones[state]?.[key];
				if (next) setState(next);

				if (numeroMapa === 4) {
					setNumeroMapa(0);
					return;
				}
				if (pastillas.some(a => a.toString() == next)) {
					setPastillas(pastillas.filter(a => a.toString() != next));
				}

				if (key === "R" && data.estados_finales.includes(state) && pastillas.length === 0) {
					if (numeroMapa < 4) {
						const data = (json as any)[`mapa_${numeroMapa}`];
						setNumeroMapa(numeroMapa + 1);
						setData(data);
						setState(data.estado_inicial);
						setPastillas(data.ctx.pastillas);
					}
					return;
				}
			};
			window.addEventListener("keydown", onKey);
			return () => window.removeEventListener("keydown", onKey);
		},
		[data, state] as unknown as any
	);

	useEffect(() => {
		if (!data || !state) return;
		const { ctx } = data;
		const cvs = canvasRef.current!;
		cvs.width = ctx.w * CELDA;
		cvs.height = ctx.h * CELDA;
		const g = cvs.getContext("2d")!;
		g.clearRect(0, 0, cvs.width, cvs.height);

		g.fillStyle = "#111";
		g.fillRect(0, 0, cvs.width, cvs.height);

		g.strokeStyle = "#222";
		g.lineWidth = 1;
		for (let x = 0; x <= ctx.w; x++) {
			g.beginPath();
			g.moveTo(x * CELDA, 0);
			g.lineTo(x * CELDA, cvs.height);
			g.stroke();
		}
		for (let y = 0; y <= ctx.h; y++) {
			g.beginPath();
			g.moveTo(0, y * CELDA);
			g.lineTo(cvs.width, y * CELDA);
			g.stroke();
		}

		g.fillStyle = "#5036d9";
		ctx.paredes.forEach(([x, y]) => {
			g.fillRect(x * CELDA - 2, y * CELDA - 2, CELDA + 4, CELDA + 4);
			g.fillStyle = "#3a2580";
			g.fillRect(x * CELDA + 2, y * CELDA + 2, CELDA - 4, CELDA - 4);
			g.fillStyle = "#5036d9";
		});

		if (ctx.meta) {
			const [gx, gy] = ctx.meta;
			g.fillStyle = "#2ecc71";
			g.fillRect(gx * CELDA, gy * CELDA, CELDA, CELDA);
		}
		const pad = 6;
		if (fantasmaImg) {
			data.ctx.fantasmas.forEach(([x, y]) => {
				g.drawImage(fantasmaImg, x * CELDA + pad, y * CELDA + pad, CELDA - 2 * pad, CELDA - 2 * pad);
			});
		} else {
			g.fillStyle = "#bbff00ff";
			data.ctx.fantasmas.forEach(([x, y]) => g.fillRect(x * CELDA + pad, y * CELDA + pad, CELDA - 2 * pad, CELDA - 2 * pad));
		}

		// estado
		const st = parseState(state);
		const ganador = data.estados_finales.includes(state) && pastillas.length === 0;

		if (!st.muerte) {
			g.fillStyle = "#f1c40f";
			pastillas.forEach(([px, py]) => {
				g.beginPath();
				g.arc(
					px * CELDA + CELDA / 2,
					py * CELDA + CELDA / 2,
					CELDA * 0.12,
					0,
					Math.PI * 2
				);
				g.fill();
			})
		}

		const [sx, sy] = ctx.inicio;
		g.fillStyle = "#ffac2fff";
		g.fillRect(sx * CELDA, sy * CELDA, CELDA, CELDA);
		g.fillStyle = "white";
		g.font = "bold 14px sans-serif";
		g.fillText("", sx * CELDA + 6, sy * CELDA + 16);

		if (st.muerte) {
			g.fillStyle = "rgba(231, 76, 60, 0.85)";
			g.fillRect(0, 0, cvs.width, cvs.height);
			g.fillStyle = "#fff";
			g.font = "bold 22px sans-serif";
			g.fillText("MUERTE — presioná R para reiniciar", 10, 28);
		} else {
			if (pacmanImg) {
				g.drawImage(pacmanImg, st.x * CELDA + pad, st.y * CELDA + pad, CELDA - 2 * pad, CELDA - 2 * pad);
			} else {
			}
		}

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
					"llegá a M comiendo todas las pastillas"
				)}
			</p>
		</div>
	);
}
