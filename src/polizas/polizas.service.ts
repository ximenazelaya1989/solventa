import { ConflictException, Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { EntityManager, Repository } from 'typeorm';
import { Poliza, EstadoPoliza } from './entities/poliza.entity';
import { EmitirPolizaDto } from './dto/emitir-poliza.dto';
import { PagosService } from '../pagos/pagos.service';

@Injectable()
export class PolizasService {
  constructor(
    @InjectRepository(Poliza)
    private readonly polizaRepository: Repository<Poliza>,
    private readonly pagosService: PagosService,
  ) {}

  // Emite la poliza y cobra la prima dentro de la MISMA transaccion (mismo
  // manager) que le pasa quien invoca. suscripcion -> polizas -> pagos: quien
  // decide la suscripcion ya no llama a Pagos directamente.
  async emitir(manager: EntityManager, datos: EmitirPolizaDto): Promise<Poliza> {
    const repository = manager.getRepository(Poliza);
    const poliza = repository.create({
      estado: EstadoPoliza.EMITIDA,
      clienteId: datos.clienteId,
      productoId: datos.productoId,
    });
    const emitida = await repository.save(poliza);

    await this.pagosService.cobrarPrima(manager, emitida.id, datos.monto);

    return emitida;
  }

  // Usado por Suscripcion cuando la decision es revision_asistida: la poliza
  // queda pendiente (sin cobro) dentro de la misma transaccion de emision.
  async registrarPendiente(
    manager: EntityManager,
    datos: { clienteId: string; productoId: string },
  ): Promise<Poliza> {
    const repository = manager.getRepository(Poliza);
    const poliza = repository.create({
      estado: EstadoPoliza.PENDIENTE,
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