import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Reaseguradora } from './entities/reaseguradora.entity';
import { CesionPoliza } from './entities/cesion-poliza.entity';
import { PolizasService } from '../polizas/polizas.service';

@Injectable()
export class ReaseguroService {
  constructor(
    @InjectRepository(Reaseguradora)
    private readonly reaseguradoraRepository: Repository<Reaseguradora>,
    @InjectRepository(CesionPoliza)
    private readonly cesionPolizaRepository: Repository<CesionPoliza>,
    private readonly polizasService: PolizasService,
  ) {}

  // TODO(reaseguro): implementar por el dueño del modulo (las cesiones se
  // generan en el batch, no en la emision de la poliza)
  async registrarCesiones(): Promise<void> {
    throw new Error('No implementado');
  }
}
