// Registro de eventos del experimento EXP-006 en una linea JSON por evento.
// En ECS van a CloudWatch Logs; los scripts de analisis los descargan para
// calcular deteccion (primer error tras la falla) y recuperacion (primer pago
// completado por reintento). El reloj de la tarea esta sincronizado por
// Amazon Time Sync, igual que la instancia que inyecta las fallas.
export function registrarEvento(
  evento: string,
  datos: Record<string, unknown>,
): void {
  console.log(JSON.stringify({ ts: new Date().toISOString(), evento, ...datos }));
}
