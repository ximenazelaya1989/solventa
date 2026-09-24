import { ConflictException, Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { EntityManager, Repository } from 'typeorm';
import { Poliza, EstadoPoliza } from './entities/poliza.entity';
import { EmitirPolizaDto } from './dto/emitir-poliza.dto';

@Injectable()
export class PolizasService {
  constructor(
    @InjectRepository(Poliza)
    private readonly polizaRepository: Repository<Poliza>,
  ) {}

  async emitir(manager: EntityManager, datos: EmitirPolizaDto): Promise<Poliza> {
    const repository = manager.getRepository(Poliza);
    const poliza = repository.create({
      estado: EstadoPoliza.EMITIDA,
      clienteId: datos.clienteId,
      productoId: datos.productoId,
    });

    return repository.save(poliza);
  }

  async renovar(id: string, version: number): Promise<Poliza> {
    const poliza = await this.polizaRepository.findOneByOrFail({ id });
    if (poliza.version !== version) {
      throw new ConflictException('La version de la poliza no coincide');
    }
    poliza.estado = EstadoPoliza.RENOVADA;
    return this.polizaRepository.save(poliza);
  }

  async cancelar(id: string, version: number): Promise<Poliza> {
    const poliza = await this.polizaRepository.findOneByOrFail({ id });
    if (poliza.version !== version) {
      throw new ConflictException('La version de la poliza no coincide');
    }
    poliza.estado = EstadoPoliza.CANCELADA;
    return this.polizaRepository.save(poliza);
  }
}