import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { Desembolso } from './entities/desembolso.entity';
import { Reaseguradora } from './entities/reaseguradora.entity';
import { ReporteReaseguro } from './entities/reporte-reaseguro.entity';

@Module({
  imports: [
    TypeOrmModule.forFeature([Desembolso, Reaseguradora, ReporteReaseguro]),
  ],
})
export class PagosModule {}
