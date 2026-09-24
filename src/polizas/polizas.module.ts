import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { Poliza } from './entities/poliza.entity';
import { PolizasService } from './polizas.service';
import { PagosModule } from '../pagos/pagos.module';

@Module({
  imports: [TypeOrmModule.forFeature([Poliza]), PagosModule],
  providers: [PolizasService],
  exports: [PolizasService],
})
export class PolizasModule {}