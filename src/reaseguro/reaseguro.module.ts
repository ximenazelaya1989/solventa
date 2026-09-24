import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { Reaseguradora } from './entities/reaseguradora.entity';
import { CesionPoliza } from './entities/cesion-poliza.entity';

@Module({
  imports: [TypeOrmModule.forFeature([Reaseguradora, CesionPoliza])],
})
export class ReaseguroModule {}
