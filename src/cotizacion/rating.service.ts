import { Injectable, Logger, OnModuleInit } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { ReglaRating } from './entities/regla-rating.entity';

// HU1.1.2 exige deteccion de falla <= 60s. Dejamos margen para
// demostrarlo con holgura durante el experimento (30s).
const UMBRAL_ROLLBACK_MS = 30000;
const FACTOR_MIN = 0.5;
const FACTOR_MAX = 5;

export interface EstadoRating {
  status: 'ok' | 'unhealthy';
  versionCargada: number | null;
  saludable: boolean;
  motivo?: string;
}

/**
 * Motor de rating (Pricing Service) de una instancia individual.
 * Cada replica del servicio tiene su propia instancia de este service,
 * con su propio estado en memoria: por eso el rollout es "instancia por
 * instancia" en vez de un cambio global instantaneo.
 */
@Injectable()
export class RatingService implements OnModuleInit {
  private readonly logger = new Logger(RatingService.name);
  private versionCargada: ReglaRating | null = null;
  private versionAnteriorSana: ReglaRating | null = null;
  private saludable = false;
  private rollbackProgramado: NodeJS.Timeout | null = null;

  constructor(
    @InjectRepository(ReglaRating)
    private readonly reglaRepository: Repository<ReglaRating>,
  ) {}

  async onModuleInit() {
    const ultima = await this.reglaRepository.find({
      order: { version: 'DESC' },
      take: 1,
    });

    if (ultima.length > 0) {
      await this.aplicarVersion(ultima[0].version);
      return;
    }

    // Bootstrap: si la tabla esta vacia (primer arranque del sistema),
    // publica y aplica una v1 segura por defecto.
    const v1 = await this.publicarNuevaVersion(
      { bajo: 1, medio: 1.3, alto: 1.8 },
      false,
    );
    await this.aplicarVersion(v1.version);
  }

  /** Escribe una nueva version en el almacen de configuracion compartido (Postgres). */
  async publicarNuevaVersion(factores: Record<string, number>, fallaSanityCheck = false) {
    const ultima = await this.reglaRepository.find({ order: { version: 'DESC' }, take: 1 });
    const siguienteVersion = (ultima[0]?.version ?? 0) + 1;

    const nueva = await this.reglaRepository.save(
      this.reglaRepository.create({ version: siguienteVersion, factores, fallaSanityCheck }),
    );
    this.logger.log(
      `[${new Date().toISOString()}] Publicada v${nueva.version} en el almacen de configuracion (fallaSanityCheck=${fallaSanityCheck})`,
    );
    return nueva;
  }

  async listarVersiones() {
    return this.reglaRepository.find({ order: { version: 'DESC' } });
  }

  /**
   * Le dice A ESTA INSTANCIA que cargue una version especifica.
   * Este es el endpoint que el script de rolling update llama
   * instancia por instancia (nunca a todas a la vez).
   */
  async aplicarVersion(version: number) {
    const regla = await this.reglaRepository.findOneByOrFail({ version });

    const pasaSelfTest = this.ejecutarSelfTest(regla);
    const versionAnterior = this.versionCargada;
    this.versionCargada = regla;

    if (pasaSelfTest) {
      this.saludable = true;
      this.versionAnteriorSana = regla;
      if (this.rollbackProgramado) {
        clearTimeout(this.rollbackProgramado);
        this.rollbackProgramado = null;
      }
      this.logger.log(
        `[${new Date().toISOString()}] Instancia aplico v${regla.version}. Self-test OK. saludable=true`,
      );
      return this.health();
    }

    this.saludable = false;
    this.logger.warn(
      `[${new Date().toISOString()}] Instancia aplico v${regla.version}. Self-test FALLO. saludable=false. Rollback programado en ${UMBRAL_ROLLBACK_MS / 1000}s`,
    );
    this.programarRollback(regla, versionAnterior);
    return this.health();
  }

  calcularPrima(primaBase: number, nivelRiesgo: 'bajo' | 'medio' | 'alto') {
    if (!this.saludable || !this.versionCargada) {
      throw new Error('El motor de rating no tiene una version sana cargada en esta instancia');
    }
    const factor = this.versionCargada.factores[nivelRiesgo] ?? 1;
    return Number((primaBase * factor).toFixed(2));
  }

  estaSaludable() {
    return this.saludable;
  }

  health(): EstadoRating {
    return {
      status: this.saludable ? 'ok' : 'unhealthy',
      versionCargada: this.versionCargada?.version ?? null,
      saludable: this.saludable,
      ...(this.saludable ? {} : { motivo: 'la version cargada no paso el self-test' }),
    };
  }

  /** Health check sustantivo: valida coherencia de las reglas, no solo "proceso vivo". */
  private ejecutarSelfTest(regla: ReglaRating): boolean {
    if (regla.fallaSanityCheck) return false;
    const factores = Object.values(regla.factores);
    if (factores.length === 0) return false;
    return factores.every((f) => typeof f === 'number' && f >= FACTOR_MIN && f <= FACTOR_MAX);
  }

  private programarRollback(reglaMala: ReglaRating, versionAnterior: ReglaRating | null) {
    if (this.rollbackProgramado) clearTimeout(this.rollbackProgramado);

    this.rollbackProgramado = setTimeout(() => {
      if (this.versionCargada?.id !== reglaMala.id) return; // ya se resolvio de otra forma

      const objetivo = this.versionAnteriorSana ?? versionAnterior;
      if (!objetivo) {
        this.logger.error(
          `[${new Date().toISOString()}] No hay version sana previa para hacer rollback en esta instancia.`,
        );
        return;
      }

      this.versionCargada = objetivo;
      this.saludable = true;
      this.logger.warn(
        `[${new Date().toISOString()}] Rollback automatico ejecutado: v${reglaMala.version} -> v${objetivo.version}. saludable=true`,
      );
    }, UMBRAL_ROLLBACK_MS);
  }
}