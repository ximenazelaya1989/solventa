import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Cliente } from './entities/cliente.entity';
import { IdentidadCredencial } from './entities/identidad-credencial.entity';

@Injectable()
export class IdentidadService {
  constructor(
    @InjectRepository(Cliente)
    private readonly clienteRepository: Repository<Cliente>,
    @InjectRepository(IdentidadCredencial)
    private readonly credencialRepository: Repository<IdentidadCredencial>,
  ) {}

  // TODO(identidad): implementar por el dueño del modulo
  async registrar(nombre: string, documentoIdentidad: string): Promise<Cliente> {
    throw new Error('No implementado');
  }

  // TODO(identidad): implementar por el dueño del modulo (llamar al Orquestador
  // -- src/integraciones -- con timeout duro de 700ms, HU3.1.1)
  async verificarKyc(clienteId: string): Promise<IdentidadCredencial> {
    throw new Error('No implementado');
  }
}
