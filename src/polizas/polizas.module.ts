import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { Poliza } from './entities/poliza.entity';
import { Subscripcion } from './entities/subscripcion.entity';

@Module({
  imports: [TypeOrmModule.forFeature([Poliza, Subscripcion])],
})
export class PolizasModule {}