import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { PerfilRiesgo } from './entities/perfil-riesgo.entity';
import { IdentidadService } from '../identidad/identidad.service';
import { ConsentimientoService } from '../consentimiento/consentimiento.service';

@Injectable()
export class PerfilamientoService {
  constructor(
    @InjectRepository(PerfilRiesgo)
    private readonly perfilRiesgoRepository: Repository<PerfilRiesgo>,
    private readonly identidadService: IdentidadService,
    private readonly consentimientoService: ConsentimientoService,
  ) {}

  async obtenerScore(perfilRiesgoId: string): Promise<number> {
    const perfil = await this.perfilRiesgoRepository.findOneByOrFail({
      id: perfilRiesgoId,
    });
    return perfil.score;
  }

  // TODO(perfilamiento): implementar por el dueño del modulo -- solo calcular
  // si this.consentimientoService.tieneConsentimientoActivo(clienteId, alcance)
  // es true (score simple, formula por definir)
  async calcularPerfil(clienteId: string): Promise<PerfilRiesgo> {
    throw new Error('No implementado');
  }

  // TODO(perfilamiento): implementar por el dueño del modulo (job de batch,
  // HU4.3.1: >=10M perfiles en <2h sin afectar el canal en linea)
  async recalcularTodos(): Promise<void> {
    throw new Error('No implementado');
  }
}
