import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { Reaseguradora } from './entities/reaseguradora.entity';
import { CesionPoliza } from './entities/cesion-poliza.entity';
import { ReaseguroService } from './reaseguro.service';
import { ReaseguroController } from './reaseguro.controller';
import { PolizasModule } from '../polizas/polizas.module';

@Module({
  imports: [
    TypeOrmModule.forFeature([Reaseguradora, CesionPoliza]),
    PolizasModule,
  ],
  controllers: [ReaseguroController],
  providers: [ReaseguroService],
  exports: [ReaseguroService],
})
export class ReaseguroModule {}
