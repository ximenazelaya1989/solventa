import { Injectable } from '@nestjs/common';
import { registrarEvento } from '../common/eventos';

export interface OrdenPago {
  claveIdempotencia: string;
  siniestroId: string;
  polizaId: string;
  monto: number;
  moneda: string;
}

export interface ConfirmacionPago {
  pagoId: string;
  estado: string;
  idempotente: boolean;
  atendidoPor?: string;
}

export interface ResultadoLlamada {
  ok: boolean;
  confirmacion?: ConfirmacionPago;
  intentos: number;
  duracionMs: number;
  ultimoError?: string;
}

const num = (v: string | undefined, d: number) => Number(v ?? d);

// Errores que vale la pena reintentar: red, timeout, 5xx y 429.
// Un 4xx (datos invalidos, 409) no se arregla reintentando.
function esReintentable(status: number | null): boolean {
  return status === null || status >= 500 || status === 429;
}

const dormir = (ms: number) => new Promise((r) => setTimeout(r, ms));

// EXP-006 (H7.2.1): cliente de Siniestros hacia Pagos (via ALB interno).
// Tactica: reintentos con backoff exponencial y jitter completo, siempre con
// la MISMA llave de idempotencia, dentro de un presupuesto de tiempo.
// Con RETRY_IDEMPOTENCY_ENABLED=false (prueba de control) se hace un solo
// intento: si falla, la orden queda fallida.
@Injectable()
export class PagosClient {
  private readonly url = process.env.PAGOS_URL ?? 'http://localhost:3000';
  private readonly reintentar = process.env.RETRY_IDEMPOTENCY_ENABLED === 'true';
  private readonly timeoutIntentoMs = num(process.env.PAGOS_TIMEOUT_MS, 3000);
  private readonly maxIntentos = num(process.env.RETRY_MAX_ATTEMPTS, 10);
  private readonly baseMs = num(process.env.RETRY_BASE_MS, 200);
  private readonly techoMs = num(process.env.RETRY_MAX_DELAY_MS, 8000);
  private readonly presupuestoMs = num(process.env.RETRY_BUDGET_MS, 30000);

  get reintentosActivos(): boolean {
    return this.reintentar;
  }

  async pagar(orden: OrdenPago): Promise<ResultadoLlamada> {
    const inicio = Date.now();
    const limite = this.reintentar ? this.maxIntentos : 1;
    let ultimoError = '';
    let hechos = 0;

    for (let intento = 1; intento <= limite; intento++) {
      hechos = intento;
      const { status, cuerpo, error } = await this.intentar(orden);

      if (status !== null && status >= 200 && status < 300) {
        const confirmacion = cuerpo as ConfirmacionPago;
        registrarEvento('pago_confirmado', {
          clave: orden.claveIdempotencia,
          siniestroId: orden.siniestroId,
          pagoId: confirmacion.pagoId,
          intentos: intento,
          idempotente: confirmacion.idempotente,
          replica: confirmacion.atendidoPor,
          duracionMs: Date.now() - inicio,
        });
        return {
          ok: true,
          confirmacion,
          intentos: intento,
          duracionMs: Date.now() - inicio,
        };
      }

      ultimoError = error ?? `HTTP ${status}`;
      registrarEvento('intento_fallido', {
        clave: orden.claveIdempotencia,
        siniestroId: orden.siniestroId,
        intento,
        status,
        error: ultimoError,
      });

      if (!esReintentable(status) || intento === limite) break;

      // Backoff exponencial con jitter completo: espera aleatoria en
      // [0, min(techo, base * 2^(intento-1))], para que los reintentos de
      // muchas ordenes no lleguen todos juntos cuando Pagos se recupera.
      const tope = Math.min(this.techoMs, this.baseMs * 2 ** (intento - 1));
      const espera = Math.random() * tope;
      if (Date.now() - inicio + espera + this.timeoutIntentoMs > this.presupuestoMs) {
        ultimoError = `presupuesto de ${this.presupuestoMs} ms agotado: ${ultimoError}`;
        break;
      }
      await dormir(espera);
    }

    registrarEvento('pago_fallido_definitivo', {
      clave: orden.claveIdempotencia,
      siniestroId: orden.siniestroId,
      intentos: hechos,
      error: ultimoError,
      duracionMs: Date.now() - inicio,
    });
    return {
      ok: false,
      intentos: hechos,
      duracionMs: Date.now() - inicio,
      ultimoError,
    };
  }

  private async intentar(
    orden: OrdenPago,
  ): Promise<{ status: number | null; cuerpo?: unknown; error?: string }> {
    try {
      const res = await fetch(`${this.url}/pagos`, {
        method: 'POST',
        headers: {
          'content-type': 'application/json',
          'idempotency-key': orden.claveIdempotencia,
        },
        body: JSON.stringify(orden),
        signal: AbortSignal.timeout(this.timeoutIntentoMs),
      });
      const texto = await res.text();
      let cuerpo: unknown = texto;
      try {
        cuerpo = JSON.parse(texto);
      } catch {
        /* respuesta no JSON (p. ej. 502 del ALB) */
      }
      return {
        status: res.status,
        cuerpo,
        error: res.ok ? undefined : `HTTP ${res.status}`,
      };
    } catch (err) {
      const e = err as Error & { cause?: { code?: string } };
      return { status: null, error: e.cause?.code ?? e.name ?? String(err) };
    }
  }
}
