import {
  CanActivate,
  ExecutionContext,
  HttpException,
  Injectable,
  Logger,
  OnModuleDestroy,
} from '@nestjs/common';
import { createHash } from 'crypto';
import { TokenBucket } from './token-bucket';

// EXP-008 (HU5.1.2, Daniela): cuota por socio en el API Gateway.
//
// Tactica: limitacion de tasa por socio con token bucket en Redis. Cada socio
// se identifica por su credencial (encabezado x-api-key) y tiene su propio
// balde, asi que el pico de uno no consume la capacidad de los demas. El exceso
// se rechaza aqui con 429 y Retry-After, antes de llegar a Cotizacion y
// Perfilamiento.
//
// Apagado por defecto (RATE_LIMIT_ENABLED=false): con el flag apagado el guard
// deja pasar todo y el gateway se comporta como la base compartida.
const ENCABEZADO_SOCIO = 'x-api-key';

@Injectable()
export class CuotaSocioGuard implements CanActivate, OnModuleDestroy {
  private readonly logger = new Logger('CuotaSocio');
  private readonly activo = process.env.RATE_LIMIT_ENABLED === 'true';
  private readonly tasa = Number(process.env.RATE_LIMIT_RPS ?? '20');
  private readonly capacidad = Math.max(
    1,
    Math.round(this.tasa * Number(process.env.RATE_LIMIT_BURST_S ?? '2')),
  );
  private readonly balde?: TokenBucket;
  private readonly conteo = new Map<string, { aceptadas: number; rechazadas: number }>();
  private fallosRedis = 0;
  private readonly reporte?: NodeJS.Timeout;

  constructor() {
    if (!this.activo) return;
    this.balde = new TokenBucket(
      process.env.REDIS_URL ?? 'redis://localhost:6379/1',
      Number(process.env.RATE_LIMIT_REDIS_TIMEOUT_MS ?? '50'),
    );
    this.logger.log(
      `Cuota por socio activa: ${this.tasa} peticiones/s y rafaga de ${this.capacidad} por socio`,
    );
    // Resumen cada 10 s en el log (evidencia en CloudWatch sin escribir una
    // linea por peticion).
    this.reporte = setInterval(() => this.reportar(), 10_000);
    this.reporte.unref();
  }

  async canActivate(contexto: ExecutionContext): Promise<boolean> {
    if (!this.activo || !this.balde) return true;
    const peticion = contexto.switchToHttp().getRequest();
    const respuesta = contexto.switchToHttp().getResponse();
    if (!String(peticion.path ?? peticion.url).startsWith('/v1/')) return true; // /health libre

    const credencial = peticion.headers[ENCABEZADO_SOCIO];
    if (typeof credencial !== 'string' || credencial.length === 0) {
      throw new HttpException('Falta la credencial del socio (x-api-key)', 401);
    }
    // En Redis y en el log solo va un resumen de la credencial, nunca la clave.
    const socio = createHash('sha256').update(credencial).digest('hex').slice(0, 12);

    let resultado;
    try {
      resultado = await this.balde.tomar(`cuota:${socio}`, this.tasa, this.capacidad);
    } catch {
      // Si Redis falla o tarda mas que el timeout, se deja pasar (fail-open):
      // el limitador no debe convertirse en el punto unico de falla de la venta.
      this.fallosRedis++;
      return true;
    }

    const c = this.conteo.get(socio) ?? { aceptadas: 0, rechazadas: 0 };
    respuesta.setHeader('X-RateLimit-Limit', String(this.tasa));
    respuesta.setHeader('X-RateLimit-Remaining', String(resultado.restantes));
    if (resultado.permitido) {
      c.aceptadas++;
      this.conteo.set(socio, c);
      return true;
    }
    c.rechazadas++;
    this.conteo.set(socio, c);
    respuesta.setHeader('Retry-After', String(Math.max(1, Math.ceil(resultado.esperaMs / 1000))));
    throw new HttpException({ statusCode: 429, message: 'Cuota del socio excedida', socio }, 429);
  }

  private reportar() {
    if (this.conteo.size === 0 && this.fallosRedis === 0) return;
    const partes = [...this.conteo.entries()].map(
      ([socio, c]) => `${socio} aceptadas=${c.aceptadas} rechazadas=${c.rechazadas}`,
    );
    if (this.fallosRedis > 0) partes.push(`fallos_redis=${this.fallosRedis}`);
    this.logger.log(`Ultimos 10 s: ${partes.join(' | ')}`);
    this.conteo.clear();
    this.fallosRedis = 0;
  }

  onModuleDestroy() {
    if (this.reporte) clearInterval(this.reporte);
  }
}
