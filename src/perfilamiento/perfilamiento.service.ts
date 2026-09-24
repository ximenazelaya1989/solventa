import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { PerfilRiesgo } from './entities/perfil-riesgo.entity';

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
}
