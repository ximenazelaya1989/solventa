import { hostname } from 'os';

// Identifica la replica que atiende cada pago (host y zona de disponibilidad).
// En ECS Fargate la zona se lee del endpoint de metadatos de la tarea; en local
// queda solo el hostname del contenedor.
let zona: string | null = null;

export async function cargarZona(): Promise<void> {
  const uri = process.env.ECS_CONTAINER_METADATA_URI_V4;
  if (!uri) return;
  try {
    const res = await fetch(`${uri}/task`, { signal: AbortSignal.timeout(2000) });
    const datos = (await res.json()) as { AvailabilityZone?: string };
    zona = datos.AvailabilityZone ?? null;
  } catch {
    zona = null;
  }
}

export function instancia(): string {
  return zona ? `${hostname()}@${zona}` : hostname();
}
