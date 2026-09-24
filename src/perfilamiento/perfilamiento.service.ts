import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { PerfilRiesgo } from './entities/perfil-riesgo.entity';
import { ReprocesarPerfilDto } from './dto/reprocesar-perfil.dto';

@Injectable()
export class PerfilamientoService {
  constructor(
    @InjectRepository(PerfilRiesgo)
    private readonly perfilRiesgoRepository: Repository<PerfilRiesgo>,
  ) {}

  // TODO(perfilamiento): calcularPerfil(), recalcularTodos() y el resto de la
  // logica de negocio del modulo se definen en el Paso 5
  async obtenerScore(perfilRiesgoId: string): Promise<number> {
    const perfil = await this.perfilRiesgoRepository.findOneByOrFail({
      id: perfilRiesgoId,
    });
    return perfil.score;
  }

  async reprocesar(dto: ReprocesarPerfilDto): Promise<PerfilRiesgo> {
    const score = this.calcularScore(dto.señalesOpenData);
    const resultado = await this.perfilRiesgoRepository.upsert(
      {
        clienteId: dto.clienteId,
        score,
        // TypeORM tipa los valores JSONB como un deep-partial; el DTO ya fue
        // validado por ValidationPipe antes de llegar a este punto.
        señalesOpenFinance: dto.señalesOpenData as any,
      },
      ['clienteId'],
    );

    return this.perfilRiesgoRepository.findOneByOrFail({
      id: resultado.identifiers[0].id as string,
    });
  }

  private calcularScore(
    señales: ReprocesarPerfilDto['señalesOpenData'],
  ): number {
    const ingresoNormalizado = Math.min(señales.ingresoMensual / 20_000_000, 1);
    const deudaNormalizada = Math.min(señales.deudaTotal / 100_000_000, 1);
    const score =
      100 *
      (0.45 * ingresoNormalizado +
        0.35 * señales.indicePago +
        0.2 * (1 - deudaNormalizada));

    return Math.round(Math.max(0, Math.min(score, 100)) * 100) / 100;
  }
}
