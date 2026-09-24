import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import {
  Consentimiento,
  EstadoConsentimiento,
} from './entities/consentimiento.entity';

@Injectable()
export class ConsentimientoService {
  constructor(
    @InjectRepository(Consentimiento)
    private readonly consentimientoRepository: Repository<Consentimiento>,
  ) {}

  async tieneConsentimientoActivo(
    clienteId: string,
    alcance: string,
  ): Promise<boolean> {
    const consentimiento = await this.consentimientoRepository.findOneBy({
      clienteId,
      alcance,
      estado: EstadoConsentimiento.ACTIVO,
    });
    return consentimiento !== null;
  }

  // TODO(consentimiento): implementar por el dueño del modulo
  async otorgar(
    clienteId: string,
    fuente: string,
    alcance: string,
  ): Promise<Consentimiento> {
    throw new Error('No implementado');
  }

  // TODO(consentimiento): implementar por el dueño del modulo (revocacion efectiva <= 5min, HU3.2.1)
  async revocar(id: string): Promise<Consentimiento> {
    throw new Error('No implementado');
  }

  // TODO(consentimiento): implementar por el dueño del modulo
  async consultar(clienteId: string): Promise<Consentimiento[]> {
    throw new Error('No implementado');
  }
}
